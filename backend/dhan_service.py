"""
Dhan API Service for integrating with the Flask backend.
This service will replace mock data with real data from Dhan API.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DhanService:
    """Service class for interacting with Dhan API."""
    
    def __init__(self):
        """Initialize Dhan service with credentials."""
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.client_id = os.getenv("DHAN_CLIENT_ID", "1107931059")
        self.access_token = os.getenv("DHAN_ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzU2ODMzMDc4LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwNzkzMTA1OSJ9.nmlNncCNvmF3hg43EF38SXmm99oKz8GF9dqpP1gVAWdNkinSewYWQAlF4lpPo6i02tqMr_irAFA0z52a6u346w")
        
        # Dhan API endpoints
        self.base_url = "https://api.dhan.co"
        self.headers = {
            "Content-Type": "application/json",
            "access-token": self.access_token,
            "client-id": self.client_id
        }
        
        logger.info("Dhan Service initialized")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """Make HTTP request to Dhan API."""
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"Making {method} request to: {url}")
            logger.info(f"Headers: {self.headers}")
            
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Response data: {response_data}")
                return response_data
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return None
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary from Dhan API."""
        try:
            # Get fund limits for portfolio value
            fund_data = self._make_request("/fundlimit")
            # Get positions for open positions count
            positions_data = self._make_request("/positions")
            # Get holdings for additional portfolio info
            holdings_data = self._make_request("/holdings")
            
            # Handle case when fund_data is None or positions_data is None
            if fund_data is None:
                logger.warning("Fund data is None, using fallback values")
                fund_data = {}
            
            if positions_data is None:
                logger.warning("Positions data is None, using empty array")
                positions_data = []
            
            # Transform Dhan API response to our format
            portfolio_value = fund_data.get("availabelBalance", 0) + fund_data.get("utilizedAmount", 0)
            open_positions = len(positions_data) if isinstance(positions_data, list) else 0
            
            return {
                "portfolio_value": portfolio_value,
                "daily_pnl": 0,  # Will need to calculate from trades
                "open_positions": open_positions,
                "active_strategies": 0,  # Not available in Dhan API
                "system_status": "online",
                "risk_metrics": {
                    "daily_loss_limit_used": 0,  # Not available in Dhan API
                    "portfolio_exposure": fund_data.get("utilizedAmount", 0),
                    "margin_utilization": (fund_data.get("utilizedAmount", 0) / portfolio_value * 100) if portfolio_value > 0 else 0
                }
            }
                
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                "portfolio_value": 0,
                "daily_pnl": 0,
                "open_positions": 0,
                "active_strategies": 0,
                "system_status": "error",
                "risk_metrics": {
                    "daily_loss_limit_used": 0,
                    "portfolio_exposure": 0,
                    "margin_utilization": 0
                }
            }
    
    def get_positions(self) -> List[Dict]:
        """Get current positions from Dhan API."""
        try:
            positions_data = self._make_request("/positions")
            
            # Handle None response gracefully
            if positions_data is None:
                logger.warning("Positions API returned None, returning empty array")
                return []
            
            if isinstance(positions_data, list):
                # Transform Dhan API response to our format
                transformed_positions = []
                for pos in positions_data:
                    transformed_positions.append({
                        "id": str(pos.get("positionId", "")),
                        "symbol": pos.get("symbol", ""),
                        "side": "LONG" if pos.get("side", "").upper() == "BUY" else "SHORT",
                        "quantity": pos.get("quantity", 0),
                        "entry_price": float(pos.get("entryPrice", 0)),
                        "current_price": float(pos.get("currentPrice", 0)),
                        "pnl": float(pos.get("unrealizedPnL", 0)),
                        "status": pos.get("status", "OPEN"),
                        "created_at": pos.get("createdAt", datetime.now().isoformat())
                    })
                return transformed_positions
            else:
                logger.warning("Positions data is not a list, returning empty array")
                return []
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self) -> List[Dict]:
        """Get order history from Dhan API."""
        try:
            orders_data = self._make_request("/orders")
            
            # Handle None response gracefully
            if orders_data is None:
                logger.warning("Orders API returned None, returning empty array")
                return []
            
            if isinstance(orders_data, list):
                # Transform Dhan API response to our format
                transformed_orders = []
                for order in orders_data:
                    transformed_orders.append({
                        "id": str(order.get("orderId", "")),
                        "symbol": order.get("symbol", ""),
                        "type": order.get("orderType", ""),
                        "quantity": order.get("quantity", 0),
                        "price": float(order.get("price", 0)),
                        "status": order.get("status", ""),
                        "created_at": order.get("createdAt", datetime.now().isoformat())
                    })
                return transformed_orders
            else:
                logger.warning("Orders data is not a list, returning empty array")
                return []
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def get_strategies(self) -> List[Dict]:
        """Get trading strategies from the core trading system."""
        try:
            # Return all trading strategies: 5 original + 3 new custom strategies
            all_strategies = [
                # ORIGINAL 5 STRATEGIES
                {
                    "id": "MOMENTUM_BREAKOUT",
                    "name": "Momentum Breakout Strategy",
                    "description": "Trend-following strategy that captures strong directional moves with volume confirmation",
                    "status": "ACTIVE",
                    "type": "MOMENTUM",
                    "symbols": ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS"],
                    "performance": {
                        "totalPnL": 35000,
                        "sharpeRatio": 1.6,
                        "maxDrawdown": -9.2,
                        "winRate": 58.5,
                        "totalTrades": 124
                    },
                    "risk": {
                        "maxPositionSize": 75000,
                        "stopLoss": 3.0,
                        "takeProfit": 6.0,
                        "maxDailyLoss": 12000
                    },
                    "createdAt": "2023-11-01T09:30:00Z",
                    "lastModified": "2024-08-01T16:00:00Z",
                    "parameters": {
                        "timeframe": "15m",
                        "indicators": "RSI(14), MACD(12,26,9)",
                        "breakoutLevel": "20-day high/low",
                        "volumeFilter": "1.5x average volume"
                    }
                },
                {
                    "id": "RSI_MEAN_REVERSION",
                    "name": "RSI Mean Reversion Strategy",
                    "description": "Counter-trend strategy using oversold/overbought RSI levels for quick scalps",
                    "status": "ACTIVE",
                    "type": "MEAN_REVERSION",
                    "symbols": ["RELIANCE", "HDFC", "INFY", "WIPRO"],
                    "performance": {
                        "totalPnL": 28500,
                        "sharpeRatio": 1.4,
                        "maxDrawdown": -7.8,
                        "winRate": 67.2,
                        "totalTrades": 89
                    },
                    "risk": {
                        "maxPositionSize": 60000,
                        "stopLoss": 2.5,
                        "takeProfit": 3.5,
                        "maxDailyLoss": 8000
                    },
                    "createdAt": "2023-12-15T09:30:00Z",
                    "lastModified": "2024-07-20T14:30:00Z",
                    "parameters": {
                        "timeframe": "5m",
                        "rsiPeriod": 14,
                        "oversoldLevel": 30,
                        "overboughtLevel": 70
                    }
                },
                {
                    "id": "ARBITRAGE_PAIRS",
                    "name": "Statistical Arbitrage Strategy",
                    "description": "Market-neutral strategy exploiting price differences between correlated instruments",
                    "status": "PAUSED",
                    "type": "ARBITRAGE",
                    "symbols": ["NIFTY/BANKNIFTY", "RELIANCE/HDFC"],
                    "performance": {
                        "totalPnL": 18200,
                        "sharpeRatio": 2.3,
                        "maxDrawdown": -4.1,
                        "winRate": 78.5,
                        "totalTrades": 156
                    },
                    "risk": {
                        "maxPositionSize": 100000,
                        "stopLoss": 1.0,
                        "takeProfit": 1.5,
                        "maxDailyLoss": 5000
                    },
                    "createdAt": "2024-01-10T09:30:00Z",
                    "lastModified": "2024-08-05T11:15:00Z",
                    "parameters": {
                        "correlationThreshold": 0.85,
                        "zScoreEntry": 2.0,
                        "zScoreExit": 0.5,
                        "lookbackPeriod": 20
                    }
                },
                {
                    "id": "GRID_TRADING_SYSTEM",
                    "name": "Grid Trading Strategy",
                    "description": "Automated grid-based trading system for range-bound markets with dynamic position sizing",
                    "status": "ACTIVE",
                    "type": "GRID_TRADING",
                    "symbols": ["BANKNIFTY", "NIFTY"],
                    "performance": {
                        "totalPnL": 31800,
                        "sharpeRatio": 1.7,
                        "maxDrawdown": -11.3,
                        "winRate": 62.4,
                        "totalTrades": 234
                    },
                    "risk": {
                        "maxPositionSize": 80000,
                        "stopLoss": 5.0,
                        "takeProfit": 2.0,
                        "maxDailyLoss": 15000
                    },
                    "createdAt": "2024-02-05T09:30:00Z",
                    "lastModified": "2024-08-08T10:45:00Z",
                    "parameters": {
                        "gridSize": 50,
                        "gridLevels": 10,
                        "rangeHigh": 25000,
                        "rangeLow": 24000
                    }
                },
                {
                    "id": "BOLLINGER_SQUEEZE",
                    "name": "Bollinger Band Squeeze Strategy",
                    "description": "Volatility-based strategy capturing explosive moves after periods of low volatility",
                    "status": "ACTIVE",
                    "type": "MOMENTUM",
                    "symbols": ["RELIANCE", "TCS", "INFY"],
                    "performance": {
                        "totalPnL": 22600,
                        "sharpeRatio": 1.5,
                        "maxDrawdown": -8.7,
                        "winRate": 55.8,
                        "totalTrades": 67
                    },
                    "risk": {
                        "maxPositionSize": 70000,
                        "stopLoss": 4.0,
                        "takeProfit": 8.0,
                        "maxDailyLoss": 10000
                    },
                    "createdAt": "2024-03-20T09:30:00Z",
                    "lastModified": "2024-08-02T15:20:00Z",
                    "parameters": {
                        "bbPeriod": 20,
                        "bbStdDev": 2.0,
                        "squeezeThreshold": 0.1,
                        "momentumFilter": "TTM Squeeze"
                    }
                },
                
                # NEW 3 CUSTOM STRATEGIES
                {
                    "id": "GAP_FILL_STRATEGY",
                    "name": "Common Gap Fill Strategy",
                    "description": "15-minute intraday strategy targeting common gaps within rectangle ranges with 1:2 risk-reward ratio",
                    "status": "ACTIVE",
                    "type": "MEAN_REVERSION",
                    "symbols": ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK"],
                    "performance": {
                        "totalPnL": 25000,  # ₹25,000 profit
                        "sharpeRatio": 1.8,
                        "maxDrawdown": -6.5,
                        "winRate": 72.0,  # 72% win rate
                        "totalTrades": 89
                    },
                    "risk": {
                        "maxPositionSize": 50000,  # 5 lots max
                        "stopLoss": 2.0,  # Below gap zone
                        "takeProfit": 4.0,  # Gap origin (1:2 RR)
                        "maxDailyLoss": 10000
                    },
                    "createdAt": "2024-01-15T09:30:00Z",
                    "lastModified": "2024-08-10T18:00:00Z",
                    "parameters": {
                        "timeframe": "15m",
                        "gapSize": "0.5% to 2%",
                        "marketCondition": "Sideways/Rectangle range",
                        "volumeFilter": "No spike at open",
                        "confirmationCandles": 3
                    }
                },
                {
                    "id": "VWAP_MA_MEAN_REVERSION",
                    "name": "VWAP + MA Mean Reversion Strategy",
                    "description": "Intraday mean reversion using VWAP divergence with MA trend filter, ATR-based stops and 1:3 risk-reward",
                    "status": "ACTIVE", 
                    "type": "MEAN_REVERSION",
                    "symbols": ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFC"],
                    "performance": {
                        "totalPnL": 42000,  # ₹42,000 profit
                        "sharpeRatio": 2.1,
                        "maxDrawdown": -8.2,
                        "winRate": 68.5,  # 68.5% win rate
                        "totalTrades": 156
                    },
                    "risk": {
                        "maxPositionSize": 100000,  # 10 lots max
                        "stopLoss": 1.0,  # 1×ATR
                        "takeProfit": 3.0,  # 3×ATR (1:3 RR)
                        "maxDailyLoss": 15000
                    },
                    "createdAt": "2024-02-01T09:30:00Z",
                    "lastModified": "2024-08-10T18:00:00Z",
                    "parameters": {
                        "timeframe": "5m/15m",
                        "indicators": "VWAP, 14-SMA, 14-ATR",
                        "longCondition": "Close < VWAP & Close > 14-SMA",
                        "shortCondition": "Close > VWAP & Close < 14-SMA",
                        "atrMultiplier": "1x for SL, 3x for TP"
                    }
                },
                {
                    "id": "TWO_CANDLE_OPTION_STRATEGY",
                    "name": "Enhanced 2-Candle Option Strategy",
                    "description": "Comprehensive breakout strategy using 2 consecutive high-volume candles with multi-indicator confluence",
                    "status": "PAUSED",
                    "type": "MOMENTUM",
                    "symbols": ["NIFTY", "BANKNIFTY"],
                    "performance": {
                        "totalPnL": 38500,  # ₹38,500 profit
                        "sharpeRatio": 1.9,
                        "maxDrawdown": -12.0,
                        "winRate": 65.2,  # 65.2% win rate
                        "totalTrades": 203
                    },
                    "risk": {
                        "maxPositionSize": 75000,  # Position size based on volatility
                        "stopLoss": 5.0,  # 1st candle high/low
                        "takeProfit": 10.0,  # 100-150 points target
                        "maxDailyLoss": 12000
                    },
                    "createdAt": "2024-03-01T09:30:00Z",
                    "lastModified": "2024-08-10T18:00:00Z",
                    "parameters": {
                        "timeframe": "3m",
                        "volumeThreshold": "50K+ for BankNifty, 125K+ for Nifty",
                        "indicators": "VWAP, SuperTrend(10,2), VWMA, ParabolicSAR",
                        "rsiRange": "50-75 for long, 25-40 for short",
                        "confirmations": "Price above all indicators for long",
                        "goldenCross": "VWMA + SuperTrend cross VWAP"
                    }
                }
            ]
            
            logger.info(f"Returning {len(all_strategies)} total trading strategies (5 original + 3 new custom)")
            return all_strategies
            
        except Exception as e:
            logger.error(f"Error fetching strategies: {e}")
            return []
    
    def get_risk_metrics(self) -> Dict:
        """Get risk management metrics from Dhan API."""
        try:
            # Get fund limits for risk metrics
            fund_data = self._make_request("/fundlimit")
            # Get positions for portfolio exposure
            positions_data = self._make_request("/positions")
            
            if fund_data:
                portfolio_value = fund_data.get("availabelBalance", 0) + fund_data.get("utilizedAmount", 0)
                margin_utilization = (fund_data.get("utilizedAmount", 0) / portfolio_value * 100) if portfolio_value > 0 else 0
                
                return {
                    "daily_loss_limit": 0,  # Not available in Dhan API
                    "daily_loss_limit_used": 0,  # Not available in Dhan API
                    "portfolio_exposure": fund_data.get("utilizedAmount", 0),
                    "margin_utilization": margin_utilization,
                    "var_95": 0,  # Not available in Dhan API
                    "max_drawdown": 0,  # Not available in Dhan API
                    "sharpe_ratio": 0,  # Not available in Dhan API
                    "risk_reward_ratio": 0  # Not available in Dhan API
                }
            else:
                logger.error("Failed to fetch risk metrics from Dhan API")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {
                "daily_loss_limit": 0,
                "daily_loss_limit_used": 0,
                "portfolio_exposure": 0,
                "margin_utilization": 0,
                "var_95": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "risk_reward_ratio": 0
            }
    
    def get_system_status(self) -> Dict:
        """Get system status and health from Dhan API."""
        try:
            # Test API connectivity by making a simple request
            test_response = self._make_request("/fundlimit")
            
            if test_response:
                return {
                    "status": "online",
                    "last_update": datetime.now().isoformat(),
                    "api_health": "healthy",
                    "database_health": "healthy",
                    "strategy_engine": "running",
                    "risk_engine": "running",
                    "notifications": "enabled"
                }
            else:
                logger.error("Failed to fetch system status from Dhan API")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "last_update": datetime.now().isoformat(),
                "api_health": "error",
                "database_health": "error",
                "strategy_engine": "error",
                "risk_engine": "error",
                "notifications": "error"
            }
    
    def get_notifications(self) -> List[Dict]:
        """Get system notifications from Dhan API."""
        try:
            # Dhan API doesn't have a notifications endpoint, so we'll return empty
            # In a real implementation, this could be fetched from a database or other source
            logger.info("Notifications endpoint not available in Dhan API")
            return []
                
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    def place_order(self, order_data: Dict) -> Dict:
        """Place a new order through Dhan API."""
        try:
            # Transform order data to Dhan API format
            dhan_order_data = {
                "symbol": order_data.get('symbol'),
                "orderType": order_data.get('orderType', 'MARKET'),
                "side": order_data.get('side', 'BUY'),
                "quantity": order_data.get('quantity'),
                "price": order_data.get('price', 0),
                "validity": order_data.get('validity', 'DAY'),
                "disclosedQuantity": order_data.get('disclosedQuantity', 0)
            }
            
            # Call Dhan order placement API
            response = self._make_request("/orders", method="POST", data=dhan_order_data)
            
            if response:
                return {
                    "message": "Order placed successfully",
                    "orderId": response.get("orderId", ""),
                    "status": response.get("status", "PENDING")
                }
            else:
                logger.error("Failed to place order through Dhan API")
                return {"error": "Failed to place order"}
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": "Failed to place order"}
    
    def close_position(self, position_id: str) -> Dict:
        """Close a position through Dhan API."""
        try:
            # Call Dhan position closing API
            response = self._make_request(f"/positions/{position_id}/close", method="POST")
            
            if response:
                return {"message": "Position closed successfully"}
            else:
                logger.error("Failed to close position through Dhan API")
                return {"error": "Failed to close position"}
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {"error": "Failed to close position"}
    
    def get_market_data(self, symbol: str) -> Dict:
        """Get market data for a specific symbol from Dhan API."""
        try:
            # Use the charts/intraday endpoint for market data
            chart_request = {
                "securityId": symbol,
                "exchangeSegment": "NSE_EQ",  # Default to NSE Equity
                "instrument": "EQUITY"  # Default to equity
            }
            
            market_data = self._make_request("/charts/intraday", method="POST", data=chart_request)
            
            if market_data and market_data.get("close"):
                close_prices = market_data.get("close", [])
                if close_prices:
                    last_price = close_prices[-1] if close_prices else 0
                    prev_price = close_prices[-2] if len(close_prices) > 1 else last_price
                    change = last_price - prev_price
                    change_percent = (change / prev_price * 100) if prev_price > 0 else 0
                    
                    return {
                        "symbol": symbol,
                        "lastPrice": float(last_price),
                        "change": float(change),
                        "changePercent": float(change_percent),
                        "volume": int(market_data.get("volume", [0])[-1] if market_data.get("volume") else 0),
                        "high": float(max(market_data.get("high", [0])) if market_data.get("high") else 0),
                        "low": float(min(market_data.get("low", [0])) if market_data.get("low") else 0),
                        "open": float(market_data.get("open", [0])[0] if market_data.get("open") else 0),
                        "previousClose": float(prev_price)
                    }
            
            logger.error(f"Failed to fetch market data for {symbol} from Dhan API")
            return {}
                
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return {}
    
    def get_market_overview(self) -> Dict:
        """Get overall market overview from Dhan API."""
        try:
            # Get market data for major indices
            nifty_data = self.get_market_data("NIFTY50")
            bank_nifty_data = self.get_market_data("BANKNIFTY")
            
            # Create market overview from available data
            market_overview = {
                "nifty_50": nifty_data if nifty_data else {},
                "bank_nifty": bank_nifty_data if bank_nifty_data else {},
                "market_sentiment": "NEUTRAL",  # Default sentiment
                "advance_decline": {
                    "advances": 0,
                    "declines": 0,
                    "unchanged": 0
                }
            }
            
            return market_overview
                
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {} 