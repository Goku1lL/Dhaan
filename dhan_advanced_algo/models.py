"""Data models and structures for the Algo Trading System."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, date


@dataclass
class OrderTemplate:
    """Template for individual trade orders."""
    Name: Optional[str] = None
    Date: Optional[str] = None
    Entry_Time: Optional[str] = None
    Entry_Price: Optional[float] = None
    Buy_Sell: Optional[str] = None
    Quantity: Optional[int] = None
    StopLoss: Optional[float] = None
    Target: Optional[float] = None
    Exit_Time: Optional[str] = None
    Exit_Price: Optional[float] = None
    PNL: Optional[float] = None
    Remark: Optional[str] = None
    Traded: Optional[str] = None
    Entry_Order_ID: Optional[str] = None
    StopLoss_Order_ID: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Excel export."""
        return {
            key: value for key, value in self.__dict__.items()
        }

    def update_entry_details(self, **kwargs):
        """Update entry-related fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def update_exit_details(self, **kwargs):
        """Update exit-related fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def reset_for_reentry(self):
        """Reset order for potential re-entry."""
        self.Date = None
        self.Entry_Time = None
        self.Entry_Price = None
        self.Buy_Sell = None
        self.Quantity = None
        self.StopLoss = None
        self.Target = None
        self.Exit_Time = None
        self.Exit_Price = None
        self.PNL = None
        self.Remark = None
        self.Traded = None
        self.Entry_Order_ID = None
        self.StopLoss_Order_ID = None


@dataclass
class TradingState:
    """Global trading state management."""
    order_book: Dict[str, OrderTemplate] = field(default_factory=dict)
    completed_orders: list = field(default_factory=list)
    selected_watchlist: list = field(default_factory=list)
    pre_market_done: bool = False
    current_time: Optional[datetime] = None
    ltp_data: Dict[str, float] = field(default_factory=dict)

    def add_order(self, symbol: str, order: OrderTemplate):
        """Add a new order to the order book."""
        self.order_book[symbol] = order

    def get_order(self, symbol: str) -> Optional[OrderTemplate]:
        """Get order for a specific symbol."""
        return self.order_book.get(symbol)

    def mark_order_completed(self, symbol: str):
        """Mark an order as completed and move to completed orders."""
        if symbol in self.order_book:
            completed_order = self.order_book[symbol]
            self.completed_orders.append(completed_order)
            del self.order_book[symbol]

    def reset_order_for_reentry(self, symbol: str):
        """Reset an order for potential re-entry."""
        if symbol in self.order_book:
            self.order_book[symbol].reset_for_reentry()

    def clear_completed_orders(self):
        """Clear the completed orders list."""
        self.completed_orders.clear()

    def update_ltp_data(self, ltp_dict: Dict[str, float]):
        """Update LTP data for all symbols."""
        self.ltp_data.update(ltp_dict)

    def get_ltp(self, symbol: str) -> Optional[float]:
        """Get LTP for a specific symbol."""
        return self.ltp_data.get(symbol) 