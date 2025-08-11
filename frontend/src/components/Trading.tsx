import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, TextField, Button, Grid, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Paper, Chip, Select, MenuItem,
  FormControl, InputLabel, Alert, Snackbar, IconButton, Tooltip, CircularProgress
} from '@mui/material';
import {
  TrendingUp, TrendingDown, ShoppingCart, AccountBalance, Refresh,
  PlayArrow, Stop, Warning, CheckCircle, Error
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface MarketData {
  symbol: string;
  lastPrice: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
}

interface OrderForm {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  orderType: 'MARKET' | 'LIMIT';
  limitPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
}

const Trading: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [orderForm, setOrderForm] = useState<OrderForm>({
    symbol: '',
    side: 'BUY',
    quantity: 0,
    orderType: 'MARKET'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [operationLoading, setOperationLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Fetch market data from API
  useEffect(() => {
    fetchMarketData();
  }, []);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await tradingAPI.getMarketSymbols();
      if (response.data && Array.isArray(response.data)) {
        // Transform API data to match our interface
        const transformedData: MarketData[] = response.data.map((item: any) => ({
          symbol: item.symbol || item.name || 'UNKNOWN',
          lastPrice: item.lastPrice || item.price || 0,
          change: item.change || 0,
          changePercent: item.changePercent || 0,
          volume: item.volume || 0,
          high: item.high || item.lastPrice || 0,
          low: item.low || item.lastPrice || 0
        }));
        setMarketData(transformedData);
      } else {
        // API returned unexpected format, set empty data
        setMarketData([]);
        setError('Invalid data format received from server');
      }
    } catch (error) {
      console.error('Error fetching market data:', error);
      setError('Failed to fetch market data. Please try again later.');
      
      // Set empty data instead of mock data
      setMarketData([]);
      setLoading(false);
    }
  };

  const handleOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setOperationLoading(true);
    
    try {
      // Place order logic here
      const response = await tradingAPI.placeOrder(orderForm);
      
      setSnackbar({
        open: true,
        message: `Order placed successfully! Order ID: ${response.data.orderId}`,
        severity: 'success'
      });
      
      // Reset form
      setOrderForm({
        symbol: '',
        side: 'BUY',
        quantity: 0,
        orderType: 'MARKET'
      });
      
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to place order. Please try again.',
        severity: 'error'
      });
    } finally {
      setOperationLoading(false);
    }
  };

  const handleInputChange = (field: keyof OrderForm, value: any) => {
    setOrderForm(prev => ({ ...prev, [field]: value }));
  };

  const refreshMarketData = () => {
    fetchMarketData();
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Trading Terminal
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={refreshMarketData}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh Market Data'}
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3 }}>
          {/* Market Data */}
          <Box>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Live Market Data
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell>Last Price</TableCell>
                        <TableCell>Change</TableCell>
                        <TableCell>Volume</TableCell>
                        <TableCell>High</TableCell>
                        <TableCell>Low</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {marketData.map((stock) => (
                        <TableRow key={stock.symbol} hover>
                          <TableCell>
                            <Typography variant="subtitle2" fontWeight="bold">
                              {stock.symbol}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              ₹{stock.lastPrice.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              {stock.change >= 0 ? (
                                <TrendingUp sx={{ color: 'success.main', mr: 1, fontSize: 16 }} />
                              ) : (
                                <TrendingDown sx={{ color: 'error.main', mr: 1, fontSize: 16 }} />
                              )}
                              <Typography
                                variant="body2"
                                color={stock.change >= 0 ? 'success.main' : 'error.main'}
                              >
                                {stock.change >= 0 ? '+' : ''}₹{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {stock.volume.toLocaleString()}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              ₹{stock.high.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              ₹{stock.low.toFixed(2)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Box>

          {/* Order Placement */}
          <Box>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Place Order
                </Typography>
                <Box component="form" onSubmit={handleOrderSubmit} sx={{ mt: 2 }}>
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>Symbol</InputLabel>
                      <Select
                        value={orderForm.symbol}
                        label="Symbol"
                        onChange={(e) => handleInputChange('symbol', e.target.value)}
                        required
                      >
                        {marketData.map((stock) => (
                          <MenuItem key={stock.symbol} value={stock.symbol}>
                            {stock.symbol} - ₹{stock.lastPrice.toFixed(2)}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                      <FormControl fullWidth>
                        <InputLabel>Side</InputLabel>
                        <Select
                          value={orderForm.side}
                          label="Side"
                          onChange={(e) => handleInputChange('side', e.target.value)}
                        >
                          <MenuItem value="BUY">
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <TrendingUp sx={{ color: 'success.main', mr: 1 }} />
                              BUY
                            </Box>
                          </MenuItem>
                          <MenuItem value="SELL">
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <TrendingDown sx={{ color: 'error.main', mr: 1 }} />
                              SELL
                            </Box>
                          </MenuItem>
                        </Select>
                      </FormControl>
                      
                      <TextField
                        fullWidth
                        label="Quantity"
                        type="number"
                        value={orderForm.quantity}
                        onChange={(e) => handleInputChange('quantity', parseInt(e.target.value) || 0)}
                        required
                        inputProps={{ min: 1 }}
                      />
                    </Box>
                    
                    <FormControl fullWidth>
                      <InputLabel>Order Type</InputLabel>
                      <Select
                        value={orderForm.orderType}
                        label="Order Type"
                        onChange={(e) => handleInputChange('orderType', e.target.value)}
                      >
                        <MenuItem value="MARKET">Market Order</MenuItem>
                        <MenuItem value="LIMIT">Limit Order</MenuItem>
                      </Select>
                    </FormControl>
                    
                    {orderForm.orderType === 'LIMIT' && (
                      <TextField
                        fullWidth
                        label="Limit Price"
                        type="number"
                        value={orderForm.limitPrice || ''}
                        onChange={(e) => handleInputChange('limitPrice', parseFloat(e.target.value) || undefined)}
                        required
                        inputProps={{ step: 0.01, min: 0 }}
                      />
                    )}
                    
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                      <TextField
                        fullWidth
                        label="Stop Loss"
                        type="number"
                        value={orderForm.stopLoss || ''}
                        onChange={(e) => handleInputChange('stopLoss', parseFloat(e.target.value) || undefined)}
                        inputProps={{ step: 0.01, min: 0 }}
                      />
                      
                      <TextField
                        fullWidth
                        label="Take Profit"
                        type="number"
                        value={orderForm.takeProfit || ''}
                        onChange={(e) => handleInputChange('takeProfit', parseFloat(e.target.value) || undefined)}
                        inputProps={{ step: 0.01, min: 0 }}
                      />
                    </Box>
                    
                    <Button
                      type="submit"
                      variant="contained"
                      fullWidth
                      size="large"
                      disabled={operationLoading || !orderForm.symbol || orderForm.quantity <= 0}
                      startIcon={orderForm.side === 'BUY' ? <TrendingUp /> : <TrendingDown />}
                      sx={{
                        backgroundColor: orderForm.side === 'BUY' ? 'success.main' : 'error.main',
                        '&:hover': {
                          backgroundColor: orderForm.side === 'BUY' ? 'success.dark' : 'error.dark',
                        }
                      }}
                    >
                      {operationLoading ? 'Placing Order...' : `Place ${orderForm.side} Order`}
                    </Button>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}

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

export default Trading; 