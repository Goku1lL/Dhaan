"""
Core interfaces for the Dhan Advanced Algo Trading System.
These define contracts that implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from .entities import (
    Position, Order, MarketData, IndicatorData, 
    TradingSignal, AccountBalance, OrderSide, OrderType, OrderStatus, Trade
)


class IMarketDataProvider(ABC):
    """Interface for market data providers."""
    
    @abstractmethod
    def get_ltp(self, symbol: str) -> Optional[Decimal]:
        """Get Last Traded Price for a symbol."""
        pass
    
    @abstractmethod
    def get_ltp_bulk(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Get LTP for multiple symbols in bulk."""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, timeframe: str, count: int) -> List[MarketData]:
        """Get historical market data."""
        pass
    
    @abstractmethod
    def is_market_open(self) -> bool:
        """Check if market is open."""
        pass


class ITradingBroker(ABC):
    """Interface for trading broker operations."""
    
    @abstractmethod
    def place_order(self, order: Order) -> str:
        """Place a trading order and return order ID."""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> str:
        """Get status of an order."""
        pass
    
    @abstractmethod
    def get_executed_price(self, order_id: str) -> Optional[Decimal]:
        """Get executed price of an order."""
        pass
    
    @abstractmethod
    def get_account_balance(self) -> AccountBalance:
        """Get current account balance."""
        pass
    
    @abstractmethod
    def square_off_position(self, symbol: str, quantity: int, side: OrderSide) -> bool:
        """Square off an existing position."""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get current open positions."""
        pass


class IIndicatorCalculator(ABC):
    """Interface for technical indicator calculations."""
    
    @abstractmethod
    def calculate_rsi(self, prices: List[Decimal], period: int = 14) -> List[Decimal]:
        """Calculate RSI indicator."""
        pass
    
    @abstractmethod
    def calculate_supertrend(self, high: List[Decimal], low: List[Decimal], 
                           close: List[Decimal], period: int = 10, multiplier: float = 3.0) -> List[Dict[str, Any]]:
        """Calculate SuperTrend indicator."""
        pass
    
    @abstractmethod
    def calculate_sma(self, prices: List[Decimal], period: int) -> List[Decimal]:
        """Calculate Simple Moving Average."""
        pass
    
    @abstractmethod
    def calculate_bollinger_bands(self, prices: List[Decimal], period: int = 20, 
                                std_dev: float = 2.0) -> List[Dict[str, Decimal]]:
        """Calculate Bollinger Bands."""
        pass
    
    @abstractmethod
    def calculate_all_indicators(self, market_data: List[MarketData]) -> List[IndicatorData]:
        """Calculate all indicators for market data."""
        pass


class ISignalGenerator(ABC):
    """Interface for trading signal generation."""
    
    @abstractmethod
    def generate_signals(self, market_data: List[MarketData], 
                        indicator_data: List[IndicatorData]) -> List[TradingSignal]:
        """Generate trading signals."""
        pass
    
    @abstractmethod
    def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate a trading signal."""
        pass


class IRiskManager(ABC):
    """Interface for risk management."""
    
    @abstractmethod
    def calculate_position_size(self, symbol: str, entry_price: Decimal, 
                              stop_loss: Decimal, available_capital: Decimal) -> int:
        """Calculate position size based on risk parameters."""
        pass
    
    @abstractmethod
    def validate_order(self, order: Order, current_positions: List[Position]) -> bool:
        """Validate order against risk parameters."""
        pass
    
    @abstractmethod
    def calculate_risk_metrics(self, positions: List[Position], 
                             current_prices: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate current risk metrics."""
        pass
    
    @abstractmethod
    def update_daily_tracking(self, realized_pnl: Decimal) -> None:
        """Update daily tracking metrics."""
        pass
    
    @abstractmethod
    def update_portfolio_value(self, new_value: Decimal) -> None:
        """Update portfolio value."""
        pass
    
    @abstractmethod
    def update_open_positions_count(self, count: int) -> None:
        """Update open positions count."""
        pass
    
    @abstractmethod
    def check_risk_limits(self, positions: List[Position], 
                         current_prices: Dict[str, Decimal]) -> Dict[str, bool]:
        """Check if current positions violate any risk limits."""
        pass
    
    @abstractmethod
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk summary."""
        pass


class IPositionManager(ABC):
    """Interface for position management."""
    
    @abstractmethod
    def create_position(self, order: Order, entry_price: Decimal, 
                       stop_loss: Optional[Decimal] = None, target: Optional[Decimal] = None) -> Position:
        """Create a new position from an order."""
        pass
    
    @abstractmethod
    def update_position(self, position_id: str, current_price: Decimal, 
                       unrealized_pnl: Optional[Decimal] = None) -> bool:
        """Update position with current market data."""
        pass
    
    @abstractmethod
    def close_position(self, position_id: str, exit_price: Decimal, 
                      exit_reason: str = "MANUAL") -> Optional[Position]:
        """Close a position."""
        pass
    
    @abstractmethod
    def get_positions(self, symbol: Optional[str] = None, 
                     status: Optional[str] = None) -> List[Position]:
        """Get positions with optional filtering."""
        pass
    
    @abstractmethod
    def get_open_positions(self) -> List[Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    def update_stop_loss(self, position_id: str, new_stop_loss: Decimal) -> bool:
        """Update stop loss for a position."""
        pass
    
    @abstractmethod
    def update_target(self, position_id: str, new_target: Decimal) -> bool:
        """Update target for a position."""
        pass
    
    @abstractmethod
    def cleanup_expired_positions(self) -> int:
        """Clean up expired positions."""
        pass
    
    @abstractmethod
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions."""
        pass


class IOrderManager(ABC):
    """Interface for order management."""
    
    @abstractmethod
    def place_order(self, order: Order) -> str:
        """Place an order and return order ID."""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        pass
    
    @abstractmethod
    def get_orders(self, symbol: Optional[str] = None, 
                  status: Optional[OrderStatus] = None) -> List[Order]:
        """Get orders with optional filtering."""
        pass
    
    @abstractmethod
    def update_order_status(self, order_id: str, status: OrderStatus, 
                          filled_price: Optional[Decimal] = None, 
                          filled_quantity: Optional[int] = None) -> bool:
        """Update order status."""
        pass
    
    @abstractmethod
    def get_order_summary(self) -> Dict[str, Any]:
        """Get summary of all orders."""
        pass


class IDataRepository(ABC):
    """Interface for data repository operations."""
    
    @abstractmethod
    def save_market_data(self, symbol: str, data: MarketData) -> bool:
        """Save market data to repository."""
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str, start_time: datetime, end_time: datetime) -> List[MarketData]:
        """Retrieve market data from repository."""
        pass
    
    @abstractmethod
    def save_order(self, order: Order) -> bool:
        """Save order to repository."""
        pass
    
    @abstractmethod
    def get_orders(self, symbol: Optional[str] = None, status: Optional[OrderStatus] = None) -> List[Order]:
        """Get orders from repository."""
        pass
    
    @abstractmethod
    def save_trade(self, trade: Trade) -> bool:
        """Save trade to repository."""
        pass
    
    @abstractmethod
    def get_trades(self, symbol: Optional[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Trade]:
        """Get trades from repository."""
        pass


class INotificationService(ABC):
    """Interface for notification services."""
    
    @abstractmethod
    def send_notification(self, message: str, notification_type: str = "INFO") -> bool:
        """Send a notification."""
        pass
    
    @abstractmethod
    def send_trade_alert(self, trade: Trade) -> bool:
        """Send trade-specific alert."""
        pass
    
    @abstractmethod
    def send_error_alert(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Send error alert."""
        pass
    
    @abstractmethod
    def send_position_alert(self, symbol: str, side: str, quantity: int, 
                           entry_price: float, current_price: float, 
                           unrealized_pnl: float) -> bool:
        """Send position update alert."""
        pass
    
    @abstractmethod
    def send_daily_summary(self, summary: Dict[str, Any]) -> bool:
        """Send daily trading summary."""
        pass
    
    @abstractmethod
    def test_telegram_connection(self) -> bool:
        """Test Telegram bot connection."""
        pass
    
    @abstractmethod
    def get_notification_status(self) -> Dict[str, Any]:
        """Get notification service status."""
        pass


class IStrategyManager(ABC):
    """Interface for strategy management."""
    
    @abstractmethod
    def add_strategy(self, strategy: Any) -> bool:
        """Add a new trading strategy."""
        pass
    
    @abstractmethod
    def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> bool:
        """Update strategy parameters."""
        pass
    
    @abstractmethod
    def remove_strategy(self, strategy_id: str) -> bool:
        """Remove a strategy."""
        pass
    
    @abstractmethod
    def enable_strategy(self, strategy_id: str) -> bool:
        """Enable a strategy."""
        pass
    
    @abstractmethod
    def disable_strategy(self, strategy_id: str) -> bool:
        """Disable a strategy."""
        pass
    
    @abstractmethod
    def generate_signals(self, market_data: Dict[str, Any]) -> List[Any]:
        """Generate trading signals from all active strategies."""
        pass
    
    @abstractmethod
    def get_signals(self, strategy_id: Optional[str] = None, 
                    signal_type: Optional[Any] = None,
                    active_only: bool = True) -> List[Any]:
        """Get signals with optional filtering."""
        pass
    
    @abstractmethod
    def get_strategy(self, strategy_id: str) -> Optional[Any]:
        """Get strategy by ID."""
        pass
    
    @abstractmethod
    def get_strategies(self, active_only: bool = False) -> List[Any]:
        """Get all strategies."""
        pass
    
    @abstractmethod
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get summary of all strategies."""
        pass


class ITradingEngine(ABC):
    """Interface for the main trading engine."""
    
    @abstractmethod
    def start(self) -> bool:
        """Start the trading engine."""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop the trading engine."""
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """Check if trading engine is running."""
        pass
    
    @abstractmethod
    def process_market_data(self, symbol: str, market_data: MarketData) -> None:
        """Process incoming market data."""
        pass
    
    @abstractmethod
    def execute_strategy(self, symbol: str) -> None:
        """Execute trading strategy for a symbol."""
        pass
    
    @abstractmethod
    def place_order(self, order: Order) -> str:
        """Place a trading order."""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a trading order."""
        pass
    
    @abstractmethod
    def get_engine_status(self) -> Dict[str, Any]:
        """Get trading engine status."""
        pass
    
    @abstractmethod
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get active positions."""
        pass
    
    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        pass


class IStrategy(ABC):
    """Interface for individual trading strategies."""
    
    @abstractmethod
    def should_enter(self, market_data: MarketData, 
                    indicator_data: IndicatorData) -> Optional[TradingSignal]:
        """Check if strategy should enter a position."""
        pass
    
    @abstractmethod
    def should_exit(self, position: Position, market_data: MarketData, 
                   indicator_data: IndicatorData) -> bool:
        """Check if strategy should exit a position."""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        pass
    
    @abstractmethod
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        pass 