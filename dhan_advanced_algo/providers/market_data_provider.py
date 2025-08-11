"""
Market Data Provider implementation.
Handles market data fetching, caching, and management from various sources.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
import json

from ..core.interfaces import IMarketDataProvider
from ..core.entities import MarketData, OHLCV, Symbol
from ..core.exceptions import MarketDataException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager
from .dhan_market_data_provider import DhanMarketDataProvider


class MarketDataProvider(IMarketDataProvider):
    """
    Market data provider implementation.
    Handles market data fetching, caching, and management from various sources.
    """

    def __init__(self, config: ConfigurationManager, dhan_client=None):
        """
        Initialize market data provider.

        Args:
            config: Configuration manager instance
            dhan_client: Dhan API client instance (optional)
        """
        self.config = config
        self.logger = LoggingService()

        # Data storage
        self.market_data_cache: Dict[str, MarketData] = {}
        self.ohlcv_cache: Dict[str, List[OHLCV]] = {}
        self.symbols: Dict[str, Symbol] = {}
        
        # Configuration
        self.cache_timeout_seconds = getattr(config.market_data, 'cache_timeout_seconds', 300)
        self.max_cache_size = getattr(config.market_data, 'max_cache_size', 1000)
        self.update_interval_seconds = getattr(config.market_data, 'update_interval_seconds', 60)

        # Connection status
        self.is_connected = False
        self.last_update = None
        self.update_task = None

        # Initialize Dhan provider if client is available
        self.dhan_provider = None
        if dhan_client:
            try:
                self.dhan_provider = DhanMarketDataProvider(dhan_client, config)
                self.logger.info("Dhan Market Data Provider initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Dhan provider: {e}")

        self.logger.info("Market Data Provider initialized")

    def initialize(self) -> None:
        """Initialize market data provider components."""
        try:
            # Load symbols
            self._load_symbols()
            
            # Initialize cache
            self._initialize_cache()
            
            # Start data update loop
            self._start_update_loop()
            
            self.logger.info("Market Data Provider initialized successfully")
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize"})
            raise MarketDataException(f"Failed to initialize market data provider: {str(e)}")

    def connect(self) -> bool:
        """
        Connect to market data source.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Try to connect to Dhan provider first
            if self.dhan_provider:
                self.is_connected = True
                self.last_update = datetime.now()
                self.logger.info("Connected to Dhan market data source")
                return True
            
            # Fallback to basic connection
            self.is_connected = True
            self.last_update = datetime.now()
            self.logger.info("Connected to market data source (basic mode)")
            return True

        except Exception as e:
            self.logger.log_error(e, {"operation": "connect"})
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from market data source.

        Returns:
            True if disconnected successfully, False otherwise
        """
        try:
            # Stop update loop
            if self.update_task:
                self.update_task.cancel()
                self.update_task = None

            self.is_connected = False
            self.logger.info("Disconnected from market data source")
            return True

        except Exception as e:
            self.logger.log_error(e, {"operation": "disconnect"})
            return False

    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """
        Get market data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Market data or None if not available
        """
        try:
            # Check cache first
            if symbol in self.market_data_cache:
                cached_data = self.market_data_cache[symbol]
                if self._is_cache_valid(cached_data):
                    return cached_data

            # Try to get data from Dhan provider
            if self.dhan_provider and self.is_connected:
                try:
                    # Get LTP from Dhan provider
                    ltp = self.dhan_provider.get_ltp(symbol)
                    if ltp is not None:
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
                        
                        # Update cache
                        self._update_cache(symbol, market_data)
                        return market_data
                except Exception as e:
                    self.logger.warning(f"Failed to get data from Dhan provider for {symbol}: {e}")

            # Return cached data if available (even if expired)
            if symbol in self.market_data_cache:
                return self.market_data_cache[symbol]

            return None

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "get_market_data",
                "symbol": symbol
            })
            return None

    def get_ohlcv(self, symbol: str, interval: str = "1D", 
                   limit: int = 100) -> List[OHLCV]:
        """
        Get OHLCV data for a symbol.

        Args:
            symbol: Trading symbol
            interval: Time interval (1D, 1H, 15M, etc.)
            limit: Number of candles to return

        Returns:
            List of OHLCV data
        """
        try:
            cache_key = f"{symbol}_{interval}_{limit}"
            
            # Check cache first
            if cache_key in self.ohlcv_cache:
                cached_data = self.ohlcv_cache[cache_key]
                if cached_data and len(cached_data) > 0:
                    return cached_data

            # Try to get data from Dhan provider
            if self.dhan_provider and self.is_connected:
                try:
                    historical_data = self.dhan_provider.get_historical_data(symbol, interval, limit)
                    if historical_data:
                        # Convert to OHLCV format
                        ohlcv_data = []
                        for data in historical_data:
                            ohlcv = OHLCV(
                                timestamp=data.timestamp,
                                open_price=data.open_price,
                                high_price=data.high_price,
                                low_price=data.low_price,
                                close_price=data.close_price,
                                volume=data.volume
                            )
                            ohlcv_data.append(ohlcv)
                        
                        # Update cache
                        self._update_ohlcv_cache(cache_key, ohlcv_data)
                        return ohlcv_data
                except Exception as e:
                    self.logger.warning(f"Failed to get OHLCV from Dhan provider for {symbol}: {e}")

            # Return empty list if no data available
            return []

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "get_ohlcv",
                "symbol": symbol,
                "interval": interval
            })
            return []

    def get_symbols(self, exchange: Optional[str] = None) -> List[Symbol]:
        """
        Get available trading symbols.

        Args:
            exchange: Exchange filter (optional)

        Returns:
            List of available symbols
        """
        try:
            # Try to get symbols from Dhan provider
            if self.dhan_provider and self.is_connected:
                try:
                    # This would need to be implemented in Dhan provider
                    # For now, use basic symbols
                    return list(self.symbols.values())
                except Exception as e:
                    self.logger.warning(f"Failed to get symbols from Dhan provider: {e}")

            # Return cached symbols
            return list(self.symbols.values())

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_symbols"})
            return []

    def subscribe_symbol(self, symbol: str) -> bool:
        """
        Subscribe to market data updates for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            True if subscribed successfully, False otherwise
        """
        try:
            # For now, just log the subscription
            # In a real implementation, this would establish a websocket connection
            self.logger.info(f"Subscribed to symbol: {symbol}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "subscribe_symbol",
                "symbol": symbol
            })
            return False

    def unsubscribe_symbol(self, symbol: str) -> bool:
        """
        Unsubscribe from market data updates for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            # For now, just log the unsubscription
            self.logger.info(f"Unsubscribed from symbol: {symbol}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "unsubscribe_symbol",
                "symbol": symbol
            })
            return False

    def get_market_status(self) -> Dict[str, Any]:
        """
        Get market status information.

        Returns:
            Market status dictionary
        """
        try:
            # Try to get status from Dhan provider
            if self.dhan_provider and self.is_connected:
                try:
                    return self.dhan_provider.get_market_status()
                except Exception as e:
                    self.logger.warning(f"Failed to get market status from Dhan provider: {e}")

            # Return basic status
            return {
                "status": "unknown",
                "last_update": self.last_update.isoformat() if self.last_update else None,
                "connected": self.is_connected
            }

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_market_status"})
            return {"status": "error", "error": str(e)}

    def refresh_cache(self) -> int:
        """
        Refresh market data cache.

        Returns:
            Number of symbols refreshed
        """
        try:
            if not self.is_connected:
                return 0

            refreshed_count = 0
            
            # Refresh symbols that are subscribed
            for symbol in list(self.symbols.keys()):
                try:
                    market_data = self.get_market_data(symbol)
                    if market_data:
                        refreshed_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to refresh data for {symbol}: {e}")

            self.last_update = datetime.now()
            self.logger.debug(f"Refreshed {refreshed_count} symbols")
            return refreshed_count

        except Exception as e:
            self.logger.log_error(e, {"operation": "refresh_cache"})
            return 0

    def cleanup_cache(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of entries cleaned up
        """
        try:
            cleaned_count = 0
            current_time = datetime.now()

            # Clean up market data cache
            expired_symbols = []
            for symbol, data in self.market_data_cache.items():
                if not self._is_cache_valid(data):
                    expired_symbols.append(symbol)

            for symbol in expired_symbols:
                del self.market_data_cache[symbol]
                cleaned_count += 1

            # Clean up OHLCV cache
            expired_ohlcv_keys = []
            for key, data in self.ohlcv_cache.items():
                if not data or len(data) == 0:
                    expired_ohlcv_keys.append(key)

            for key in expired_ohlcv_keys:
                del self.ohlcv_cache[key]
                cleaned_count += 1

            # Limit cache size
            if len(self.market_data_cache) > self.max_cache_size:
                # Remove oldest entries
                sorted_cache = sorted(
                    self.market_data_cache.items(),
                    key=lambda x: x[1].timestamp
                )
                excess_count = len(self.market_data_cache) - self.max_cache_size
                for i in range(excess_count):
                    symbol = sorted_cache[i][0]
                    del self.market_data_cache[symbol]
                    cleaned_count += 1

            if cleaned_count > 0:
                self.logger.debug(f"Cleaned up {cleaned_count} cache entries")

            return cleaned_count

        except Exception as e:
            self.logger.log_error(e, {"operation": "cleanup_cache"})
            return 0

    def _load_symbols(self) -> None:
        """Load available trading symbols."""
        try:
            # Try to get symbols from Dhan provider first
            if self.dhan_provider and self.is_connected:
                try:
                    # This would need to be implemented in Dhan provider
                    # For now, use basic symbols
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to load symbols from Dhan provider: {e}")

            # Load basic symbols if Dhan provider is not available
            if not self.symbols:
                basic_symbols = [
                    Symbol(
                        symbol_id="NIFTY50",
                        name="NIFTY 50",
                        exchange="NSE",
                        instrument_type="INDEX",
                        lot_size=50,
                        tick_size=Decimal("0.05"),
                        is_active=True
                    ),
                    Symbol(
                        symbol_id="BANKNIFTY",
                        name="BANK NIFTY",
                        exchange="NSE",
                        instrument_type="INDEX",
                        lot_size=25,
                        tick_size=Decimal("0.05"),
                        is_active=True
                    )
                ]

                for symbol in basic_symbols:
                    self.symbols[symbol.symbol_id] = symbol

            self.logger.info(f"Loaded {len(self.symbols)} symbols")

        except Exception as e:
            self.logger.log_error(e, {"operation": "load_symbols"})

    def _initialize_cache(self) -> None:
        """Initialize data cache."""
        try:
            self.market_data_cache.clear()
            self.ohlcv_cache.clear()
            self.logger.debug("Market data cache initialized")

        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize_cache"})

    def _start_update_loop(self) -> None:
        """Start the data update loop."""
        try:
            if self.update_task:
                self.update_task.cancel()

            self.update_task = asyncio.create_task(self._update_loop())
            self.logger.debug("Market data update loop started")

        except Exception as e:
            self.logger.log_error(e, {"operation": "start_update_loop"})

    async def _update_loop(self) -> None:
        """Main update loop for market data."""
        try:
            while self.is_connected:
                try:
                    # Refresh cache
                    self.refresh_cache()
                    
                    # Clean up old cache entries
                    self.cleanup_cache()
                    
                    # Wait for next update
                    await asyncio.sleep(self.update_interval_seconds)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.log_error(e, {"operation": "update_loop"})
                    await asyncio.sleep(5)  # Wait before retrying

        except Exception as e:
            self.logger.log_error(e, {"operation": "update_loop"})

    def _update_cache(self, symbol: str, market_data: MarketData) -> None:
        """Update market data cache."""
        try:
            self.market_data_cache[symbol] = market_data

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_cache",
                "symbol": symbol
            })

    def _update_ohlcv_cache(self, key: str, ohlcv_data: List[OHLCV]) -> None:
        """Update OHLCV cache."""
        try:
            self.ohlcv_cache[key] = ohlcv_data

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_ohlcv_cache",
                "key": key
            })

    def _is_cache_valid(self, market_data: MarketData) -> bool:
        """Check if cached market data is still valid."""
        try:
            if not market_data or not market_data.timestamp:
                return False

            age = datetime.now() - market_data.timestamp
            return age.total_seconds() < self.cache_timeout_seconds

        except Exception as e:
            self.logger.log_error(e, {"operation": "is_cache_valid"})
            return False 