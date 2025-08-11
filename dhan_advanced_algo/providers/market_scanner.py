"""
Market Scanner Service
Continuously scans the entire market for trading opportunities based on defined strategies.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd

from ..core.interfaces import IMarketDataProvider
from ..core.entities import MarketData, OHLCV
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager
from .strategy_manager import StrategyManager


@dataclass
class TradingOpportunity:
    """Represents a detected trading opportunity."""
    symbol: str
    strategy_name: str
    strategy_id: str
    signal_type: str  # 'BUY', 'SELL', 'SHORT'
    confidence_score: float  # 0.0 to 1.0
    entry_price: float
    target_price: float
    stop_loss: float
    risk_reward_ratio: float
    volume: int
    timestamp: datetime
    indicators: Dict[str, Any]
    description: str


@dataclass
class MarketScanResult:
    """Result of a market scan operation."""
    scan_timestamp: datetime
    total_stocks_scanned: int
    opportunities_found: int
    opportunities: List[TradingOpportunity]
    scan_duration: float
    market_sentiment: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'


class MarketScanner:
    """
    Market Scanner Engine
    Continuously scans the market for trading opportunities using defined strategies.
    """
    
    def __init__(self, 
                 market_data_provider: IMarketDataProvider,
                 strategy_manager: StrategyManager,
                 config: ConfigurationManager):
        """
        Initialize the market scanner.
        
        Args:
            market_data_provider: Provider for market data
            strategy_manager: Manager for trading strategies
            config: Configuration manager
        """
        self.market_data_provider = market_data_provider
        self.strategy_manager = strategy_manager
        self.config = config
        self.logger = LoggingService()
        
        # Scanner configuration
        self.scan_interval_seconds = getattr(config.market_scanner, 'scan_interval_seconds', 300)  # 5 minutes
        self.max_concurrent_scans = getattr(config.market_scanner, 'max_concurrent_scans', 50)
        self.min_confidence_score = getattr(config.market_scanner, 'min_confidence_score', 0.7)
        
        # Stock universe
        self.stock_universe = self._load_stock_universe()
        self.current_scan_results: Optional[MarketScanResult] = None
        
        # Scanner state
        self.is_scanning = False
        self.last_scan_time = None
        self.scan_task = None
        
        # Performance tracking
        self.scan_count = 0
        self.total_opportunities_found = 0
        self.successful_signals = 0
        
        self.logger.info("Market Scanner initialized")
    
    def _load_stock_universe(self) -> List[str]:
        """Load the complete stock universe to scan."""
        try:
            # Load from configuration or default to major indices
            default_universe = [
                # NIFTY 50
                "RELIANCE", "TCS", "HDFC", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN",
                "BHARTIARTL", "AXISBANK", "ASIANPAINT", "MARUTI", "HCLTECH", "ULTRACEMCO",
                "SUNPHARMA", "TITAN", "WIPRO", "BAJFINANCE", "NESTLEIND", "POWERGRID",
                
                # BANKNIFTY
                "HDFCBANK", "KOTAKBANK", "INDUSINDBK", "AUROPHARMA", "ADANIENT", "ADANIPORTS",
                "BAJAJFINSV", "BAJAJ-AUTO", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB",
                "DRREDDY", "EICHERMOT", "GAIL", "HEROMOTOCO", "HINDALCO", "JSWSTEEL",
                
                # Additional liquid stocks
                "VEDL", "TATAMOTORS", "ONGC", "GRASIM", "TATASTEEL", "SHREECEM", "NTPC",
                "TECHM", "BPCL", "M&M", "UPL", "ZEEL", "LT", "TATACONSUM", "APOLLOHOSP",
                
                # NIFTY NEXT 50 (Additional High-Quality Stocks)
                "GODREJCP", "PIDILITIND", "DABUR", "MARICO", "COLPAL", "BERGEPAINT", "PAGEIND",
                "INDIGO", "BAJAJ-FINANCE", "MCDOWELL-N", "MOTHERSUMI", "MUTHOOTFIN", "BIOCON",
                "BOSCHLTD", "AMBUJACEM", "ACC", "SIEMENS", "HAVELLS", "VOLTAS", "JINDALSTEL",
                "TRENT", "BANDHANBNK", "TORNTPHARM", "CADILAHC", "LUPIN", "GLENMARK", "SRTRANSFIN",
                
                # PSU and Infrastructure
                "SAIL", "NMDC", "RECLTD", "PFC", "IRCTC", "HAL", "BEL", "BHEL", "IOC", "HPCL",
                "CONCOR", "RAILTEL", "IRFC", "IREDA", "SJVN", "NHPC", "THERMAX", "NBCC",
                
                # Banking and Financial Services
                "FEDERALBNK", "YESBANK", "IDFCFIRSTB", "RBLBANK", "EQUITASBNK", "AUBANK",
                "CHOLAFIN", "BAJAJHLDNG", "LICHSGFIN", "MANAPPURAM", "L&TFH", "SHRIRAMFIN",
                
                # Auto and Auto Ancillaries
                "ASHOKLEY", "ESCORTS", "EICHERMOT", "MAHINDRA", "TVSMOTOR", "HEROMOTOCO",
                "APOLLOTYRE", "MRF", "BALKRISIND", "ENDURANCE", "RAMCOCEM", "EXIDEIND",
                
                # Pharma and Healthcare
                "REDDY", "AUROPHARMA", "GLAND", "GRANULES", "DIVIS", "LALPATHLAB", "DRREDDY",
                "METROPOLIS", "THYROCARE", "SYNGENE", "BIOCON", "NATCOPHARM", "JUBLFOOD",
                
                # Technology and IT Services
                "MINDTREE", "LTTS", "COFORGE", "PERSISTENT", "MPHASIS", "LTIM", "TECHM",
                "CYIENT", "RPOWER", "ZENTEC", "SONACOMS", "KPITTECH", "RAMCOIND",
                
                # Consumer and Retail
                "AVENUE", "RELAXO", "VBL", "HONAUT", "PGHH", "EMAMILTD", "VGUARD",
                "CROMPTON", "WHIRLPOOL", "DIXON", "AMBER", "SHOPERSTOP", "TRENT",
                
                # Metals and Mining
                "JSW", "NATIONALUM", "MOIL", "RATNAMANI", "APL", "WELCORP", "GMRINFRA",
                "ADANIENT", "ADANIGREEN", "ADANITRANS", "ADANIPOWER", "RPOWER",
                
                # Chemicals and Petrochemicals
                "PIDILITIND", "KANSAINER", "DEEPAKNTR", "ALKYLAMINE", "CLEAN", "NOCIL",
                "TATACHEM", "BALRAMCHIN", "GUJALKALI", "CHAMBLFERT", "GSFC"
            ]
            
            # TODO: Load from configuration file or database
            if hasattr(self.config, 'market_scanner') and hasattr(self.config.market_scanner, 'stock_universe'):
                if self.config.market_scanner.stock_universe:
                    universe = self.config.market_scanner.stock_universe
                    self.logger.info(f"Using custom stock universe from configuration")
                else:
                    universe = default_universe
                    self.logger.info(f"Using default stock universe")
            else:
                universe = default_universe
                self.logger.info(f"No configuration found, using default stock universe")
            
            self.logger.info(f"Loaded stock universe with {len(universe)} stocks")
            return universe
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "load_stock_universe"})
            # Fallback to basic universe
            return ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFC", "INFY"]
    
    async def start_scanning(self):
        """Start continuous market scanning."""
        if self.is_scanning:
            self.logger.warning("Market scanner is already running")
            return
        
        self.is_scanning = True
        self.scan_task = asyncio.create_task(self._scan_loop())
        self.logger.info("Market scanner started")
    
    async def stop_scanning(self):
        """Stop continuous market scanning."""
        if not self.is_scanning:
            return
        
        self.is_scanning = False
        if self.scan_task:
            self.scan_task.cancel()
            try:
                await self.scan_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Market scanner stopped")
    
    async def _scan_loop(self):
        """Main scanning loop."""
        while self.is_scanning:
            try:
                start_time = datetime.now()
                
                # Perform market scan
                scan_result = await self._perform_market_scan()
                self.current_scan_results = scan_result
                self.last_scan_time = start_time
                
                # Log scan results
                self.logger.info(f"Market scan completed: {scan_result.opportunities_found} opportunities found "
                               f"in {scan_result.scan_duration:.2f}s")
                
                # Wait for next scan
                await asyncio.sleep(self.scan_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.log_error(e, {"operation": "scan_loop"})
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_market_scan(self) -> MarketScanResult:
        """Perform a complete market scan."""
        start_time = datetime.now()
        opportunities = []
        
        try:
            # Scan stocks in batches to avoid overwhelming the API
            batches = self._create_scan_batches()
            
            for batch in batches:
                batch_opportunities = await self._scan_stock_batch(batch)
                opportunities.extend(batch_opportunities)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            # Filter opportunities by confidence score
            filtered_opportunities = [
                opp for opp in opportunities 
                if opp.confidence_score >= self.min_confidence_score
            ]
            
            # Determine market sentiment
            market_sentiment = self._calculate_market_sentiment(filtered_opportunities)
            
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            # Update performance metrics
            self.scan_count += 1
            self.total_opportunities_found += len(filtered_opportunities)
            
            return MarketScanResult(
                scan_timestamp=start_time,
                total_stocks_scanned=len(self.stock_universe),
                opportunities_found=len(filtered_opportunities),
                opportunities=filtered_opportunities,
                scan_duration=scan_duration,
                market_sentiment=market_sentiment
            )
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "perform_market_scan"})
            # Return empty result on error
            return MarketScanResult(
                scan_timestamp=start_time,
                total_stocks_scanned=0,
                opportunities_found=0,
                opportunities=[],
                scan_duration=(datetime.now() - start_time).total_seconds(),
                market_sentiment="UNKNOWN"
            )
    
    def _create_scan_batches(self) -> List[List[str]]:
        """Create batches of stocks for scanning."""
        batch_size = min(self.max_concurrent_scans, len(self.stock_universe))
        batches = []
        
        for i in range(0, len(self.stock_universe), batch_size):
            batch = self.stock_universe[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    async def _scan_stock_batch(self, stock_batch: List[str]) -> List[TradingOpportunity]:
        """Scan a batch of stocks for opportunities."""
        opportunities = []
        
        try:
            # Create tasks for concurrent scanning
            scan_tasks = [
                self._scan_single_stock(symbol) 
                for symbol in stock_batch
            ]
            
            # Execute all scans concurrently
            batch_results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.warning(f"Stock scan failed: {result}")
                    continue
                
                if result:  # If opportunity found
                    opportunities.append(result)
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "scan_stock_batch"})
        
        return opportunities
    
    async def _scan_single_stock(self, symbol: str) -> Optional[TradingOpportunity]:
        """Scan a single stock for trading opportunities."""
        try:
            # Get market data for the stock
            market_data = await self._get_stock_data(symbol)
            if not market_data:
                return None
            
            # Apply all strategies to the stock
            opportunities = []
            
            for strategy in self.strategy_manager.get_active_strategies():
                try:
                    opportunity = await self._apply_strategy_to_stock(strategy, symbol, market_data)
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    self.logger.warning(f"Strategy {strategy.name} failed for {symbol}: {e}")
                    continue
            
            # Return the best opportunity (highest confidence score)
            if opportunities:
                return max(opportunities, key=lambda x: x.confidence_score)
            
            return None
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "scan_single_stock", "symbol": symbol})
            return None
    
    async def _get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive stock data for analysis."""
        try:
            # Get current market data (synchronous call)
            current_data = self.market_data_provider.get_market_data(symbol)
            if not current_data:
                return None
            
            # Get OHLCV data for technical analysis (synchronous call)
            ohlcv_data = self.market_data_provider.get_ohlcv(symbol, "15m")
            
            # Convert OHLCV to list format for strategy engine
            ohlcv_list = []
            if ohlcv_data:
                for candle in ohlcv_data:
                    ohlcv_list.append([
                        candle.timestamp.isoformat(),
                        float(candle.open) if candle.open else 0,
                        float(candle.high) if candle.high else 0,
                        float(candle.low) if candle.low else 0,
                        float(candle.close) if candle.close else 0,
                        candle.volume if candle.volume else 0
                    ])
            
            # Compile comprehensive data
            stock_data = {
                "symbol": symbol,
                "current_price": float(current_data.ltp) if current_data.ltp else 0,
                "open": float(current_data.open_price) if current_data.open_price else 0,
                "high": float(current_data.high_price) if current_data.high_price else 0,
                "low": float(current_data.low_price) if current_data.low_price else 0,
                "volume": current_data.volume if current_data.volume else 0,
                "timestamp": current_data.timestamp,
                "ohlcv": ohlcv_list,
                "change": 0,  # Calculate from open
                "change_percent": 0
            }
            
            # Calculate change if we have open price
            if stock_data["open"] > 0:
                stock_data["change"] = stock_data["current_price"] - stock_data["open"]
                stock_data["change_percent"] = (stock_data["change"] / stock_data["open"]) * 100
            
            return stock_data
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_stock_data", "symbol": symbol})
            return None
    
    async def _apply_strategy_to_stock(self, strategy: Any, symbol: str, stock_data: Dict[str, Any]) -> Optional[TradingOpportunity]:
        """Apply a specific strategy to a stock."""
        try:
            # Import the strategy engine
            from .strategy_engine import StrategyEngine
            
            # Create strategy engine instance
            strategy_engine = StrategyEngine()
            
            # Apply the strategy
            signal = strategy_engine.apply_strategy(strategy.id, stock_data)
            
            if signal and signal.confidence_score >= self.min_confidence_score:
                # Convert StrategySignal to TradingOpportunity
                opportunity = TradingOpportunity(
                    symbol=symbol,
                    strategy_name=strategy.name,
                    strategy_id=strategy.id,
                    signal_type=signal.signal_type,
                    confidence_score=signal.confidence_score,
                    entry_price=signal.entry_price,
                    target_price=signal.target_price,
                    stop_loss=signal.stop_loss,
                    risk_reward_ratio=signal.risk_reward_ratio,
                    volume=stock_data.get('volume', 0),
                    timestamp=datetime.now(),
                    indicators=signal.indicators,
                    description=signal.description
                )
                return opportunity
            
            return None
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "apply_strategy_to_stock", "symbol": symbol, "strategy": getattr(strategy, 'name', 'unknown')})
            return None
    
    def _calculate_market_sentiment(self, opportunities: List[TradingOpportunity]) -> str:
        """Calculate overall market sentiment based on opportunities."""
        if not opportunities:
            return "NEUTRAL"
        
        # Count buy vs sell signals
        buy_signals = sum(1 for opp in opportunities if opp.signal_type == "BUY")
        sell_signals = sum(1 for opp in opportunities if opp.signal_type in ["SELL", "SHORT"])
        
        total_signals = len(opportunities)
        buy_ratio = buy_signals / total_signals
        
        if buy_ratio > 0.6:
            return "BULLISH"
        elif buy_ratio < 0.4:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def get_current_opportunities(self) -> List[TradingOpportunity]:
        """Get current trading opportunities."""
        if self.current_scan_results:
            return self.current_scan_results.opportunities
        return []
    
    def get_scan_summary(self) -> Optional[MarketScanResult]:
        """Get the latest scan summary."""
        return self.current_scan_results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get scanner performance metrics."""
        return {
            "total_scans": self.scan_count,
            "total_opportunities": self.total_opportunities_found,
            "successful_signals": self.successful_signals,
            "last_scan_time": self.last_scan_time,
            "is_scanning": self.is_scanning
        } 