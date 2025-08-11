"""Main entry point for the Dhan Advanced Algo Trading System."""

import logging
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from dhan_advanced_algo.trading_engine import TradingEngine
from dhan_advanced_algo.config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function to run the trading system."""
    try:
        logger.info("=" * 60)
        logger.info("Starting Dhan Advanced Algo Trading System")
        logger.info("=" * 60)
        
        # Check configuration
        if CLIENT_ID == "YOUR_CLIENT_ID" or ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
            logger.error("Please configure your Dhan API credentials in config.py or environment variables")
            logger.error("Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN environment variables")
            return
        
        if BOT_TOKEN == "YOUR_BOT_TOKEN" or CHAT_ID == "YOUR_CHAT_ID":
            logger.warning("Telegram credentials not configured. Alerts will be disabled.")
            logger.warning("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        
        # Check if Excel files exist
        if not LIVE_TRADE_FILE.exists():
            logger.error(f"Live trade Excel file not found: {LIVE_TRADE_FILE}")
            logger.info("Please create the Excel file or check the path in config.py")
            return
        
        if not COMPLETED_ORDERS_FILE.exists():
            logger.error(f"Completed orders Excel file not found: {COMPLETED_ORDERS_FILE}")
            logger.info("Please create the Excel file or check the path in config.py")
            return
        
        # Initialize and run trading engine
        trading_engine = TradingEngine()
        
        # Check if all components are available
        if not trading_engine.dhan_client:
            logger.error("Dhan API client not available. Cannot proceed.")
            return
        
        logger.info("All systems ready. Starting trading engine...")
        
        # Run the trading engine
        trading_engine.run()
        
    except KeyboardInterrupt:
        logger.info("Trading system stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        logger.info("Trading system shutdown complete")


if __name__ == "__main__":
    main() 