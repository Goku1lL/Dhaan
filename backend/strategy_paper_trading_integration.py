"""
Backend Integration for Strategy Paper Trading
Provides Flask API endpoints for strategy-based paper trading functionality.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import strategy paper trading components
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    from dhan_advanced_algo.providers.strategy_paper_trading_manager import StrategyPaperTradingManager
    STRATEGY_PAPER_TRADING_AVAILABLE = True
    
except ImportError as e:
    print(f"❌ Warning: Strategy Paper Trading components not available: {e}")
    STRATEGY_PAPER_TRADING_AVAILABLE = False


class StrategyPaperTradingIntegration:
    """
    Backend integration for Strategy Paper Trading Manager.
    Provides API endpoints and coordination between market scanner and paper trading.
    """
    
    def __init__(self, market_scanner_manager, paper_trading_manager):
        """
        Initialize strategy paper trading integration.
        
        Args:
            market_scanner_manager: Market scanner manager instance
            paper_trading_manager: Paper trading manager instance
        """
        self.market_scanner_manager = market_scanner_manager
        self.paper_trading_manager = paper_trading_manager
        self.logger = logging.getLogger(__name__)
        
        # Strategy paper trading manager
        self.strategy_paper_trading_manager = None
        
        # Initialize if components are available
        if STRATEGY_PAPER_TRADING_AVAILABLE:
            self._initialize_strategy_integration()
        else:
            self.logger.warning("Strategy Paper Trading not available - using mock mode")
    
    def _initialize_strategy_integration(self):
        """Initialize the strategy paper trading manager."""
        try:
            # Get components from managers
            market_scanner = self.market_scanner_manager.market_scanner
            paper_broker = self.paper_trading_manager.paper_broker
            strategy_manager = market_scanner.strategy_manager if market_scanner else None
            
            if market_scanner and paper_broker and strategy_manager:
                # Create strategy paper trading manager
                self.strategy_paper_trading_manager = StrategyPaperTradingManager(
                    market_scanner=market_scanner,
                    paper_broker=paper_broker,
                    strategy_manager=strategy_manager
                )
                
                self.logger.info("Strategy Paper Trading Integration initialized successfully")
            else:
                self.logger.warning("Required components not available for strategy paper trading")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize strategy paper trading: {e}")
    
    def is_available(self) -> bool:
        """Check if strategy paper trading is available."""
        return (STRATEGY_PAPER_TRADING_AVAILABLE and 
                self.strategy_paper_trading_manager is not None)
    
    async def process_market_opportunities(self) -> Dict[str, Any]:
        """
        Process market scanner opportunities and execute strategy-based paper trades.
        
        Returns:
            Processing results summary
        """
        try:
            if not self.is_available():
                return {
                    "error": "Strategy paper trading not available",
                    "available": False
                }
            
            # Process opportunities
            result = await self.strategy_paper_trading_manager.process_market_opportunities()
            
            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing market opportunities: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """Get comprehensive strategy performance summary."""
        try:
            if not self.is_available():
                return {
                    "error": "Strategy paper trading not available",
                    "available": False
                }
            
            performance = self.strategy_paper_trading_manager.get_strategy_performance_summary()
            
            return {
                "success": True,
                "performance": performance,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting strategy performance: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def get_active_strategy_trades(self) -> Dict[str, Any]:
        """Get list of currently active strategy trades."""
        try:
            if not self.is_available():
                return {
                    "error": "Strategy paper trading not available",
                    "available": False,
                    "trades": []
                }
            
            trades = self.strategy_paper_trading_manager.get_active_trades()
            
            return {
                "success": True,
                "trades": trades,
                "count": len(trades),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting active strategy trades: {e}")
            return {
                "error": str(e),
                "success": False,
                "trades": []
            }
    
    def enable_auto_trading(self) -> Dict[str, Any]:
        """Enable automatic strategy-based paper trading."""
        try:
            if not self.is_available():
                return {
                    "error": "Strategy paper trading not available",
                    "success": False
                }
            
            enabled = self.strategy_paper_trading_manager.enable_auto_trading()
            
            return {
                "success": enabled,
                "message": "Strategy auto-trading enabled" if enabled else "Failed to enable auto-trading",
                "auto_trading_enabled": enabled
            }
            
        except Exception as e:
            self.logger.error(f"Error enabling auto trading: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def disable_auto_trading(self) -> Dict[str, Any]:
        """Disable automatic strategy-based paper trading."""
        try:
            if not self.is_available():
                return {
                    "error": "Strategy paper trading not available",
                    "success": False
                }
            
            disabled = self.strategy_paper_trading_manager.disable_auto_trading()
            
            return {
                "success": disabled,
                "message": "Strategy auto-trading disabled" if disabled else "Failed to disable auto-trading",
                "auto_trading_enabled": not disabled
            }
            
        except Exception as e:
            self.logger.error(f"Error disabling auto trading: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def get_auto_trading_status(self) -> Dict[str, Any]:
        """Get current auto-trading status and configuration."""
        try:
            if not self.is_available():
                return {
                    "error": "Strategy paper trading not available",
                    "success": False,
                    "auto_trading_enabled": False
                }
            
            manager = self.strategy_paper_trading_manager
            
            return {
                "success": True,
                "auto_trading_enabled": manager.auto_trading_enabled,
                "max_position_size": float(manager.max_position_size),
                "max_positions_per_strategy": manager.max_positions_per_strategy,
                "risk_per_trade": float(manager.risk_per_trade),
                "total_strategies": len(manager.strategy_performances),
                "total_active_trades": len(manager.active_trades)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting auto trading status: {e}")
            return {
                "error": str(e),
                "success": False,
                "auto_trading_enabled": False
            }
    
    def run_strategy_processing_loop(self, interval_seconds: int = 30):
        """
        Run a background loop to continuously process market opportunities.
        
        Args:
            interval_seconds: Interval between processing cycles
        """
        async def processing_loop():
            while True:
                try:
                    if self.is_available():
                        # Process opportunities
                        result = await self.process_market_opportunities()
                        
                        if result.get("success") and result.get("result", {}).get("trades_executed", 0) > 0:
                            self.logger.info(f"Strategy processing executed {result['result']['trades_executed']} trades")
                    
                    # Wait for next cycle
                    await asyncio.sleep(interval_seconds)
                    
                except Exception as e:
                    self.logger.error(f"Error in strategy processing loop: {e}")
                    await asyncio.sleep(interval_seconds)
        
        # Run the loop in the background
        asyncio.create_task(processing_loop())
        self.logger.info(f"Started strategy processing loop with {interval_seconds}s interval")


# Global instance (will be initialized in app.py)
strategy_paper_trading_integration = None


def get_strategy_paper_trading_integration():
    """Get the global strategy paper trading integration instance."""
    global strategy_paper_trading_integration
    return strategy_paper_trading_integration


def initialize_strategy_paper_trading_integration(market_scanner_manager, paper_trading_manager):
    """Initialize the global strategy paper trading integration."""
    global strategy_paper_trading_integration
    strategy_paper_trading_integration = StrategyPaperTradingIntegration(
        market_scanner_manager, paper_trading_manager
    )
    return strategy_paper_trading_integration 