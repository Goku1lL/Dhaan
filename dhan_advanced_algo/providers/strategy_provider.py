"""
Strategy provider implementation.
Handles trading strategy logic and signal generation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime

from ..core.interfaces import IStrategyProvider
from ..core.entities import MarketData, OrderSide
from ..core.exceptions import StrategyException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager


class StrategyProvider(IStrategyProvider):
    """
    Strategy provider implementation.
    Handles trading strategy logic and signal generation.
    """
    
    def __init__(self, config: ConfigurationManager):
        """
        Initialize strategy provider.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = LoggingService()
        
        # Strategy parameters
        self.rsi_period = self.config.strategy.rsi_period
        self.rsi_overbought = self.config.strategy.rsi_overbought
        self.rsi_oversold = self.config.strategy.rsi_oversold
        
        self.supertrend_period = self.config.strategy.supertrend_period
        self.supertrend_multiplier = self.config.strategy.supertrend_multiplier
        
        self.bb_period = self.config.strategy.bb_period
        self.bb_std_dev = self.config.strategy.bb_std_dev
        
        self.logger.info("Strategy Provider initialized")
    
    def get_signals(self, symbol: str, market_data: List[MarketData]) -> Dict[str, Any]:
        """
        Get trading signals for a symbol based on market data.
        
        Args:
            symbol: Trading symbol
            market_data: List of market data points
            
        Returns:
            Dictionary containing trading signals
        """
        try:
            if not market_data or len(market_data) < 50:  # Need minimum data for indicators
                return {}
            
            # Convert to pandas DataFrame
            df = self._convert_to_dataframe(market_data)
            
            # Calculate indicators
            df = self._calculate_indicators(df)
            
            # Generate signals
            signals = self._generate_signals(df)
            
            self.logger.debug(f"Generated signals for {symbol}: {signals}")
            return signals
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "get_signals",
                "symbol": symbol
            })
            return {}
    
    def _convert_to_dataframe(self, market_data: List[MarketData]) -> pd.DataFrame:
        """
        Convert market data list to pandas DataFrame.
        
        Args:
            market_data: List of MarketData objects
            
        Returns:
            Pandas DataFrame with market data
        """
        data = []
        for md in market_data:
            data.append({
                'timestamp': md.timestamp,
                'open': float(md.open),
                'high': float(md.high),
                'low': float(md.low),
                'close': float(md.close),
                'volume': md.volume,
                'ltp': float(md.ltp) if md.ltp else float(md.close)
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators on the DataFrame.
        
        Args:
            df: Pandas DataFrame with OHLCV data
            
        Returns:
            DataFrame with calculated indicators
        """
        try:
            # RSI
            df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
            
            # SuperTrend
            df['supertrend'], df['supertrend_direction'] = self._calculate_supertrend(
                df, self.supertrend_period, self.supertrend_multiplier
            )
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger_bands(
                df['close'], self.bb_period, self.bb_std_dev
            )
            
            # Moving Averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_histogram'] = self._calculate_macd(df['close'])
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            return df
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_indicators"})
            return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Price series
            period: RSI period
            
        Returns:
            RSI series
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_rsi"})
            return pd.Series([np.nan] * len(prices))
    
    def _calculate_supertrend(self, df: pd.DataFrame, period: int, multiplier: float) -> tuple[pd.Series, pd.Series]:
        """
        Calculate SuperTrend indicator.
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period
            multiplier: ATR multiplier
            
        Returns:
            Tuple of (supertrend, direction)
        """
        try:
            # Calculate ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            atr = true_range.rolling(period).mean()
            
            # Calculate SuperTrend
            hl2 = (df['high'] + df['low']) / 2
            upperband = hl2 + (multiplier * atr)
            lowerband = hl2 - (multiplier * atr)
            
            supertrend = pd.Series([np.nan] * len(df))
            direction = pd.Series([np.nan] * len(df))
            
            for i in range(1, len(df)):
                if df['close'].iloc[i] > upperband.iloc[i-1]:
                    direction.iloc[i] = 1
                elif df['close'].iloc[i] < lowerband.iloc[i-1]:
                    direction.iloc[i] = -1
                else:
                    direction.iloc[i] = direction.iloc[i-1]
                
                if direction.iloc[i] == 1 and lowerband.iloc[i] < lowerband.iloc[i-1]:
                    lowerband.iloc[i] = lowerband.iloc[i-1]
                if direction.iloc[i] == -1 and upperband.iloc[i] > upperband.iloc[i-1]:
                    upperband.iloc[i] = upperband.iloc[i-1]
                
                if direction.iloc[i] == 1:
                    supertrend.iloc[i] = lowerband.iloc[i]
                else:
                    supertrend.iloc[i] = upperband.iloc[i]
            
            return supertrend, direction
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_supertrend"})
            return pd.Series([np.nan] * len(df)), pd.Series([np.nan] * len(df))
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int, std_dev: float) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Price series
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (upper, middle, lower) bands
        """
        try:
            middle = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return upper, middle, lower
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_bollinger_bands"})
            return pd.Series([np.nan] * len(prices)), pd.Series([np.nan] * len(prices)), pd.Series([np.nan] * len(prices))
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD indicator.
        
        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            
        Returns:
            Tuple of (macd, signal, histogram)
        """
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signal).mean()
            macd_histogram = macd - macd_signal
            
            return macd, macd_signal, macd_histogram
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_macd"})
            return pd.Series([np.nan] * len(prices)), pd.Series([np.nan] * len(prices)), pd.Series([np.nan] * len(prices))
    
    def _generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on calculated indicators.
        
        Args:
            df: DataFrame with calculated indicators
            
        Returns:
            Dictionary containing trading signals
        """
        try:
            if df.empty or df['close'].isna().all():
                return {}
            
            # Get latest values (second to last to avoid repainting)
            latest_idx = -2 if len(df) > 1 else -1
            
            signals = {}
            
            # Entry signals
            entry_signal = self._check_entry_conditions(df, latest_idx)
            if entry_signal:
                signals['entry_signal'] = True
                signals['side'] = entry_signal['side']
                signals['confidence'] = entry_signal['confidence']
                signals['reason'] = entry_signal['reason']
            
            # Exit signals
            exit_signal = self._check_exit_conditions(df, latest_idx)
            if exit_signal:
                signals['exit_signal'] = True
                signals['exit_reason'] = exit_signal['reason']
                signals['exit_confidence'] = exit_signal['confidence']
            
            # Stop loss and target levels
            if entry_signal:
                stop_loss, target = self._calculate_stop_loss_target(df, latest_idx, entry_signal['side'])
                signals['stop_loss'] = stop_loss
                signals['target'] = target
                signals['stop_loss_distance'] = abs(stop_loss - df['close'].iloc[latest_idx]) / df['close'].iloc[latest_idx]
            
            return signals
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_signals"})
            return {}
    
    def _check_entry_conditions(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """
        Check entry conditions for a given index.
        
        Args:
            df: DataFrame with indicators
            idx: Index to check
            
        Returns:
            Entry signal dictionary or None
        """
        try:
            if idx < 0 or idx >= len(df):
                return None
            
            # Get current values
            current = df.iloc[idx]
            previous = df.iloc[idx-1] if idx > 0 else current
            
            # Initialize signal components
            buy_signals = []
            sell_signals = []
            
            # RSI conditions
            if not pd.isna(current['rsi']):
                if current['rsi'] < self.rsi_oversold:
                    buy_signals.append(('RSI_OVERSOLD', 0.3))
                elif current['rsi'] > self.rsi_overbought:
                    sell_signals.append(('RSI_OVERBOUGHT', 0.3))
            
            # SuperTrend conditions
            if not pd.isna(current['supertrend_direction']):
                if current['supertrend_direction'] == 1 and previous['supertrend_direction'] == -1:
                    buy_signals.append(('SUPERTREND_BULLISH_CROSS', 0.4))
                elif current['supertrend_direction'] == -1 and previous['supertrend_direction'] == 1:
                    sell_signals.append(('SUPERTREND_BEARISH_CROSS', 0.4))
            
            # Bollinger Bands conditions
            if not pd.isna(current['bb_lower']) and not pd.isna(current['bb_upper']):
                if current['close'] <= current['bb_lower']:
                    buy_signals.append(('BB_LOWER_TOUCH', 0.2))
                elif current['close'] >= current['bb_upper']:
                    sell_signals.append(('BB_UPPER_TOUCH', 0.2))
            
            # Moving Average conditions
            if not pd.isna(current['sma_20']) and not pd.isna(current['sma_50']):
                if current['sma_20'] > current['sma_50'] and current['close'] > current['sma_20']:
                    buy_signals.append(('MA_BULLISH_ALIGNMENT', 0.3))
                elif current['sma_20'] < current['sma_50'] and current['close'] < current['sma_20']:
                    sell_signals.append(('MA_BEARISH_ALIGNMENT', 0.3))
            
            # MACD conditions
            if not pd.isna(current['macd']) and not pd.isna(current['macd_signal']):
                if current['macd'] > current['macd_signal'] and previous['macd'] <= previous['macd_signal']:
                    buy_signals.append(('MACD_BULLISH_CROSS', 0.3))
                elif current['macd'] < current['macd_signal'] and previous['macd'] >= previous['macd_signal']:
                    sell_signals.append(('MACD_BEARISH_CROSS', 0.3))
            
            # Volume confirmation
            volume_confirmation = 0.1
            if not pd.isna(current['volume_ratio']) and current['volume_ratio'] > 1.5:
                volume_confirmation = 0.2
            
            # Determine best signal
            if buy_signals and len(buy_signals) > 0:
                # Sort by confidence and take the highest
                buy_signals.sort(key=lambda x: x[1], reverse=True)
                best_buy = buy_signals[0]
                
                return {
                    'side': OrderSide.BUY,
                    'confidence': min(0.9, best_buy[1] + volume_confirmation),
                    'reason': best_buy[0]
                }
            
            elif sell_signals and len(sell_signals) > 0:
                # Sort by confidence and take the highest
                sell_signals.sort(key=lambda x: x[1], reverse=True)
                best_sell = sell_signals[0]
                
                return {
                    'side': OrderSide.SELL,
                    'confidence': min(0.9, best_sell[1] + volume_confirmation),
                    'reason': best_sell[0]
                }
            
            return None
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "check_entry_conditions"})
            return None
    
    def _check_exit_conditions(self, df: pd.DataFrame, idx: int) -> Optional[Dict[str, Any]]:
        """
        Check exit conditions for a given index.
        
        Args:
            df: DataFrame with indicators
            idx: Index to check
            
        Returns:
            Exit signal dictionary or None
        """
        try:
            if idx < 0 or idx >= len(df):
                return None
            
            current = df.iloc[idx]
            previous = df.iloc[idx-1] if idx > 0 else current
            
            exit_signals = []
            
            # RSI extreme conditions
            if not pd.isna(current['rsi']):
                if current['rsi'] > 80:
                    exit_signals.append(('RSI_EXTREME_OVERBOUGHT', 0.4))
                elif current['rsi'] < 20:
                    exit_signals.append(('RSI_EXTREME_OVERSOLD', 0.4))
            
            # SuperTrend reversal
            if not pd.isna(current['supertrend_direction']) and not pd.isna(previous['supertrend_direction']):
                if current['supertrend_direction'] != previous['supertrend_direction']:
                    exit_signals.append(('SUPERTREND_REVERSAL', 0.5))
            
            # Moving Average crossover
            if not pd.isna(current['sma_20']) and not pd.isna(current['sma_50']):
                if (current['sma_20'] > current['sma_50'] and previous['sma_20'] <= previous['sma_50']) or \
                   (current['sma_20'] < current['sma_50'] and previous['sma_20'] >= previous['sma_50']):
                    exit_signals.append(('MA_CROSSOVER', 0.3))
            
            # MACD divergence
            if not pd.isna(current['macd']) and not pd.isna(current['macd_histogram']):
                if (current['macd'] > 0 and current['macd_histogram'] < 0) or \
                   (current['macd'] < 0 and current['macd_histogram'] > 0):
                    exit_signals.append(('MACD_DIVERGENCE', 0.3))
            
            if exit_signals:
                # Sort by confidence and take the highest
                exit_signals.sort(key=lambda x: x[1], reverse=True)
                best_exit = exit_signals[0]
                
                return {
                    'reason': best_exit[0],
                    'confidence': best_exit[1]
                }
            
            return None
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "check_exit_conditions"})
            return None
    
    def _calculate_stop_loss_target(self, df: pd.DataFrame, idx: int, side: OrderSide) -> tuple[Decimal, Decimal]:
        """
        Calculate stop loss and target levels.
        
        Args:
            df: DataFrame with indicators
            idx: Index to calculate from
            side: Order side (BUY/SELL)
            
        Returns:
            Tuple of (stop_loss, target)
        """
        try:
            if idx < 0 or idx >= len(df):
                return Decimal('0'), Decimal('0')
            
            current_price = df['close'].iloc[idx]
            
            # Calculate ATR for dynamic levels
            atr = self._calculate_atr(df, idx, 14)
            
            if side == OrderSide.BUY:
                # For buy orders: SL below, target above
                stop_loss = current_price - (atr * 2)  # 2 ATR below
                target = current_price + (atr * 3)     # 3 ATR above
            else:
                # For sell orders: SL above, target below
                stop_loss = current_price + (atr * 2)  # 2 ATR above
                target = current_price - (atr * 3)     # 3 ATR below
            
            return Decimal(str(stop_loss)), Decimal(str(target))
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_stop_loss_target"})
            # Return default levels
            current_price = float(df['close'].iloc[idx]) if idx >= 0 and idx < len(df) else 100
            
            if side == OrderSide.BUY:
                return Decimal(str(current_price * 0.98)), Decimal(str(current_price * 1.02))
            else:
                return Decimal(str(current_price * 1.02)), Decimal(str(current_price * 0.98))
    
    def _calculate_atr(self, df: pd.DataFrame, idx: int, period: int) -> float:
        """
        Calculate Average True Range.
        
        Args:
            df: DataFrame with OHLC data
            idx: Current index
            period: ATR period
            
        Returns:
            ATR value
        """
        try:
            start_idx = max(0, idx - period + 1)
            end_idx = idx + 1
            
            high_low = df['high'].iloc[start_idx:end_idx] - df['low'].iloc[start_idx:end_idx]
            high_close = np.abs(df['high'].iloc[start_idx:end_idx] - df['close'].iloc[start_idx:end_idx-1].shift(1))
            low_close = np.abs(df['low'].iloc[start_idx:end_idx] - df['close'].iloc[start_idx:end_idx-1].shift(1))
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            atr = true_range.mean()
            
            return atr if not pd.isna(atr) else 0.0
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_atr"})
            return 0.0
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about the strategy provider.
        
        Returns:
            Dictionary containing strategy information
        """
        return {
            'name': 'Multi-Strategy Provider',
            'version': '1.0',
            'indicators': ['RSI', 'SuperTrend', 'Bollinger Bands', 'MACD', 'Moving Averages'],
            'parameters': {
                'rsi_period': self.rsi_period,
                'rsi_overbought': self.rsi_overbought,
                'rsi_oversold': self.rsi_oversold,
                'supertrend_period': self.supertrend_period,
                'supertrend_multiplier': self.supertrend_multiplier,
                'bb_period': self.bb_period,
                'bb_std_dev': self.bb_std_dev
            }
        } 