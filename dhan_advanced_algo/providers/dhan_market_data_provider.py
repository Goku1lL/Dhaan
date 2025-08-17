"""
Dhan market data provider implementation.
Implements IMarketDataProvider interface using Dhan API.
"""

import time
import requests
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime, timedelta

from ..core.interfaces import IMarketDataProvider
from ..core.entities import MarketData
from ..core.exceptions import MarketDataException, RateLimitException, ConnectionException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager


class DhanMarketDataProvider(IMarketDataProvider):
	"""
	Dhan market data provider implementation.
	Handles market data fetching from Dhan API with rate limiting and error handling.
	"""
	
	def __init__(self, tsl_client, config):
		"""
		Initialize Dhan market data provider.
		
		Args:
			tsl_client: Dhan TSL client instance
			config: Configuration manager instance
		"""
		self.tsl_client = tsl_client
		self.config = config
		self.logger = LoggingService()
		self.last_request_time = 0
		self.request_count = 0
		self.max_requests_per_minute = 30  # Reduced from 60 to be more conservative
		self.consecutive_429_errors = 0  # Track consecutive rate limit errors
		self.backoff_multiplier = 1.0  # Exponential backoff multiplier
		
		# Cache for scrip master mapping
		self._scrip_master_cache = {}
		self._scrip_master_cache_time = 0
		self._cache_validity_hours = 24  # Cache for 24 hours
		
		self.logger.info("Dhan Market Data Provider initialized")
	
	def _rate_limit_check(self) -> None:
		"""Check and enforce rate limiting with intelligent backoff."""
		current_time = time.time()
		time_diff = current_time - self.last_request_time
		
		# Apply exponential backoff if we've had recent 429 errors
		effective_delay = self.config.broker.rate_limit_delay * self.backoff_multiplier
		
		# Enforce minimum delay between requests
		if time_diff < effective_delay:
			sleep_time = effective_delay - time_diff
			time.sleep(sleep_time)
		
		# Check requests per minute limit
		if time_diff >= 60:  # Reset counter after 1 minute
			self.request_count = 0
			self.last_request_time = current_time
			# Gradually reduce backoff if no recent errors
			if self.consecutive_429_errors > 0:
				self.consecutive_429_errors = max(0, self.consecutive_429_errors - 1)
				self.backoff_multiplier = max(1.0, self.backoff_multiplier * 0.9)
		elif self.request_count >= self.max_requests_per_minute:
			sleep_time = 60 - time_diff
			self.logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
			time.sleep(sleep_time)
			self.request_count = 0
			self.last_request_time = time.time()
		
		self.request_count += 1
		self.last_request_time = time.time()
	
	def _handle_rate_limit_error(self) -> None:
		"""Handle rate limit errors with exponential backoff."""
		self.consecutive_429_errors += 1
		self.backoff_multiplier = min(5.0, 1.0 + (self.consecutive_429_errors * 0.5))
		
		# Force a longer sleep for rate limit errors
		backoff_sleep = self.config.broker.rate_limit_delay * self.backoff_multiplier
		self.logger.warning(f"Rate limit error detected. Applying {backoff_sleep:.1f}s delay (backoff: {self.backoff_multiplier:.1f}x)")
		time.sleep(backoff_sleep)
	
	def _handle_api_error(self, error: Exception, operation: str) -> None:
		"""Handle API errors and raise appropriate exceptions."""
		error_msg = str(error).lower()
		
		if "rate limit" in error_msg or "too many requests" in error_msg:
			raise RateLimitException(f"Rate limit exceeded during {operation}: {str(error)}")
		elif "connection" in error_msg or "timeout" in error_msg:
			raise ConnectionException(f"Connection error during {operation}: {str(error)}")
		else:
			raise MarketDataException(f"API error during {operation}: {str(error)}")
	
	def get_ltp(self, symbol: str) -> Optional[Decimal]:
		"""
		Get Last Traded Price for a symbol.
		
		Args:
			symbol: Trading symbol
			
		Returns:
			Last traded price as Decimal or None if failed
			
		Raises:
			MarketDataException: If API call fails
			RateLimitException: If rate limit exceeded
			ConnectionException: If connection fails
		"""
		try:
			self._rate_limit_check()
			
			self.logger.debug(f"Fetching LTP for symbol: {symbol}")
			
			# Use Dhan service to get market data
			market_data = self.tsl_client.get_market_data(symbol)
			
			if not market_data or "lastPrice" not in market_data:
				self.logger.warning(f"No market data received for symbol: {symbol}")
				return None
			
			ltp_value = market_data["lastPrice"]
			
			if ltp_value is None or ltp_value <= 0:
				self.logger.warning(f"Invalid LTP value for symbol {symbol}: {ltp_value}")
				return None
			
			ltp_decimal = Decimal(str(ltp_value))
			self.logger.debug(f"LTP for {symbol}: {ltp_decimal}")
			
			return ltp_decimal
			
		except Exception as e:
			self.logger.error(f"Failed to get LTP for {symbol}: {str(e)}")
			self._handle_api_error(e, f"get_ltp for {symbol}")
	
	def get_market_data(self, symbol: str) -> Optional[MarketData]:
		"""
		Get market data for a symbol.
		
		Args:
			symbol: Trading symbol
			
		Returns:
			Market data or None if not available
		"""
		try:
			# Get LTP from Dhan provider
			ltp = self.get_ltp(symbol)
			if ltp is None:
				return None
			
			# Create market data from LTP
			market_data = MarketData(
				symbol=symbol,
				ltp=ltp,
				open_price=ltp,  # Use LTP as fallback
				high_price=ltp,
				low_price=ltp,
				close_price=ltp,
				volume=0,  # Not available from LTP
				timestamp=datetime.now()
			)
			
			return market_data
			
		except Exception as e:
			self.logger.log_error(e, {
				"operation": "get_market_data", 
				"symbol": symbol
			})
			return None
	
	def get_ohlcv(self, symbol: str, interval: str = "1D", limit: int = 100) -> List:
		"""
		Get OHLCV data for a symbol.
		
		Args:
			symbol: Trading symbol
			interval: Time interval (1D, 1H, 15M, etc.)
			limit: Number of candles to fetch
			
		Returns:
			List of OHLCV data dictionaries
		"""
		try:
			self._rate_limit_check()
			
			# Get security ID from scrip master
			security_id = self._get_security_id(symbol)
			if not security_id:
				self.logger.log_error(
					Exception(f"Symbol {symbol} not found in scrip master"), 
					{"operation": "get_ohlcv", "symbol": symbol}
				)
				return []
			
			# Build request payload using security ID
			payload = {
				"securityId": security_id,  # Use numeric security ID from scrip master
				"exchangeSegment": "NSE_EQ",
				"instrument": "EQUITY"
			}
			
			# Make API request
			endpoint = "/charts/intraday"
			response = self.tsl_client._make_request(endpoint, method="POST", data=payload)
			
			if not response or not isinstance(response, dict):
				return []
			
			# Parse response data
			data = response.get("data", {})
			opens = data.get("opens", [])
			highs = data.get("highs", [])
			lows = data.get("lows", [])
			closes = data.get("closes", [])
			volumes = data.get("volumes", [])
			timestamps = data.get("timestamps", [])
			
			# Validate data arrays
			if not all([opens, highs, lows, closes, volumes, timestamps]):
				return []
			
			# Build OHLCV candles
			candles = []
			for i in range(min(len(opens), limit)):
				try:
					# Handle different timestamp formats
					timestamp = timestamps[i]
					if isinstance(timestamp, (int, float)):
						# Convert epoch timestamp to ISO format
						from datetime import datetime
						timestamp = datetime.fromtimestamp(timestamp / 1000).isoformat()
					
					candle = {
						"timestamp": timestamp,
						"open": float(opens[i]),
						"high": float(highs[i]),
						"low": float(lows[i]),
						"close": float(closes[i]),
						"volume": int(volumes[i])
					}
					candles.append(candle)
				except (ValueError, IndexError) as e:
					self.logger.log_error(e, {
						"operation": "parse_ohlcv_candle",
						"symbol": symbol,
						"index": i
					})
					continue
			
			return candles
			
		except Exception as e:
			# Check if it's a rate limit error and handle accordingly
			error_msg = str(e).lower()
			if "rate limit" in error_msg or "429" in error_msg or "too many requests" in error_msg:
				self._handle_rate_limit_error()
			else:
				self.logger.log_error(e, {
					"operation": "get_ohlcv",
					"symbol": symbol,
					"interval": interval
				})
			return []
	
	def get_ltp_bulk(self, symbols: List[str]) -> Dict[str, Decimal]:
		"""
		Get LTP for multiple symbols in bulk.
		
		Args:
			symbols: List of trading symbols
			
		Returns:
			Dictionary mapping symbols to their LTP values
			
		Raises:
			MarketDataException: If API call fails
			RateLimitException: If rate limit exceeded
			ConnectionException: If connection fails
		"""
		try:
			self._rate_limit_check()
			
			if not symbols:
				return {}
			
			self.logger.debug(f"Fetching bulk LTP for {len(symbols)} symbols")
			
			# Get market data for each symbol (no bulk method available)
			result = {}
			for symbol in symbols:
				try:
					market_data = self.tsl_client.get_market_data(symbol)
					if market_data and "lastPrice" in market_data:
						ltp_value = market_data["lastPrice"]
						if ltp_value > 0:
							result[symbol] = Decimal(str(ltp_value))
						else:
							self.logger.warning(f"Invalid LTP value for symbol {symbol}: {ltp_value}")
					else:
						self.logger.warning(f"No market data for symbol: {symbol}")
				except Exception as e:
					self.logger.warning(f"Failed to get LTP for {symbol}: {e}")
					
				# Rate limiting for individual calls
				time.sleep(self.config.broker.rate_limit_delay)  # Use configured delay instead of hardcoded 0.1
			
			self.logger.debug(f"Bulk LTP fetched successfully for {len(result)} symbols")
			return result
			
		except Exception as e:
			self.logger.error(f"Failed to get bulk LTP: {str(e)}")
			self._handle_api_error(e, "get_ltp_bulk")
	
	def get_historical_data(self, symbol: str, timeframe: str, count: int) -> List[MarketData]:
		"""
		Get historical market data for a symbol.
		
		Args:
			symbol: Trading symbol
			timeframe: Timeframe (e.g., '5min', '1day')
			count: Number of candles to fetch
			
		Returns:
			List of MarketData objects
			
		Raises:
			MarketDataException: If API call fails
			RateLimitException: If rate limit exceeded
			ConnectionException: If connection fails
		"""
		try:
			self._rate_limit_check()
			
			self.logger.debug(f"Fetching historical data for {symbol}, timeframe: {timeframe}, count: {count}")
			
			# Map timeframe to Dhan API format
			timeframe_map = {
				'1min': '1min',
				'5min': '5min',
				'15min': '15min',
				'30min': '30min',
				'1hour': '1hour',
				'1day': '1day'
			}
			
			dhan_timeframe = timeframe_map.get(timeframe, '5min')
			
			# Historical data not available from DhanService for now
			self.logger.debug(f"Historical data requested for {symbol} but not available")
			return []
			
			# Convert to MarketData objects
			market_data_list = []
			for candle in historical_data:
				try:
					market_data = MarketData(
						symbol=symbol,
						open=Decimal(str(candle.get('open', 0))),
						high=Decimal(str(candle.get('high', 0))),
						low=Decimal(str(candle.get('low', 0))),
						close=Decimal(str(candle.get('close', 0))),
						volume=int(candle.get('volume', 0)),
						timestamp=datetime.fromisoformat(candle.get('timestamp', datetime.now().isoformat())),
						ltp=Decimal(str(candle.get('close', 0)))  # Use close as LTP for historical data
					)
					market_data_list.append(market_data)
				except Exception as e:
					self.logger.warning(f"Failed to parse candle data for {symbol}: {str(e)}")
					continue
			
			self.logger.debug(f"Historical data fetched successfully for {symbol}: {len(market_data_list)} candles")
			return market_data_list
			
		except Exception as e:
			self.logger.error(f"Failed to get historical data for {symbol}: {str(e)}")
			self._handle_api_error(e, f"get_historical_data for {symbol}")
	
	def is_market_open(self) -> bool:
		"""
		Check if market is currently open.
		
		Returns:
			True if market is open, False otherwise
		"""
		try:
			current_time = datetime.now()
			current_time_str = current_time.strftime("%H:%M")
			
			# Get market hours from config
			market_open = self.config.market.market_open_time
			market_close = self.config.market.market_close_time
			
			# Simple time-based check (can be enhanced with holiday calendar)
			is_open = market_open <= current_time_str <= market_close
			
			self.logger.debug(f"Market status check: {current_time_str}, Open: {is_open}")
			return is_open
			
		except Exception as e:
			self.logger.error(f"Failed to check market status: {str(e)}")
			# Default to closed if check fails
			return False
	
	def get_market_status(self) -> Dict[str, any]:
		"""
		Get detailed market status information.
		
		Returns:
			Dictionary containing market status details
		"""
		try:
			current_time = datetime.now()
			current_time_str = current_time.strftime("%H:%M")
			
			market_open = self.config.market.market_open_time
			market_close = self.config.market.market_close_time
			pre_market_start = self.config.market.pre_market_start
			post_market_end = self.config.market.post_market_end
			
			# Determine market phase
			if pre_market_start <= current_time_str < market_open:
				phase = "PRE_MARKET"
			elif market_open <= current_time_str <= market_close:
				phase = "MARKET_OPEN"
			elif market_close < current_time_str <= post_market_end:
				phase = "POST_MARKET"
			else:
				phase = "MARKET_CLOSED"
			
			# Calculate time to next phase
			time_to_next = self._calculate_time_to_next_phase(current_time_str, phase)
			
			status = {
				'current_time': current_time_str,
				'market_phase': phase,
				'is_trading': phase == "MARKET_OPEN",
				'time_to_next_phase': time_to_next,
				'market_open_time': market_open,
				'market_close_time': market_close,
				'pre_market_start': pre_market_start,
				'post_market_end': post_market_end
			}
			
			self.logger.debug(f"Market status: {status}")
			return status
			
		except Exception as e:
			self.logger.error(f"Failed to get market status: {str(e)}")
			return {
				'current_time': datetime.now().strftime("%H:%M"),
				'market_phase': "UNKNOWN",
				'is_trading': False,
				'error': str(e)
			}
	
	def _calculate_time_to_next_phase(self, current_time: str, current_phase: str) -> str:
		"""Calculate time to next market phase."""
		try:
			current = datetime.strptime(current_time, "%H:%M")
			
			if current_phase == "PRE_MARKET":
				next_time = datetime.strptime(self.config.market.market_open_time, "%H:%M")
			elif current_phase == "MARKET_OPEN":
				next_time = datetime.strptime(self.config.market.market_close_time, "%H:%M")
			elif current_phase == "POST_MARKET":
				next_time = datetime.strptime(self.config.market.pre_market_start, "%H:%M")
				next_time += timedelta(days=1)  # Next day
			else:  # MARKET_CLOSED
				next_time = datetime.strptime(self.config.market.pre_market_start, "%H:%M")
				next_time += timedelta(days=1)  # Next day
			
			time_diff = next_time - current
			if time_diff.total_seconds() < 0:
				time_diff += timedelta(days=1)
			
			hours = int(time_diff.total_seconds() // 3600)
			minutes = int((time_diff.total_seconds() % 3600) // 60)
			
			return f"{hours:02d}:{minutes:02d}"
			
		except Exception as e:
			self.logger.warning(f"Failed to calculate time to next phase: {str(e)}")
			return "00:00"
	
	def get_symbol_info(self, symbol: str) -> Optional[Dict[str, any]]:
		"""
		Get basic information about a trading symbol.
		
		Args:
			symbol: Trading symbol
			
		Returns:
			Dictionary containing symbol information or None if failed
		"""
		try:
			self._rate_limit_check()
			
			# This would typically call a different API endpoint
			# For now, return basic info
			info = {
				'symbol': symbol,
				'exchange': 'NSE',  # Default to NSE
				'instrument_type': 'EQ',  # Default to Equity
				'lot_size': 1,
				'tick_size': 0.05,
				'last_updated': datetime.now().isoformat()
			}
			
			self.logger.debug(f"Symbol info for {symbol}: {info}")
			return info
			
		except Exception as e:
			self.logger.error(f"Failed to get symbol info for {symbol}: {str(e)}")
			return None
	
	def validate_symbol(self, symbol: str) -> bool:
		"""
		Validate if a symbol is valid and tradeable.
		
		Args:
			symbol: Trading symbol to validate
			
		Returns:
			True if symbol is valid, False otherwise
		"""
		try:
			# Try to get LTP - if it fails, symbol might be invalid
			ltp = self.get_ltp(symbol)
			return ltp is not None and ltp > 0
			
		except Exception as e:
			self.logger.debug(f"Symbol validation failed for {symbol}: {str(e)}")
			return False 
	
	def _fetch_scrip_master(self) -> Dict[str, str]:
		"""
		Fetch Dhan's scrip master to map trading symbols to security IDs.
		"""
		try:
			# Check if cache is still valid
			current_time = time.time()
			if (self._scrip_master_cache and 
				current_time - self._scrip_master_cache_time < self._cache_validity_hours * 3600):
				return self._scrip_master_cache
			
			# Fetch fresh scrip master
			url = "https://images.dhan.co/api-data/api-scrip-master.csv"
			response = requests.get(url, timeout=30)
			response.raise_for_status()
			
			# Parse CSV and build mapping
			lines = response.text.strip().split('\n')
			symbol_to_security_id = {}
			
			self.logger.info(f"Parsing {len(lines)} lines from scrip master")
			
			# Look for NSE equity symbols throughout the entire CSV
			nse_count = 0
			major_stocks = ["RELIANCE", "TCS", "HDFC", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN", 
						   "BHARTIARTL", "AXISBANK", "ASIANPAINT", "MARUTI", "HCLTECH", "ULTRACEMCO"]
			
			# First pass: look for major stocks specifically
			for i, line in enumerate(lines[1:]):  # Skip header
				parts = line.split(',')
				if len(parts) >= 6:
					exchange = parts[0].strip()
					segment = parts[1].strip()
					security_id = parts[2].strip()
					instrument_name = parts[3].strip()
					trading_symbol = parts[5].strip()
					
					# Only include NSE equity symbols
					if exchange == "NSE" and instrument_name == "EQUITY":
						symbol_to_security_id[trading_symbol] = security_id
						nse_count += 1
						
						# Log major stock mappings
						if trading_symbol in major_stocks:
							self.logger.info(f"Found major stock: {trading_symbol} -> {security_id}")
						
						# Log first few NSE entries for debugging
						if nse_count <= 10:
							self.logger.info(f"Added NSE mapping: {trading_symbol} -> {security_id}")
			
			self.logger.info(f"Scrip master updated with {len(symbol_to_security_id)} NSE equity symbols")
			self.logger.info(f"Major stocks found: {[s for s in major_stocks if s in symbol_to_security_id]}")
			
			# Update cache
			self._scrip_master_cache = symbol_to_security_id
			self._scrip_master_cache_time = current_time
			return symbol_to_security_id
			
		except Exception as e:
			self.logger.log_error(e, {"operation": "fetch_scrip_master"})
			# Return empty dict if fetch fails
			return {}
	
	def _get_security_id(self, symbol: str) -> Optional[str]:
		"""
		Get security ID for a trading symbol.
		"""
		scrip_master = self._fetch_scrip_master()
		return scrip_master.get(symbol) 