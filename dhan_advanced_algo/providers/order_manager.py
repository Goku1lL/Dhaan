"""
Order Manager implementation.
Handles order lifecycle, order book management, and order execution tracking.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from ..core.interfaces import IOrderManager
from ..core.entities import Order, OrderStatus, OrderSide, OrderType
from ..core.exceptions import OrderManagementException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager


class OrderManager(IOrderManager):
    """
    Order manager implementation.
    Handles order lifecycle, order book management, and order execution tracking.
    """

    def __init__(self, config: ConfigurationManager):
        """
        Initialize order manager.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = LoggingService()

        # Order storage
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        
        # Order book (simplified)
        self.buy_orders: Dict[str, List[Order]] = {}
        self.sell_orders: Dict[str, List[Order]] = {}
        
        # Configuration
        self.max_pending_orders = self.config.trading.max_pending_orders
        self.order_timeout_minutes = self.config.trading.order_timeout_minutes

        self.logger.info("Order Manager initialized")

    def initialize(self) -> None:
        """Initialize order manager components."""
        try:
            # Load existing orders from storage if any
            self._load_orders()
            
            self.logger.info("Order Manager initialized successfully")
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize"})
            raise OrderManagementException(f"Failed to initialize order manager: {str(e)}")

    def create_order(self, symbol: str, side: OrderSide, order_type: OrderType, 
                    quantity: int, price: Optional[Decimal] = None, 
                    stop_loss: Optional[Decimal] = None, target: Optional[Decimal] = None) -> Order:
        """
        Create a new order.

        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            order_type: Order type (MARKET/LIMIT)
            quantity: Order quantity
            price: Order price (required for LIMIT orders)
            stop_loss: Stop loss price
            target: Target price

        Returns:
            Created order object

        Raises:
            OrderManagementException: If order creation fails
        """
        try:
            # Validate order parameters
            if not self._validate_order_parameters(symbol, side, order_type, quantity, price):
                raise OrderManagementException("Invalid order parameters")

            # Check pending order limits
            if self._get_pending_order_count(symbol) >= self.max_pending_orders:
                raise OrderManagementException(f"Maximum pending orders limit {self.max_pending_orders} reached for {symbol}")

            # Generate unique order ID
            order_id = str(uuid.uuid4())

            # Create order
            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_loss=stop_loss,
                target=target,
                status=OrderStatus.PENDING,
                created_at=datetime.now()
            )

            # Store order
            self.orders[order_id] = order

            # Add to order book
            self._add_to_order_book(order)

            self.logger.info(f"Order created: {order_id} {symbol} {side.value} {quantity} @ {price}")
            return order

        except Exception as e:
            if isinstance(e, OrderManagementException):
                raise
            self.logger.log_error(e, {
                "operation": "create_order",
                "symbol": symbol,
                "side": side.value if side else None
            })
            raise OrderManagementException(f"Order creation failed: {str(e)}")

    def place_order(self, order: Order) -> str:
        """
        Place an order with the broker.

        Args:
            order: Order to place

        Returns:
            Broker order ID

        Raises:
            OrderManagementException: If order placement fails
        """
        try:
            # Validate order exists
            if order.order_id not in self.orders:
                raise OrderManagementException(f"Order {order.order_id} not found")

            # Update order status
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.now()

            # Simulate broker response (in real implementation, this would call broker API)
            broker_order_id = f"BROKER_{order.order_id}"
            order.broker_order_id = broker_order_id

            self.logger.info(f"Order placed with broker: {order.order_id} -> {broker_order_id}")
            return broker_order_id

        except Exception as e:
            if isinstance(e, OrderManagementException):
                raise
            self.logger.log_error(e, {
                "operation": "place_order",
                "order_id": order.order_id
            })
            raise OrderManagementException(f"Order placement failed: {str(e)}")

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully, False otherwise

        Raises:
            OrderManagementException: If order cancellation fails
        """
        try:
            if order_id not in self.orders:
                raise OrderManagementException(f"Order {order_id} not found")

            order = self.orders[order_id]

            # Check if order can be cancelled
            if order.status not in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                raise OrderManagementException(f"Order {order_id} cannot be cancelled in status {order.status.value}")

            # Update order status
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = datetime.now()

            # Remove from order book
            self._remove_from_order_book(order)

            # Simulate broker cancellation (in real implementation, this would call broker API)
            self.logger.info(f"Order cancelled: {order_id}")
            return True

        except Exception as e:
            if isinstance(e, OrderManagementException):
                raise
            self.logger.log_error(e, {
                "operation": "cancel_order",
                "order_id": order_id
            })
            raise OrderManagementException(f"Order cancellation failed: {str(e)}")

    def update_order_status(self, order_id: str, status: OrderStatus, 
                          fill_price: Optional[Decimal] = None, 
                          filled_quantity: Optional[int] = None) -> bool:
        """
        Update order status and execution details.

        Args:
            order_id: Order ID to update
            status: New order status
            fill_price: Fill price (for filled orders)
            filled_quantity: Filled quantity (for filled orders)

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if order_id not in self.orders:
                self.logger.warning(f"Order {order_id} not found for status update")
                return False

            order = self.orders[order_id]

            # Update status
            order.status = status
            order.last_update = datetime.now()

            # Update execution details if order is filled
            if status == OrderStatus.FILLED:
                if fill_price is not None:
                    order.fill_price = fill_price
                if filled_quantity is not None:
                    order.filled_quantity = filled_quantity
                order.filled_at = datetime.now()

                # Remove from order book
                self._remove_from_order_book(order)

            # Move to history if order is completed
            if status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                self._move_to_history(order)

            self.logger.info(f"Order status updated: {order_id} -> {status.value}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_order_status",
                "order_id": order_id
            })
            return False

    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order object if exists, None otherwise
        """
        return self.orders.get(order_id)

    def get_orders(self, symbol: Optional[str] = None, 
                   status: Optional[OrderStatus] = None) -> List[Order]:
        """
        Get orders with optional filtering.

        Args:
            symbol: Filter by symbol
            status: Filter by status

        Returns:
            List of filtered orders
        """
        try:
            filtered_orders = list(self.orders.values())

            if symbol:
                filtered_orders = [o for o in filtered_orders if o.symbol == symbol]

            if status:
                filtered_orders = [o for o in filtered_orders if o.status == status]

            return filtered_orders

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_orders"})
            return []

    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get pending orders.

        Args:
            symbol: Filter by symbol

        Returns:
            List of pending orders
        """
        return self.get_orders(symbol, OrderStatus.PENDING)

    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get active (pending + submitted) orders.

        Args:
            symbol: Filter by symbol

        Returns:
            List of active orders
        """
        try:
            active_orders = []
            for order in self.orders.values():
                if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                    if symbol is None or order.symbol == symbol:
                        active_orders.append(order)

            return active_orders

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_active_orders"})
            return []

    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Cancel all orders for a symbol or all symbols.

        Args:
            symbol: Symbol to cancel orders for (None for all symbols)

        Returns:
            Number of orders cancelled
        """
        try:
            orders_to_cancel = self.get_active_orders(symbol)
            cancelled_count = 0

            for order in orders_to_cancel:
                try:
                    if self.cancel_order(order.order_id):
                        cancelled_count += 1
                except Exception as e:
                    self.logger.log_error(e, {
                        "operation": "cancel_all_orders",
                        "order_id": order.order_id
                    })

            self.logger.info(f"Cancelled {cancelled_count} orders for {symbol or 'all symbols'}")
            return cancelled_count

        except Exception as e:
            self.logger.log_error(e, {"operation": "cancel_all_orders"})
            return 0

    def get_order_book(self, symbol: str) -> Dict[str, Any]:
        """
        Get order book for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary containing order book data
        """
        try:
            buy_orders = self.buy_orders.get(symbol, [])
            sell_orders = self.sell_orders.get(symbol, [])

            # Sort by price (best prices first)
            buy_orders.sort(key=lambda x: x.price or Decimal('0'), reverse=True)
            sell_orders.sort(key=lambda x: x.price or Decimal('0'))

            order_book = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'buy_orders': [
                    {
                        'price': float(order.price) if order.price else None,
                        'quantity': order.quantity,
                        'order_id': order.order_id
                    }
                    for order in buy_orders[:10]  # Top 10 buy orders
                ],
                'sell_orders': [
                    {
                        'price': float(order.price) if order.price else None,
                        'quantity': order.quantity,
                        'order_id': order.order_id
                    }
                    for order in sell_orders[:10]  # Top 10 sell orders
                ]
            }

            return order_book

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "get_order_book",
                "symbol": symbol
            })
            return {'error': str(e)}

    def cleanup_expired_orders(self) -> int:
        """
        Clean up expired orders.

        Returns:
            Number of orders cleaned up
        """
        try:
            if not self.order_timeout_minutes:
                return 0

            cutoff_time = datetime.now() - timedelta(minutes=self.order_timeout_minutes)
            expired_orders = []

            for order in self.get_active_orders():
                if order.created_at and order.created_at < cutoff_time:
                    expired_orders.append(order)

            cleaned_count = 0
            for order in expired_orders:
                try:
                    if self.cancel_order(order.order_id):
                        cleaned_count += 1
                except Exception as e:
                    self.logger.log_error(e, {
                        "operation": "cleanup_expired_orders",
                        "order_id": order.order_id
                    })

            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired orders")

            return cleaned_count

        except Exception as e:
            self.logger.log_error(e, {"operation": "cleanup_expired_orders"})
            return 0

    def get_order_summary(self) -> Dict[str, Any]:
        """
        Get summary of all orders.

        Returns:
            Dictionary containing order summary
        """
        try:
            active_orders = self.get_active_orders()
            completed_orders = [o for o in self.orders.values() 
                              if o.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]]

            summary = {
                'total_orders': len(self.orders),
                'active_orders': len(active_orders),
                'completed_orders': len(completed_orders),
                'orders_by_status': {
                    status.value: len([o for o in self.orders.values() if o.status == status])
                    for status in OrderStatus
                },
                'orders_by_side': {
                    'BUY': len([o for o in active_orders if o.side == OrderSide.BUY]),
                    'SELL': len([o for o in active_orders if o.side == OrderSide.SELL])
                },
                'pending_orders_count': len(self.get_pending_orders())
            }

            return summary

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_order_summary"})
            return {'error': str(e)}

    def _validate_order_parameters(self, symbol: str, side: OrderSide, 
                                 order_type: OrderType, quantity: int, 
                                 price: Optional[Decimal]) -> bool:
        """Validate order parameters."""
        try:
            if not symbol or not symbol.strip():
                return False

            if not side or not isinstance(side, OrderSide):
                return False

            if not order_type or not isinstance(order_type, OrderType):
                return False

            if quantity <= 0:
                return False

            if order_type == OrderType.LIMIT and (price is None or price <= 0):
                return False

            return True

        except Exception as e:
            self.logger.log_error(e, {"operation": "validate_order_parameters"})
            return False

    def _add_to_order_book(self, order: Order) -> None:
        """Add order to order book."""
        try:
            if order.side == OrderSide.BUY:
                if order.symbol not in self.buy_orders:
                    self.buy_orders[order.symbol] = []
                self.buy_orders[order.symbol].append(order)
            else:
                if order.symbol not in self.sell_orders:
                    self.sell_orders[order.symbol] = []
                self.sell_orders[order.symbol].append(order)

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "add_to_order_book",
                "order_id": order.order_id
            })

    def _remove_from_order_book(self, order: Order) -> None:
        """Remove order from order book."""
        try:
            if order.side == OrderSide.BUY:
                if order.symbol in self.buy_orders:
                    self.buy_orders[order.symbol] = [
                        o for o in self.buy_orders[order.symbol] 
                        if o.order_id != order.order_id
                    ]
            else:
                if order.symbol in self.sell_orders:
                    self.sell_orders[order.symbol] = [
                        o for o in self.sell_orders[order.symbol] 
                        if o.order_id != order.order_id
                    ]

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "remove_from_order_book",
                "order_id": order.order_id
            })

    def _get_pending_order_count(self, symbol: str) -> int:
        """Get count of pending orders for a symbol."""
        try:
            return len(self.get_pending_orders(symbol))
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_pending_order_count"})
            return 0

    def _move_to_history(self, order: Order) -> None:
        """Move completed order to history."""
        try:
            self.order_history.append(order)
            # Keep only last 1000 orders in history
            if len(self.order_history) > 1000:
                self.order_history = self.order_history[-1000:]

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "move_to_history",
                "order_id": order.order_id
            })

    def _load_orders(self) -> None:
        """Load existing orders from storage."""
        try:
            # This would typically load from a database or file
            # For now, just log that we're ready to accept new orders
            self.logger.info("Order storage ready for new orders")

        except Exception as e:
            self.logger.log_error(e, {"operation": "load_orders"}) 