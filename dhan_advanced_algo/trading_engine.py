"""Main trading engine for the Algo Trading System."""

import datetime as dt
import time
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from copy import deepcopy

from .config import *
from .models import OrderTemplate, TradingState
from .excel_manager import ExcelManager
from .telegram_manager import TelegramManager
from .indicators import indicators

# Configure logging
logger = logging.getLogger(__name__)

try:
    import dhanhq
    DHAN_AVAILABLE = True
except ImportError:
    DHAN_AVAILABLE = False
    logger.warning("dhanhq not available. Trading features will be disabled.")

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False
    logger.warning("winsound not available. Audio alerts will be disabled.")


class TradingEngine:
    """Main trading engine that orchestrates all trading operations."""
    
    def __init__(self):
        """Initialize the trading engine."""
        self.state = TradingState()
        self.excel_manager = ExcelManager(EXCEL_FILES["live_trade"], EXCEL_FILES["completed_orders"])
        self.telegram_manager = TelegramManager(BOT_TOKEN, CHAT_ID)
        self.dhan_client = None
        
        if DHAN_AVAILABLE:
            self._initialize_dhan_client()
        else:
            logger.error("Dhan API not available. Trading features disabled.")
    
    def _initialize_dhan_client(self):
        """Initialize Dhan API client."""
        try:
            self.dhan_client = dhanhq.dhanhq(client_id=CLIENT_ID, access_token=ACCESS_TOKEN)
            logger.info("Dhan API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Dhan API client: {e}")
            self.dhan_client = None
    
    def _check_market_hours(self) -> bool:
        """
        Check if market is open.
        
        Returns:
            True if market is open, False otherwise
        """
        current_time = dt.datetime.now().time()
        market_open = dt.datetime.strptime(MARKET_OPEN_TIME, "%H:%M:%S").time()
        market_close = dt.datetime.strptime(MARKET_CLOSE_TIME, "%H:%M:%S").time()
        
        return market_open <= current_time <= market_close
    
    def _wait_for_market_open(self):
        """Wait for market to open."""
        while not self._check_market_hours():
            logger.info("Waiting for market to start...")
            time.sleep(5)
    
    def _perform_market_close_operations(self):
        """Perform market close operations."""
        if not self.dhan_client:
            logger.warning("Cannot perform market close operations: Dhan client not available")
            return
        
        try:
            # Cancel pending orders - get order list and cancel each
            try:
                orders = self.dhan_client.get_order_list()
                if orders and isinstance(orders, list):
                    for order in orders:
                        if isinstance(order, dict) and order.get('orderStatus') in ['PENDING', 'OPEN']:
                            order_id = order.get('orderId')
                            if order_id:
                                self.dhan_client.cancel_order(order_id)
                    logger.info("Cancelled pending orders")
                else:
                    logger.info("No pending orders to cancel")
            except Exception as e:
                logger.warning(f"Failed to cancel pending orders: {e}")
            
            # Square off positions - get positions and square off each
            try:
                positions = self.dhan_client.get_positions()
                if positions and isinstance(positions, list):
                    for position in positions:
                        if isinstance(position, dict) and position.get('quantity', 0) != 0:
                            # Place opposite order to square off
                            side = 'SELL' if position.get('side') == 'BUY' else 'BUY'
                            symbol = position.get('symbol')
                            quantity = abs(position.get('quantity', 0))
                            if symbol and quantity > 0:
                                self.dhan_client.place_order(
                                    security_id=symbol,
                                    exchange_segment="NSE",
                                    transaction_type=side,
                                    quantity=quantity,
                                    order_type="MARKET",
                                    product_type="INTRA",
                                    price=0
                                )
                    logger.info("Squared off all positions")
                else:
                    logger.info("No positions to square off")
            except Exception as e:
                logger.warning(f"Failed to square off positions: {e}")
            
        except Exception as e:
            logger.error(f"Market close operations failed: {e}")
    
    def _perform_pre_market_scan(self, full_watchlist: List[str]) -> List[str]:
        """
        Perform pre-market scanning to filter watchlist.
        
        Args:
            full_watchlist: Full watchlist from Excel
            
        Returns:
            Filtered watchlist based on technical criteria
        """
        if not self.dhan_client:
            logger.warning("Cannot perform pre-market scan: Dhan client not available")
            return full_watchlist
        
        selected = []
        for symbol in full_watchlist:
            try:
                # Get daily historical data
                hist_data = self.dhan_client.historical_daily_data(symbol)
                if not hist_data:
                    continue
                
                df = pd.DataFrame(hist_data)
                if df.empty:
                    continue
                
                # Apply SMA filter
                df["SMA"] = indicators.compute_sma(df["close"], SMA_PERIOD)
                if df["close"].iloc[-1] > df["SMA"].iloc[-1]:
                    selected.append(symbol)
                    
            except Exception as e:
                logger.warning(f"Pre-market scan failed for {symbol}: {e}")
                continue
        
        logger.info(f"Pre-market scan completed. Selected {len(selected)} symbols from {len(full_watchlist)}")
        return selected
    
    def _fetch_ltp_data(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch LTP data for multiple symbols in bulk.
        
        Args:
            symbols: List of symbols to fetch LTP for
            
        Returns:
            Dictionary of symbol: LTP pairs
        """
        if not self.dhan_client or not symbols:
            return {}
        
        try:
            ltp_data = self.dhan_client.quote_data(symbols)
            logger.debug(f"Fetched LTP data for {len(ltp_data)} symbols")
            return ltp_data
        except Exception as e:
            logger.error(f"Failed to fetch LTP data: {e}")
            return {}
    
    def _fetch_historical_data(self, symbol: str, timeframe: str = "5m") -> pd.DataFrame:
        """
        Fetch historical data for a symbol.
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe for data
            
        Returns:
            DataFrame with historical data
        """
        if not self.dhan_client:
            return pd.DataFrame()
        
        try:
            hist_data = self.dhan_client.intraday_minute_data(symbol)
            if hist_data:
                df = pd.DataFrame(hist_data)
                return indicators.add_all_indicators(df)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _check_entry_conditions(self, indicator_values: Dict, order: OrderTemplate) -> Tuple[bool, str]:
        """
        Check if entry conditions are met.
        
        Args:
            indicator_values: Technical indicator values
            order: Order template to check
            
        Returns:
            Tuple of (conditions_met, entry_side)
        """
        rsi = indicator_values.get("RSI")
        st_dir = indicator_values.get("SuperTrend_Dir")
        
        # Check if already traded
        if order.Traded == "Yes":
            return False, ""
        
        # Buy conditions
        if (rsi is not None and st_dir == 1 and rsi > RSI_OVERBOUGHT):
            return True, "BUY"
        
        # Sell conditions
        if (rsi is not None and st_dir == -1 and rsi < RSI_OVERSOLD):
            return True, "SELL"
        
        return False, ""
    
    def _check_margin(self, symbol: str, ltp: float, quantity: int) -> bool:
        """
        Check if sufficient margin is available.
        
        Args:
            symbol: Trading symbol
            ltp: Last traded price
            quantity: Quantity to trade
            
        Returns:
            True if margin is sufficient
        """
        if not self.dhan_client:
            return False
        
        try:
            balance = self.dhan_client.get_fund_limits()
            available_margin = balance.get("available", 0)
            margin_required = ltp * quantity / MARGIN_LEVERAGE
            
            if available_margin < margin_required:
                self.telegram_manager.send_margin_alert(symbol, available_margin, margin_required)
                logger.warning(f"Insufficient margin for {symbol}. Available: {available_margin}, Required: {margin_required}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Margin check failed for {symbol}: {e}")
            return False
    
    def _place_entry_order(self, symbol: str, side: str, quantity: int) -> Tuple[Optional[str], float]:
        """
        Place entry order.
        
        Args:
            symbol: Trading symbol
            side: Buy/Sell side
            quantity: Quantity to trade
            
        Returns:
            Tuple of (order_id, executed_price)
        """
        if not self.dhan_client:
            return None, 0.0
        
        try:
            order_resp = self.dhan_client.place_order(
                security_id=symbol,
                exchange_segment="NSE",
                transaction_type=side,
                quantity=quantity,
                order_type="MARKET",
                product_type="INTRA",
                price=0
            )
            
            order_id = order_resp.get("orderId") if order_resp else None
            executed_price = order_resp.get("price", 0.0)
            
            logger.info(f"Entry order placed for {symbol}: {side} {quantity} @ {executed_price}")
            return order_id, executed_price
            
        except Exception as e:
            logger.error(f"Entry order failed for {symbol}: {e}")
            return None, 0.0
    
    def _place_stop_loss_order(self, symbol: str, side: str, quantity: int, 
                               stop_price: float) -> Optional[str]:
        """
        Place stop loss order.
        
        Args:
            symbol: Trading symbol
            side: Original trade side (BUY/SELL)
            quantity: Quantity to protect
            stop_price: Stop loss price
            
        Returns:
            Stop loss order ID
        """
        if not self.dhan_client:
            return None
        
        try:
            # Reverse side for stop loss
            stop_side = "SELL" if side == "BUY" else "BUY"
            
            stop_resp = self.dhan_client.place_order(
                security_id=symbol,
                exchange_segment="NSE",
                transaction_type=stop_side,
                quantity=quantity,
                order_type="SL",
                product_type="INTRA",
                price=stop_price,
                trigger_price=stop_price
            )
            
            stop_order_id = stop_resp.get("orderId") if stop_resp else None
            logger.info(f"Stop loss order placed for {symbol} @ {stop_price}")
            return stop_order_id
            
        except Exception as e:
            logger.error(f"Stop loss order failed for {symbol}: {e}")
            return None
    
    def _check_exit_conditions(self, symbol: str, order: OrderTemplate, ltp: float) -> bool:
        """
        Check if exit conditions are met.
        
        Args:
            symbol: Trading symbol
            order: Order template
            ltp: Last traded price
            
        Returns:
            True if exit conditions met
        """
        if order.Traded != "Yes":
            return False
        
        # Check stop loss hit
        sl_hit = False
        if order.StopLoss_Order_ID and self.dhan_client:
            try:
                # Get order details to check status
                order_details = self.dhan_client.get_order_by_id(order.StopLoss_Order_ID)
                sl_hit = order_details.get("orderStatus") == "EXECUTED" if order_details else False
            except Exception as e:
                logger.error(f"Stop loss status check failed for {symbol}: {e}")
        
        # Check target hit
        target_hit = False
        if order.Target and ltp:
            if order.Buy_Sell == "Buy" and ltp >= order.Target:
                target_hit = True
            elif order.Buy_Sell == "Sell" and ltp <= order.Target:
                target_hit = True
        
        return sl_hit or target_hit
    
    def _execute_exit(self, symbol: str, order: OrderTemplate, ltp: float, 
                      sl_hit: bool) -> bool:
        """
        Execute exit from position.
        
        Args:
            symbol: Trading symbol
            order: Order template
            ltp: Last traded price
            sl_hit: Whether stop loss was hit
            
        Returns:
            True if exit successful
        """
        if not self.dhan_client:
            return False
        
        try:
            # Cancel stop loss order first
            if order.StopLoss_Order_ID:
                self.dhan_client.cancel_order(order.StopLoss_Order_ID)
                time.sleep(ORDER_STATUS_DELAY)
            
            # Place exit order
            exit_side = "SELL" if order.Buy_Sell == "Buy" else "BUY"
            exit_resp = self.dhan_client.place_order(
                security_id=symbol,
                exchange_segment="NSE",
                transaction_type=exit_side,
                quantity=order.Quantity,
                order_type="MARKET",
                product_type="INTRA",
                price=0
            )
            
            # Get exit price
            exit_price = ltp
            if exit_resp and exit_resp.get("orderId"):
                exit_price = exit_resp.get("price", ltp)
            
            # Update order details
            order.Exit_Time = dt.datetime.now().strftime("%H:%M:%S")
            order.Exit_Price = exit_price
            
            # Calculate PNL
            if order.Buy_Sell == "Buy":
                pnl = (exit_price - order.Entry_Price) * order.Quantity
            else:
                pnl = (order.Entry_Price - exit_price) * order.Quantity
            
            order.PNL = pnl
            order.Remark = "SL Hit" if sl_hit else "Target Hit"
            
            # Send alerts
            self.telegram_manager.send_exit_alert(symbol, exit_price, pnl, order.Remark)
            
            # Audio alert
            if WINSOUND_AVAILABLE:
                frequency = 1000 if sl_hit else 1500
                duration = 500 if sl_hit else 300
                winsound.Beep(frequency, duration)
            
            logger.info(f"Exit executed for {symbol}: {order.Remark}, PNL: {pnl}")
            return True
            
        except Exception as e:
            logger.error(f"Exit execution failed for {symbol}: {e}")
            return False
    
    def _handle_reentry(self, symbol: str):
        """Handle re-entry logic for a symbol."""
        re_entry_flag = self.excel_manager.read_reentry_flag()
        
        if re_entry_flag == "Yes":
            # Reset order for re-entry
            fresh_order = OrderTemplate()
            fresh_order.Name = symbol
            self.state.order_book[symbol] = fresh_order
            logger.info(f"Reset {symbol} for re-entry")
        else:
            # Mark as completed
            self.state.mark_order_completed(symbol)
            logger.info(f"Marked {symbol} as completed")
    
    def run(self):
        """Main trading loop."""
        logger.info("Starting trading engine...")
        
        # Clear Excel sheets
        self.excel_manager.clear_sheets()
        
        while True:
            try:
                current_time = dt.datetime.now()
                self.state.current_time = current_time
                
                # Check market hours
                if not self._check_market_hours():
                    if current_time.time() < dt.datetime.strptime(MARKET_OPEN_TIME, "%H:%M:%S").time():
                        self._wait_for_market_open()
                    else:
                        # Market close operations
                        self._perform_market_close_operations()
                        self.telegram_manager.send_market_status_alert("Close", "See you tomorrow!")
                        logger.info("Market Over, Closing all Orders. See you tomorrow!")
                        break
                
                logger.debug(f"Trading loop iteration at {current_time.time()}")
                
                # Read watchlist and perform pre-market scan
                full_watchlist = self.excel_manager.read_watchlist()
                if not self.state.pre_market_done:
                    self.state.selected_watchlist = self._perform_pre_market_scan(full_watchlist)
                    self.state.pre_market_done = True
                elif not self.state.selected_watchlist:
                    self.state.selected_watchlist = full_watchlist
                
                # Initialize order book for new symbols
                for symbol in self.state.selected_watchlist:
                    if symbol not in self.state.order_book:
                        order = OrderTemplate()
                        order.Name = symbol
                        self.state.add_order(symbol, order)
                
                # Fetch LTP data for all symbols
                ltp_data = self._fetch_ltp_data(self.state.selected_watchlist)
                self.state.update_ltp_data(ltp_data)
                
                # Process each symbol
                for symbol in self.state.selected_watchlist:
                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        self.telegram_manager.send_error_alert(str(e), f"Processing {symbol}")
                
                # Update Excel sheets
                self.excel_manager.update_live_trading_sheet(self.state.order_book)
                self.excel_manager.update_completed_orders_sheet(self.state.completed_orders)
                
                # Rate limiting
                time.sleep(LOOP_SLEEP_SECONDS)
                
            except KeyboardInterrupt:
                logger.info("Trading engine stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in trading loop: {e}")
                self.telegram_manager.send_error_alert(str(e), "Main trading loop")
                time.sleep(LOOP_SLEEP_SECONDS)
        
        # Cleanup
        self.excel_manager.close_workbooks()
        logger.info("Trading engine stopped")
    
    def _process_symbol(self, symbol: str):
        """Process a single symbol for trading decisions."""
        order = self.state.get_order(symbol)
        if not order:
            return
        
        ltp = self.state.get_ltp(symbol)
        if not ltp:
            return
        
        # Check exit conditions first
        if order.Traded == "Yes":
            sl_hit = False
            if order.StopLoss_Order_ID and self.dhan_client:
                try:
                    order_details = self.dhan_client.get_order_by_id(order.StopLoss_Order_ID)
                    status = order_details.get("orderStatus") if order_details else "UNKNOWN"
                    sl_hit = status == "EXECUTED"
                except Exception as e:
                    logger.error(f"Stop loss status check failed for {symbol}: {e}")
            
            target_hit = False
            if order.Target:
                if order.Buy_Sell == "Buy" and ltp >= order.Target:
                    target_hit = True
                elif order.Buy_Sell == "Sell" and ltp <= order.Target:
                    target_hit = True
            
            if sl_hit or target_hit:
                if self._execute_exit(symbol, order, ltp, sl_hit):
                    self._handle_reentry(symbol)
                return
        
        # Check entry conditions
        hist_df = self._fetch_historical_data(symbol)
        if hist_df.empty or len(hist_df) < 2:
            return
        
        indicator_values = indicators.get_indicator_values(hist_df)
        entry_conditions_met, entry_side = self._check_entry_conditions(indicator_values, order)
        
        if not entry_conditions_met:
            return
        
        # Check margin
        quantity = self.excel_manager.read_quantity(symbol, self.state.selected_watchlist)
        if not self._check_margin(symbol, ltp, quantity):
            return
        
        # Place entry order
        entry_order_id, executed_price = self._place_entry_order(symbol, entry_side, quantity)
        if not entry_order_id:
            return
        
        # Calculate stop loss and target
        if entry_side == "BUY":
            stop_loss_price = executed_price * (1 - STOP_LOSS_PERCENTAGE)
            target_price = executed_price * (1 + TARGET_PERCENTAGE)
        else:
            stop_loss_price = executed_price * (1 + STOP_LOSS_PERCENTAGE)
            target_price = executed_price * (1 - TARGET_PERCENTAGE)
        
        # Place stop loss order
        stop_order_id = self._place_stop_loss_order(symbol, entry_side, quantity, stop_loss_price)
        
        # Update order details
        order.update_entry_details(
            Date=dt.date.today().isoformat(),
            Entry_Time=dt.datetime.now().strftime("%H:%M:%S"),
            Entry_Price=executed_price,
            Buy_Sell="Buy" if entry_side == "BUY" else "Sell",
            Quantity=quantity,
            StopLoss=stop_loss_price,
            Target=target_price,
            Traded="Yes",
            Entry_Order_ID=entry_order_id,
            StopLoss_Order_ID=stop_order_id
        )
        
        # Send entry alert
        self.telegram_manager.send_entry_alert(
            symbol, executed_price, quantity, stop_loss_price, 
            target_price, entry_order_id, entry_side
        )
        
        # Audio alert
        if WINSOUND_AVAILABLE:
            winsound.Beep(1500, 300)
        
        logger.info(f"Entry completed for {symbol}: {entry_side} {quantity} @ {executed_price}") 