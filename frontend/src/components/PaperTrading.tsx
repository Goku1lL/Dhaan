import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Paper,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  Tabs,
  Tab,
  LinearProgress,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Assessment,
  Add,
  Close,
  Refresh,
  RestartAlt,
  ShowChart,
  BarChart,
  MonetizationOn,
  Cancel,
  CheckCircle,
  Warning
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface Position {
  symbol: string;
  quantity: number;
  side: string;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  entry_time: string;
}

interface Order {
  order_id: string;
  virtual_order_id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: number;
  price: number;
  executed_price?: number;
  executed_quantity?: number;
  status: string;
  submitted_at?: string;
  executed_at?: string;
}

interface TradingStats {
  initial_balance: number;
  current_balance: number;
  available_margin: number;
  used_margin: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_return_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_commission_paid: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  active_positions: number;
  pending_orders: number;
}

const PaperTrading: React.FC = () => {
  const [tradingMode, setTradingMode] = useState<string>('PAPER');
  const [isPaperMode, setIsPaperMode] = useState<boolean>(true);
  const [positions, setPositions] = useState<Position[]>([]);
  const [pendingOrders, setPendingOrders] = useState<Order[]>([]);
  const [orderHistory, setOrderHistory] = useState<Order[]>([]);
  const [tradingStats, setTradingStats] = useState<TradingStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  // Dialog states
  const [orderDialogOpen, setOrderDialogOpen] = useState<boolean>(false);
  const [resetDialogOpen, setResetDialogOpen] = useState<boolean>(false);
  const [closePositionDialog, setClosePositionDialog] = useState<{
    open: boolean;
    position: Position | null;
  }>({ open: false, position: null });

  // Order form state
  const [orderForm, setOrderForm] = useState({
    symbol: '',
    side: 'BUY',
    order_type: 'MARKET',
    quantity: '',
    price: ''
  });

  // Close position form state
  const [closeForm, setCloseForm] = useState({
    quantity: ''
  });

  useEffect(() => {
    loadTradingMode();
    loadPaperData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadPaperData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadTradingMode = async () => {
    try {
      const response = await tradingAPI.getTradingMode();
      if (response.data) {
        setTradingMode(response.data.trading_mode);
        setIsPaperMode(response.data.is_paper_mode);
      }
    } catch (error) {
      console.error('Error loading trading mode:', error);
    }
  };

  const loadPaperData = async () => {
    if (!isPaperMode) return;
    
    try {
      setLoading(true);
      setError(null);

      // Load all paper trading data with individual error handling
      const [portfolioRes, ordersRes, statsRes] = await Promise.allSettled([
        tradingAPI.getPaperPortfolio(),
        tradingAPI.getPaperOrders(),
        tradingAPI.getPaperStats()
      ]);

      // Handle portfolio response
      if (portfolioRes.status === 'fulfilled' && portfolioRes.value.data && portfolioRes.value.data.success) {
        setPositions(portfolioRes.value.data.positions || []);
      } else {
        console.error('Portfolio API failed:', portfolioRes.status === 'rejected' ? portfolioRes.reason : portfolioRes.value);
        setPositions([]);
      }

      // Handle orders response
      if (ordersRes.status === 'fulfilled' && ordersRes.value.data && ordersRes.value.data.success) {
        setPendingOrders(ordersRes.value.data.pending_orders || []);
        setOrderHistory(ordersRes.value.data.order_history || []);
      } else {
        console.error('Orders API failed:', ordersRes.status === 'rejected' ? ordersRes.reason : ordersRes.value);
        setPendingOrders([]);
        setOrderHistory([]);
      }

      // Handle stats response
      if (statsRes.status === 'fulfilled' && statsRes.value.data && statsRes.value.data.success) {
        setTradingStats(statsRes.value.data.stats);
      } else {
        console.error('Stats API failed:', statsRes.status === 'rejected' ? statsRes.reason : statsRes.value);
        setTradingStats(null);
      }

      // Only show error if all APIs failed
      const allFailed = portfolioRes.status === 'rejected' && ordersRes.status === 'rejected' && statsRes.status === 'rejected';
      if (allFailed) {
        setError('Failed to load paper trading data. Please check if the backend is running.');
      }

    } catch (error) {
      console.error('Error loading paper trading data:', error);
      setError('Failed to load paper trading data');
      // Set safe defaults
      setPositions([]);
      setPendingOrders([]);
      setOrderHistory([]);
      setTradingStats(null);
    } finally {
      setLoading(false);
    }
  };

  const toggleTradingMode = async () => {
    try {
      const newMode = isPaperMode ? 'LIVE' : 'PAPER';
      const response = await tradingAPI.setTradingMode(newMode);
      
      if (response.data && response.data.success) {
        setTradingMode(newMode);
        setIsPaperMode(newMode === 'PAPER');
        
        if (newMode === 'PAPER') {
          loadPaperData();
        }
      } else {
        setError(response.data?.error || 'Failed to change trading mode');
      }
    } catch (error) {
      console.error('Error changing trading mode:', error);
      setError('Failed to change trading mode');
    }
  };

  const placePaperOrder = async () => {
    try {
      const orderData = {
        symbol: orderForm.symbol.toUpperCase(),
        side: orderForm.side,
        order_type: orderForm.order_type,
        quantity: parseInt(orderForm.quantity),
        price: parseFloat(orderForm.price)
      };

      const response = await tradingAPI.placePaperOrder(orderData);
      
      if (response.data && response.data.success) {
        setOrderDialogOpen(false);
        setOrderForm({ symbol: '', side: 'BUY', order_type: 'MARKET', quantity: '', price: '' });
        loadPaperData();
      } else {
        setError(response.data?.error || 'Failed to place order');
      }
    } catch (error) {
      console.error('Error placing order:', error);
      setError('Failed to place order');
    }
  };

  const cancelOrder = async (orderId: string) => {
    try {
      const response = await tradingAPI.cancelPaperOrder(orderId);
      
      if (response.data && response.data.success) {
        loadPaperData();
      } else {
        setError(response.data?.error || 'Failed to cancel order');
      }
    } catch (error) {
      console.error('Error cancelling order:', error);
      setError('Failed to cancel order');
    }
  };

  const closePosition = async () => {
    if (!closePositionDialog.position) return;

    try {
      const quantity = closeForm.quantity ? parseInt(closeForm.quantity) : undefined;
      const response = await tradingAPI.closePaperPosition(closePositionDialog.position.symbol, quantity);
      
      if (response.data && response.data.success) {
        setClosePositionDialog({ open: false, position: null });
        setCloseForm({ quantity: '' });
        loadPaperData();
      } else {
        setError(response.data?.error || 'Failed to close position');
      }
    } catch (error) {
      console.error('Error closing position:', error);
      setError('Failed to close position');
    }
  };

  const resetPortfolio = async () => {
    try {
      const response = await tradingAPI.resetPaperPortfolio();
      
      if (response.data && response.data.success) {
        setResetDialogOpen(false);
        loadPaperData();
      } else {
        setError(response.data?.error || 'Failed to reset portfolio');
      }
    } catch (error) {
      console.error('Error resetting portfolio:', error);
      setError('Failed to reset portfolio');
    }
  };

  const formatCurrency = (amount: number) => {
    if (amount == null || isNaN(amount)) {
      return '₹0';
    }
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    if (value == null || isNaN(value)) {
      return '0.00%';
    }
    return `${value.toFixed(2)}%`;
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'executed': return 'success';
      case 'cancelled': return 'error';
      case 'submitted': case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getSideColor = (side: string) => {
    return side === 'BUY' ? 'success' : 'error';
  };

  const getPnLColor = (pnl: number) => {
    if (pnl == null || isNaN(pnl)) {
      return 'text.primary';
    }
    if (pnl > 0) return 'success.main';
    if (pnl < 0) return 'error.main';
    return 'text.primary';
  };

  if (!isPaperMode) {
    return (
      <Box sx={{ p: 3 }}>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <AccountBalance sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Paper Trading Not Active
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 3 }}>
              Switch to Paper Trading mode to start virtual trading
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={isPaperMode}
                  onChange={toggleTradingMode}
                  color="primary"
                />
              }
              label={`Current Mode: ${tradingMode}`}
            />
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4">
            Paper Trading
          </Typography>
          <Chip 
            icon={<ShowChart />}
            label="PAPER MODE"
            color="primary"
            variant="outlined"
          />
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <FormControlLabel
            control={
              <Switch
                checked={isPaperMode}
                onChange={toggleTradingMode}
                color="primary"
              />
            }
            label={tradingMode}
          />
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setOrderDialogOpen(true)}
            color="primary"
          >
            Place Order
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadPaperData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<RestartAlt />}
            onClick={() => setResetDialogOpen(true)}
            color="error"
          >
            Reset Portfolio
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Portfolio Summary */}
      {tradingStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountBalance color="primary" />
                  <Typography color="textSecondary" gutterBottom>
                    Portfolio Value
                  </Typography>
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {formatCurrency(tradingStats.current_balance || 0)}
                </Typography>
                <Typography variant="body2" color={getPnLColor(tradingStats.total_return_pct || 0)}>
                  {(tradingStats.total_return_pct || 0) >= 0 ? '+' : ''}{formatPercentage(tradingStats.total_return_pct || 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <MonetizationOn color="success" />
                  <Typography color="textSecondary" gutterBottom>
                    Available Cash
                  </Typography>
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {formatCurrency(tradingStats.available_margin || 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Used: {formatCurrency(tradingStats.used_margin || 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Assessment color="info" />
                  <Typography color="textSecondary" gutterBottom>
                    Total P&L
                  </Typography>
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600, color: getPnLColor(tradingStats.realized_pnl || 0) }}>
                  {(tradingStats.realized_pnl || 0) >= 0 ? '+' : ''}{formatCurrency(tradingStats.realized_pnl || 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Unrealized: {formatCurrency(tradingStats.unrealized_pnl || 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BarChart color="warning" />
                  <Typography color="textSecondary" gutterBottom>
                    Win Rate
                  </Typography>
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {formatPercentage(tradingStats.win_rate || 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {tradingStats.winning_trades || 0}/{tradingStats.total_trades || 0} trades
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label={`Positions (${positions.length})`} />
            <Tab label={`Pending Orders (${pendingOrders.length})`} />
            <Tab label={`Order History (${orderHistory.length})`} />
            <Tab label="Statistics" />
          </Tabs>
        </Box>

        {/* Positions Tab */}
        {tabValue === 0 && (
          <CardContent>
            {positions.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography color="text.secondary">
                  No open positions
                </Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell>Side</TableCell>
                      <TableCell align="right">Entry Price</TableCell>
                      <TableCell align="right">Current Price</TableCell>
                      <TableCell align="right">P&L</TableCell>
                      <TableCell>Entry Time</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {positions.map((position, index) => (
                      <TableRow key={index}>
                        <TableCell sx={{ fontWeight: 600 }}>{position.symbol}</TableCell>
                        <TableCell align="right">{position.quantity}</TableCell>
                        <TableCell>
                          <Chip 
                            label={position.side} 
                            color={getSideColor(position.side)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">{formatCurrency(position.entry_price)}</TableCell>
                        <TableCell align="right">{formatCurrency(position.current_price)}</TableCell>
                        <TableCell align="right" sx={{ color: getPnLColor(position.unrealized_pnl) }}>
                          {position.unrealized_pnl >= 0 ? '+' : ''}{formatCurrency(position.unrealized_pnl)}
                        </TableCell>
                        <TableCell>{new Date(position.entry_time).toLocaleString()}</TableCell>
                        <TableCell align="center">
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            onClick={() => setClosePositionDialog({ open: true, position })}
                          >
                            Close
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        )}

        {/* Pending Orders Tab */}
        {tabValue === 1 && (
          <CardContent>
            {pendingOrders.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography color="text.secondary">
                  No pending orders
                </Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Order ID</TableCell>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Side</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Submitted</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pendingOrders.map((order) => (
                      <TableRow key={order.virtual_order_id}>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                          {order.virtual_order_id}
                        </TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>{order.symbol}</TableCell>
                        <TableCell>
                          <Chip 
                            label={order.side} 
                            color={getSideColor(order.side)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{order.order_type}</TableCell>
                        <TableCell align="right">{order.quantity}</TableCell>
                        <TableCell align="right">{formatCurrency(order.price)}</TableCell>
                        <TableCell>
                          <Chip 
                            label={order.status} 
                            color={getStatusColor(order.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {order.submitted_at ? new Date(order.submitted_at).toLocaleString() : '-'}
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => cancelOrder(order.virtual_order_id)}
                          >
                            <Cancel />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        )}

        {/* Order History Tab */}
        {tabValue === 2 && (
          <CardContent>
            {orderHistory.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography color="text.secondary">
                  No order history
                </Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Order ID</TableCell>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Side</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell align="right">Order Price</TableCell>
                      <TableCell align="right">Executed Price</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Executed</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {orderHistory.map((order) => (
                      <TableRow key={order.virtual_order_id}>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                          {order.virtual_order_id}
                        </TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>{order.symbol}</TableCell>
                        <TableCell>
                          <Chip 
                            label={order.side} 
                            color={getSideColor(order.side)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{order.order_type}</TableCell>
                        <TableCell align="right">{order.executed_quantity || order.quantity}</TableCell>
                        <TableCell align="right">{formatCurrency(order.price)}</TableCell>
                        <TableCell align="right">
                          {order.executed_price ? formatCurrency(order.executed_price) : '-'}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={order.status} 
                            color={getStatusColor(order.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {order.executed_at ? new Date(order.executed_at).toLocaleString() : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        )}

        {/* Statistics Tab */}
        {tabValue === 3 && tradingStats && (
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Portfolio Performance</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Initial Balance:</Typography>
                    <Typography sx={{ fontWeight: 600 }}>{formatCurrency(tradingStats.initial_balance || 0)}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Current Balance:</Typography>
                    <Typography sx={{ fontWeight: 600 }}>{formatCurrency(tradingStats.current_balance || 0)}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Total Return:</Typography>
                    <Typography sx={{ fontWeight: 600, color: getPnLColor(tradingStats.total_return_pct || 0) }}>
                      {formatPercentage(tradingStats.total_return_pct || 0)}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Max Drawdown:</Typography>
                    <Typography sx={{ fontWeight: 600, color: 'error.main' }}>
                      {formatPercentage(tradingStats.max_drawdown_pct || 0)}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Trading Statistics</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Total Trades:</Typography>
                    <Typography sx={{ fontWeight: 600 }}>{tradingStats.total_trades || 0}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Winning Trades:</Typography>
                    <Typography sx={{ fontWeight: 600, color: 'success.main' }}>{tradingStats.winning_trades || 0}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Losing Trades:</Typography>
                    <Typography sx={{ fontWeight: 600, color: 'error.main' }}>{tradingStats.losing_trades || 0}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Win Rate:</Typography>
                    <Typography sx={{ fontWeight: 600 }}>{formatPercentage(tradingStats.win_rate || 0)}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Total Commission:</Typography>
                    <Typography sx={{ fontWeight: 600 }}>{formatCurrency(tradingStats.total_commission_paid || 0)}</Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        )}
      </Card>

      {/* Place Order Dialog */}
      <Dialog open={orderDialogOpen} onClose={() => setOrderDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Place Paper Order</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Symbol"
              value={orderForm.symbol}
              onChange={(e) => setOrderForm({ ...orderForm, symbol: e.target.value.toUpperCase() })}
              placeholder="e.g., RELIANCE"
              fullWidth
            />
            
            <FormControl fullWidth>
              <InputLabel>Side</InputLabel>
              <Select
                value={orderForm.side}
                onChange={(e) => setOrderForm({ ...orderForm, side: e.target.value })}
                label="Side"
              >
                <MenuItem value="BUY">Buy</MenuItem>
                <MenuItem value="SELL">Sell</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth>
              <InputLabel>Order Type</InputLabel>
              <Select
                value={orderForm.order_type}
                onChange={(e) => setOrderForm({ ...orderForm, order_type: e.target.value })}
                label="Order Type"
              >
                <MenuItem value="MARKET">Market</MenuItem>
                <MenuItem value="LIMIT">Limit</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="Quantity"
              type="number"
              value={orderForm.quantity}
              onChange={(e) => setOrderForm({ ...orderForm, quantity: e.target.value })}
              fullWidth
            />
            
            <TextField
              label="Price"
              type="number"
              value={orderForm.price}
              onChange={(e) => setOrderForm({ ...orderForm, price: e.target.value })}
              fullWidth
              inputProps={{ step: 0.01 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOrderDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={placePaperOrder} 
            variant="contained" 
            disabled={!orderForm.symbol || !orderForm.quantity || !orderForm.price}
          >
            Place Order
          </Button>
        </DialogActions>
      </Dialog>

      {/* Close Position Dialog */}
      <Dialog 
        open={closePositionDialog.open} 
        onClose={() => setClosePositionDialog({ open: false, position: null })} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Close Position</DialogTitle>
        <DialogContent>
          {closePositionDialog.position && (
            <Box sx={{ mt: 1 }}>
              <Typography gutterBottom>
                <strong>Symbol:</strong> {closePositionDialog.position.symbol}
              </Typography>
              <Typography gutterBottom>
                <strong>Current Position:</strong> {closePositionDialog.position.quantity} shares
              </Typography>
              <Typography gutterBottom sx={{ mb: 2 }}>
                <strong>Entry Price:</strong> {formatCurrency(closePositionDialog.position.entry_price)}
              </Typography>
              
              <TextField
                label="Quantity to Close"
                type="number"
                value={closeForm.quantity}
                onChange={(e) => setCloseForm({ ...closeForm, quantity: e.target.value })}
                placeholder={`Max: ${closePositionDialog.position.quantity} (leave empty for full position)`}
                fullWidth
                inputProps={{ 
                  max: closePositionDialog.position.quantity,
                  min: 1
                }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClosePositionDialog({ open: false, position: null })}>
            Cancel
          </Button>
          <Button onClick={closePosition} variant="contained" color="error">
            Close Position
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset Portfolio Dialog */}
      <Dialog open={resetDialogOpen} onClose={() => setResetDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Warning color="error" />
          Reset Paper Portfolio
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Are you sure you want to reset your paper trading portfolio?
          </Typography>
          <Typography color="text.secondary">
            This will:
          </Typography>
          <Typography component="ul" sx={{ pl: 2, mt: 1 }}>
            <li>Close all open positions</li>
            <li>Cancel all pending orders</li>
            <li>Reset balance to initial amount</li>
            <li>Clear all trading history</li>
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone!
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>Cancel</Button>
          <Button onClick={resetPortfolio} variant="contained" color="error">
            Reset Portfolio
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PaperTrading; 