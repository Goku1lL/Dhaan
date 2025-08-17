"""
Configuration management for the Dhan Advanced Algo Trading System.
Uses Singleton pattern to ensure single configuration instance.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from decimal import Decimal

from .exceptions import ConfigurationException


@dataclass
class TradingConfig:
    """Trading configuration parameters."""
    risk_per_trade: float = 0.02  # 2% risk per trade
    risk_reward_ratio: float = 1.5  # 1:1.5 risk-reward
    max_positions: int = 10
    max_capital_per_trade: Decimal = Decimal('10000')
    min_capital_per_trade: Decimal = Decimal('1000')
    position_sizing_method: str = "RISK_BASED"  # RISK_BASED, FIXED_AMOUNT, KELLY_CRITERION
    
    # Strategy Manager specific configurations
    max_strategies: int = 20  # Maximum number of active strategies
    signal_timeout_minutes: int = 60  # Signal timeout in minutes
    
    # Paper Trading Configuration
    trading_mode: str = "PAPER"  # PAPER or LIVE
    paper_trading_balance: Decimal = Decimal('100000')  # ₹1 Lakh virtual money
    paper_trading_commission: Decimal = Decimal('20')  # ₹20 per trade
    paper_trading_slippage: float = 0.001  # 0.1% slippage simulation
    max_pending_orders: int = 50  # Maximum pending orders
    order_timeout_minutes: int = 60  # Order timeout in minutes


@dataclass
class MarketConfig:
    """Market configuration parameters."""
    market_open_time: str = "09:15"
    market_close_time: str = "15:30"
    pre_market_start: str = "09:00"
    post_market_end: str = "15:45"
    trading_timezone: str = "Asia/Kolkata"
    candle_timeframe: str = "5min"
    max_historical_candles: int = 100


@dataclass
class BrokerConfig:
    """Broker configuration parameters."""
    client_id: str = ""
    access_token: str = ""
    api_base_url: str = ""
    request_timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0  # Increased from 0.1 to 1 second to respect Dhan's rate limits


@dataclass
class NotificationConfig:
    """Notification configuration parameters."""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    enable_telegram: bool = True
    enable_email: bool = False
    enable_sms: bool = False
    notification_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR


@dataclass
class DatabaseConfig:
    """Database configuration parameters."""
    database_type: str = "EXCEL"  # EXCEL, SQLITE, POSTGRESQL
    excel_file_path: str = "live_trade_data.xlsx"
    completed_orders_file: str = "completed_orders.xlsx"
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class SystemConfig:
    """System configuration parameters."""
    log_level: str = "INFO"
    log_file: str = "trading_system.log"
    max_log_size_mb: int = 100
    log_backup_count: int = 5
    enable_debug_mode: bool = False
    performance_monitoring: bool = True


@dataclass
class MarketScannerConfig:
    """Market scanner configuration parameters."""
    scan_interval_seconds: int = 300  # 5 minutes
    min_confidence_score: float = 0.7  # Minimum confidence for opportunities
    max_concurrent_stocks: int = 3  # Reduced from 10 to 3 to avoid overwhelming Dhan's API
    batch_size: int = 2  # Reduced from 5 to 2 for smaller batches
    timeout_seconds: int = 30  # Timeout for individual stock analysis
    stock_universe: Optional[List[str]] = None  # Custom stock universe (if None, uses default)


@dataclass
class EODSummaryConfig:
    """EOD Summary configuration parameters."""
    report_retention_days: int = 30  # Number of days to keep reports
    min_confidence_threshold: float = 0.7  # Minimum confidence for including in reports


class ConfigurationManager:
    """
    Configuration manager using Singleton pattern.
    Manages all configuration parameters for the trading system.
    """
    
    _instance: Optional['ConfigurationManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ConfigurationManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._trading_config = TradingConfig()
            self._market_config = MarketConfig()
            self._broker_config = BrokerConfig()
            self._notification_config = NotificationConfig()
            self._database_config = DatabaseConfig()
            self._system_config = SystemConfig()
            self._market_scanner_config = MarketScannerConfig()
            self._eod_summary_config = EODSummaryConfig()
            
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'ConfigurationManager':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        try:
            # Broker config
            self._broker_config.client_id = os.getenv('DHAN_CLIENT_ID', '')
            self._broker_config.access_token = os.getenv('DHAN_ACCESS_TOKEN', '')
            self._broker_config.api_base_url = os.getenv('DHAN_API_URL', '')
            
            # Notification config
            self._notification_config.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
            self._notification_config.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
            
            # Trading config
            risk_per_trade = os.getenv('RISK_PER_TRADE')
            if risk_per_trade:
                self._trading_config.risk_per_trade = float(risk_per_trade)
            
            max_positions = os.getenv('MAX_POSITIONS')
            if max_positions:
                self._trading_config.max_positions = int(max_positions)
            
            # System config
            log_level = os.getenv('LOG_LEVEL')
            if log_level:
                self._system_config.log_level = log_level.upper()
            
            enable_debug = os.getenv('ENABLE_DEBUG')
            if enable_debug:
                self._system_config.enable_debug_mode = enable_debug.lower() == 'true'
                
        except Exception as e:
            raise ConfigurationException(f"Failed to load environment configuration: {str(e)}")
    
    def load_from_file(self, config_file_path: str) -> None:
        """Load configuration from a JSON/YAML file."""
        try:
            import json
            with open(config_file_path, 'r') as f:
                config_data = json.load(f)
            
            # Update configurations based on file data
            if 'trading' in config_data:
                self._update_trading_config(config_data['trading'])
            if 'market' in config_data:
                self._update_market_config(config_data['market'])
            if 'broker' in config_data:
                self._update_broker_config(config_data['broker'])
            if 'notification' in config_data:
                self._update_notification_config(config_data['notification'])
            if 'database' in config_data:
                self._update_database_config(config_data['database'])
            if 'system' in config_data:
                self._update_system_config(config_data['system'])
                
        except Exception as e:
            raise ConfigurationException(f"Failed to load configuration file {config_file_path}: {str(e)}")
    
    def _update_trading_config(self, config_data: Dict[str, Any]) -> None:
        """Update trading configuration from dictionary."""
        for key, value in config_data.items():
            if hasattr(self._trading_config, key):
                if key in ['max_capital_per_trade', 'min_capital_per_trade']:
                    setattr(self._trading_config, key, Decimal(str(value)))
                else:
                    setattr(self._trading_config, key, value)
    
    def _update_market_config(self, config_data: Dict[str, Any]) -> None:
        """Update market configuration from dictionary."""
        for key, value in config_data.items():
            if hasattr(self._market_config, key):
                setattr(self._market_config, key, value)
    
    def _update_broker_config(self, config_data: Dict[str, Any]) -> None:
        """Update broker configuration from dictionary."""
        for key, value in config_data.items():
            if hasattr(self._broker_config, key):
                setattr(self._broker_config, key, value)
    
    def _update_notification_config(self, config_data: Dict[str, Any]) -> None:
        """Update notification configuration from dictionary."""
        for key, value in config_data.items():
            if hasattr(self._notification_config, key):
                setattr(self._notification_config, key, value)
    
    def _update_database_config(self, config_data: Dict[str, Any]) -> None:
        """Update database configuration from dictionary."""
        for key, value in config_data.items():
            if hasattr(self._database_config, key):
                setattr(self._database_config, key, value)
    
    def _update_system_config(self, config_data: Dict[str, Any]) -> None:
        """Update system configuration from dictionary."""
        for key, value in config_data.items():
            if hasattr(self._system_config, key):
                setattr(self._system_config, key, value)
    
    def set_custom_config(self, key: str, value: Any) -> None:
        """Set a custom configuration value."""
        self._custom_config[key] = value
    
    def get_custom_config(self, key: str, default: Any = None) -> Any:
        """Get a custom configuration value."""
        return self._custom_config.get(key, default)
    
    # Property getters for each configuration section
    @property
    def trading(self) -> TradingConfig:
        return self._trading_config
    
    @property
    def market(self) -> MarketConfig:
        return self._market_config
    
    @property
    def broker(self) -> BrokerConfig:
        return self._broker_config
    
    @property
    def notification(self) -> NotificationConfig:
        return self._notification_config
    
    @property
    def database(self) -> DatabaseConfig:
        return self._database_config
    
    @property
    def system(self) -> SystemConfig:
        return self._system_config
    
    @property
    def market_scanner(self) -> MarketScannerConfig:
        return self._market_scanner_config
    
    @property
    def eod_summary(self) -> EODSummaryConfig:
        return self._eod_summary_config
    
    def validate_configuration(self) -> bool:
        """Validate that all required configuration is present."""
        required_fields = [
            (self._broker_config.client_id, "DHAN_CLIENT_ID"),
            (self._broker_config.access_token, "DHAN_ACCESS_TOKEN"),
            (self._notification_config.telegram_bot_token, "TELEGRAM_BOT_TOKEN"),
            (self._notification_config.telegram_chat_id, "TELEGRAM_CHAT_ID")
        ]
        
        missing_fields = []
        for value, field_name in required_fields:
            if not value:
                missing_fields.append(field_name)
        
        if missing_fields:
            raise ConfigurationException(f"Missing required configuration fields: {', '.join(missing_fields)}")
        
        return True
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return {
            'trading': {
                'risk_per_trade': self._trading_config.risk_per_trade,
                'max_positions': self._trading_config.max_positions,
                'position_sizing_method': self._trading_config.position_sizing_method
            },
            'market': {
                'market_open_time': self._market_config.market_open_time,
                'market_close_time': self._market_config.market_close_time,
                'candle_timeframe': self._market_config.candle_timeframe
            },
            'broker': {
                'client_id': self._broker_config.client_id[:8] + "..." if self._broker_config.client_id else None,
                'api_base_url': self._broker_config.api_base_url
            },
            'notification': {
                'enable_telegram': self._notification_config.enable_telegram,
                'notification_level': self._notification_config.notification_level
            },
            'system': {
                'log_level': self._system_config.log_level,
                'enable_debug_mode': self._system_config.enable_debug_mode
            }
        } 