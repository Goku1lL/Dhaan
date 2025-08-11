"""
Custom exceptions for the Dhan Advanced Algo Trading System.
Each exception class handles a specific type of error.
"""

from typing import Optional, Any


class TradingSystemException(Exception):
    """Base exception for all trading system errors."""
    
    def __init__(self, message: str, context: Optional[Any] = None):
        self.message = message
        self.context = context
        super().__init__(self.message)


class MarketDataException(TradingSystemException):
    """Exception for market data related errors."""
    pass


class BrokerException(TradingSystemException):
    """Exception for broker API related errors."""
    pass


class OrderException(TradingSystemException):
    """Exception for order related errors."""
    pass


class OrderManagementException(TradingSystemException):
    """Exception for order management related errors."""
    pass


class PositionException(TradingSystemException):
    """Exception for position related errors."""
    pass


class PositionManagementException(TradingSystemException):
    """Exception for position management related errors."""
    pass


class RiskManagementException(TradingSystemException):
    """Exception for risk management related errors."""
    pass


class StrategyException(TradingSystemException):
    """Exception for strategy related errors."""
    pass


class StrategyManagementException(TradingSystemException):
    """Exception for strategy management related errors."""
    pass


class IndicatorException(TradingSystemException):
    """Exception for technical indicator calculation errors."""
    pass


class DataRepositoryException(TradingSystemException):
    """Exception for data persistence related errors."""
    pass


class NotificationException(TradingSystemException):
    """Exception for notification service errors."""
    pass


class ConfigurationException(TradingSystemException):
    """Exception for configuration related errors."""
    pass


class ValidationException(TradingSystemException):
    """Exception for data validation errors."""
    pass


class MarketClosedException(TradingSystemException):
    """Exception when trying to trade outside market hours."""
    pass


class InsufficientMarginException(TradingSystemException):
    """Exception when there's insufficient margin for a trade."""
    pass


class RateLimitException(TradingSystemException):
    """Exception when API rate limits are exceeded."""
    pass


class ConnectionException(TradingSystemException):
    """Exception for connection related errors."""
    pass


class TimeoutException(TradingSystemException):
    """Exception for operation timeout errors."""
    pass 