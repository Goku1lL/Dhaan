import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, Snackbar, IconButton, Tooltip, CircularProgress
} from '@mui/material';
import {
  TrendingUp, TrendingDown, Refresh, Search, FilterList,
  PlayArrow, Stop, Warning, CheckCircle, Error, Schedule
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  orderType: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
  status: 'PENDING' | 'PARTIALLY_FILLED' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  price: number;
  filledQuantity: number;
  remainingQuantity: number;
  timestamp: string;
  strategy?: string;
}

const Orders: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([]);
  const [cancelDialog, setCancelDialog] = useState<{ open: boolean; order: Order | null }>({
    open: false,
    order: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Fetch real orders data from API
  useEffect(() => {
    fetchOrdersData();
  }, []);

  const fetchOrdersData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await tradingAPI.getOrders();
      const apiOrders = response.data;
      
      // Transform API data to match our interface
      const transformedOrders: Order[] = apiOrders.map((order: any) => ({
        id: order.id || order.order_id || '',
        symbol: order.symbol || order.instrument || 'UNKNOWN',
        side: order.side || order.order_side || 'BUY',
        quantity: order.quantity || order.qty || 0,
        orderType: order.order_type || order.type || 'MARKET',
        status: order.status || 'PENDING',
        price: order.price || order.limit_price || 0,
        filledQuantity: order.filled_quantity || order.executed_qty || 0,
        remainingQuantity: order.remaining_quantity || (order.quantity - (order.filled_quantity || 0)) || 0,
        timestamp: order.created_at || order.timestamp || new Date().toISOString(),
        strategy: order.strategy || undefined
      }));
      
      setOrders(transformedOrders);
      setFilteredOrders(transformedOrders);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
      setError('Failed to load orders data. Please try again.');
      // Fallback to empty array
      setOrders([]);
      setFilteredOrders([]);
    } finally {
      setLoading(false);
    }
  };

  // Filter orders based on search term and status
  useEffect(() => {
    let filtered = orders;
    
    if (searchTerm) {
      filtered = filtered.filter(order => 
        order.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    if (statusFilter !== 'ALL') {
      filtered = filtered.filter(order => order.status === statusFilter);
    }
    
    setFilteredOrders(filtered);
  }, [orders, searchTerm, statusFilter]);

  const handleCancelOrder = (order: Order) => {
    setCancelDialog({ open: true, order });
  };

  const handleCancelConfirm = async () => {
    if (!cancelDialog.order) return;

    setLoading(true);
    try {
      // Cancel order logic here
      await tradingAPI.cancelOrder(cancelDialog.order.id);

      setSnackbar({
        open: true,
        message: `Order ${cancelDialog.order.id} cancelled successfully!`,
        severity: 'success'
      });

      // Refresh orders data
      await fetchOrdersData();
      setCancelDialog({ open: false, order: null });

    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to cancel order. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING': return 'warning';
      case 'PARTIALLY_FILLED': return 'info';
      case 'FILLED': return 'success';
      case 'CANCELLED': return 'default';
      case 'REJECTED': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING': return <Schedule />;
      case 'PARTIALLY_FILLED': return <PlayArrow />;
      case 'FILLED': return <CheckCircle />;
      case 'CANCELLED': return <Stop />;
      case 'REJECTED': return <Error />;
      default: return <Warning />;
    }
  };

  const getOrderStats = () => {
    const total = orders.length;
    const pending = orders.filter(o => o.status === 'PENDING').length;
    const filled = orders.filter(o => o.status === 'FILLED').length;
    const cancelled = orders.filter(o => o.status === 'CANCELLED').length;
    const rejected = orders.filter(o => o.status === 'REJECTED').length;

    return { total, pending, filled, cancelled, rejected };
  };

  const stats = getOrderStats();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ flexGrow: 1, p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={fetchOrdersData}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Orders
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchOrdersData}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh Data'}
        </Button>
      </Box>

      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(5, 1fr)' }, gap: 3, mb: 3 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Total Orders
            </Typography>
            <Typography variant="h4" color="primary.main">
              {stats.total}
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Pending
            </Typography>
            <Typography variant="h4" color="warning.main">
              {stats.pending}
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Filled
            </Typography>
            <Typography variant="h4" color="success.main">
              {stats.filled}
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Cancelled
            </Typography>
            <Typography variant="h4" color="default">
              {stats.cancelled}
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Rejected
            </Typography>
            <Typography variant="h4" color="error.main">
              {stats.rejected}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Filters and Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr 1fr' }, gap: 2, alignItems: 'end' }}>
            <TextField
              fullWidth
              label="Search Orders"
              placeholder="Search by symbol or order ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />

            <FormControl fullWidth>
              <InputLabel>Status Filter</InputLabel>
              <Select
                value={statusFilter}
                label="Status Filter"
                onChange={(e) => setStatusFilter(e.target.value)}
                startAdornment={<FilterList sx={{ mr: 1, color: 'text.secondary' }} />}
              >
                <MenuItem value="ALL">All Statuses</MenuItem>
                <MenuItem value="PENDING">Pending</MenuItem>
                <MenuItem value="PARTIALLY_FILLED">Partially Filled</MenuItem>
                <MenuItem value="FILLED">Filled</MenuItem>
                <MenuItem value="CANCELLED">Cancelled</MenuItem>
                <MenuItem value="REJECTED">Rejected</MenuItem>
              </Select>
            </FormControl>

            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('ALL');
              }}
            >
              Clear Filters
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Order History ({filteredOrders.length} orders)
          </Typography>
          {filteredOrders.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No orders found
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
                    <TableCell>Quantity</TableCell>
                    <TableCell>Price</TableCell>
                    <TableCell>Filled</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Strategy</TableCell>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredOrders.map((order) => (
                    <TableRow key={order.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {order.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {order.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={order.side}
                          color={order.side === 'BUY' ? 'success' : 'error'}
                          size="small"
                          icon={order.side === 'BUY' ? <TrendingUp /> : <TrendingDown />}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {order.orderType}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {order.quantity.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {order.price > 0 ? `₹${order.price.toFixed(2)}` : 'Market'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                          <Typography variant="body2">
                            {order.filledQuantity.toLocaleString()}
                          </Typography>
                          {order.status === 'PARTIALLY_FILLED' && (
                            <Typography variant="caption" color="text.secondary">
                              {order.remainingQuantity.toLocaleString()} remaining
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={order.status}
                          color={getStatusColor(order.status) as any}
                          size="small"
                          icon={getStatusIcon(order.status)}
                        />
                      </TableCell>
                      <TableCell>
                        {order.strategy ? (
                          <Chip
                            label={order.strategy}
                            size="small"
                            variant="outlined"
                          />
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            Manual
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {new Date(order.timestamp).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {order.status === 'PENDING' && (
                          <Button
                            variant="outlined"
                            size="small"
                            color="warning"
                            onClick={() => handleCancelOrder(order)}
                          >
                            Cancel
                          </Button>
                        )}
                        {order.status === 'REJECTED' && (
                          <Tooltip title="Order was rejected">
                            <IconButton size="small" color="error">
                              <Warning />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Cancel Order Dialog */}
      <Dialog open={cancelDialog.open} onClose={() => setCancelDialog({ open: false, order: null })} maxWidth="sm" fullWidth>
        <DialogTitle>
          Cancel Order - {cancelDialog.order?.symbol}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Are you sure you want to cancel this order?
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Order ID:</strong> {cancelDialog.order?.id}
              </Typography>
              <Typography variant="body2">
                <strong>Symbol:</strong> {cancelDialog.order?.symbol}
              </Typography>
              <Typography variant="body2">
                <strong>Side:</strong> {cancelDialog.order?.side}
              </Typography>
              <Typography variant="body2">
                <strong>Quantity:</strong> {cancelDialog.order?.quantity.toLocaleString()}
              </Typography>
              <Typography variant="body2">
                <strong>Price:</strong> ₹{cancelDialog.order?.price.toFixed(2)}
              </Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialog({ open: false, order: null })}>
            Keep Order
          </Button>
          <Button
            onClick={handleCancelConfirm}
            variant="contained"
            color="warning"
            disabled={loading}
          >
            {loading ? 'Cancelling...' : 'Cancel Order'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Orders; 