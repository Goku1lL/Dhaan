"""
Strategy Paper Trading Integration Manager
Connects market scanner opportunities to paper trading execution for strategy testing.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from uuid import uuid4

from ..core.logging_service import LoggingService
from ..core.entities import Order, OrderSide, OrderType
from .market_scanner import TradingOpportunity, MarketScanner
from .paper_trading_broker_provider import PaperTradingBrokerProvider
from .strategy_manager import StrategyManager


@dataclass
class StrategyPerformance:
    """Track performance metrics for each strategy."""
    strategy_id: str
    strategy_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: Decimal = Decimal('0')
    win_rate: float = 0.0
    avg_profit_per_trade: Decimal = Decimal('0')
    max_drawdown: Decimal = Decimal('0')
    sharpe_ratio: float = 0.0
    active_positions: int = 0
    last_signal_time: Optional[datetime] = None


@dataclass
class StrategyTrade:
    """Represents a trade executed by a strategy."""
    trade_id: str
    strategy_id: str
    symbol: str
    order_side: OrderSide
    entry_price: Decimal
    quantity: int
    entry_time: datetime
    exit_price: Optional[Decimal] = None
    exit_time: Optional[datetime] = None
    pnl: Optional[Decimal] = None
    commission: Decimal = Decimal('20')
    status: str = "OPEN"  # OPEN, CLOSED, CANCELLED


class StrategyPaperTradingManager:
    """
    Strategy Paper Trading Integration Manager
    
    Automatically executes paper trades based on market scanner opportunities
    and tracks strategy performance for optimization.
    """
    
    def __init__(self, 
                 market_scanner: MarketScanner,
                 paper_broker: PaperTradingBrokerProvider,
                 strategy_manager: StrategyManager):
        """
        Initialize the strategy paper trading manager.
        
        Args:
            market_scanner: Market scanner instance
            paper_broker: Paper trading broker instance
            strategy_manager: Strategy manager instance
        """
        self.market_scanner = market_scanner
        self.paper_broker = paper_broker
        self.strategy_manager = strategy_manager
        self.logger = LoggingService()
        
        # Performance tracking
        self.strategy_performances: Dict[str, StrategyPerformance] = {}
        self.strategy_trades: List[StrategyTrade] = []
        self.active_trades: Dict[str, StrategyTrade] = {}  # trade_id -> trade
        
        # Configuration
        self.auto_trading_enabled = True
        self.max_position_size = Decimal('10000')  # ₹10,000 per position
        self.max_positions_per_strategy = 3
        self.risk_per_trade = Decimal('0.02')  # 2% risk per trade
        
        # Initialize strategy performance tracking
        self._initialize_strategy_performance()
        
        self.logger.info("Strategy Paper Trading Manager initialized")
    
    def _initialize_strategy_performance(self) -> None:
        """Initialize performance tracking for all strategies."""
        try:
            active_strategies = self.strategy_manager.get_active_strategies()
            for strategy in active_strategies:
                self.strategy_performances[strategy.strategy_id] = StrategyPerformance(
                    strategy_id=strategy.strategy_id,
                    strategy_name=strategy.name
                )
            
            self.logger.info(f"Initialized performance tracking for {len(active_strategies)} strategies")
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize_strategy_performance"})
    
    async def process_market_opportunities(self) -> Dict[str, Any]:
        """
        Process market scanner opportunities and execute paper trades.
        
        Returns:
            Summary of processing results
        """
        try:
            if not self.auto_trading_enabled:
                return {"status": "disabled", "message": "Auto trading is disabled"}
            
            # Get latest scan results from market scanner
            scan_results = self.market_scanner.current_scan_results
            if not scan_results or not scan_results.opportunities:
                return {
                    "status": "no_opportunities", 
                    "message": "No opportunities found in latest scan"
                }
            
            # Process each opportunity
            trades_executed = 0
            trades_skipped = 0
            
            for opportunity in scan_results.opportunities:
                try:
                    trade_executed = await self._process_opportunity(opportunity)
                    if trade_executed:
                        trades_executed += 1
                    else:
                        trades_skipped += 1
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process opportunity for {opportunity.symbol}: {e}")
                    trades_skipped += 1
            
            # Update strategy performance metrics
            await self._update_strategy_performance()
            
            return {
                "status": "success",
                "trades_executed": trades_executed,
                "trades_skipped": trades_skipped,
                "total_opportunities": len(scan_results.opportunities),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "process_market_opportunities"})
            return {"status": "error", "message": str(e)}
    
    async def _process_opportunity(self, opportunity: TradingOpportunity) -> bool:
        """
        Process a single trading opportunity and execute paper trade if conditions are met.
        
        Args:
            opportunity: Trading opportunity from market scanner
        
        Returns:
            True if trade was executed, False otherwise
        """
        try:
            strategy_id = opportunity.strategy_id
            
            # Check if strategy exists and is active
            if strategy_id not in self.strategy_performances:
                self.logger.warning(f"Strategy {strategy_id} not found in performance tracking")
                return False
            
            # Risk management checks
            if not await self._validate_trade_risk(opportunity):
                return False
            
            # Check position limits
            if not self._check_position_limits(strategy_id):
                self.logger.debug(f"Position limit reached for strategy {strategy_id}")
                return False
            
            # Calculate position size
            position_size = self._calculate_position_size(opportunity)
            if position_size <= 0:
                return False
            
            # Execute paper trade
            trade_executed = await self._execute_paper_trade(opportunity, position_size)
            
            if trade_executed:
                # Update strategy performance
                self.strategy_performances[strategy_id].last_signal_time = datetime.now()
                self.logger.info(f"Executed paper trade for {opportunity.symbol} using {strategy_id}")
            
            return trade_executed
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "process_opportunity",
                "symbol": opportunity.symbol,
                "strategy": opportunity.strategy_id
            })
            return False
    
    async def _validate_trade_risk(self, opportunity: TradingOpportunity) -> bool:
        """Validate if the trade meets risk management criteria."""
        try:
            # Check confidence score
            if opportunity.confidence_score < 0.7:  # Minimum 70% confidence
                return False
            
            # Check risk-reward ratio
            if opportunity.risk_reward_ratio < 1.5:  # Minimum 1:1.5 risk-reward
                return False
            
            # Check if we have sufficient virtual balance
            account_balance = self.paper_broker.get_account_balance()
            if account_balance.available_margin < self.max_position_size:
                return False
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "validate_trade_risk"})
            return False
    
    def _check_position_limits(self, strategy_id: str) -> bool:
        """Check if strategy has reached maximum position limits."""
        try:
            # Count active positions for this strategy
            active_count = sum(1 for trade in self.active_trades.values() 
                             if trade.strategy_id == strategy_id and trade.status == "OPEN")
            
            return active_count < self.max_positions_per_strategy
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "check_position_limits"})
            return False
    
    def _calculate_position_size(self, opportunity: TradingOpportunity) -> int:
        """Calculate appropriate position size based on risk management."""
        try:
            # Get account balance
            account_balance = self.paper_broker.get_account_balance()
            available_capital = min(account_balance.available_margin, self.max_position_size)
            
            # Calculate risk amount (2% of available capital)
            risk_amount = available_capital * self.risk_per_trade
            
            # Calculate stop loss distance
            entry_price = Decimal(str(opportunity.entry_price))
            stop_loss = Decimal(str(opportunity.stop_loss))
            stop_loss_distance = abs(entry_price - stop_loss)
            
            if stop_loss_distance == 0:
                return 0
            
            # Calculate quantity based on risk
            quantity = int(risk_amount / stop_loss_distance)
            
            # Ensure minimum quantity
            return max(quantity, 1)
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_position_size"})
            return 0
    
    async def _execute_paper_trade(self, opportunity: TradingOpportunity, quantity: int) -> bool:
        """Execute the actual paper trade."""
        try:
            # Determine order side
            order_side = OrderSide.BUY if opportunity.signal_type == "BUY" else OrderSide.SELL
            
            # Build Order expected by the broker
            order = Order(
                order_id=str(uuid4()),
                symbol=opportunity.symbol,
                side=order_side,
                order_type=OrderType.MARKET,
                quantity=quantity,
                price=Decimal(str(opportunity.entry_price)),
                stop_loss=Decimal(str(opportunity.stop_loss)) if opportunity.stop_loss else None,
                target=Decimal(str(opportunity.target_price)) if opportunity.target_price else None
            )
            
            # Place order
            virtual_order_id = self.paper_broker.place_order(order)
            if not virtual_order_id:
                return False
            
            # Create strategy trade record
            trade = StrategyTrade(
                trade_id=virtual_order_id,
                strategy_id=opportunity.strategy_id,
                symbol=opportunity.symbol,
                order_side=order_side,
                entry_price=Decimal(str(opportunity.entry_price)),
                quantity=quantity,
                entry_time=datetime.now()
            )
            
            # Track trade
            self.strategy_trades.append(trade)
            self.active_trades[trade.trade_id] = trade
            
            # Update strategy performance counters
            performance = self.strategy_performances[opportunity.strategy_id]
            performance.total_trades += 1
            performance.active_positions += 1
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "execute_paper_trade"})
            return False
    
    async def _update_strategy_performance(self) -> None:
        """Update performance metrics for all strategies."""
        try:
            # Check for completed trades and update performance
            for trade_id, trade in list(self.active_trades.items()):
                if trade.status == "OPEN":
                    # Check if position should be closed (simplified logic)
                    await self._check_trade_exit(trade)
            
            # Calculate performance metrics
            for strategy_id, performance in self.strategy_performances.items():
                self._calculate_performance_metrics(performance)
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "update_strategy_performance"})
    
    async def _check_trade_exit(self, trade: StrategyTrade) -> None:
        """Check if a trade should be exited and close if necessary."""
        try:
            # Get current market price (simplified - would use real market data)
            current_price = trade.entry_price * Decimal('1.02')  # Simulate 2% move
            
            # Simple exit logic (in reality, would use stop loss and target prices)
            if abs(current_price - trade.entry_price) / trade.entry_price > Decimal('0.05'):  # 5% move
                await self._close_trade(trade, current_price)
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "check_trade_exit"})
    
    async def _close_trade(self, trade: StrategyTrade, exit_price: Decimal) -> None:
        """Close a trade and update performance metrics."""
        try:
            # Close position in paper broker
            close_result = self.paper_broker.square_off_position(
                symbol=trade.symbol,
                quantity=trade.quantity,
                side=OrderSide.SELL if trade.order_side == OrderSide.BUY else OrderSide.BUY
            )
            
            if close_result:
                # Update trade record
                trade.exit_price = exit_price
                trade.exit_time = datetime.now()
                trade.status = "CLOSED"
                
                # Calculate P&L
                if trade.order_side == OrderSide.BUY:
                    trade.pnl = (exit_price - trade.entry_price) * trade.quantity - trade.commission
                else:
                    trade.pnl = (trade.entry_price - exit_price) * trade.quantity - trade.commission
                
                # Update strategy performance
                performance = self.strategy_performances[trade.strategy_id]
                performance.active_positions -= 1
                performance.total_pnl += trade.pnl
                
                if trade.pnl > 0:
                    performance.winning_trades += 1
                else:
                    performance.losing_trades += 1
                
                # Remove from active trades
                del self.active_trades[trade.trade_id]
                
                self.logger.info(f"Closed trade {trade.trade_id} for {trade.symbol} with P&L: ₹{trade.pnl}")
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "close_trade"})
    
    def _calculate_performance_metrics(self, performance: StrategyPerformance) -> None:
        """Calculate comprehensive performance metrics for a strategy."""
        try:
            if performance.total_trades > 0:
                performance.win_rate = performance.winning_trades / performance.total_trades
                performance.avg_profit_per_trade = performance.total_pnl / performance.total_trades
            
            # Calculate max drawdown (simplified)
            strategy_trades = [t for t in self.strategy_trades if t.strategy_id == performance.strategy_id]
            if strategy_trades:
                running_pnl = Decimal('0')
                max_pnl = Decimal('0')
                max_drawdown = Decimal('0')
                
                for trade in strategy_trades:
                    if trade.pnl:
                        running_pnl += trade.pnl
                        max_pnl = max(max_pnl, running_pnl)
                        drawdown = max_pnl - running_pnl
                        max_drawdown = max(max_drawdown, drawdown)
                
                performance.max_drawdown = max_drawdown
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_performance_metrics"})
    
    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary for all strategies."""
        try:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "auto_trading_enabled": self.auto_trading_enabled,
                "total_strategies": len(self.strategy_performances),
                "total_active_trades": len(self.active_trades),
                "strategies": {}
            }
            
            for strategy_id, performance in self.strategy_performances.items():
                summary["strategies"][strategy_id] = {
                    "name": performance.strategy_name,
                    "total_trades": performance.total_trades,
                    "winning_trades": performance.winning_trades,
                    "losing_trades": performance.losing_trades,
                    "win_rate": float(performance.win_rate),
                    "total_pnl": float(performance.total_pnl),
                    "avg_profit_per_trade": float(performance.avg_profit_per_trade),
                    "max_drawdown": float(performance.max_drawdown),
                    "active_positions": performance.active_positions,
                    "last_signal_time": performance.last_signal_time.isoformat() if performance.last_signal_time else None
                }
            
            return summary
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_strategy_performance_summary"})
            return {"error": str(e)}
    
    def enable_auto_trading(self) -> bool:
        """Enable automatic strategy-based paper trading."""
        self.auto_trading_enabled = True
        self.logger.info("Strategy auto-trading enabled")
        return True
    
    def disable_auto_trading(self) -> bool:
        """Disable automatic strategy-based paper trading."""
        self.auto_trading_enabled = False
        self.logger.info("Strategy auto-trading disabled")
        return True
    
    def get_active_trades(self) -> List[Dict[str, Any]]:
        """Get list of currently active strategy trades."""
        try:
            active_trades = []
            for trade in self.active_trades.values():
                active_trades.append({
                    "trade_id": trade.trade_id,
                    "strategy_id": trade.strategy_id,
                    "symbol": trade.symbol,
                    "side": trade.order_side.value,
                    "entry_price": float(trade.entry_price),
                    "quantity": trade.quantity,
                    "entry_time": trade.entry_time.isoformat(),
                    "unrealized_pnl": self._calculate_unrealized_pnl(trade)
                })
            
            return active_trades
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_active_trades"})
            return []
    
    def _calculate_unrealized_pnl(self, trade: StrategyTrade) -> float:
        """Calculate unrealized P&L for an active trade."""
        try:
            # Simplified - would use real market data
            current_price = trade.entry_price * Decimal('1.01')  # Simulate 1% move
            
            if trade.order_side == OrderSide.BUY:
                unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
            else:
                unrealized_pnl = (trade.entry_price - current_price) * trade.quantity
            
            return float(unrealized_pnl)
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_unrealized_pnl"})
            return 0.0 