"""
Notification Service implementation.
Handles Telegram notifications, trade alerts, and error alerts.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import telepot
import requests

from ..core.interfaces import INotificationService
from ..core.entities import Trade
from ..core.exceptions import NotificationException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager


class NotificationService(INotificationService):
    """
    Notification service implementation.
    Handles Telegram notifications, trade alerts, and error alerts.
    """

    def __init__(self, config: ConfigurationManager):
        """
        Initialize notification service.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = LoggingService()

        # Telegram configuration
        self.telegram_token = self.config.notification.telegram_bot_token
        self.telegram_chat_id = self.config.notification.telegram_chat_id
        self.telegram_enabled = self.config.notification.telegram_enabled

        # Initialize Telegram bot if enabled
        self.bot = None
        if self.telegram_enabled and self.telegram_token:
            try:
                self.bot = telepot.Bot(self.telegram_token)
                self.logger.info("Telegram bot initialized")
            except Exception as e:
                self.logger.log_error(e, {"operation": "telegram_bot_init"})
                self.telegram_enabled = False

        # Notification settings
        self.trade_alerts_enabled = self.config.notification.trade_alerts_enabled
        self.error_alerts_enabled = self.config.notification.error_alerts_enabled
        self.info_notifications_enabled = self.config.notification.info_notifications_enabled

        # Rate limiting
        self.last_notification_time = {}
        self.min_notification_interval = self.config.notification.min_notification_interval_seconds

        self.logger.info("Notification Service initialized")

    def initialize(self) -> None:
        """Initialize notification service components."""
        try:
            # Test Telegram connection if enabled
            if self.telegram_enabled and self.bot:
                try:
                    bot_info = self.bot.getMe()
                    self.logger.info(f"Telegram bot connected: @{bot_info['username']}")
                except Exception as e:
                    self.logger.log_error(e, {"operation": "telegram_connection_test"})
                    self.telegram_enabled = False

            self.logger.info("Notification Service initialized successfully")
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize"})
            raise NotificationException(f"Failed to initialize notification service: {str(e)}")

    def send_notification(self, message: str, notification_type: str = "INFO") -> bool:
        """
        Send a notification.

        Args:
            message: Message to send
            notification_type: Type of notification (INFO, WARNING, ERROR)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Check rate limiting
            if not self._can_send_notification(notification_type):
                self.logger.debug(f"Rate limited: {notification_type} notification")
                return False

            # Format message
            formatted_message = self._format_message(message, notification_type)

            # Send based on type
            if notification_type == "ERROR" and self.error_alerts_enabled:
                return self._send_telegram_message(formatted_message)
            elif notification_type == "INFO" and self.info_notifications_enabled:
                return self._send_telegram_message(formatted_message)
            elif notification_type == "WARNING":
                return self._send_telegram_message(formatted_message)

            # Update rate limiting
            self._update_notification_time(notification_type)

            self.logger.debug(f"Notification sent: {notification_type}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "send_notification",
                "notification_type": notification_type
            })
            return False

    def send_trade_alert(self, trade: Trade) -> bool:
        """
        Send trade-specific alert.

        Args:
            trade: Trade to send alert for

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.trade_alerts_enabled:
                return False

            # Check rate limiting
            if not self._can_send_notification("TRADE"):
                self.logger.debug("Rate limited: trade notification")
                return False

            # Format trade message
            message = self._format_trade_message(trade)

            # Send via Telegram
            success = self._send_telegram_message(message)

            # Update rate limiting
            if success:
                self._update_notification_time("TRADE")

            return success

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "send_trade_alert",
                "trade_id": trade.trade_id
            })
            return False

    def send_error_alert(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Send error alert.

        Args:
            error: Exception that occurred
            context: Additional context information

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.error_alerts_enabled:
                return False

            # Check rate limiting
            if not self._can_send_notification("ERROR"):
                self.logger.debug("Rate limited: error notification")
                return False

            # Format error message
            message = self._format_error_message(error, context)

            # Send via Telegram
            success = self._send_telegram_message(message)

            # Update rate limiting
            if success:
                self._update_notification_time("ERROR")

            return success

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "send_error_alert",
                "original_error": str(error)
            })
            return False

    def send_position_alert(self, symbol: str, side: str, quantity: int, 
                           entry_price: float, current_price: float, 
                           unrealized_pnl: float) -> bool:
        """
        Send position update alert.

        Args:
            symbol: Trading symbol
            side: Position side (BUY/SELL)
            quantity: Position quantity
            entry_price: Entry price
            current_price: Current market price
            unrealized_pnl: Unrealized P&L

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.trade_alerts_enabled:
                return False

            # Check rate limiting
            if not self._can_send_notification("POSITION"):
                self.logger.debug("Rate limited: position notification")
                return False

            # Format position message
            message = self._format_position_message(
                symbol, side, quantity, entry_price, current_price, unrealized_pnl
            )

            # Send via Telegram
            success = self._send_telegram_message(message)

            # Update rate limiting
            if success:
                self._update_notification_time("POSITION")

            return success

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "send_position_alert",
                "symbol": symbol
            })
            return False

    def send_daily_summary(self, summary: Dict[str, Any]) -> bool:
        """
        Send daily trading summary.

        Args:
            summary: Daily summary data

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.info_notifications_enabled:
                return False

            # Check rate limiting
            if not self._can_send_notification("DAILY_SUMMARY"):
                self.logger.debug("Rate limited: daily summary notification")
                return False

            # Format summary message
            message = self._format_daily_summary_message(summary)

            # Send via Telegram
            success = self._send_telegram_message(message)

            # Update rate limiting
            if success:
                self._update_notification_time("DAILY_SUMMARY")

            return success

        except Exception as e:
            self.logger.log_error(e, {"operation": "send_daily_summary"})
            return False

    def test_telegram_connection(self) -> bool:
        """
        Test Telegram bot connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.telegram_enabled or not self.bot:
                return False

            bot_info = self.bot.getMe()
            test_message = f"🤖 Bot connection test successful!\nBot: @{bot_info['username']}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            success = self._send_telegram_message(test_message)
            
            if success:
                self.logger.info("Telegram connection test successful")
            else:
                self.logger.warning("Telegram connection test failed")

            return success

        except Exception as e:
            self.logger.log_error(e, {"operation": "test_telegram_connection"})
            return False

    def get_notification_status(self) -> Dict[str, Any]:
        """
        Get notification service status.

        Returns:
            Dictionary containing service status
        """
        try:
            return {
                'telegram_enabled': self.telegram_enabled,
                'telegram_connected': self.bot is not None,
                'trade_alerts_enabled': self.trade_alerts_enabled,
                'error_alerts_enabled': self.error_alerts_enabled,
                'info_notifications_enabled': self.info_notifications_enabled,
                'last_notifications': self.last_notification_time,
                'min_notification_interval': self.min_notification_interval
            }

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_notification_status"})
            return {'error': str(e)}

    def _send_telegram_message(self, message: str) -> bool:
        """Send message via Telegram."""
        try:
            if not self.telegram_enabled or not self.bot:
                return False

            # Send message
            self.bot.sendMessage(self.telegram_chat_id, message, parse_mode='HTML')
            return True

        except Exception as e:
            self.logger.log_error(e, {"operation": "send_telegram_message"})
            return False

    def _format_message(self, message: str, notification_type: str) -> str:
        """Format message for Telegram."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if notification_type == "ERROR":
                icon = "❌"
                prefix = "ERROR"
            elif notification_type == "WARNING":
                icon = "⚠️"
                prefix = "WARNING"
            elif notification_type == "INFO":
                icon = "ℹ️"
                prefix = "INFO"
            else:
                icon = "📢"
                prefix = notification_type.upper()

            formatted = f"{icon} <b>{prefix}</b>\n"
            formatted += f"⏰ {timestamp}\n\n"
            formatted += f"{message}"

            return formatted

        except Exception as e:
            self.logger.log_error(e, {"operation": "format_message"})
            return message

    def _format_trade_message(self, trade: Trade) -> str:
        """Format trade message for Telegram."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Determine emoji based on side
            side_emoji = "🟢" if trade.side.value == "BUY" else "🔴"
            
            # Format P&L with color
            pnl_text = ""
            if trade.realized_pnl:
                pnl_value = float(trade.realized_pnl)
                if pnl_value > 0:
                    pnl_text = f"💰 P&L: +₹{pnl_value:.2f}"
                elif pnl_value < 0:
                    pnl_text = f"💸 P&L: -₹{abs(pnl_value):.2f}"
                else:
                    pnl_text = f"⚖️ P&L: ₹{pnl_value:.2f}"

            message = f"{side_emoji} <b>TRADE EXECUTED</b>\n\n"
            message += f"📊 Symbol: {trade.symbol}\n"
            message += f"📈 Side: {trade.side.value}\n"
            message += f"🔢 Quantity: {trade.quantity}\n"
            message += f"💵 Price: ₹{float(trade.execution_price):.2f}\n"
            message += f"⏰ Time: {timestamp}\n"
            
            if pnl_text:
                message += f"\n{pnl_text}"

            return message

        except Exception as e:
            self.logger.log_error(e, {"operation": "format_trade_message"})
            return f"Trade executed: {trade.symbol} {trade.side.value} {trade.quantity}"

    def _format_error_message(self, error: Exception, context: Dict[str, Any]) -> str:
        """Format error message for Telegram."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            message = f"❌ <b>ERROR ALERT</b>\n\n"
            message += f"🚨 Error: {type(error).__name__}\n"
            message += f"📝 Message: {str(error)}\n"
            message += f"⏰ Time: {timestamp}\n"
            
            if context:
                message += f"\n📋 Context:\n"
                for key, value in context.items():
                    message += f"• {key}: {value}\n"

            return message

        except Exception as e:
            self.logger.log_error(e, {"operation": "format_error_message"})
            return f"Error occurred: {str(error)}"

    def _format_position_message(self, symbol: str, side: str, quantity: int,
                               entry_price: float, current_price: float, 
                               unrealized_pnl: float) -> str:
        """Format position message for Telegram."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Determine emoji based on side
            side_emoji = "🟢" if side == "BUY" else "🔴"
            
            # Format P&L with color
            if unrealized_pnl > 0:
                pnl_emoji = "💰"
                pnl_text = f"+₹{unrealized_pnl:.2f}"
            elif unrealized_pnl < 0:
                pnl_emoji = "💸"
                pnl_text = f"-₹{abs(unrealized_pnl):.2f}"
            else:
                pnl_emoji = "⚖️"
                pnl_text = f"₹{unrealized_pnl:.2f}"

            message = f"{side_emoji} <b>POSITION UPDATE</b>\n\n"
            message += f"📊 Symbol: {symbol}\n"
            message += f"📈 Side: {side}\n"
            message += f"🔢 Quantity: {quantity}\n"
            message += f"💵 Entry: ₹{entry_price:.2f}\n"
            message += f"📊 Current: ₹{current_price:.2f}\n"
            message += f"{pnl_emoji} P&L: {pnl_text}\n"
            message += f"⏰ Time: {timestamp}"

            return message

        except Exception as e:
            self.logger.log_error(e, {"operation": "format_position_message"})
            return f"Position update: {symbol} {side} {quantity}"

    def _format_daily_summary_message(self, summary: Dict[str, Any]) -> str:
        """Format daily summary message for Telegram."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            message = f"📊 <b>DAILY TRADING SUMMARY</b>\n\n"
            message += f"📅 Date: {timestamp.split()[0]}\n"
            message += f"⏰ Time: {timestamp.split()[1]}\n\n"
            
            # Add summary details
            for key, value in summary.items():
                if isinstance(value, (int, float)):
                    if 'pnl' in key.lower() or 'profit' in key.lower() or 'loss' in key.lower():
                        if value > 0:
                            message += f"💰 {key.replace('_', ' ').title()}: +₹{value:.2f}\n"
                        elif value < 0:
                            message += f"💸 {key.replace('_', ' ').title()}: -₹{abs(value):.2f}\n"
                        else:
                            message += f"⚖️ {key.replace('_', ' ').title()}: ₹{value:.2f}\n"
                    else:
                        message += f"📈 {key.replace('_', ' ').title()}: {value}\n"
                else:
                    message += f"📋 {key.replace('_', ' ').title()}: {value}\n"

            return message

        except Exception as e:
            self.logger.log_error(e, {"operation": "format_daily_summary_message"})
            return f"Daily summary: {json.dumps(summary, default=str)}"

    def _can_send_notification(self, notification_type: str) -> bool:
        """Check if notification can be sent (rate limiting)."""
        try:
            if not self.min_notification_interval:
                return True

            current_time = datetime.now()
            last_time = self.last_notification_time.get(notification_type)

            if last_time is None:
                return True

            time_diff = (current_time - last_time).total_seconds()
            return time_diff >= self.min_notification_interval

        except Exception as e:
            self.logger.log_error(e, {"operation": "can_send_notification"})
            return True

    def _update_notification_time(self, notification_type: str) -> None:
        """Update last notification time for rate limiting."""
        try:
            self.last_notification_time[notification_type] = datetime.now()
        except Exception as e:
            self.logger.log_error(e, {"operation": "update_notification_time"}) 