"""Telegram bot integration for trading alerts."""

import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

try:
    import telepot
    TELEPOT_AVAILABLE = True
except ImportError:
    TELEPOT_AVAILABLE = False
    logger.warning("telepot not available. Telegram features will be disabled.")


class TelegramManager:
    """Manages Telegram bot operations and alerts."""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram manager.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID for alerts
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = None
        
        if TELEPOT_AVAILABLE and bot_token and chat_id:
            self._initialize_bot()
        else:
            logger.warning("Telegram bot not initialized. Check token and chat ID.")
    
    def _initialize_bot(self):
        """Initialize the Telegram bot."""
        try:
            self.bot = telepot.Bot(self.bot_token)
            logger.info("Telegram bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.bot = None
    
    def send_alert(self, message: str) -> bool:
        """
        Send alert message to Telegram.
        
        Args:
            message: Message to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.bot or not self.chat_id:
            logger.warning("Cannot send Telegram alert: bot not initialized")
            return False
        
        try:
            self.bot.sendMessage(self.chat_id, message)
            logger.debug(f"Telegram alert sent: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def send_entry_alert(self, symbol: str, entry_price: float, quantity: int, 
                        stop_loss: float, target: float, order_id: str, side: str) -> bool:
        """
        Send entry alert to Telegram.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            quantity: Quantity traded
            stop_loss: Stop loss price
            target: Target price
            order_id: Order ID
            side: Buy/Sell side
            
        Returns:
            True if alert sent successfully
        """
        emoji = "📈" if side == "BUY" else "📉"
        side_text = "Buy" if side == "BUY" else "Sell"
        
        message = (
            f"{emoji} Entry Done: {symbol}\n"
            f"Side: {side_text}\n"
            f"Entry Price: {entry_price}\n"
            f"Quantity: {quantity}\n"
            f"SL: {stop_loss}\n"
            f"Target: {target}\n"
            f"Order ID: {order_id}"
        )
        
        return self.send_alert(message)
    
    def send_exit_alert(self, symbol: str, exit_price: float, pnl: float, 
                        reason: str) -> bool:
        """
        Send exit alert to Telegram.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            pnl: Profit/Loss
            reason: Reason for exit (SL Hit, Target Hit, etc.)
            
        Returns:
            True if alert sent successfully
        """
        if "SL" in reason:
            emoji = "📉"
        elif "Target" in reason:
            emoji = "🎯"
        else:
            emoji = "📊"
        
        message = (
            f"{emoji} {reason}: {symbol}\n"
            f"Exit Price: {exit_price}\n"
            f"PNL: {pnl}"
        )
        
        return self.send_alert(message)
    
    def send_margin_alert(self, symbol: str, available_margin: float, 
                          required_margin: float) -> bool:
        """
        Send margin warning alert to Telegram.
        
        Args:
            symbol: Trading symbol
            available_margin: Available margin
            required_margin: Required margin
            
        Returns:
            True if alert sent successfully
        """
        message = (
            f"⚠️ Low Margin: Not taking order for {symbol}\n"
            f"Available: {available_margin}\n"
            f"Required: {required_margin}"
        )
        
        return self.send_alert(message)
    
    def send_market_status_alert(self, status: str, message: str = "") -> bool:
        """
        Send market status alert to Telegram.
        
        Args:
            status: Market status (Open, Close, etc.)
            message: Additional message
            
        Returns:
            True if alert sent successfully
        """
        if status == "Open":
            emoji = "🌅"
        elif status == "Close":
            emoji = "🌆"
        else:
            emoji = "📊"
        
        full_message = f"{emoji} Market {status}"
        if message:
            full_message += f": {message}"
        
        return self.send_alert(full_message)
    
    def send_error_alert(self, error_message: str, context: str = "") -> bool:
        """
        Send error alert to Telegram.
        
        Args:
            error_message: Error message
            context: Context where error occurred
            
        Returns:
            True if alert sent successfully
        """
        full_message = f"🚨 Error: {error_message}"
        if context:
            full_message += f"\nContext: {context}"
        
        return self.send_alert(full_message)
    
    def is_available(self) -> bool:
        """Check if Telegram functionality is available."""
        return TELEPOT_AVAILABLE and self.bot is not None and self.chat_id is not None 