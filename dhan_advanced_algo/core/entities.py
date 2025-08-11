"""
Core domain entities for the Dhan Advanced Algo Trading System.
These are the fundamental business objects that represent trading concepts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


class OrderType(Enum):
    """Enumeration of order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"


class OrderSide(Enum):
    """Enumeration of order sides."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Enumeration of order statuses."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TradeStatus(Enum):
    """Enumeration of trade statuses."""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ExitReason(Enum):
    """Enumeration of exit reasons."""
    STOP_LOSS_HIT = "STOP_LOSS_HIT"
    TARGET_HIT = "TARGET_HIT"
    MARKET_CLOSE = "MARKET_CLOSE"
    MANUAL_EXIT = "MANUAL_EXIT"


class PositionStatus(Enum):
    """Enumeration of position statuses."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class SignalType(Enum):
    """Enumeration of signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStrength(Enum):
    """Enumeration of signal strengths."""
    WEAK = "WEAK"
    MEDIUM = "MEDIUM"
    STRONG = "STRONG"


@dataclass
class Position:
    """Represents a trading position."""
    position_id: str = ""
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    quantity: int = 0
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    target: Optional[Decimal] = None
    status: PositionStatus = PositionStatus.OPEN
    created_at: Optional[datetime] = None
    last_update: Optional[datetime] = None
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    exit_price: Optional[Decimal] = None
    exit_reason: Optional[str] = None
    closed_at: Optional[datetime] = None
    realized_pnl: Optional[Decimal] = None
    order_id: Optional[str] = None
    
    def is_active(self) -> bool:
        """Check if position is active."""
        return self.status == PositionStatus.OPEN
    
    def calculate_pnl(self, current_price: Decimal) -> Decimal:
        """Calculate unrealized P&L."""
        if not self.entry_price or not self.quantity:
            return Decimal('0')
        
        if self.side == OrderSide.BUY:
            return (current_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - current_price) * self.quantity
    
    def close_position(self, exit_price: Decimal, exit_reason: str, exit_time: Optional[datetime] = None) -> None:
        """Close the position."""
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        self.closed_at = exit_time or datetime.now()
        self.realized_pnl = self.calculate_pnl(exit_price)
        self.status = PositionStatus.CLOSED


@dataclass
class Order:
    """Represents a trading order."""
    order_id: str = ""
    symbol: str = ""
    order_type: OrderType = OrderType.MARKET
    side: OrderSide = OrderSide.BUY
    quantity: int = 0
    price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    target: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    broker_order_id: Optional[str] = None
    placed_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    filled_price: Optional[Decimal] = None
    filled_quantity: int = 0
    remarks: str = ""
    
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED and self.filled_quantity == self.quantity
    
    def is_partially_filled(self) -> bool:
        """Check if order is partially filled."""
        return self.status == OrderStatus.PARTIALLY_FILLED
    
    def can_cancel(self) -> bool:
        """Check if order can be cancelled."""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]


@dataclass
class Trade:
    """Represents a completed trade."""
    trade_id: str = ""
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    quantity: int = 0
    execution_price: Optional[Decimal] = None
    execution_time: Optional[datetime] = None
    realized_pnl: Optional[Decimal] = None
    order_id: Optional[str] = None
    position_id: Optional[str] = None
    remarks: str = ""


@dataclass
class MarketData:
    """Represents market data for a symbol."""
    symbol: str = ""
    ltp: Optional[Decimal] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    volume: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_valid(self) -> bool:
        """Check if market data is valid."""
        return all([
            self.symbol,
            self.ltp is not None,
            self.open is not None,
            self.high is not None,
            self.low is not None,
            self.close is not None
        ])


@dataclass
class OHLCV:
    """Represents OHLCV data."""
    open: Decimal = Decimal('0')
    high: Decimal = Decimal('0')
    low: Decimal = Decimal('0')
    close: Decimal = Decimal('0')
    volume: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Symbol:
    """Represents a trading symbol."""
    symbol: str = ""
    name: str = ""
    exchange: str = ""
    instrument_type: str = ""
    lot_size: int = 1
    tick_size: Decimal = Decimal('0.01')
    is_active: bool = True


@dataclass
class IndicatorData:
    """Represents calculated indicator values."""
    symbol: str = ""
    rsi: Optional[Decimal] = None
    supertrend: Optional[Decimal] = None
    supertrend_direction: Optional[int] = None
    sma_20: Optional[Decimal] = None
    sma_50: Optional[Decimal] = None
    bollinger_upper: Optional[Decimal] = None
    bollinger_lower: Optional[Decimal] = None
    bollinger_middle: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TradingSignal:
    """Represents a trading signal."""
    id: UUID = field(default_factory=uuid4)
    symbol: str = ""
    signal_type: OrderSide = OrderSide.BUY
    strength: float = 0.0  # 0.0 to 1.0
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    target: Optional[Decimal] = None
    confidence: float = 0.0  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    indicators: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if signal is valid."""
        return (
            self.symbol and
            self.strength > 0.0 and
            self.confidence > 0.0 and
            self.entry_price is not None
        )


@dataclass
class Strategy:
    """Represents a trading strategy."""
    strategy_id: str = ""
    name: str = ""
    description: str = ""
    strategy_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: Optional[datetime] = None


@dataclass
class Signal:
    """Represents a strategy signal."""
    signal_id: str = ""
    strategy_id: str = ""
    symbol: str = ""
    signal_type: SignalType = SignalType.BUY
    strength: SignalStrength = SignalStrength.MEDIUM
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    target: Optional[Decimal] = None
    confidence: float = 0.0
    timestamp: Optional[datetime] = None
    status: str = "ACTIVE"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountBalance:
    """Represents account balance information."""
    available_margin: Decimal = Decimal('0')
    used_margin: Decimal = Decimal('0')
    total_margin: Decimal = Decimal('0')
    cash_balance: Decimal = Decimal('0')
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_free_margin(self) -> Decimal:
        """Get available free margin."""
        return self.available_margin - self.used_margin
    
    def has_sufficient_margin(self, required_margin: Decimal) -> bool:
        """Check if there's sufficient margin for a trade."""
        return self.get_free_margin() >= required_margin


class Entity(ABC):
    """Abstract base class for all entities."""
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the entity."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        pass
    
    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Create entity from dictionary."""
        pass 