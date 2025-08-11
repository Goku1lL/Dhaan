"""
Trading Engine implementation.
Main orchestrator using Facade pattern to coordinate all trading operations.
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from .interfaces import (
    ITradingEngine, IMarketDataProvider, IBrokerProvider, 
    IStrategyProvider, IRiskManager, IPositionManager, 
    IOrderManager, IDataRepository, INotificationService
)
from .entities import (
    Order, OrderSide, OrderType, OrderStatus, MarketData, 
    Position, Trade, TradingSignal
)
from .exceptions import (
    TradingEngineException, OrderException, 
    InsufficientMarginException, StrategyException
)
from .logging_service import LoggingService
from .config import ConfigurationManager


class TradingEngine(ITradingEngine):
    """
    Main trading engine that orchestrates all trading operations.
    Implements Facade pattern to simplify complex subsystem interactions.
    """

    def __init__(self, 
                 market_data_provider: IMarketDataProvider,
                 broker_provider: IBrokerProvider,
                 strategy_provider: IStrategyProvider,
                 risk_manager: IRiskManager,
                 position_manager: IPositionManager,
                 order_manager: IOrderManager,
                 data_repository: IDataRepository,
                 notification_service: INotificationService,
                 config: ConfigurationManager):
        """
        Initialize trading engine with all required providers.

        Args:
            market_data_provider: Provider for market data
            broker_provider: Provider for broker operations
            strategy_provider: Provider for trading strategies
            risk_manager: Risk management component
            position_manager: Position management component
            order_manager: Order management component
            data_repository: Data persistence component
            notification_service: Notification service
            config: Configuration manager
        """
        self.market_data_provider = market_data_provider
        self.broker_provider = broker_provider
        self.strategy_provider = strategy_provider
        self.risk_manager = risk_manager
        self.position_manager = position_manager
        self.order_manager = order_manager
        self.data_repository = data_repository
        self.notification_service = notification_service
        self.config = config
        
        self.logger = LoggingService()
        
        # Engine state
        self._running = False
        self._engine_thread = None
        self._stop_event = threading.Event()
        
        # Trading state
        self.active_symbols = set()
        self.last_signal_check = {}
        self.signal_cooldown = self.config.trading.signal_cooldown_seconds
        
        # Performance tracking
        self.start_time = None
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        
        self.logger.info("Trading Engine initialized")

    def start(self) -> bool:
        """
        Start the trading engine.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self._running:
                self.logger.warning("Trading engine is already running")
                return True

            self.logger.info("Starting trading engine...")
            
            # Initialize components
            if not self._initialize_components():
                raise TradingEngineException("Failed to initialize components")
            
            # Start market data streaming
            if not self._start_market_data_streaming():
                raise TradingEngineException("Failed to start market data streaming")
            
            # Start main trading loop
            self._stop_event.clear()
            self._engine_thread = threading.Thread(target=self._main_trading_loop, daemon=True)
            self._engine_thread.start()
            
            self._running = True
            self.start_time = datetime.now()
            
            self.logger.info("Trading engine started successfully")
            self.notification_service.send_notification("Trading engine started", "INFO")
            
            return True

        except Exception as e:
            self.logger.log_error(e, {"operation": "start_engine"})
            self.notification_service.send_error_alert(e, {"operation": "start_engine"})
            return False

    def stop(self) -> bool:
        """
        Stop the trading engine.

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self._running:
                self.logger.warning("Trading engine is not running")
                return True

            self.logger.info("Stopping trading engine...")
            
            # Signal stop
            self._stop_event.set()
            
            # Wait for thread to finish
            if self._engine_thread and self._engine_thread.is_alive():
                self._engine_thread.join(timeout=10)
            
            # Stop market data streaming
            self._stop_market_data_streaming()
            
            # Close all positions if configured
            if self.config.trading.close_positions_on_stop:
                self._close_all_positions()
            
            self._running = False
            
            self.logger.info("Trading engine stopped successfully")
            self.notification_service.send_notification("Trading engine stopped", "INFO")
            
            return True

        except Exception as e:
            self.logger.log_error(e, {"operation": "stop_engine"})
            self.notification_service.send_error_alert(e, {"operation": "stop_engine"})
            return False

    def is_running(self) -> bool:
        """
        Check if engine is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def process_market_data(self, symbol: str, market_data: MarketData) -> None:
        """
        Process incoming market data.

        Args:
            symbol: Trading symbol
            market_data: Market data to process
        """
        try:
            # Save to repository
            self.data_repository.save_market_data(symbol, market_data)
            
            # Update position manager
            self.position_manager.update_market_data(symbol, market_data)
            
            # Check if we should execute strategy
            if self._should_execute_strategy(symbol):
                self.execute_strategy(symbol)
                
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "process_market_data",
                "symbol": symbol
            })

    def execute_strategy(self, symbol: str) -> None:
        """
        Execute trading strategy for a symbol.

        Args:
            symbol: Trading symbol
        """
        try:
            self.logger.debug(f"Executing strategy for {symbol}")
            
            # Get recent market data
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=self.config.strategy.lookback_minutes)
            market_data = self.data_repository.get_market_data(symbol, start_time, end_time)
            
            if not market_data:
                self.logger.warning(f"No market data available for {symbol}")
                return
            
            # Get trading signals
            signals = self.strategy_provider.get_signals(symbol, market_data)
            
            if not signals:
                return
            
            # Process entry signals
            if 'entry_signal' in signals:
                self._process_entry_signal(symbol, signals)
            
            # Process exit signals
            if 'exit_signal' in signals:
                self._process_exit_signal(symbol, signals)
            
            # Update last signal check
            self.last_signal_check[symbol] = datetime.now()
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "execute_strategy",
                "symbol": symbol
            })

    def place_order(self, order: Order) -> str:
        """
        Place a new order.

        Args:
            order: Order to place

        Returns:
            Order ID if successful

        Raises:
            OrderException: If order placement fails
        """
        try:
            # Validate order
            if not self._validate_order(order):
                raise OrderException("Order validation failed")
            
            # Check risk limits
            if not self.risk_manager.validate_order(order):
                raise OrderException("Order rejected by risk manager")
            
            # Check margin
            if not self._check_margin(order):
                raise InsufficientMarginException("Insufficient margin for order")
            
            # Place order through broker
            order_id = self.broker_provider.place_order(order)
            
            # Update order with ID
            order.order_id = order_id
            order.status = OrderStatus.PENDING
            order.timestamp = datetime.now()
            
            # Save to repository
            self.data_repository.save_order(order)
            
            # Update order manager
            self.order_manager.add_order(order)
            
            # Send notification
            self.notification_service.send_notification(
                f"Order placed: {order.side.value} {order.quantity} {order.symbol} @ {order.price}",
                "INFO"
            )
            
            self.logger.info(f"Order placed successfully: {order_id}")
            return order_id
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "place_order",
                "symbol": order.symbol,
                "side": order.side.value
            })
            self.notification_service.send_error_alert(e, {
                "operation": "place_order",
                "symbol": order.symbol
            })
            raise

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            # Cancel through broker
            success = self.broker_provider.cancel_order(order_id)
            
            if success:
                # Update order status
                order = self.order_manager.get_order(order_id)
                if order:
                    order.status = OrderStatus.CANCELLED
                    order.cancelled_at = datetime.now()
                    self.data_repository.save_order(order)
                
                # Update order manager
                self.order_manager.remove_order(order_id)
                
                self.logger.info(f"Order cancelled successfully: {order_id}")
                return True
            else:
                self.logger.warning(f"Order cancellation failed: {order_id}")
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "cancel_order",
                "order_id": order_id
            })
            return False

    def get_engine_status(self) -> Dict[str, Any]:
        """
        Get current engine status.

        Returns:
            Dictionary containing engine status
        """
        try:
            status = {
                'running': self._running,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'uptime': self._get_uptime(),
                'active_symbols': list(self.active_symbols),
                'total_trades': self.total_trades,
                'successful_trades': self.successful_trades,
                'failed_trades': self.failed_trades,
                'success_rate': self._calculate_success_rate(),
                'active_positions': len(self.position_manager.get_active_positions()),
                'pending_orders': len(self.order_manager.get_pending_orders()),
                'available_margin': float(self.broker_provider.get_available_margin()),
                'last_signal_checks': {
                    symbol: time.isoformat() for symbol, time in self.last_signal_check.items()
                }
            }
            
            return status
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_engine_status"})
            return {'error': str(e)}

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Get all active positions.

        Returns:
            List of position dictionaries
        """
        try:
            positions = self.position_manager.get_active_positions()
            return [self._position_to_dict(pos) for pos in positions]
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_active_positions"})
            return []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.

        Returns:
            Dictionary containing performance metrics
        """
        try:
            # Get trade history
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days
            trades = self.data_repository.get_trades(start_date=start_date, end_date=end_date)
            
            if not trades:
                return {'error': 'No trade data available'}
            
            # Calculate metrics
            total_pnl = sum(float(trade.realized_pnl) for trade in trades)
            winning_trades = [t for t in trades if float(t.realized_pnl) > 0]
            losing_trades = [t for t in trades if float(t.realized_pnl) < 0]
            
            metrics = {
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / len(trades) if trades else 0,
                'total_pnl': total_pnl,
                'average_win': sum(float(t.realized_pnl) for t in winning_trades) / len(winning_trades) if winning_trades else 0,
                'average_loss': sum(float(t.realized_pnl) for t in losing_trades) / len(losing_trades) if losing_trades else 0,
                'profit_factor': abs(sum(float(t.realized_pnl) for t in winning_trades) / sum(float(t.realized_pnl) for t in losing_trades)) if losing_trades else float('inf'),
                'max_drawdown': self._calculate_max_drawdown(trades),
                'sharpe_ratio': self._calculate_sharpe_ratio(trades)
            }
            
            return metrics
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_performance_metrics"})
            return {'error': str(e)}

    def _initialize_components(self) -> bool:
        """Initialize all trading components."""
        try:
            # Initialize market data provider
            if not self.market_data_provider.initialize():
                self.logger.error("Failed to initialize market data provider")
                return False
            
            # Initialize broker provider
            if not self.broker_provider.initialize():
                self.logger.error("Failed to initialize broker provider")
                return False
            
            # Initialize other components
            self.position_manager.initialize()
            self.order_manager.initialize()
            self.risk_manager.initialize()
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize_components"})
            return False

    def _start_market_data_streaming(self) -> bool:
        """Start market data streaming for configured symbols."""
        try:
            symbols = self.config.trading.symbols
            for symbol in symbols:
                if self.market_data_provider.subscribe(symbol):
                    self.active_symbols.add(symbol)
                    self.logger.info(f"Subscribed to {symbol}")
                else:
                    self.logger.error(f"Failed to subscribe to {symbol}")
            
            return len(self.active_symbols) > 0
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "start_market_data_streaming"})
            return False

    def _stop_market_data_streaming(self) -> None:
        """Stop market data streaming."""
        try:
            for symbol in list(self.active_symbols):
                self.market_data_provider.unsubscribe(symbol)
                self.active_symbols.remove(symbol)
                self.logger.info(f"Unsubscribed from {symbol}")
        except Exception as e:
            self.logger.log_error(e, {"operation": "stop_market_data_streaming"})

    def _main_trading_loop(self) -> None:
        """Main trading loop running in separate thread."""
        try:
            self.logger.info("Main trading loop started")
            
            while not self._stop_event.is_set():
                try:
                    # Process pending orders
                    self._process_pending_orders()
                    
                    # Update positions
                    self._update_positions()
                    
                    # Check for stop loss and target hits
                    self._check_stop_loss_target()
                    
                    # Sleep for configured interval
                    time.sleep(self.config.trading.loop_interval_seconds)
                    
                except Exception as e:
                    self.logger.log_error(e, {"operation": "main_trading_loop"})
                    time.sleep(5)  # Wait before retrying
            
            self.logger.info("Main trading loop stopped")
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "main_trading_loop"})

    def _should_execute_strategy(self, symbol: str) -> bool:
        """Check if strategy should be executed for a symbol."""
        if symbol not in self.last_signal_check:
            return True
        
        time_since_last = datetime.now() - self.last_signal_check[symbol]
        return time_since_last.total_seconds() >= self.signal_cooldown

    def _process_entry_signal(self, symbol: str, signals: Dict[str, Any]) -> None:
        """Process entry signal from strategy."""
        try:
            side = signals.get('side')
            confidence = signals.get('confidence', 0)
            
            # Check confidence threshold
            if confidence < self.config.strategy.min_confidence:
                self.logger.debug(f"Signal confidence too low: {confidence}")
                return
            
            # Check if we already have a position
            if self.position_manager.has_position(symbol):
                self.logger.debug(f"Already have position in {symbol}")
                return
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(symbol, signals)
            
            if position_size <= 0:
                self.logger.warning(f"Invalid position size calculated: {position_size}")
                return
            
            # Create order
            order = Order(
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=position_size,
                price=Decimal('0'),  # Market order
                stop_loss=signals.get('stop_loss'),
                target=signals.get('target')
            )
            
            # Place order
            order_id = self.place_order(order)
            self.logger.info(f"Entry order placed: {order_id}")
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "process_entry_signal",
                "symbol": symbol
            })

    def _process_exit_signal(self, symbol: str, signals: Dict[str, Any]) -> None:
        """Process exit signal from strategy."""
        try:
            # Check if we have a position to exit
            position = self.position_manager.get_position(symbol)
            if not position:
                return
            
            # Create exit order
            exit_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            
            order = Order(
                symbol=symbol,
                side=exit_side,
                order_type=OrderType.MARKET,
                quantity=position.quantity,
                price=Decimal('0'),  # Market order
                reason="Strategy Exit Signal"
            )
            
            # Place exit order
            order_id = self.place_order(order)
            self.logger.info(f"Exit order placed: {order_id}")
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "process_exit_signal",
                "symbol": symbol
            })

    def _validate_order(self, order: Order) -> bool:
        """Validate order before placement."""
        try:
            if not order.symbol or not order.side or not order.order_type:
                return False
            
            if order.quantity <= 0:
                return False
            
            if order.order_type == OrderType.LIMIT and order.price <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "validate_order"})
            return False

    def _check_margin(self, order: Order) -> bool:
        """Check if sufficient margin is available for order."""
        try:
            required_margin = self.risk_manager.calculate_required_margin(order)
            available_margin = self.broker_provider.get_available_margin()
            
            return available_margin >= required_margin
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "check_margin"})
            return False

    def _process_pending_orders(self) -> None:
        """Process pending orders and update their status."""
        try:
            pending_orders = self.order_manager.get_pending_orders()
            
            for order in pending_orders:
                # Get current status from broker
                status = self.broker_provider.get_order_status(order.order_id)
                
                if status != order.status:
                    order.status = status
                    self.data_repository.save_order(order)
                    
                    # If order is filled, create position
                    if status == OrderStatus.FILLED:
                        self._handle_filled_order(order)
                    
                    # If order is rejected, log and notify
                    elif status == OrderStatus.REJECTED:
                        self.logger.warning(f"Order rejected: {order.order_id}")
                        self.notification_service.send_notification(
                            f"Order rejected: {order.symbol} {order.side.value}",
                            "WARNING"
                        )
                        
        except Exception as e:
            self.logger.log_error(e, {"operation": "process_pending_orders"})

    def _handle_filled_order(self, order: Order) -> None:
        """Handle a filled order by creating or updating position."""
        try:
            # Get fill price from broker
            # This would need to be implemented based on broker API
            fill_price = order.price  # Placeholder
            
            if self.position_manager.has_position(order.symbol):
                # Update existing position
                self.position_manager.update_position(order.symbol, order, fill_price)
            else:
                # Create new position
                position = Position(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity,
                    entry_price=fill_price,
                    entry_time=datetime.now(),
                    stop_loss=order.stop_loss,
                    target=order.target
                )
                self.position_manager.add_position(position)
            
            # Create trade record
            trade = Trade(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                timestamp=datetime.now(),
                order_id=order.order_id
            )
            self.data_repository.save_trade(trade)
            
            # Send notification
            self.notification_service.send_trade_alert(trade)
            
            # Update metrics
            self.total_trades += 1
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "handle_filled_order",
                "order_id": order.order_id
            })

    def _update_positions(self) -> None:
        """Update position P&L and other metrics."""
        try:
            positions = self.position_manager.get_active_positions()
            
            for position in positions:
                # Get current market price
                current_price = self.market_data_provider.get_current_price(position.symbol)
                
                if current_price:
                    # Update P&L
                    if position.side == OrderSide.BUY:
                        unrealized_pnl = (current_price - position.entry_price) * position.quantity
                    else:
                        unrealized_pnl = (position.entry_price - current_price) * position.quantity
                    
                    position.unrealized_pnl = Decimal(str(unrealized_pnl))
                    position.last_update = datetime.now()
                    
                    # Update in repository
                    self.position_manager.update_position_metadata(position)
                    
        except Exception as e:
            self.logger.log_error(e, {"operation": "update_positions"})

    def _check_stop_loss_target(self) -> None:
        """Check for stop loss and target hits."""
        try:
            positions = self.position_manager.get_active_positions()
            
            for position in positions:
                current_price = self.market_data_provider.get_current_price(position.symbol)
                
                if not current_price:
                    continue
                
                # Check stop loss
                if position.stop_loss and self._check_stop_loss_hit(position, current_price):
                    self._execute_stop_loss(position)
                
                # Check target
                elif position.target and self._check_target_hit(position, current_price):
                    self._execute_target(position)
                    
        except Exception as e:
            self.logger.log_error(e, {"operation": "check_stop_loss_target"})

    def _check_stop_loss_hit(self, position: Position, current_price: Decimal) -> bool:
        """Check if stop loss has been hit."""
        if position.side == OrderSide.BUY:
            return current_price <= position.stop_loss
        else:
            return current_price >= position.stop_loss

    def _check_target_hit(self, position: Position, current_price: Decimal) -> bool:
        """Check if target has been hit."""
        if position.side == OrderSide.BUY:
            return current_price >= position.target
        else:
            return current_price <= position.target

    def _execute_stop_loss(self, position: Position) -> None:
        """Execute stop loss exit."""
        try:
            exit_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            
            order = Order(
                symbol=position.symbol,
                side=exit_side,
                order_type=OrderType.MARKET,
                quantity=position.quantity,
                price=Decimal('0'),
                reason="Stop Loss Hit"
            )
            
            order_id = self.place_order(order)
            self.logger.info(f"Stop loss order placed: {order_id}")
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "execute_stop_loss",
                "symbol": position.symbol
            })

    def _execute_target(self, position: Position) -> None:
        """Execute target exit."""
        try:
            exit_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            
            order = Order(
                symbol=position.symbol,
                side=exit_side,
                order_type=OrderType.MARKET,
                quantity=position.quantity,
                price=Decimal('0'),
                reason="Target Hit"
            )
            
            order_id = self.place_order(order)
            self.logger.info(f"Target exit order placed: {order_id}")
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "execute_target",
                "symbol": position.symbol
            })

    def _close_all_positions(self) -> None:
        """Close all open positions."""
        try:
            positions = self.position_manager.get_active_positions()
            
            for position in positions:
                exit_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
                
                order = Order(
                    symbol=position.symbol,
                    side=exit_side,
                    order_type=OrderType.MARKET,
                    quantity=position.quantity,
                    price=Decimal('0'),
                    reason="Engine Stop - Close All Positions"
                )
                
                self.place_order(order)
                
        except Exception as e:
            self.logger.log_error(e, {"operation": "close_all_positions"})

    def _position_to_dict(self, position: Position) -> Dict[str, Any]:
        """Convert position to dictionary for API response."""
        return {
            'symbol': position.symbol,
            'side': position.side.value,
            'quantity': position.quantity,
            'entry_price': float(position.entry_price),
            'entry_time': position.entry_time.isoformat(),
            'unrealized_pnl': float(position.unrealized_pnl) if position.unrealized_pnl else 0,
            'stop_loss': float(position.stop_loss) if position.stop_loss else None,
            'target': float(position.target) if position.target else None,
            'last_update': position.last_update.isoformat() if position.last_update else None
        }

    def _get_uptime(self) -> str:
        """Get engine uptime as formatted string."""
        if not self.start_time:
            return "0:00:00"
        
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        seconds = int(uptime.total_seconds() % 60)
        
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    def _calculate_success_rate(self) -> float:
        """Calculate trade success rate."""
        if self.total_trades == 0:
            return 0.0
        return self.successful_trades / self.total_trades

    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        """Calculate maximum drawdown from trades."""
        try:
            if not trades:
                return 0.0
            
            cumulative_pnl = []
            running_total = 0.0
            
            for trade in trades:
                running_total += float(trade.realized_pnl)
                cumulative_pnl.append(running_total)
            
            if not cumulative_pnl:
                return 0.0
            
            peak = cumulative_pnl[0]
            max_dd = 0.0
            
            for pnl in cumulative_pnl:
                if pnl > peak:
                    peak = pnl
                dd = (peak - pnl) / peak if peak != 0 else 0
                max_dd = max(max_dd, dd)
            
            return max_dd
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_max_drawdown"})
            return 0.0

    def _calculate_sharpe_ratio(self, trades: List[Trade]) -> float:
        """Calculate Sharpe ratio from trades."""
        try:
            if not trades or len(trades) < 2:
                return 0.0
            
            returns = [float(trade.realized_pnl) for trade in trades]
            mean_return = sum(returns) / len(returns)
            
            if mean_return == 0:
                return 0.0
            
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            
            if std_dev == 0:
                return 0.0
            
            # Assuming risk-free rate of 0 for simplicity
            sharpe = mean_return / std_dev
            
            return sharpe
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_sharpe_ratio"})
            return 0.0 