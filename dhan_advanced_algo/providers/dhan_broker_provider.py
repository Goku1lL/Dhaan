"""
Dhan broker provider implementation.
Implements IBrokerProvider interface using Dhan API.
"""

import time
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime

from ..core.interfaces import IBrokerProvider
from ..core.entities import Order, OrderStatus, AccountBalance
from ..core.exceptions import BrokerException, OrderException, InsufficientMarginException
from ..core.logging_service import LoggingService


class DhanBrokerProvider(IBrokerProvider):
    """
    Dhan broker provider implementation.
    Handles all broker operations using Dhan API.
    """
    
    def __init__(self, tsl_client, config):
        """
        Initialize Dhan broker provider.
        
        Args:
            tsl_client: Dhan TSL client instance
            config: Configuration manager instance
        """
        self.tsl_client = tsl_client
        self.config = config
        self.logger = LoggingService()
        self.last_request_time = 0
        self.request_count = 0
        self.max_requests_per_minute = 60
        
        self.logger.info("Dhan Broker Provider initialized")
    
    def _rate_limit_check(self) -> None:
        """Check and enforce rate limiting."""
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        
        # Enforce minimum delay between requests
        min_delay = self.config.broker.rate_limit_delay
        if time_diff < min_delay:
            sleep_time = min_delay - time_diff
            time.sleep(sleep_time)
        
        # Check requests per minute limit
        if time_diff >= 60:  # Reset counter after 1 minute
            self.request_count = 0
            self.last_request_time = current_time
        elif self.request_count >= self.max_requests_per_minute:
            sleep_time = 60 - time_diff
            self.logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            self.request_count = 0
            self.last_request_time = time.time()
        
        self.request_count += 1
        self.last_request_time = time.time()
    
    def place_order(self, order) -> str:
        """
        Place a new order.
        
        Args:
            order: Order object to place
            
        Returns:
            Order ID of the placed order
            
        Raises:
            OrderException: If order placement fails
            InsufficientMarginException: If insufficient margin
        """
        try:
            self._rate_limit_check()
            
            self.logger.info(f"Placing order: {order.side.value} {order.quantity} {order.symbol}")
            
            # Convert order to Dhan API format
            order_params = self._convert_order_to_dhan_format(order)
            
            # Place order through TSL client
            response = self.tsl_client.place_order(**order_params)
            
            if not response or 'orderId' not in response:
                raise OrderException("Invalid response from broker API")
            
            order_id = response['orderId']
            
            self.logger.info(f"Order placed successfully: {order_id}")
            return order_id
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "insufficient" in error_msg or "margin" in error_msg:
                raise InsufficientMarginException(f"Insufficient margin for order: {str(e)}")
            else:
                raise OrderException(f"Failed to place order: {str(e)}")
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            self._rate_limit_check()
            
            self.logger.info(f"Cancelling order: {order_id}")
            
            # Cancel order through TSL client
            response = self.tsl_client.cancel_order(order_id)
            
            if response and response.get('status') == 'SUCCESS':
                self.logger.info(f"Order cancelled successfully: {order_id}")
                return True
            else:
                self.logger.warning(f"Order cancellation failed: {order_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str) -> OrderStatus:
        """
        Get the status of an order.
        
        Args:
            order_id: ID of the order
            
        Returns:
            OrderStatus enum value
        """
        try:
            self._rate_limit_check()
            
            # Get order status through TSL client
            response = self.tsl_client.get_order_status(order_id)
            
            if not response:
                return OrderStatus.UNKNOWN
            
            # Map Dhan status to our enum
            dhan_status = response.get('status', '').upper()
            return self._map_dhan_status_to_order_status(dhan_status)
            
        except Exception as e:
            self.logger.error(f"Failed to get order status for {order_id}: {str(e)}")
            return OrderStatus.UNKNOWN
    
    def get_account_balance(self) -> AccountBalance:
        """
        Get current account balance and margin information.
        
        Returns:
            AccountBalance object
        """
        try:
            self._rate_limit_check()
            
            # Get account details through TSL client
            response = self.tsl_client.get_account_details()
            
            if not response:
                raise BrokerException("Failed to get account details")
            
            # Extract balance information
            balance = AccountBalance(
                total_balance=Decimal(str(response.get('totalBalance', 0))),
                available_margin=Decimal(str(response.get('availableMargin', 0))),
                used_margin=Decimal(str(response.get('usedMargin', 0))),
                free_margin=Decimal(str(response.get('freeMargin', 0))),
                timestamp=datetime.now()
            )
            
            self.logger.debug(f"Account balance retrieved: {balance}")
            return balance
            
        except Exception as e:
            self.logger.error(f"Failed to get account balance: {str(e)}")
            raise BrokerException(f"Failed to get account balance: {str(e)}")
    
    def get_available_margin(self) -> Decimal:
        """
        Get available margin for trading.
        
        Returns:
            Available margin as Decimal
        """
        try:
            balance = self.get_account_balance()
            return balance.available_margin
            
        except Exception as e:
            self.logger.error(f"Failed to get available margin: {str(e)}")
            return Decimal('0')
    
    def get_positions(self) -> List[Dict]:
        """
        Get current open positions.
        
        Returns:
            List of position dictionaries
        """
        try:
            self._rate_limit_check()
            
            # Get positions through TSL client
            response = self.tsl_client.get_positions()
            
            if not response:
                return []
            
            # Convert to standard format
            positions = []
            for pos in response:
                position = {
                    'symbol': pos.get('symbol'),
                    'quantity': int(pos.get('quantity', 0)),
                    'average_price': Decimal(str(pos.get('averagePrice', 0))),
                    'side': pos.get('side', 'BUY'),
                    'timestamp': datetime.now()
                }
                positions.append(position)
            
            self.logger.debug(f"Retrieved {len(positions)} positions")
            return positions
            
        except Exception as e:
            self.logger.error(f"Failed to get positions: {str(e)}")
            return []
    
    def get_order_history(self, symbol: Optional[str] = None, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get order history.
        
        Args:
            symbol: Optional symbol filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of order history dictionaries
        """
        try:
            self._rate_limit_check()
            
            # Get order history through TSL client
            response = self.tsl_client.get_order_history(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if not response:
                return []
            
            # Convert to standard format
            orders = []
            for order in response:
                order_info = {
                    'order_id': order.get('orderId'),
                    'symbol': order.get('symbol'),
                    'side': order.get('side'),
                    'quantity': int(order.get('quantity', 0)),
                    'price': Decimal(str(order.get('price', 0))),
                    'status': order.get('status'),
                    'timestamp': datetime.fromisoformat(order.get('timestamp', datetime.now().isoformat()))
                }
                orders.append(order_info)
            
            self.logger.debug(f"Retrieved {len(orders)} orders from history")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get order history: {str(e)}")
            return []
    
    def get_trade_history(self, symbol: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get trade history.
        
        Args:
            symbol: Optional symbol filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of trade history dictionaries
        """
        try:
            self._rate_limit_check()
            
            # Get trade history through TSL client
            response = self.tsl_client.get_trade_history(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if not response:
                return []
            
            # Convert to standard format
            trades = []
            for trade in response:
                trade_info = {
                    'trade_id': trade.get('tradeId'),
                    'order_id': trade.get('orderId'),
                    'symbol': trade.get('symbol'),
                    'side': trade.get('side'),
                    'quantity': int(trade.get('quantity', 0)),
                    'price': Decimal(str(trade.get('price', 0))),
                    'timestamp': datetime.fromisoformat(trade.get('timestamp', datetime.now().isoformat()))
                }
                trades.append(trade_info)
            
            self.logger.debug(f"Retrieved {len(trades)} trades from history")
            return trades
            
        except Exception as e:
            self.logger.error(f"Failed to get trade history: {str(e)}")
            return []
    
    def modify_order(self, order_id: str, new_price: Optional[Decimal] = None,
                    new_quantity: Optional[int] = None) -> bool:
        """
        Modify an existing order.
        
        Args:
            order_id: ID of the order to modify
            new_price: New price (optional)
            new_quantity: New quantity (optional)
            
        Returns:
            True if modification successful, False otherwise
        """
        try:
            self._rate_limit_check()
            
            self.logger.info(f"Modifying order: {order_id}")
            
            # Build modification parameters
            mod_params = {'orderId': order_id}
            if new_price is not None:
                mod_params['price'] = float(new_price)
            if new_quantity is not None:
                mod_params['quantity'] = new_quantity
            
            # Modify order through TSL client
            response = self.tsl_client.modify_order(**mod_params)
            
            if response and response.get('status') == 'SUCCESS':
                self.logger.info(f"Order modified successfully: {order_id}")
                return True
            else:
                self.logger.warning(f"Order modification failed: {order_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to modify order {order_id}: {str(e)}")
            return False
    
    def get_market_status(self) -> Dict:
        """
        Get current market status.
        
        Returns:
            Dictionary containing market status information
        """
        try:
            self._rate_limit_check()
            
            # Get market status through TSL client
            response = self.tsl_client.get_market_status()
            
            if not response:
                return {'status': 'UNKNOWN'}
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get market status: {str(e)}")
            return {'status': 'UNKNOWN'}
    
    def _convert_order_to_dhan_format(self, order) -> Dict:
        """
        Convert internal order object to Dhan API format.
        
        Args:
            order: Internal order object
            
        Returns:
            Dictionary in Dhan API format
        """
        # Map order side
        side_map = {
            'BUY': 'BUY',
            'SELL': 'SELL'
        }
        
        # Map order type
        type_map = {
            'MARKET': 'MARKET',
            'LIMIT': 'LIMIT',
            'STOP': 'STOP',
            'STOP_LIMIT': 'STOP_LIMIT'
        }
        
        order_params = {
            'symbol': order.symbol,
            'side': side_map.get(order.side.value, 'BUY'),
            'orderType': type_map.get(order.order_type.value, 'MARKET'),
            'quantity': order.quantity,
            'productType': 'INTRADAY',  # Default to intraday
            'validity': 'DAY'  # Default to day validity
        }
        
        # Add price for limit orders
        if order.order_type.value in ['LIMIT', 'STOP_LIMIT'] and order.price > 0:
            order_params['price'] = float(order.price)
        
        # Add stop loss for stop orders
        if order.order_type.value in ['STOP', 'STOP_LIMIT']:
            # This would need to be passed from the strategy
            # For now, use a default calculation
            pass
        
        return order_params
    
    def _map_dhan_status_to_order_status(self, dhan_status: str) -> OrderStatus:
        """
        Map Dhan API status to internal OrderStatus enum.
        
        Args:
            dhan_status: Status string from Dhan API
            
        Returns:
            OrderStatus enum value
        """
        status_mapping = {
            'PENDING': OrderStatus.PENDING,
            'CONFIRMED': OrderStatus.CONFIRMED,
            'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED,
            'FILLED': OrderStatus.FILLED,
            'CANCELLED': OrderStatus.CANCELLED,
            'REJECTED': OrderStatus.REJECTED,
            'EXPIRED': OrderStatus.EXPIRED
        }
        
        return status_mapping.get(dhan_status, OrderStatus.UNKNOWN)
    
    def get_broker_info(self) -> Dict:
        """
        Get broker information and capabilities.
        
        Returns:
            Dictionary containing broker information
        """
        return {
            'broker_name': 'Dhan',
            'api_version': '1.0',
            'supported_order_types': ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT'],
            'supported_products': ['INTRADAY', 'DELIVERY', 'MARGIN'],
            'max_orders_per_minute': self.max_requests_per_minute,
            'rate_limit_delay': self.config.broker.rate_limit_delay
        } 