"""
Logging service for the Dhan Advanced Algo Trading System.
Uses Observer pattern for multiple log handlers and follows SRP.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from .exceptions import ConfigurationException
from .config import ConfigurationManager


class LogHandler(ABC):
    """Abstract base class for log handlers."""
    
    @abstractmethod
    def handle_log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle a log message."""
        pass


class FileLogHandler(LogHandler):
    """File-based log handler."""
    
    def __init__(self, log_file: str, max_size_mb: int = 100, backup_count: int = 5):
        self.log_file = log_file
        self.max_size_mb = max_size_mb
        self.backup_count = backup_count
        self._setup_handler()
    
    def _setup_handler(self) -> None:
        """Setup the file handler with rotation."""
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Create rotating file handler
            handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_size_mb * 1024 * 1024,
                backupCount=self.backup_count
            )
            
            # Set formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            self.handler = handler
            
        except Exception as e:
            raise ConfigurationException(f"Failed to setup file log handler: {str(e)}")
    
    def handle_log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle log message by writing to file."""
        try:
            logger = logging.getLogger('TradingSystem')
            logger.setLevel(logging.DEBUG)
            
            # Add handler if not already added
            if not logger.handlers:
                logger.addHandler(self.handler)
            
            # Format message with context
            formatted_message = message
            if context:
                context_str = ' | '.join([f"{k}: {v}" for k, v in context.items()])
                formatted_message = f"{message} | Context: {context_str}"
            
            # Log based on level
            level_map = {
                'DEBUG': logger.debug,
                'INFO': logger.info,
                'WARNING': logger.warning,
                'ERROR': logger.error,
                'CRITICAL': logger.critical
            }
            
            log_func = level_map.get(level.upper(), logger.info)
            log_func(formatted_message)
            
        except Exception as e:
            # Fallback to stderr if logging fails
            print(f"Logging failed: {str(e)}", file=sys.stderr)


class ConsoleLogHandler(LogHandler):
    """Console-based log handler."""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level
        self._setup_handler()
    
    def _setup_handler(self) -> None:
        """Setup the console handler."""
        try:
            handler = logging.StreamHandler(sys.stdout)
            
            # Set formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # Set level
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            handler.setLevel(level_map.get(self.log_level.upper(), logging.INFO))
            
            self.handler = handler
            
        except Exception as e:
            raise ConfigurationException(f"Failed to setup console log handler: {str(e)}")
    
    def handle_log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle log message by writing to console."""
        try:
            logger = logging.getLogger('TradingSystem')
            logger.setLevel(logging.DEBUG)
            
            # Add handler if not already added
            if not logger.handlers:
                logger.addHandler(self.handler)
            
            # Format message with context
            formatted_message = message
            if context:
                context_str = ' | '.join([f"{k}: {v}" for k, v in context.items()])
                formatted_message = f"{message} | Context: {context_str}"
            
            # Log based on level
            level_map = {
                'DEBUG': logger.debug,
                'INFO': logger.info,
                'WARNING': logger.warning,
                'ERROR': logger.error,
                'CRITICAL': logger.critical
            }
            
            log_func = level_map.get(level.upper(), logger.info)
            log_func(formatted_message)
            
        except Exception as e:
            # Fallback to stderr if logging fails
            print(f"Console logging failed: {str(e)}", file=sys.stderr)


class TelegramLogHandler(LogHandler):
    """Telegram-based log handler."""
    
    def __init__(self, bot_token: str, chat_id: str, log_level: str = "ERROR"):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.log_level = log_level
        self._setup_handler()
    
    def _setup_handler(self) -> None:
        """Setup the telegram handler."""
        try:
            import telepot
            self.bot = telepot.Bot(self.bot_token)
            self.enabled = True
        except ImportError:
            print("Telepot not available, Telegram logging disabled", file=sys.stderr)
            self.enabled = False
        except Exception as e:
            print(f"Telegram setup failed: {str(e)}", file=sys.stderr)
            self.enabled = False
    
    def handle_log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle log message by sending to Telegram."""
        if not self.enabled:
            return
        
        try:
            # Only send important logs to Telegram
            important_levels = ['ERROR', 'CRITICAL', 'WARNING']
            if level.upper() not in important_levels:
                return
            
            # Format message
            formatted_message = f"🚨 {level.upper()}: {message}"
            if context:
                context_str = ' | '.join([f"{k}: {v}" for k, v in context.items()])
                formatted_message += f"\nContext: {context_str}"
            
            # Send to Telegram
            self.bot.sendMessage(self.chat_id, formatted_message)
            
        except Exception as e:
            # Fallback to stderr if Telegram fails
            print(f"Telegram logging failed: {str(e)}", file=sys.stderr)


class LoggingService:
    """
    Centralized logging service using Observer pattern.
    Manages multiple log handlers and provides unified logging interface.
    """
    
    def __init__(self):
        self.config = ConfigurationManager.get_instance()
        self.handlers: List[LogHandler] = []
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup log handlers based on configuration."""
        try:
            # File handler
            if self.config.system.log_file:
                file_handler = FileLogHandler(
                    self.config.system.log_file,
                    self.config.system.max_log_size_mb,
                    self.config.system.log_backup_count
                )
                self.handlers.append(file_handler)
            
            # Console handler
            console_handler = ConsoleLogHandler(self.config.system.log_level)
            self.handlers.append(console_handler)
            
            # Telegram handler (only for important logs)
            if (self.config.notification.enable_telegram and 
                self.config.notification.telegram_bot_token and 
                self.config.notification.telegram_chat_id):
                telegram_handler = TelegramLogHandler(
                    self.config.notification.telegram_bot_token,
                    self.config.notification.telegram_chat_id,
                    "WARNING"  # Only send warnings and errors
                )
                self.handlers.append(telegram_handler)
                
        except Exception as e:
            # Fallback to basic console logging
            print(f"Failed to setup logging handlers: {str(e)}", file=sys.stderr)
            basic_handler = ConsoleLogHandler("INFO")
            self.handlers.append(basic_handler)
    
    def add_handler(self, handler: LogHandler) -> None:
        """Add a new log handler."""
        self.handlers.append(handler)
    
    def remove_handler(self, handler: LogHandler) -> None:
        """Remove a log handler."""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log a message with the specified level and context."""
        timestamp = datetime.now().isoformat()
        
        # Add timestamp to context
        if context is None:
            context = {}
        context['timestamp'] = timestamp
        
        # Notify all handlers
        for handler in self.handlers:
            try:
                handler.handle_log(level, message, context)
            except Exception as e:
                # If a handler fails, log the error to stderr
                print(f"Handler {handler.__class__.__name__} failed: {str(e)}", file=sys.stderr)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self.log('DEBUG', message, context)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self.log('INFO', message, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self.log('WARNING', message, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error message."""
        self.log('ERROR', message, context)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log critical message."""
        self.log('CRITICAL', message, context)
    
    def log_trade_event(self, event_type: str, symbol: str, details: Dict[str, Any]) -> None:
        """Log trade-specific events."""
        context = {
            'event_type': event_type,
            'symbol': symbol,
            **details
        }
        self.info(f"Trade Event: {event_type} for {symbol}", context)
    
    def log_system_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log system-specific events."""
        context = {
            'event_type': event_type,
            **details
        }
        self.info(f"System Event: {event_type}", context)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an exception with context."""
        error_context = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            **(context or {})
        }
        self.error(f"Exception occurred: {str(error)}", error_context)
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get a summary of logging configuration."""
        return {
            'handlers_count': len(self.handlers),
            'handler_types': [type(handler).__name__ for handler in self.handlers],
            'log_level': self.config.system.log_level,
            'log_file': self.config.system.log_file,
            'telegram_enabled': any(isinstance(h, TelegramLogHandler) for h in self.handlers)
        } 