"""Technical indicators and analysis functions."""

import pandas as pd
from typing import Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logger.warning("TA-Lib not available. Technical indicators will be limited.")


class TechnicalIndicators:
    """Technical analysis indicators calculator."""
    
    def __init__(self):
        """Initialize the technical indicators calculator."""
        if not TALIB_AVAILABLE:
            logger.warning("TA-Lib is required for full functionality.")
    
    def compute_supertrend(self, df: pd.DataFrame, period: int = 7, 
                          multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
        """
        Compute SuperTrend indicator.
        
        Args:
            df: DataFrame with High, Low, Close columns
            period: ATR period
            multiplier: ATR multiplier
            
        Returns:
            Tuple of (supertrend_values, direction_values)
        """
        if not TALIB_AVAILABLE or df.empty:
            logger.warning("Cannot compute SuperTrend: TA-Lib unavailable or empty data")
            return pd.Series([0] * len(df)), pd.Series([0] * len(df))
        
        try:
            # Calculate ATR
            atr = talib.ATR(df["High"], df["Low"], df["Close"], timeperiod=period)
            
            # Calculate basic bands
            hl2 = (df["High"] + df["Low"]) / 2
            upperband = hl2 + multiplier * atr
            lowerband = hl2 - multiplier * atr
            
            # Initialize SuperTrend
            supertrend = pd.Series(0.0, index=df.index)
            direction = pd.Series(1, index=df.index)
            
            # Calculate SuperTrend values
            for i in range(1, len(df)):
                prev_super = supertrend.iloc[i - 1]
                prev_dir = direction.iloc[i - 1]
                
                if df["Close"].iloc[i] > upperband.iloc[i - 1]:
                    direction.iloc[i] = 1
                    supertrend.iloc[i] = lowerband.iloc[i]
                elif df["Close"].iloc[i] < lowerband.iloc[i - 1]:
                    direction.iloc[i] = -1
                    supertrend.iloc[i] = upperband.iloc[i]
                else:
                    direction.iloc[i] = prev_dir
                    if prev_dir == 1:
                        supertrend.iloc[i] = min(lowerband.iloc[i], prev_super)
                    else:
                        supertrend.iloc[i] = max(upperband.iloc[i], prev_super)
            
            return supertrend, direction
            
        except Exception as e:
            logger.error(f"Error computing SuperTrend: {e}")
            return pd.Series([0] * len(df)), pd.Series([0] * len(df))
    
    def compute_rsi(self, close_prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Compute RSI indicator.
        
        Args:
            close_prices: Series of closing prices
            period: RSI period
            
        Returns:
            RSI values series
        """
        if not TALIB_AVAILABLE:
            logger.warning("Cannot compute RSI: TA-Lib unavailable")
            return pd.Series([None] * len(close_prices))
        
        try:
            return talib.RSI(close_prices, timeperiod=period)
        except Exception as e:
            logger.error(f"Error computing RSI: {e}")
            return pd.Series([None] * len(close_prices))
    
    def compute_sma(self, close_prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Compute Simple Moving Average.
        
        Args:
            close_prices: Series of closing prices
            period: SMA period
            
        Returns:
            SMA values series
        """
        if not TALIB_AVAILABLE:
            logger.warning("Cannot compute SMA: TA-Lib unavailable")
            return pd.Series([None] * len(close_prices))
        
        try:
            return talib.SMA(close_prices, timeperiod=period)
        except Exception as e:
            logger.error(f"Error computing SMA: {e}")
            return pd.Series([None] * len(close_prices))
    
    def detect_doji(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Doji candlestick patterns.
        
        Args:
            df: DataFrame with Open, High, Low, Close columns
            
        Returns:
            Doji pattern values series
        """
        if not TALIB_AVAILABLE:
            logger.warning("Cannot detect Doji: TA-Lib unavailable")
            return pd.Series([0] * len(df))
        
        try:
            return talib.CDLDOJI(df["Open"], df["High"], df["Low"], df["Close"])
        except Exception as e:
            logger.error(f"Error detecting Doji: {e}")
            return pd.Series([0] * len(df))
    
    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to the DataFrame.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with indicators added
        """
        try:
            # Ensure column names are capitalized
            df = df.copy()
            df.rename(columns=lambda c: c.capitalize(), inplace=True)
            
            # Add RSI
            df["RSI"] = self.compute_rsi(df["Close"])
            
            # Add SuperTrend
            st, st_dir = self.compute_supertrend(df[["High", "Low", "Close"]])
            df["SuperTrend_Dir"] = st_dir
            
            # Add Doji pattern
            df["Doji"] = self.detect_doji(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding indicators: {e}")
            return df
    
    def get_indicator_values(self, df: pd.DataFrame, candle_index: int = -2) -> dict:
        """
        Get indicator values for a specific candle.
        
        Args:
            df: DataFrame with indicators
            candle_index: Index of the candle (default: -2 for completed candle)
            
        Returns:
            Dictionary of indicator values
        """
        try:
            if df.empty or len(df) < abs(candle_index):
                return {}
            
            candle = df.iloc[candle_index]
            
            return {
                "RSI": candle.get("RSI"),
                "SuperTrend_Dir": candle.get("SuperTrend_Dir"),
                "Doji": candle.get("Doji"),
                "Close": candle.get("Close"),
                "High": candle.get("High"),
                "Low": candle.get("Low"),
                "Open": candle.get("Open")
            }
            
        except Exception as e:
            logger.error(f"Error getting indicator values: {e}")
            return {}


# Global instance
indicators = TechnicalIndicators() 