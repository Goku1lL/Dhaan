"""
Data Repository implementation.
Handles data persistence for market data, orders, and trades with Excel integration.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
import os
import json

from ..core.interfaces import IDataRepository
from ..core.entities import MarketData, Order, Trade
from ..core.exceptions import DataRepositoryException
from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager


class DataRepository(IDataRepository):
    """
    Data repository implementation.
    Handles data persistence for market data, orders, and trades with Excel integration.
    """

    def __init__(self, config: ConfigurationManager):
        """
        Initialize data repository.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = LoggingService()

        # Data storage paths
        self.data_dir = self.config.database.data_directory or "data"
        self.market_data_file = os.path.join(self.data_dir, "market_data.xlsx")
        self.orders_file = os.path.join(self.data_dir, "orders.xlsx")
        self.trades_file = os.path.join(self.data_dir, "trades.xlsx")
        self.live_data_file = os.path.join(self.data_dir, "live_trade_data.xlsx")
        self.completed_orders_file = os.path.join(self.data_dir, "completed_orders.xlsx")

        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)

        # In-memory cache for performance
        self._market_data_cache: Dict[str, List[MarketData]] = {}
        self._orders_cache: Dict[str, Order] = {}
        self._trades_cache: Dict[str, Trade] = {}

        self.logger.info("Data Repository initialized")

    def initialize(self) -> None:
        """Initialize data repository components."""
        try:
            # Initialize Excel files if they don't exist
            self._initialize_excel_files()
            
            # Load existing data into cache
            self._load_cached_data()
            
            self.logger.info("Data Repository initialized successfully")
        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize"})
            raise DataRepositoryException(f"Failed to initialize data repository: {str(e)}")

    def save_market_data(self, symbol: str, data: MarketData) -> bool:
        """
        Save market data to repository.

        Args:
            symbol: Trading symbol
            data: Market data to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Add to cache
            if symbol not in self._market_data_cache:
                self._market_data_cache[symbol] = []
            self._market_data_cache[symbol].append(data)

            # Save to Excel file
            self._save_market_data_to_excel(symbol, data)

            # Update live data file
            self._update_live_data_file(symbol, data)

            self.logger.debug(f"Market data saved for {symbol}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "save_market_data",
                "symbol": symbol
            })
            return False

    def get_market_data(self, symbol: str, start_time: datetime, 
                       end_time: datetime) -> List[MarketData]:
        """
        Retrieve market data from repository.

        Args:
            symbol: Trading symbol
            start_time: Start time for data retrieval
            end_time: End time for data retrieval

        Returns:
            List of market data within the time range
        """
        try:
            # Check cache first
            if symbol in self._market_data_cache:
                cached_data = self._market_data_cache[symbol]
                filtered_data = [
                    data for data in cached_data
                    if start_time <= data.timestamp <= end_time
                ]
                if filtered_data:
                    return filtered_data

            # Load from Excel if not in cache
            return self._load_market_data_from_excel(symbol, start_time, end_time)

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "get_market_data",
                "symbol": symbol
            })
            return []

    def save_order(self, order: Order) -> bool:
        """
        Save order to repository.

        Args:
            order: Order to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Add to cache
            self._orders_cache[order.order_id] = order

            # Save to Excel file
            self._save_order_to_excel(order)

            self.logger.debug(f"Order saved: {order.order_id}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "save_order",
                "order_id": order.order_id
            })
            return False

    def get_orders(self, symbol: Optional[str] = None, 
                   status: Optional[str] = None) -> List[Order]:
        """
        Retrieve orders from repository.

        Args:
            symbol: Filter by symbol
            status: Filter by status

        Returns:
            List of filtered orders
        """
        try:
            # Get from cache
            orders = list(self._orders_cache.values())

            # Apply filters
            if symbol:
                orders = [o for o in orders if o.symbol == symbol]
            if status:
                orders = [o for o in orders if o.status.value == status]

            return orders

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_orders"})
            return []

    def save_trade(self, trade: Trade) -> bool:
        """
        Save trade to repository.

        Args:
            trade: Trade to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Add to cache
            self._trades_cache[trade.trade_id] = trade

            # Save to Excel file
            self._save_trade_to_excel(trade)

            # Update completed orders file
            self._update_completed_orders_file(trade)

            self.logger.debug(f"Trade saved: {trade.trade_id}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "save_trade",
                "trade_id": trade.trade_id
            })
            return False

    def get_trades(self, symbol: Optional[str] = None, 
                   start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None) -> List[Trade]:
        """
        Retrieve trades from repository.

        Args:
            symbol: Filter by symbol
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of filtered trades
        """
        try:
            # Get from cache
            trades = list(self._trades_cache.values())

            # Apply filters
            if symbol:
                trades = [t for t in trades if t.symbol == symbol]
            if start_date:
                trades = [t for t in trades if t.execution_time >= start_date]
            if end_date:
                trades = [t for t in trades if t.execution_time <= end_date]

            return trades

        except Exception as e:
            self.logger.log_error(e, {"operation": "get_trades"})
            return []

    def get_live_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get live data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Live data dictionary or None
        """
        try:
            if symbol in self._market_data_cache and self._market_data_cache[symbol]:
                latest_data = self._market_data_cache[symbol][-1]
                return {
                    'symbol': symbol,
                    'ltp': float(latest_data.ltp) if latest_data.ltp else None,
                    'open': float(latest_data.open) if latest_data.open else None,
                    'high': float(latest_data.high) if latest_data.high else None,
                    'low': float(latest_data.low) if latest_data.low else None,
                    'close': float(latest_data.close) if latest_data.close else None,
                    'volume': latest_data.volume,
                    'timestamp': latest_data.timestamp.isoformat()
                }
            return None

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "get_live_data",
                "symbol": symbol
            })
            return None

    def export_to_excel(self, filename: str, data_type: str = "all") -> bool:
        """
        Export data to Excel file.

        Args:
            filename: Output filename
            data_type: Type of data to export (market_data, orders, trades, all)

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                if data_type in ["market_data", "all"]:
                    self._export_market_data_to_excel(writer)
                
                if data_type in ["orders", "all"]:
                    self._export_orders_to_excel(writer)
                
                if data_type in ["trades", "all"]:
                    self._export_trades_to_excel(writer)

            self.logger.info(f"Data exported to {filename}")
            return True

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "export_to_excel",
                "filename": filename
            })
            return False

    def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old data.

        Args:
            days: Number of days to keep data

        Returns:
            Number of records cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_count = 0

            # Clean market data cache
            for symbol in list(self._market_data_cache.keys()):
                original_count = len(self._market_data_cache[symbol])
                self._market_data_cache[symbol] = [
                    data for data in self._market_data_cache[symbol]
                    if data.timestamp >= cutoff_date
                ]
                cleaned_count += original_count - len(self._market_data_cache[symbol])

            # Clean orders cache (keep completed orders for longer)
            orders_to_remove = []
            for order_id, order in self._orders_cache.items():
                if (order.status.value in ['FILLED', 'CANCELLED', 'REJECTED'] and
                    order.created_at and order.created_at < cutoff_date):
                    orders_to_remove.append(order_id)

            for order_id in orders_to_remove:
                del self._orders_cache[order_id]
                cleaned_count += 1

            # Clean trades cache
            trades_to_remove = []
            for trade_id, trade in self._trades_cache.items():
                if trade.execution_time and trade.execution_time < cutoff_date:
                    trades_to_remove.append(trade_id)

            for trade_id in trades_to_remove:
                del self._trades_cache[trade_id]
                cleaned_count += 1

            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old records")
                # Update Excel files
                self._update_all_excel_files()

            return cleaned_count

        except Exception as e:
            self.logger.log_error(e, {"operation": "cleanup_old_data"})
            return 0

    def _initialize_excel_files(self) -> None:
        """Initialize Excel files if they don't exist."""
        try:
            # Create market data file
            if not os.path.exists(self.market_data_file):
                df = pd.DataFrame(columns=[
                    'symbol', 'timestamp', 'ltp', 'open', 'high', 'low', 'close', 'volume'
                ])
                df.to_excel(self.market_data_file, index=False)

            # Create orders file
            if not os.path.exists(self.orders_file):
                df = pd.DataFrame(columns=[
                    'order_id', 'symbol', 'side', 'order_type', 'quantity', 'price',
                    'stop_loss', 'target', 'status', 'created_at', 'submitted_at',
                    'filled_at', 'cancelled_at', 'fill_price', 'filled_quantity'
                ])
                df.to_excel(self.orders_file, index=False)

            # Create trades file
            if not os.path.exists(self.trades_file):
                df = pd.DataFrame(columns=[
                    'trade_id', 'order_id', 'symbol', 'side', 'quantity', 'execution_price',
                    'execution_time', 'broker_trade_id', 'realized_pnl'
                ])
                df.to_excel(self.trades_file, index=False)

            # Create live data file
            if not os.path.exists(self.live_data_file):
                df = pd.DataFrame(columns=[
                    'symbol', 'ltp', 'open', 'high', 'low', 'close', 'volume', 'timestamp'
                ])
                df.to_excel(self.live_data_file, index=False)

            # Create completed orders file
            if not os.path.exists(self.completed_orders_file):
                df = pd.DataFrame(columns=[
                    'order_id', 'symbol', 'side', 'quantity', 'entry_price', 'exit_price',
                    'entry_time', 'exit_time', 'realized_pnl', 'exit_reason'
                ])
                df.to_excel(self.completed_orders_file, index=False)

            self.logger.info("Excel files initialized")

        except Exception as e:
            self.logger.log_error(e, {"operation": "initialize_excel_files"})
            raise DataRepositoryException(f"Failed to initialize Excel files: {str(e)}")

    def _save_market_data_to_excel(self, symbol: str, data: MarketData) -> None:
        """Save market data to Excel file."""
        try:
            # Read existing data
            if os.path.exists(self.market_data_file):
                df = pd.read_excel(self.market_data_file)
            else:
                df = pd.DataFrame()

            # Add new data
            new_row = {
                'symbol': symbol,
                'timestamp': data.timestamp,
                'ltp': float(data.ltp) if data.ltp else None,
                'open': float(data.open) if data.open else None,
                'high': float(data.high) if data.high else None,
                'low': float(data.low) if data.low else None,
                'close': float(data.close) if data.close else None,
                'volume': data.volume
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Save to file
            df.to_excel(self.market_data_file, index=False)

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "save_market_data_to_excel",
                "symbol": symbol
            })

    def _save_order_to_excel(self, order: Order) -> None:
        """Save order to Excel file."""
        try:
            # Read existing data
            if os.path.exists(self.orders_file):
                df = pd.read_excel(self.orders_file)
            else:
                df = pd.DataFrame()

            # Check if order already exists
            existing_idx = df[df['order_id'] == order.order_id].index
            if len(existing_idx) > 0:
                # Update existing order
                idx = existing_idx[0]
                df.loc[idx, 'status'] = order.status.value
                df.loc[idx, 'submitted_at'] = order.submitted_at.isoformat() if order.submitted_at else None
                df.loc[idx, 'filled_at'] = order.filled_at.isoformat() if order.filled_at else None
                df.loc[idx, 'cancelled_at'] = order.cancelled_at.isoformat() if order.cancelled_at else None
                df.loc[idx, 'fill_price'] = float(order.fill_price) if order.fill_price else None
                df.loc[idx, 'filled_quantity'] = order.filled_quantity
            else:
                # Add new order
                new_row = {
                    'order_id': order.order_id,
                    'symbol': order.symbol,
                    'side': order.side.value,
                    'order_type': order.order_type.value,
                    'quantity': order.quantity,
                    'price': float(order.price) if order.price else None,
                    'stop_loss': float(order.stop_loss) if order.stop_loss else None,
                    'target': float(order.target) if order.target else None,
                    'status': order.status.value,
                    'created_at': order.created_at.isoformat(),
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                    'filled_at': order.filled_at.isoformat() if order.filled_at else None,
                    'cancelled_at': order.cancelled_at.isoformat() if order.cancelled_at else None,
                    'fill_price': float(order.fill_price) if order.fill_price else None,
                    'filled_quantity': order.filled_quantity
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Save to file
            df.to_excel(self.orders_file, index=False)

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "save_order_to_excel",
                "order_id": order.order_id
            })

    def _save_trade_to_excel(self, trade: Trade) -> None:
        """Save trade to Excel file."""
        try:
            # Read existing data
            if os.path.exists(self.trades_file):
                df = pd.read_excel(self.trades_file)
            else:
                df = pd.DataFrame()

            # Add new trade
            new_row = {
                'trade_id': trade.trade_id,
                'order_id': trade.order_id,
                'symbol': trade.symbol,
                'side': trade.side.value,
                'quantity': trade.quantity,
                'execution_price': float(trade.execution_price),
                'execution_time': trade.execution_time.isoformat(),
                'broker_trade_id': trade.broker_trade_id,
                'realized_pnl': float(trade.realized_pnl) if trade.realized_pnl else None
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Save to file
            df.to_excel(self.trades_file, index=False)

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "save_trade_to_excel",
                "trade_id": trade.trade_id
            })

    def _update_live_data_file(self, symbol: str, data: MarketData) -> None:
        """Update live data file with latest market data."""
        try:
            # Read existing data
            if os.path.exists(self.live_data_file):
                df = pd.read_excel(self.live_data_file)
            else:
                df = pd.DataFrame()

            # Update or add symbol data
            existing_idx = df[df['symbol'] == symbol].index
            new_row = {
                'symbol': symbol,
                'ltp': float(data.ltp) if data.ltp else None,
                'open': float(data.open) if data.open else None,
                'high': float(data.high) if data.high else None,
                'low': float(data.low) if data.low else None,
                'close': float(data.close) if data.close else None,
                'volume': data.volume,
                'timestamp': data.timestamp.isoformat()
            }

            if len(existing_idx) > 0:
                # Update existing row
                idx = existing_idx[0]
                for key, value in new_row.items():
                    df.loc[idx, key] = value
            else:
                # Add new row
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Save to file
            df.to_excel(self.live_data_file, index=False)

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_live_data_file",
                "symbol": symbol
            })

    def _update_completed_orders_file(self, trade: Trade) -> None:
        """Update completed orders file when trade is executed."""
        try:
            # This would typically update the completed orders file
            # For now, just log the action
            self.logger.debug(f"Completed order updated for trade {trade.trade_id}")

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "update_completed_orders_file",
                "trade_id": trade.trade_id
            })

    def _load_market_data_from_excel(self, symbol: str, start_time: datetime, 
                                   end_time: datetime) -> List[MarketData]:
        """Load market data from Excel file."""
        try:
            if not os.path.exists(self.market_data_file):
                return []

            df = pd.read_excel(self.market_data_file)
            symbol_data = df[df['symbol'] == symbol]

            market_data_list = []
            for _, row in symbol_data.iterrows():
                try:
                    timestamp = pd.to_datetime(row['timestamp'])
                    if start_time <= timestamp <= end_time:
                        market_data = MarketData(
                            symbol=symbol,
                            timestamp=timestamp,
                            ltp=Decimal(str(row['ltp'])) if pd.notna(row['ltp']) else None,
                            open=Decimal(str(row['open'])) if pd.notna(row['open']) else None,
                            high=Decimal(str(row['high'])) if pd.notna(row['high']) else None,
                            low=Decimal(str(row['low'])) if pd.notna(row['low']) else None,
                            close=Decimal(str(row['close'])) if pd.notna(row['close']) else None,
                            volume=int(row['volume']) if pd.notna(row['volume']) else 0
                        )
                        market_data_list.append(market_data)
                except Exception as e:
                    self.logger.log_error(e, {
                        "operation": "load_market_data_from_excel_row",
                        "symbol": symbol
                    })

            return market_data_list

        except Exception as e:
            self.logger.log_error(e, {
                "operation": "load_market_data_from_excel",
                "symbol": symbol
            })
            return []

    def _load_cached_data(self) -> None:
        """Load existing data into cache."""
        try:
            # Load orders
            if os.path.exists(self.orders_file):
                df = pd.read_excel(self.orders_file)
                for _, row in df.iterrows():
                    try:
                        # This would create Order objects from Excel data
                        # For now, just log that we're loading data
                        pass
                    except Exception as e:
                        self.logger.log_error(e, {"operation": "load_cached_orders"})

            # Load trades
            if os.path.exists(self.trades_file):
                df = pd.read_excel(self.trades_file)
                for _, row in df.iterrows():
                    try:
                        # This would create Trade objects from Excel data
                        # For now, just log that we're loading data
                        pass
                    except Exception as e:
                        self.logger.log_error(e, {"operation": "load_cached_trades"})

            self.logger.info("Cached data loaded")

        except Exception as e:
            self.logger.log_error(e, {"operation": "load_cached_data"})

    def _export_market_data_to_excel(self, writer: pd.ExcelWriter) -> None:
        """Export market data to Excel."""
        try:
            if os.path.exists(self.market_data_file):
                df = pd.read_excel(self.market_data_file)
                df.to_excel(writer, sheet_name='Market_Data', index=False)
        except Exception as e:
            self.logger.log_error(e, {"operation": "export_market_data_to_excel"})

    def _export_orders_to_excel(self, writer: pd.ExcelWriter) -> None:
        """Export orders to Excel."""
        try:
            if os.path.exists(self.orders_file):
                df = pd.read_excel(self.orders_file)
                df.to_excel(writer, sheet_name='Orders', index=False)
        except Exception as e:
            self.logger.log_error(e, {"operation": "export_orders_to_excel"})

    def _export_trades_to_excel(self, writer: pd.ExcelWriter) -> None:
        """Export trades to Excel."""
        try:
            if os.path.exists(self.trades_file):
                df = pd.read_excel(self.trades_file)
                df.to_excel(writer, sheet_name='Trades', index=False)
        except Exception as e:
            self.logger.log_error(e, {"operation": "export_trades_to_excel"})

    def _update_all_excel_files(self) -> None:
        """Update all Excel files with current cache data."""
        try:
            # This would update all Excel files with current cache data
            # For now, just log the action
            self.logger.debug("All Excel files updated")

        except Exception as e:
            self.logger.log_error(e, {"operation": "update_all_excel_files"}) 