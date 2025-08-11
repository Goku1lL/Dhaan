"""
Position Manager implementation.
Handles position management, P&L tracking, and position lifecycle.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime

from ..core.interfaces import IPositionManager
from ..core.entities import Position, Order, OrderSide, PositionStatus
from ..core.exceptions import PositionManagementException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager


class PositionManager(IPositionManager):
    """
    Position manager implementation.
    Handles position management, P&L tracking, and position lifecycle.
    """

    def __init__(self, config: ConfigurationManager):
        """
        Initialize position manager.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = LoggingService()

        # Position storage
        self.positions: Dict[str, Position] = {}
        self.position_history: List[Position] = []
        
        # Configuration
        self.max_positions = self.config.trading.max_positions
        self.position_timeout_hours = self.config.trading.position_timeout_hours

        self.logger.info("Position Manager initialized")

    def initialize(self) -> None:
        """Initialize position manager components."""
        try:
            # Load existing positions from storage if any
            self._load_positions()
            
            self.logger.info("Position Manager initialized successfully")
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize"})
            raise PositionManagementException(f"Failed to initialize position manager: {str(e)}")

    def create_position(self, order: Order, entry_price: Decimal, 
                       stop_loss: Optional[Decimal] = None, target: Optional[Decimal] = None) -> Position:
        """
        Create a new position from an order.

        Args:
            order: Order that created the position
            entry_price: Entry price for the position
            stop_loss: Stop loss price
            target: Target price

        Returns:
            Created position object

        Raises:
            PositionManagementException: If position creation fails
        """
        try:
            # Validate order
            if not order or not order.order_id:
                raise PositionManagementException("Invalid order for position creation")

            # Check position limits
            if len(self.get_open_positions()) >= self.max_positions:
                raise PositionManagementException(f"Maximum positions limit {self.max_positions} reached")

            # Create position ID
            position_id = f"POS_{order.order_id}"

            # Create position
            position = Position(
                position_id=position_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                status=PositionStatus.OPEN,
                created_at=datetime.now(),
                order_id=order.order_id
            )

            # Store position
            self.positions[position_id] = position

            self.logger.info(f"Position created: {position_id} {order.symbol} {order.side.value} {order.quantity}")
            return position

        except Exception as e:
            if isinstance(e, PositionManagementException):
                raise
            self.logger.log_error(e, {
                "operation": "create_position",
                "order_id": order.order_id if order else None
            })
            raise PositionManagementException(f"Position creation failed: {str(e)}")

    def update_position(self, position_id: str, current_price: Decimal, 
                       unrealized_pnl: Optional[Decimal] = None) -> bool:
        """
        Update position with current market data.

        Args:
            position_id: Position ID to update
            current_price: Current market price
            unrealized_pnl: Unrealized P&L

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if position_id not in self.positions:
                self.logger.warning(f"Position {position_id} not found for update")
                return False

            position = self.positions[position_id]

            # Update current price and P&L
            position.current_price = current_price
            position.last_update = datetime.now()

            if unrealized_pnl is not None:
                position.unrealized_pnl = unrealized_pnl

            # Check if stop loss or target hit
            self._check_exit_conditions(position, current_price)

            self.logger.debug(f"Position updated: {position_id} @ {current_price}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_position",
                "position_id": position_id
            })
            return False

    def close_position(self, position_id: str, exit_price: Decimal, 
                      exit_reason: str = "MANUAL") -> Optional[Position]:
        """
        Close a position.

        Args:
            position_id: Position ID to close
            exit_price: Exit price
            exit_reason: Reason for closing

        Returns:
            Closed position object if successful, None otherwise
        """
        try:
            if position_id not in self.positions:
                self.logger.warning(f"Position {position_id} not found for closing")
                return None

            position = self.positions[position_id]

            # Check if position is already closed
            if position.status == PositionStatus.CLOSED:
                self.logger.warning(f"Position {position_id} is already closed")
                return position

            # Update position
            position.exit_price = exit_price
            position.exit_reason = exit_reason
            position.closed_at = datetime.now()
            position.status = PositionStatus.CLOSED

            # Calculate realized P&L
            if position.side == OrderSide.BUY:
                position.realized_pnl = (exit_price - position.entry_price) * position.quantity
            else:
                position.realized_pnl = (position.entry_price - exit_price) * position.quantity

            # Move to history
            self._move_to_history(position)

            self.logger.info(f"Position closed: {position_id} @ {exit_price}, P&L: {position.realized_pnl}")
            return position

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "close_position",
                "position_id": position_id
            })
            return None

    def get_position(self, position_id: str) -> Optional[Position]:
        """
        Get position by ID.

        Args:
            position_id: Position ID

        Returns:
            Position object if exists, None otherwise
        """
        return self.positions.get(position_id)

    def get_positions(self, symbol: Optional[str] = None, 
                      status: Optional[PositionStatus] = None) -> List[Position]:
        """
        Get positions with optional filtering.

        Args:
            symbol: Filter by symbol
            status: Filter by status

        Returns:
            List of filtered positions
        """
        try:
            filtered_positions = list(self.positions.values())

            if symbol:
                filtered_positions = [p for p in filtered_positions if p.symbol == symbol]

            if status:
                filtered_positions = [p for p in filtered_positions if p.status == status]

            return filtered_positions

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_positions"})
            return []

    def get_open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """
        Get open positions.

        Args:
            symbol: Filter by symbol

        Returns:
            List of open positions
        """
        return self.get_positions(symbol, PositionStatus.OPEN)

    def get_position_summary(self) -> Dict[str, Any]:
        """
        Get summary of all positions.

        Returns:
            Dictionary containing position summary
        """
        try:
            open_positions = self.get_open_positions()
            closed_positions = [p for p in self.positions.values() 
                               if p.status == PositionStatus.CLOSED]

            # Calculate total P&L
            total_realized_pnl = sum(p.realized_pnl for p in closed_positions if p.realized_pnl)
            total_unrealized_pnl = sum(p.unrealized_pnl for p in open_positions if p.unrealized_pnl)

            summary = {
                'total_positions': len(self.positions),
                'open_positions': len(open_positions),
                'closed_positions': len(closed_positions),
                'total_realized_pnl': float(total_realized_pnl),
                'total_unrealized_pnl': float(total_unrealized_pnl),
                'positions_by_side': {
                    'BUY': len([p for p in open_positions if p.side == OrderSide.BUY]),
                    'SELL': len([p for p in open_positions if p.side == OrderSide.SELL])
                },
                'positions_by_symbol': {}
            }

            # Group by symbol
            for position in open_positions:
                if position.symbol not in summary['positions_by_symbol']:
                    summary['positions_by_symbol'][position.symbol] = 0
                summary['positions_by_symbol'][position.symbol] += 1

            return summary

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_position_summary"})
            return {'error': str(e)}

    def update_stop_loss(self, position_id: str, new_stop_loss: Decimal) -> bool:
        """
        Update stop loss for a position.

        Args:
            position_id: Position ID
            new_stop_loss: New stop loss price

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if position_id not in self.positions:
                return False

            position = self.positions[position_id]
            
            if position.status != PositionStatus.OPEN:
                return False

            # Validate stop loss
            if position.side == OrderSide.BUY and new_stop_loss >= position.entry_price:
                self.logger.warning(f"Stop loss {new_stop_loss} must be below entry {position.entry_price} for BUY position")
                return False
            
            if position.side == OrderSide.SELL and new_stop_loss <= position.entry_price:
                self.logger.warning(f"Stop loss {new_stop_loss} must be above entry {position.entry_price} for SELL position")
                return False

            position.stop_loss = new_stop_loss
            position.last_update = datetime.now()

            self.logger.info(f"Stop loss updated for {position_id}: {new_stop_loss}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_stop_loss",
                "position_id": position_id
            })
            return False

    def update_target(self, position_id: str, new_target: Decimal) -> bool:
        """
        Update target for a position.

        Args:
            position_id: Position ID
            new_target: New target price

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if position_id not in self.positions:
                return False

            position = self.positions[position_id]
            
            if position.status != PositionStatus.OPEN:
                return False

            # Validate target
            if position.side == OrderSide.BUY and new_target <= position.entry_price:
                self.logger.warning(f"Target {new_target} must be above entry {position.entry_price} for BUY position")
                return False
            
            if position.side == OrderSide.SELL and new_target >= position.entry_price:
                self.logger.warning(f"Target {new_target} must be below entry {position.entry_price} for SELL position")
                return False

            position.target = new_target
            position.last_update = datetime.now()

            self.logger.info(f"Target updated for {position_id}: {new_target}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_target",
                "position_id": position_id
            })
            return False

    def cleanup_expired_positions(self) -> int:
        """
        Clean up expired positions.

        Returns:
            Number of positions cleaned up
        """
        try:
            if not self.position_timeout_hours:
                return 0

            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=self.position_timeout_hours)
            expired_positions = []

            for position in self.get_open_positions():
                if position.created_at and position.created_at < cutoff_time:
                    expired_positions.append(position)

            cleaned_count = 0
            for position in expired_positions:
                try:
                    # Close expired position at current price (or last known price)
                    exit_price = position.current_price or position.entry_price
                    if self.close_position(position.position_id, exit_price, "EXPIRED"):
                        cleaned_count += 1
                except Exception as e:
                    self.logger.log_error(e, {
                        "operation": "cleanup_expired_positions",
                        "position_id": position.position_id
                    })

            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired positions")

            return cleaned_count

        except Exception as e:
            self.logger.log_error(e, {"operation": "cleanup_expired_positions"})
            return 0

    def _check_exit_conditions(self, position: Position, current_price: Decimal) -> None:
        """Check if position should be closed based on stop loss or target."""
        try:
            if position.status != PositionStatus.OPEN:
                return

            # Check stop loss
            if position.stop_loss:
                if (position.side == OrderSide.BUY and current_price <= position.stop_loss) or \
                   (position.side == OrderSide.SELL and current_price >= position.stop_loss):
                    self.logger.info(f"Stop loss hit for {position.position_id} @ {current_price}")
                    self.close_position(position.position_id, current_price, "STOP_LOSS")
                    return

            # Check target
            if position.target:
                if (position.side == OrderSide.BUY and current_price >= position.target) or \
                   (position.side == OrderSide.SELL and current_price <= position.target):
                    self.logger.info(f"Target hit for {position.position_id} @ {current_price}")
                    self.close_position(position.position_id, current_price, "TARGET")
                    return

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "check_exit_conditions",
                "position_id": position.position_id
            })

    def _move_to_history(self, position: Position) -> None:
        """Move closed position to history."""
        try:
            self.position_history.append(position)
            # Keep only last 1000 positions in history
            if len(self.position_history) > 1000:
                self.position_history = self.position_history[-1000:]

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "move_to_history",
                "position_id": position.position_id
            })

    def _load_positions(self) -> None:
        """Load existing positions from storage."""
        try:
            # This would typically load from a database or file
            # For now, just log that we're ready to accept new positions
            self.logger.info("Position storage ready for new positions")

        except Exception as e:
            self.logger.log_error(e, {"operation": "load_positions"}) 