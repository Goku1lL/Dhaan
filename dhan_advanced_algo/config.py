"""Configuration settings for the Dhan Advanced Algo Trading System."""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Dhan API Configuration
CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "1107931059")
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzU2ODMzMDc4LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwNzkzMTA1OSJ9.nmlNncCNvmF3hg43EF38SXmm99oKz8GF9dqpP1gVAWdNkinSewYWQAlF4lpPo6i02tqMr_irAFA0z52a6u346w")

# Telegram Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

# Trading Configuration
MARKET_OPEN_TIME = "09:15:00"
MARKET_CLOSE_TIME = "15:15:00"
TRADING_QUANTITY = 1
STOP_LOSS_PERCENTAGE = 0.002  # 0.2%
TARGET_PERCENTAGE = 0.002     # 0.2%
MARGIN_LEVERAGE = 4.5

# Technical Indicators Configuration
RSI_PERIOD = 14
RSI_OVERBOUGHT = 60
RSI_OVERSOLD = 40
SUPERTREND_PERIOD = 7
SUPERTREND_MULTIPLIER = 3.0
SMA_PERIOD = 20

# Excel Configuration
LIVE_TRADE_FILE = BASE_DIR / "live_trade_data.xlsx"
COMPLETED_ORDERS_FILE = BASE_DIR / "completed_orders.xlsx"
EXCEL_CLEAR_RANGE = "A2:Z100"

# Rate Limiting
LOOP_SLEEP_SECONDS = 5
ORDER_STATUS_DELAY = 1

# File Paths
EXCEL_FILES = {
    "live_trade": LIVE_TRADE_FILE,
    "completed_orders": COMPLETED_ORDERS_FILE
} 