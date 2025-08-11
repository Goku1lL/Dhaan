"""
Strategy Manager implementation.
Handles trading strategies, signal generation, and strategy execution.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
import json

from ..core.interfaces import IStrategyManager
from ..core.entities import Strategy, Signal, SignalType, SignalStrength
from ..core.exceptions import StrategyManagementException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager


class StrategyManager(IStrategyManager):
    """
    Strategy manager implementation.
    Handles trading strategies, signal generation, and strategy execution.
    """

    def __init__(self, config: ConfigurationManager):
        """
        Initialize strategy manager.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = LoggingService()

        # Strategy storage
        self.strategies: Dict[str, Strategy] = {}
        self.active_strategies: List[str] = []
        
        # Signal tracking
        self.signals: List[Signal] = []
        self.signal_history: List[Signal] = []
        
        # Configuration
        self.max_strategies = self.config.trading.max_strategies
        self.signal_timeout_minutes = self.config.trading.signal_timeout_minutes

        self.logger.info("Strategy Manager initialized")

    def initialize(self) -> None:
        """Initialize strategy manager components."""
        try:
            # Load default strategies
            self._load_default_strategies()
            
            # Load custom strategies if any
            self._load_custom_strategies()
            
            self.logger.info("Strategy Manager initialized successfully")
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize"})
            raise StrategyManagementException(f"Failed to initialize strategy manager: {str(e)}")

    def add_strategy(self, strategy: Strategy) -> bool:
        """
        Add a new trading strategy.

        Args:
            strategy: Strategy to add

        Returns:
            True if added successfully, False otherwise

        Raises:
            StrategyManagementException: If strategy addition fails
        """
        try:
            # Validate strategy
            if not self._validate_strategy(strategy):
                raise StrategyManagementException("Invalid strategy data")

            # Check strategy limits
            if len(self.strategies) >= self.max_strategies:
                raise StrategyManagementException(f"Maximum strategies limit {self.max_strategies} reached")

            # Check if strategy already exists
            if strategy.strategy_id in self.strategies:
                raise StrategyManagementException(f"Strategy {strategy.strategy_id} already exists")

            # Add strategy
            self.strategies[strategy.strategy_id] = strategy
            
            # Activate if enabled
            if strategy.enabled:
                self.active_strategies.append(strategy.strategy_id)

            self.logger.info(f"Strategy added: {strategy.strategy_id} - {strategy.name}")
            return True

        except Exception as e:
            if isinstance(e, StrategyManagementException):
                raise
            self.logger.log_error(e, {
                "operation": "add_strategy",
                "strategy_id": strategy.strategy_id if strategy else None
            })
            raise StrategyManagementException(f"Strategy addition failed: {str(e)}")

    def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update strategy parameters.

        Args:
            strategy_id: Strategy ID to update
            updates: Dictionary of updates

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if strategy_id not in self.strategies:
                self.logger.warning(f"Strategy {strategy_id} not found for update")
                return False

            strategy = self.strategies[strategy_id]

            # Apply updates
            for key, value in updates.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
                    self.logger.debug(f"Updated {key} for strategy {strategy_id}")

            # Update last modified
            strategy.last_modified = datetime.now()

            # Handle activation/deactivation
            if 'enabled' in updates:
                if updates['enabled'] and strategy_id not in self.active_strategies:
                    self.active_strategies.append(strategy_id)
                elif not updates['enabled'] and strategy_id in self.active_strategies:
                    self.active_strategies.remove(strategy_id)

            self.logger.info(f"Strategy updated: {strategy_id}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_strategy",
                "strategy_id": strategy_id
            })
            return False

    def remove_strategy(self, strategy_id: str) -> bool:
        """
        Remove a strategy.

        Args:
            strategy_id: Strategy ID to remove

        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if strategy_id not in self.strategies:
                self.logger.warning(f"Strategy {strategy_id} not found for removal")
                return False

            # Remove from active strategies
            if strategy_id in self.active_strategies:
                self.active_strategies.remove(strategy_id)

            # Remove strategy
            strategy = self.strategies.pop(strategy_id)

            self.logger.info(f"Strategy removed: {strategy_id} - {strategy.name}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "remove_strategy",
                "strategy_id": strategy_id
            })
            return False

    def enable_strategy(self, strategy_id: str) -> bool:
        """
        Enable a strategy.

        Args:
            strategy_id: Strategy ID to enable

        Returns:
            True if enabled successfully, False otherwise
        """
        try:
            if strategy_id not in self.strategies:
                return False

            strategy = self.strategies[strategy_id]
            strategy.enabled = True
            strategy.last_modified = datetime.now()

            if strategy_id not in self.active_strategies:
                self.active_strategies.append(strategy_id)

            self.logger.info(f"Strategy enabled: {strategy_id}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "enable_strategy",
                "strategy_id": strategy_id
            })
            return False

    def disable_strategy(self, strategy_id: str) -> bool:
        """
        Disable a strategy.

        Args:
            strategy_id: Strategy ID to disable

        Returns:
            True if disabled successfully, False otherwise
        """
        try:
            if strategy_id not in self.strategies:
                return False

            strategy = self.strategies[strategy_id]
            strategy.enabled = False
            strategy.last_modified = datetime.now()

            if strategy_id in self.active_strategies:
                self.active_strategies.remove(strategy_id)

            self.logger.info(f"Strategy disabled: {strategy_id}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "disable_strategy",
                "strategy_id": strategy_id
            })
            return False

    def generate_signals(self, market_data: Dict[str, Any]) -> List[Signal]:
        """
        Generate trading signals from all active strategies.

        Args:
            market_data: Current market data

        Returns:
            List of generated signals
        """
        try:
            signals = []
            current_time = datetime.now()

            for strategy_id in self.active_strategies:
                strategy = self.strategies[strategy_id]
                
                try:
                    # Generate signals for this strategy
                    strategy_signals = self._execute_strategy(strategy, market_data)
                    
                    for signal in strategy_signals:
                        signal.timestamp = current_time
                        signal.strategy_id = strategy_id
                        signals.append(signal)

                except Exception as e:
                    self.logger.log_error(e, {
                        "operation": "generate_signals",
                        "strategy_id": strategy_id
                    })

            # Store signals
            self.signals.extend(signals)

            # Clean up old signals
            self._cleanup_old_signals()

            self.logger.debug(f"Generated {len(signals)} signals from {len(self.active_strategies)} strategies")
            return signals

        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_signals"})
            return []

    def get_signals(self, strategy_id: Optional[str] = None, 
                    signal_type: Optional[SignalType] = None,
                    active_only: bool = True) -> List[Signal]:
        """
        Get signals with optional filtering.

        Args:
            strategy_id: Filter by strategy ID
            signal_type: Filter by signal type
            active_only: Return only active signals

        Returns:
            List of filtered signals
        """
        try:
            filtered_signals = self.signals if active_only else self.signals + self.signal_history

            if strategy_id:
                filtered_signals = [s for s in filtered_signals if s.strategy_id == strategy_id]

            if signal_type:
                filtered_signals = [s for s in filtered_signals if s.signal_type == signal_type]

            return filtered_signals

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_signals"})
            return []

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """
        Get strategy by ID.

        Args:
            strategy_id: Strategy ID

        Returns:
            Strategy object if exists, None otherwise
        """
        return self.strategies.get(strategy_id)

    def get_strategies(self, active_only: bool = False) -> List[Strategy]:
        """
        Get all strategies.

        Args:
            active_only: Return only active strategies

        Returns:
            List of strategies
        """
        try:
            if active_only:
                return [self.strategies[sid] for sid in self.active_strategies if sid in self.strategies]
            return list(self.strategies.values())

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_strategies"})
            return []

    def get_strategy_summary(self) -> Dict[str, Any]:
        """
        Get summary of all strategies.

        Returns:
            Dictionary containing strategy summary
        """
        try:
            active_strategies = self.get_strategies(active_only=True)
            inactive_strategies = [s for s in self.strategies.values() if not s.enabled]

            summary = {
                'total_strategies': len(self.strategies),
                'active_strategies': len(active_strategies),
                'inactive_strategies': len(inactive_strategies),
                'total_signals': len(self.signals),
                'active_signals': len([s for s in self.signals if s.is_active]),
                'strategies_by_type': {},
                'recent_signals': []
            }

            # Group strategies by type
            for strategy in self.strategies.values():
                strategy_type = strategy.strategy_type
                if strategy_type not in summary['strategies_by_type']:
                    summary['strategies_by_type'][strategy_type] = 0
                summary['strategies_by_type'][strategy_type] += 1

            # Get recent signals
            recent_signals = sorted(self.signals, key=lambda x: x.timestamp, reverse=True)[:10]
            summary['recent_signals'] = [
                {
                    'strategy_id': s.strategy_id,
                    'symbol': s.symbol,
                    'signal_type': s.signal_type.value,
                    'strength': s.strength.value,
                    'timestamp': s.timestamp.isoformat()
                }
                for s in recent_signals
            ]

            return summary

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_strategy_summary"})
            return {'error': str(e)}

    def _validate_strategy(self, strategy: Strategy) -> bool:
        """Validate strategy data."""
        try:
            if not strategy.strategy_id or not strategy.strategy_id.strip():
                return False

            if not strategy.name or not strategy.name.strip():
                return False

            if not strategy.strategy_type:
                return False

            if strategy.parameters is None:
                return False

            return True

        except Exception as e:
            self.logger.log_error(e, {"operation": "validate_strategy"})
            return False

    def _execute_strategy(self, strategy: Strategy, market_data: Dict[str, Any]) -> List[Signal]:
        """Execute a strategy to generate signals."""
        try:
            signals = []

            # This is a placeholder for actual strategy execution
            # In a real implementation, this would call the strategy's execute method
            # and return actual trading signals based on technical analysis

            # For now, return empty list
            # The actual implementation would depend on the specific strategy type
            # and would involve calling technical indicators, pattern recognition, etc.

            return signals

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "execute_strategy",
                "strategy_id": strategy.strategy_id
            })
            return []

    def _cleanup_old_signals(self) -> None:
        """Clean up old signals."""
        try:
            if not self.signal_timeout_minutes:
                return

            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(minutes=self.signal_timeout_minutes)
            
            # Move old signals to history
            old_signals = [s for s in self.signals if s.timestamp < cutoff_time]
            
            for signal in old_signals:
                signal.is_active = False
                self.signal_history.append(signal)
                self.signals.remove(signal)

            # Keep only recent signals in memory
            if len(self.signals) > 1000:
                excess_signals = self.signals[:-1000]
                for signal in excess_signals:
                    signal.is_active = False
                    self.signal_history.append(signal)
                self.signals = self.signals[-1000:]

            # Keep only last 5000 signals in history
            if len(self.signal_history) > 5000:
                self.signal_history = self.signal_history[-5000:]

        except Exception as e:
            self.logger.log_error(e, {"operation": "cleanup_old_signals"})

    def _load_default_strategies(self) -> None:
        """Load default trading strategies."""
        try:
            # Add some default strategies
            default_strategies = [
                Strategy(
                    strategy_id="MA_CROSSOVER",
                    name="Moving Average Crossover",
                    description="Simple moving average crossover strategy",
                    strategy_type="TREND_FOLLOWING",
                    parameters={
                        "fast_ma": 20,
                        "slow_ma": 50,
                        "min_signal_strength": 0.7
                    },
                    enabled=True,
                    created_at=datetime.now()
                ),
                Strategy(
                    strategy_id="RSI_MEAN_REVERSION",
                    name="RSI Mean Reversion",
                    description="RSI-based mean reversion strategy",
                    strategy_type="MEAN_REVERSION",
                    parameters={
                        "rsi_period": 14,
                        "oversold_threshold": 30,
                        "overbought_threshold": 70
                    },
                    enabled=True,
                    created_at=datetime.now()
                )
            ]

            for strategy in default_strategies:
                self.strategies[strategy.strategy_id] = strategy
                if strategy.enabled:
                    self.active_strategies.append(strategy.strategy_id)

            self.logger.info(f"Loaded {len(default_strategies)} default strategies")

        except Exception as e:
            self.logger.log_error(e, {"operation": "load_default_strategies"})

    def _load_custom_strategies(self) -> None:
        """Load custom strategies from configuration or files."""
        try:
            # This would load custom strategies from configuration files
            # For now, just log that we're ready to accept custom strategies
            self.logger.info("Ready to load custom strategies")

        except Exception as e:
            self.logger.log_error(e, {"operation": "load_custom_strategies"}) 