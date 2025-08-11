"""
Paper Trading Broker Provider implementation.
Simulates real trading without actual money for risk-free strategy testing.
"""

import time
import uuid
from typing import Dict, Optional, List, Any
from decimal import Decimal
from datetime import datetime, timedelta

from ..core.interfaces import ITradingBroker
from ..core.entities import Order, OrderStatus, OrderSide, OrderType, AccountBalance
from ..core.exceptions import BrokerException, OrderException, InsufficientMarginException
from ..core.logging_service import LoggingService


class VirtualPosition:
    """Represents a virtual position in paper trading."""
    
    def __init__(self, symbol: str, quantity: int, entry_price: Decimal, side: OrderSide):
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.side = side
        self.entry_time = datetime.now()
        self.unrealized_pnl = Decimal('0')
        self.realized_pnl = Decimal('0')


class PaperTradingBrokerProvider(ITradingBroker):
    """
    Paper trading broker provider implementation.
    Simulates real trading operations without actual money.
    """
    
    def __init__(self, config):
        """
        Initialize paper trading broker provider.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = LoggingService()
        
        # Virtual portfolio
        self.virtual_balance = config.trading.paper_trading_balance
        self.initial_balance = config.trading.paper_trading_balance
        self.available_margin = self.virtual_balance
        self.used_margin = Decimal('0')
        
        # Virtual positions and orders
        self.virtual_positions: Dict[str, VirtualPosition] = {}
        self.virtual_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        
        # Trading settings
        self.commission_per_trade = config.trading.paper_trading_commission
        self.slippage_factor = config.trading.paper_trading_slippage
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_commission_paid = Decimal('0')
        self.max_drawdown = Decimal('0')
        self.peak_portfolio_value = self.virtual_balance
        
        self.logger.info(f"Paper Trading Broker initialized with ₹{self.virtual_balance:,} virtual balance")
    
    def place_order(self, order: Order) -> str:
        """
        Place a virtual order in paper trading mode.
        
        Args:
            order: Order to place
            
        Returns:
            Virtual order ID
            
        Raises:
            OrderException: If order placement fails
            InsufficientMarginException: If insufficient virtual margin
        """
        try:
            # Generate virtual order ID
            virtual_order_id = f"PAPER_{uuid.uuid4().hex[:8].upper()}"
            
            # Calculate required margin
            required_margin = self._calculate_required_margin(order)
            
            # Check available margin
            if required_margin > self.available_margin:
                raise InsufficientMarginException(
                    f"Insufficient virtual margin. Required: ₹{required_margin:,}, Available: ₹{self.available_margin:,}"
                )
            
            # Update order with virtual broker details
            order.broker_order_id = virtual_order_id
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.now()
            
            # Apply slippage for market orders
            if order.order_type == OrderType.MARKET:
                order.price = self._apply_slippage(order.price, order.side)
            
            # Store virtual order
            self.virtual_orders[virtual_order_id] = order
            
            # Reserve margin
            self.available_margin -= required_margin
            self.used_margin += required_margin
            
            self.logger.info(f"Virtual order placed: {virtual_order_id} | {order.side.value} {order.quantity} {order.symbol} @ ₹{order.price}")
            
            # Simulate order execution after a short delay
            self._schedule_order_execution(order, virtual_order_id)
            
            return virtual_order_id
            
        except Exception as e:
            if isinstance(e, (OrderException, InsufficientMarginException)):
                raise
            self.logger.log_error(e, {
                "operation": "place_order",
                "symbol": order.symbol,
                "side": order.side.value if order.side else None
            })
            raise OrderException(f"Virtual order placement failed: {str(e)}")
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a virtual order.
        
        Args:
            order_id: Virtual order ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        try:
            if order_id not in self.virtual_orders:
                return False
            
            order = self.virtual_orders[order_id]
            
            # Can only cancel pending orders
            if order.status not in [OrderStatus.SUBMITTED, OrderStatus.PENDING]:
                return False
            
            # Update order status
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = datetime.now()
            
            # Release reserved margin
            required_margin = self._calculate_required_margin(order)
            self.available_margin += required_margin
            self.used_margin -= required_margin
            
            # Move to history
            self.order_history.append(order)
            del self.virtual_orders[order_id]
            
            self.logger.info(f"Virtual order cancelled: {order_id}")
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "cancel_order",
                "order_id": order_id
            })
            return False
    
    def get_order_status(self, order_id: str) -> str:
        """
        Get virtual order status.
        
        Args:
            order_id: Virtual order ID
            
        Returns:
            Order status string or None if not found
        """
        try:
            if order_id in self.virtual_orders:
                return self.virtual_orders[order_id].status.value
            
            # Check order history
            for order in self.order_history:
                if order.broker_order_id == order_id:
                    return order.status.value
            
            return "NOT_FOUND"
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "get_order_status",
                "order_id": order_id
            })
            return "ERROR"
    
    def get_executed_price(self, order_id: str) -> Optional[Decimal]:
        """
        Get executed price of a virtual order.
        
        Args:
            order_id: Virtual order ID
            
        Returns:
            Executed price or None if not executed
        """
        try:
            if order_id in self.virtual_orders:
                order = self.virtual_orders[order_id]
                return order.executed_price
            
            # Check order history
            for order in self.order_history:
                if order.broker_order_id == order_id:
                    return order.executed_price
            
            return None
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "get_executed_price",
                "order_id": order_id
            })
            return None
    
    def square_off_position(self, symbol: str, quantity: int, side: OrderSide) -> bool:
        """
        Square off a virtual position.
        
        Args:
            symbol: Symbol to square off
            quantity: Quantity to square off
            side: Side of the position to square off
            
        Returns:
            True if successful
        """
        try:
            # Check if position exists
            if symbol not in self.virtual_positions:
                return False
            
            position = self.virtual_positions[symbol]
            
            # Determine close side (opposite of position side)
            close_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            
            if side != close_side:
                return False
            
            # Use current entry price as close price (simplified)
            close_price = position.entry_price
            
            # Create close order
            order = Order(
                order_id=str(uuid.uuid4()),
                symbol=symbol,
                side=close_side,
                order_type=OrderType.MARKET,
                quantity=quantity,
                price=close_price
            )
            
            # Place close order
            self.place_order(order)
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "square_off_position",
                "symbol": symbol
            })
            return False
    
    def get_account_balance(self) -> AccountBalance:
        """
        Get virtual account balance.
        
        Returns:
            Virtual account balance
        """
        try:
            # Calculate unrealized P&L from open positions
            unrealized_pnl = self._calculate_unrealized_pnl()
            
            # Calculate current portfolio value
            current_portfolio_value = self.virtual_balance + unrealized_pnl
            
            # Update peak and drawdown
            if current_portfolio_value > self.peak_portfolio_value:
                self.peak_portfolio_value = current_portfolio_value
            
            current_drawdown = self.peak_portfolio_value - current_portfolio_value
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown
            
            balance = AccountBalance(
                available_margin=self.available_margin,
                used_margin=self.used_margin,
                total_margin=self.virtual_balance,
                cash_balance=unrealized_pnl + (self.virtual_balance - self.initial_balance)
            )
            
            return balance
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_account_balance"})
            return AccountBalance(
                available_cash=Decimal('0'),
                used_margin=Decimal('0'),
                total_margin=Decimal('0'),
                unrealized_pnl=Decimal('0'),
                realized_pnl=Decimal('0')
            )
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get virtual positions.
        
        Returns:
            List of virtual positions (adapted format)
        """
        try:
            positions_list = []
            
            for position in self.virtual_positions.values():
                # Calculate current P&L (simplified - would need real market data)
                current_price = position.entry_price  # Placeholder - would get from market data
                
                if position.side == OrderSide.BUY:
                    pnl = (current_price - position.entry_price) * position.quantity
                else:
                    pnl = (position.entry_price - current_price) * position.quantity
                
                position.unrealized_pnl = pnl - self.commission_per_trade
                
                # Create position-like object (simplified)
                pos_dict = {
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'side': position.side.value,
                    'entry_price': float(position.entry_price),
                    'current_price': float(current_price),
                    'unrealized_pnl': float(position.unrealized_pnl),
                    'entry_time': position.entry_time.isoformat()
                }
                positions_list.append(pos_dict)
            
            return positions_list
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_positions"})
            return []
    
    def get_paper_trading_stats(self) -> Dict[str, Any]:
        """
        Get paper trading performance statistics.
        
        Returns:
            Dictionary containing performance stats
        """
        try:
            win_rate = (self.winning_trades / max(self.total_trades, 1)) * 100
            
            # Calculate P&L manually instead of relying on AccountBalance
            unrealized_pnl = self._calculate_unrealized_pnl()
            realized_pnl = self.virtual_balance - self.initial_balance
            
            return {
                'initial_balance': float(self.initial_balance),
                'current_balance': float(self.virtual_balance),
                'available_margin': float(self.available_margin),
                'used_margin': float(self.used_margin),
                'unrealized_pnl': float(unrealized_pnl),
                'realized_pnl': float(realized_pnl),
                'total_return_pct': float((self.virtual_balance - self.initial_balance) / self.initial_balance * 100),
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': float(win_rate),
                'total_commission_paid': float(self.total_commission_paid),
                'max_drawdown': float(self.max_drawdown),
                'max_drawdown_pct': float(self.max_drawdown / self.peak_portfolio_value * 100) if self.peak_portfolio_value > 0 else 0,
                'active_positions': len(self.virtual_positions),
                'pending_orders': len(self.virtual_orders)
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_paper_trading_stats"})
            return {
                'initial_balance': float(self.initial_balance),
                'current_balance': float(self.virtual_balance),
                'available_margin': float(self.available_margin),
                'used_margin': float(self.used_margin),
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'total_return_pct': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_commission_paid': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'active_positions': 0,
                'pending_orders': 0
            }
    
    def _calculate_required_margin(self, order: Order) -> Decimal:
        """Calculate required margin for an order."""
        # Simplified margin calculation
        order_value = order.price * order.quantity
        margin_rate = Decimal('0.20')  # 20% margin requirement
        return order_value * margin_rate
    
    def _apply_slippage(self, price: Decimal, side: OrderSide) -> Decimal:
        """Apply slippage to market orders."""
        slippage_amount = price * Decimal(str(self.slippage_factor))
        
        if side == OrderSide.BUY:
            return price + slippage_amount  # Buy at higher price
        else:
            return price - slippage_amount  # Sell at lower price
    
    def _schedule_order_execution(self, order: Order, order_id: str):
        """Simulate order execution after a delay."""
        # In a real implementation, this would be handled by a background task
        # For now, we'll immediately execute the order
        self._execute_virtual_order(order, order_id)
    
    def _execute_virtual_order(self, order: Order, order_id: str):
        """Execute a virtual order."""
        try:
            # Update order status
            order.status = OrderStatus.EXECUTED
            order.executed_at = datetime.now()
            order.executed_price = order.price
            order.executed_quantity = order.quantity
            
            # Calculate commission
            commission = self.commission_per_trade
            self.total_commission_paid += commission
            
            # Update virtual balance
            order_value = order.price * order.quantity
            
            if order.side == OrderSide.BUY:
                # Buying - reduce balance
                total_cost = order_value + commission
                self.virtual_balance -= total_cost
                
                # Create or update position
                if order.symbol in self.virtual_positions:
                    # Add to existing position
                    existing_pos = self.virtual_positions[order.symbol]
                    total_quantity = existing_pos.quantity + order.quantity
                    weighted_avg_price = ((existing_pos.entry_price * existing_pos.quantity) + 
                                        (order.price * order.quantity)) / total_quantity
                    existing_pos.quantity = total_quantity
                    existing_pos.entry_price = weighted_avg_price
                else:
                    # Create new position
                    self.virtual_positions[order.symbol] = VirtualPosition(
                        order.symbol, order.quantity, order.price, order.side
                    )
            
            else:  # SELL
                # Selling - increase balance
                total_proceeds = order_value - commission
                self.virtual_balance += total_proceeds
                
                # Update or close position
                if order.symbol in self.virtual_positions:
                    existing_pos = self.virtual_positions[order.symbol]
                    
                    if existing_pos.quantity <= order.quantity:
                        # Close position completely
                        pnl = (order.price - existing_pos.entry_price) * existing_pos.quantity - commission
                        existing_pos.realized_pnl = pnl
                        
                        if pnl > 0:
                            self.winning_trades += 1
                        else:
                            self.losing_trades += 1
                        
                        del self.virtual_positions[order.symbol]
                    else:
                        # Partial close
                        existing_pos.quantity -= order.quantity
                        partial_pnl = (order.price - existing_pos.entry_price) * order.quantity - commission
                        existing_pos.realized_pnl += partial_pnl
            
            # Update margin
            required_margin = self._calculate_required_margin(order)
            self.used_margin -= required_margin
            self.available_margin += required_margin
            
            # Update trade count
            self.total_trades += 1
            
            # Move to history
            self.order_history.append(order)
            if order_id in self.virtual_orders:
                del self.virtual_orders[order_id]
            
            self.logger.info(f"Virtual order executed: {order_id} | P&L impact: Commission ₹{commission}")
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "execute_virtual_order",
                "order_id": order_id
            })
    
    def _calculate_unrealized_pnl(self) -> Decimal:
        """Calculate total unrealized P&L from open positions."""
        total_unrealized = Decimal('0')
        
        for position in self.virtual_positions.values():
            # In a real implementation, this would use current market prices
            # For now, we'll use entry price (no unrealized P&L)
            total_unrealized += position.unrealized_pnl
        
        return total_unrealized
    
    def reset_paper_trading(self) -> Dict[str, Any]:
        """
        Reset paper trading portfolio to initial state.
        
        Returns:
            Reset confirmation with final stats
        """
        try:
            # Capture final stats before reset
            final_stats = self.get_paper_trading_stats()
            
            # Reset all values
            self.virtual_balance = self.initial_balance
            self.available_margin = self.virtual_balance
            self.used_margin = Decimal('0')
            self.virtual_positions.clear()
            self.virtual_orders.clear()
            self.order_history.clear()
            
            self.total_trades = 0
            self.winning_trades = 0
            self.losing_trades = 0
            self.total_commission_paid = Decimal('0')
            self.max_drawdown = Decimal('0')
            self.peak_portfolio_value = self.virtual_balance
            
            self.logger.info("Paper trading portfolio reset to initial state")
            
            return {
                'reset_successful': True,
                'final_stats': final_stats,
                'new_balance': float(self.virtual_balance)
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "reset_paper_trading"})
            return {'reset_successful': False, 'error': str(e)} 