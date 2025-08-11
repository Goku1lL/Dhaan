"""
Risk Manager implementation.
Handles position sizing, risk calculation, and risk monitoring.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime

from ..core.interfaces import IRiskManager
from ..core.entities import Position, Order, OrderSide
from ..core.exceptions import RiskManagementException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager


class RiskManager(IRiskManager):
    """
    Risk manager implementation.
    Handles position sizing, risk calculation, and risk monitoring.
    """

    def __init__(self, config: ConfigurationManager):
        """
        Initialize risk manager.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = LoggingService()

        # Risk parameters
        self.max_position_size = self.config.risk.max_position_size
        self.max_portfolio_risk = self.config.risk.max_portfolio_risk
        self.max_daily_loss = self.config.risk.max_daily_loss
        self.position_risk_percent = self.config.risk.position_risk_percent
        self.max_open_positions = self.config.risk.max_open_positions

        # Risk tracking
        self.daily_pnl = Decimal('0')
        self.daily_trades = 0
        self.portfolio_value = Decimal('0')
        self.open_positions_count = 0

        self.logger.info("Risk Manager initialized")

    def initialize(self) -> None:
        """Initialize risk manager components."""
        try:
            # Reset daily tracking
            self._reset_daily_tracking()
            
            self.logger.info("Risk Manager initialized successfully")
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize"})
            raise RiskManagementException(f"Failed to initialize risk manager: {str(e)}")

    def calculate_position_size(self, symbol: str, entry_price: Decimal, 
                               stop_loss: Decimal, available_capital: Decimal) -> int:
        """
        Calculate position size based on risk parameters.

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            available_capital: Available capital for trading

        Returns:
            Calculated position size

        Raises:
            RiskManagementException: If position size calculation fails
        """
        try:
            if entry_price <= 0 or stop_loss <= 0 or available_capital <= 0:
                raise RiskManagementException("Invalid parameters for position size calculation")

            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            if risk_per_share == 0:
                raise RiskManagementException("Entry and stop loss prices cannot be the same")

            # Calculate risk amount based on position risk percentage
            risk_amount = available_capital * (self.position_risk_percent / 100)

            # Calculate position size
            position_size = int(risk_amount / risk_per_share)

            # Apply maximum position size limit
            if position_size > self.max_position_size:
                position_size = self.max_position_size
                self.logger.warning(f"Position size limited to maximum: {position_size}")

            # Ensure minimum position size
            if position_size < 1:
                position_size = 1
                self.logger.warning(f"Position size set to minimum: 1")

            self.logger.info(f"Position size calculated: {position_size} for {symbol}")
            return position_size

        except Exception as e:
            if isinstance(e, RiskManagementException):
                raise
            self.logger.log_error(e, {
                "operation": "calculate_position_size",
                "symbol": symbol,
                "entry_price": str(entry_price),
                "stop_loss": str(stop_loss)
            })
            raise RiskManagementException(f"Position size calculation failed: {str(e)}")

    def validate_order(self, order: Order, current_positions: List[Position]) -> bool:
        """
        Validate order against risk parameters.

        Args:
            order: Order to validate
            current_positions: Current open positions

        Returns:
            True if order is valid, False otherwise

        Raises:
            RiskManagementException: If order validation fails
        """
        try:
            # Check if we can open new positions
            if len(current_positions) >= self.max_open_positions:
                self.logger.warning(f"Maximum open positions limit reached: {self.max_open_positions}")
                return False

            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                self.logger.warning(f"Daily loss limit reached: {self.daily_pnl}")
                return False

            # Check position size limit
            if order.quantity > self.max_position_size:
                self.logger.warning(f"Position size exceeds limit: {order.quantity} > {self.max_position_size}")
                return False

            # Check portfolio risk
            if not self._check_portfolio_risk(order, current_positions):
                self.logger.warning("Portfolio risk limit exceeded")
                return False

            self.logger.info(f"Order validation passed: {order.order_id}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "validate_order",
                "order_id": order.order_id
            })
            return False

    def calculate_risk_metrics(self, positions: List[Position], 
                               current_prices: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Calculate current risk metrics.

        Args:
            positions: List of open positions
            current_prices: Current market prices for symbols

        Returns:
            Dictionary containing risk metrics
        """
        try:
            total_exposure = Decimal('0')
            total_unrealized_pnl = Decimal('0')
            max_drawdown = Decimal('0')
            var_95 = Decimal('0')

            for position in positions:
                if position.symbol in current_prices:
                    current_price = current_prices[position.symbol]
                    
                    # Calculate exposure
                    exposure = position.quantity * current_price
                    total_exposure += exposure

                    # Calculate unrealized P&L
                    if position.side == OrderSide.BUY:
                        unrealized_pnl = (current_price - position.entry_price) * position.quantity
                    else:
                        unrealized_pnl = (position.entry_price - current_price) * position.quantity
                    
                    total_unrealized_pnl += unrealized_pnl

                    # Track maximum drawdown
                    if unrealized_pnl < max_drawdown:
                        max_drawdown = unrealized_pnl

            # Calculate portfolio risk percentage
            portfolio_risk_percent = 0
            if self.portfolio_value > 0:
                portfolio_risk_percent = (total_exposure / self.portfolio_value) * 100

            risk_metrics = {
                'total_exposure': float(total_exposure),
                'total_unrealized_pnl': float(total_unrealized_pnl),
                'max_drawdown': float(max_drawdown),
                'portfolio_risk_percent': float(portfolio_risk_percent),
                'open_positions_count': len(positions),
                'daily_pnl': float(self.daily_pnl),
                'daily_trades': self.daily_trades,
                'risk_limits': {
                    'max_position_size': self.max_position_size,
                    'max_portfolio_risk': self.max_portfolio_risk,
                    'max_daily_loss': float(self.max_daily_loss),
                    'max_open_positions': self.max_open_positions
                }
            }

            return risk_metrics

        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_risk_metrics"})
            return {'error': str(e)}

    def update_daily_tracking(self, realized_pnl: Decimal) -> None:
        """
        Update daily tracking metrics.

        Args:
            realized_pnl: Realized P&L from closed position
        """
        try:
            self.daily_pnl += realized_pnl
            self.daily_trades += 1

            self.logger.debug(f"Daily tracking updated: P&L={realized_pnl}, Total={self.daily_pnl}")

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_daily_tracking",
                "realized_pnl": str(realized_pnl)
            })

    def update_portfolio_value(self, new_value: Decimal) -> None:
        """
        Update portfolio value.

        Args:
            new_value: New portfolio value
        """
        try:
            self.portfolio_value = new_value
            self.logger.debug(f"Portfolio value updated: {new_value}")

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_portfolio_value",
                "new_value": str(new_value)
            })

    def update_open_positions_count(self, count: int) -> None:
        """
        Update open positions count.

        Args:
            count: New open positions count
        """
        try:
            self.open_positions_count = count
            self.logger.debug(f"Open positions count updated: {count}")

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_open_positions_count",
                "count": count
            })

    def check_risk_limits(self, positions: List[Position], 
                          current_prices: Dict[str, Decimal]) -> Dict[str, bool]:
        """
        Check if current positions violate any risk limits.

        Args:
            positions: List of open positions
            current_prices: Current market prices for symbols

        Returns:
            Dictionary indicating which limits are violated
        """
        try:
            risk_metrics = self.calculate_risk_metrics(positions, current_prices)
            
            limit_violations = {
                'portfolio_risk_exceeded': False,
                'daily_loss_exceeded': False,
                'max_positions_exceeded': False,
                'position_size_exceeded': False
            }

            # Check portfolio risk
            if risk_metrics.get('portfolio_risk_percent', 0) > self.max_portfolio_risk:
                limit_violations['portfolio_risk_exceeded'] = True

            # Check daily loss
            if risk_metrics.get('daily_pnl', 0) < -self.max_daily_loss:
                limit_violations['daily_loss_exceeded'] = True

            # Check max positions
            if risk_metrics.get('open_positions_count', 0) > self.max_open_positions:
                limit_violations['max_positions_exceeded'] = True

            # Check individual position sizes
            for position in positions:
                if position.quantity > self.max_position_size:
                    limit_violations['position_size_exceeded'] = True
                    break

            return limit_violations

        except Exception as e:
            self.logger.log_error(e, {"operation": "check_risk_limits"})
            return {'error': str(e)}

    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get current risk summary.

        Returns:
            Dictionary containing risk summary
        """
        try:
            return {
                'risk_parameters': {
                    'max_position_size': self.max_position_size,
                    'max_portfolio_risk': self.max_portfolio_risk,
                    'max_daily_loss': float(self.max_daily_loss),
                    'position_risk_percent': self.position_risk_percent,
                    'max_open_positions': self.max_open_positions
                },
                'current_status': {
                    'daily_pnl': float(self.daily_pnl),
                    'daily_trades': self.daily_trades,
                    'portfolio_value': float(self.portfolio_value),
                    'open_positions_count': self.open_positions_count
                },
                'limits_status': {
                    'daily_loss_limit_reached': self.daily_pnl <= -self.max_daily_loss,
                    'max_positions_reached': self.open_positions_count >= self.max_open_positions
                }
            }

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_risk_summary"})
            return {'error': str(e)}

    def _check_portfolio_risk(self, order: Order, current_positions: List[Position]) -> bool:
        """Check if order would exceed portfolio risk limits."""
        try:
            # This is a simplified check - in practice, you'd calculate the actual risk
            # based on position correlation, volatility, etc.
            total_positions = len(current_positions) + 1
            
            # Simple heuristic: if we have too many positions, reject
            if total_positions > self.max_open_positions:
                return False

            return True

        except Exception as e:
            self.logger.log_error(e, {"operation": "check_portfolio_risk"})
            return False

    def _reset_daily_tracking(self) -> None:
        """Reset daily tracking metrics."""
        try:
            self.daily_pnl = Decimal('0')
            self.daily_trades = 0
            self.logger.info("Daily tracking reset")

        except Exception as e:
            self.logger.log_error(e, {"operation": "reset_daily_tracking"}) 