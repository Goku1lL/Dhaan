"""
Dhan Advanced Algo Trading System
A comprehensive algorithmic trading system for the Dhan trading platform.
"""

__version__ = "1.0.0"
__author__ = "Dhan Advanced Algo Team"
__description__ = "Advanced algorithmic trading system with risk management, position management, and strategy execution"

# Import main components for easy access
from .core.interfaces import (
    IMarketDataProvider,
    ITradingBroker,
    IIndicatorCalculator,
    ISignalGenerator,
    IRiskManager,
    IPositionManager,
    IOrderManager,
    IDataRepository,
    INotificationService,
    IStrategyManager,
    ITradingEngine,
    IStrategy
)

from .core.entities import (
    Position,
    Order,
    Trade,
    MarketData,
    OHLCV,
    Symbol,
    IndicatorData,
    TradingSignal,
    Strategy,
    Signal,
    AccountBalance,
    OrderSide,
    OrderType,
    OrderStatus,
    PositionStatus,
    SignalType,
    SignalStrength
)

# Import provider implementations
from .providers.risk_manager import RiskManager
from .providers.position_manager import PositionManager
from .providers.strategy_manager import StrategyManager
from .providers.notification_service import NotificationService
from .providers.order_manager import OrderManager
from .providers.market_data_provider import MarketDataProvider
from .providers.data_repository import DataRepository

# Export main classes
__all__ = [
    # Interfaces
    'IMarketDataProvider',
    'ITradingBroker',
    'IIndicatorCalculator',
    'ISignalGenerator',
    'IRiskManager',
    'IPositionManager',
    'IOrderManager',
    'IDataRepository',
    'INotificationService',
    'IStrategyManager',
    'ITradingEngine',
    'IStrategy',
    
    # Entities
    'Position',
    'Order',
    'Trade',
    'MarketData',
    'OHLCV',
    'Symbol',
    'IndicatorData',
    'TradingSignal',
    'Strategy',
    'Signal',
    'AccountBalance',
    'OrderSide',
    'OrderType',
    'OrderStatus',
    'PositionStatus',
    'SignalType',
    'SignalStrength',
    
    # Provider Implementations
    'RiskManager',
    'PositionManager',
    'StrategyManager',
    'NotificationService',
    'OrderManager',
    'MarketDataProvider',
    'DataRepository'
] 