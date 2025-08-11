"""
Paper Trading Manager for the Backend API.
Coordinates all paper trading operations and provides API interface.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from decimal import Decimal
import uuid

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from dhan_advanced_algo.providers.paper_trading_broker_provider import PaperTradingBrokerProvider
from dhan_advanced_algo.core.config import ConfigurationManager
from dhan_advanced_algo.core.entities import Order, OrderSide, OrderType, OrderStatus
from dhan_advanced_algo.core.logging_service import LoggingService


class PaperTradingManager:
    """
    Paper Trading Manager for coordinating all paper trading operations.
    Provides a clean interface for the Flask backend.
    """
    
    def __init__(self):
        """Initialize the paper trading manager."""
        self.logger = LoggingService()
        
        # Load configuration
        self.config = ConfigurationManager.get_instance()
        
        # Initialize paper trading broker
        self.paper_broker = PaperTradingBrokerProvider(self.config)
        
        # Track if paper trading is enabled
        self.is_paper_mode = self.config.trading.trading_mode.upper() == "PAPER"
        
        self.logger.info(f"Paper Trading Manager initialized | Mode: {self.config.trading.trading_mode}")
    
    def get_trading_mode(self) -> Dict[str, Any]:
        """
        Get current trading mode.
        
        Returns:
            Dictionary with trading mode information
        """
        return {
            'trading_mode': self.config.trading.trading_mode,
            'is_paper_mode': self.is_paper_mode,
            'paper_balance': float(self.config.trading.paper_trading_balance),
            'commission_per_trade': float(self.config.trading.paper_trading_commission),
            'slippage_factor': self.config.trading.paper_trading_slippage
        }
    
    def set_trading_mode(self, mode: str) -> Dict[str, Any]:
        """
        Set trading mode (PAPER or LIVE).
        
        Args:
            mode: Trading mode to set
            
        Returns:
            Dictionary with operation result
        """
        try:
            mode = mode.upper()
            if mode not in ['PAPER', 'LIVE']:
                return {
                    'success': False,
                    'error': 'Invalid trading mode. Must be PAPER or LIVE'
                }
            
            # Update configuration
            self.config.trading.trading_mode = mode
            self.is_paper_mode = mode == "PAPER"
            
            self.logger.info(f"Trading mode changed to: {mode}")
            
            return {
                'success': True,
                'trading_mode': mode,
                'is_paper_mode': self.is_paper_mode,
                'message': f'Trading mode set to {mode}'
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "set_trading_mode"})
            return {
                'success': False,
                'error': str(e)
            }
    
    def place_paper_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a paper trading order.
        
        Args:
            order_data: Order details dictionary
            
        Returns:
            Dictionary with order placement result
        """
        try:
            if not self.is_paper_mode:
                return {
                    'success': False,
                    'error': 'Paper trading is not enabled. Current mode: LIVE'
                }
            
            # Create order object
            order = Order(
                order_id=str(uuid.uuid4()),
                symbol=order_data['symbol'],
                side=OrderSide(order_data['side']),
                order_type=OrderType(order_data.get('order_type', 'MARKET')),
                quantity=int(order_data['quantity']),
                price=Decimal(str(order_data['price'])),
                stop_loss=Decimal(str(order_data.get('stop_loss', 0))) if order_data.get('stop_loss') else None,
                target=Decimal(str(order_data.get('target', 0))) if order_data.get('target') else None
            )
            
            # Place order through paper broker
            virtual_order_id = self.paper_broker.place_order(order)
            
            return {
                'success': True,
                'order_id': order.order_id,
                'virtual_order_id': virtual_order_id,
                'symbol': order.symbol,
                'side': order.side.value,
                'quantity': order.quantity,
                'price': float(order.price),
                'status': order.status.value,
                'message': f'Paper order placed successfully: {virtual_order_id}'
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "place_paper_order"})
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_paper_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel a paper trading order.
        
        Args:
            order_id: Virtual order ID to cancel
            
        Returns:
            Dictionary with cancellation result
        """
        try:
            if not self.is_paper_mode:
                return {
                    'success': False,
                    'error': 'Paper trading is not enabled'
                }
            
            cancelled = self.paper_broker.cancel_order(order_id)
            
            if cancelled:
                return {
                    'success': True,
                    'order_id': order_id,
                    'message': f'Paper order cancelled: {order_id}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to cancel order {order_id}. Order may not exist or already executed.'
                }
                
        except Exception as e:
            self.logger.log_error(e, {"operation": "cancel_paper_order"})
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_paper_portfolio(self) -> Dict[str, Any]:
        """
        Get paper trading portfolio summary.
        
        Returns:
            Dictionary with portfolio information
        """
        try:
            if not self.is_paper_mode:
                return {
                    'success': False,
                    'error': 'Paper trading is not enabled'
                }
            
            # Get account balance
            balance = self.paper_broker.get_account_balance()
            
            # Get positions
            positions = self.paper_broker.get_positions()
            
            # Get trading stats
            stats = self.paper_broker.get_paper_trading_stats()
            
            # Calculate unrealized P&L manually
            unrealized_pnl = self.paper_broker._calculate_unrealized_pnl()
            
            return {
                'success': True,
                'account_balance': {
                    'available_margin': float(balance.available_margin),
                    'used_margin': float(balance.used_margin),
                    'total_margin': float(balance.total_margin),
                    'cash_balance': float(balance.cash_balance),
                    'unrealized_pnl': float(unrealized_pnl),
                    'realized_pnl': float(self.paper_broker.virtual_balance - self.paper_broker.initial_balance)
                },
                'positions': positions,
                'trading_stats': stats
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_paper_portfolio"})
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_paper_positions(self) -> Dict[str, Any]:
        """
        Get paper trading positions.
        
        Returns:
            Dictionary with positions list
        """
        try:
            if not self.is_paper_mode:
                return {
                    'success': False,
                    'error': 'Paper trading is not enabled'
                }
            
            positions = self.paper_broker.get_positions()
            
            return {
                'success': True,
                'positions': positions,
                'position_count': len(positions)
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_paper_positions"})
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_paper_orders(self) -> Dict[str, Any]:
        """
        Get paper trading orders.
        
        Returns:
            Dictionary with orders information
        """
        try:
            if not self.is_paper_mode:
                return {
                    'success': False,
                    'error': 'Paper trading is not enabled'
                }
            
            # Get pending orders
            pending_orders = []
            for order_id, order in self.paper_broker.virtual_orders.items():
                pending_orders.append({
                    'order_id': order.order_id,
                    'virtual_order_id': order_id,
                    'symbol': order.symbol,
                    'side': order.side.value,
                    'order_type': order.order_type.value,
                    'quantity': order.quantity,
                    'price': float(order.price),
                    'status': order.status.value,
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None
                })
            
            # Get order history (last 50 orders)
            order_history = []
            for order in self.paper_broker.order_history[-50:]:
                order_history.append({
                    'order_id': order.order_id,
                    'virtual_order_id': order.broker_order_id,
                    'symbol': order.symbol,
                    'side': order.side.value,
                    'order_type': order.order_type.value,
                    'quantity': order.quantity,
                    'price': float(order.price),
                    'executed_price': float(order.executed_price) if order.executed_price else None,
                    'executed_quantity': order.executed_quantity,
                    'status': order.status.value,
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                    'executed_at': order.executed_at.isoformat() if order.executed_at else None
                })
            
            return {
                'success': True,
                'pending_orders': pending_orders,
                'order_history': order_history,
                'pending_count': len(pending_orders),
                'history_count': len(order_history)
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_paper_orders"})
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_paper_stats(self) -> Dict[str, Any]:
        """
        Get paper trading performance statistics.
        
        Returns:
            Dictionary with performance stats
        """
        try:
            if not self.is_paper_mode:
                return {
                    'success': False,
                    'error': 'Paper trading is not enabled'
                }
            
            stats = self.paper_broker.get_paper_trading_stats()
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_paper_stats"})
            return {
                'success': False,
                'error': str(e)
            }
    
    def reset_paper_portfolio(self) -> Dict[str, Any]:
        """
        Reset paper trading portfolio to initial state.
        
        Returns:
            Dictionary with reset result
        """
        try:
            if not self.is_paper_mode:
                return {
                    'success': False,
                    'error': 'Paper trading is not enabled'
                }
            
            result = self.paper_broker.reset_paper_trading()
            
            if result.get('reset_successful'):
                return {
                    'success': True,
                    'message': 'Paper trading portfolio reset successfully',
                    'final_stats': result.get('final_stats'),
                    'new_balance': result.get('new_balance')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error during reset')
                }
                
        except Exception as e:
            self.logger.log_error(e, {"operation": "reset_paper_portfolio"})
            return {
                'success': False,
                'error': str(e)
            }
    
    def close_paper_position(self, symbol: str, quantity: Optional[int] = None) -> Dict[str, Any]:
        """
        Close a paper trading position.
        
        Args:
            symbol: Symbol to close position for
            quantity: Quantity to close (None for full position)
            
        Returns:
            Dictionary with close position result
        """
        try:
            if not self.is_paper_mode:
                return {
                    'success': False,
                    'error': 'Paper trading is not enabled'
                }
            
            # Check if position exists
            if symbol not in self.paper_broker.virtual_positions:
                return {
                    'success': False,
                    'error': f'No position found for symbol: {symbol}'
                }
            
            position = self.paper_broker.virtual_positions[symbol]
            
            # Determine quantity to close
            close_quantity = quantity if quantity else position.quantity
            
            if close_quantity > position.quantity:
                return {
                    'success': False,
                    'error': f'Cannot close {close_quantity} shares. Position size: {position.quantity}'
                }
            
            # Create close order (opposite side)
            close_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            
            # Use current entry price as close price (simplified)
            close_price = position.entry_price
            
            order_data = {
                'symbol': symbol,
                'side': close_side.value,
                'order_type': 'MARKET',
                'quantity': close_quantity,
                'price': float(close_price)
            }
            
            # Place close order
            result = self.place_paper_order(order_data)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Position close order placed for {symbol}',
                    'close_order': result,
                    'closed_quantity': close_quantity,
                    'remaining_quantity': position.quantity - close_quantity
                }
            else:
                return result
                
        except Exception as e:
            self.logger.log_error(e, {"operation": "close_paper_position"})
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
paper_trading_manager = PaperTradingManager() 