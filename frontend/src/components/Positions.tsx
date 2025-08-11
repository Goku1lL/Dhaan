import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, Snackbar, IconButton, Tooltip, CircularProgress
} from '@mui/material';
import {
  Close, TrendingUp, TrendingDown, AccountBalance, Warning, CheckCircle
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface Position {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  status: 'OPEN' | 'CLOSING' | 'CLOSED';
  timestamp: string;
}

const Positions: React.FC = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [closeDialog, setCloseDialog] = useState<{ open: boolean; position: Position | null }>({
    open: false,
    position: null
  });
  const [closeForm, setCloseForm] = useState({ quantity: 0, reason: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Fetch real positions data from API
  useEffect(() => {
    fetchPositionsData();
  }, []);

  const fetchPositionsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await tradingAPI.getPositions();
      const apiPositions = response.data;
      
      // Transform API data to match our interface
      const transformedPositions: Position[] = apiPositions.map((pos: any) => ({
        id: pos.id || pos.position_id || '',
        symbol: pos.symbol || pos.instrument || 'UNKNOWN',
        side: pos.side || 'LONG',
        quantity: pos.quantity || pos.qty || 0,
        entryPrice: pos.entry_price || pos.avg_price || 0,
        currentPrice: pos.current_price || pos.market_price || 0,
        pnl: pos.pnl || pos.unrealized_pnl || 0,
        pnlPercent: pos.pnl_percent || ((pos.pnl || 0) / (pos.entry_price || 1)) * 100 || 0,
        status: pos.status || 'OPEN',
        timestamp: pos.created_at || pos.timestamp || new Date().toISOString()
      }));
      
      setPositions(transformedPositions);
    } catch (err) {
      console.error('Failed to fetch positions:', err);
      setError('Failed to load positions data. Please try again.');
      // Fallback to empty array
      setPositions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClosePosition = (position: Position) => {
    setCloseDialog({ open: true, position });
    setCloseForm({ quantity: position.quantity, reason: '' });
  };

  const handleCloseConfirm = async () => {
    if (!closeDialog.position) return;
    
    setLoading(true);
    try {
      // Close position logic here
      await tradingAPI.closePosition(closeDialog.position.id, closeForm);
      
      setSnackbar({
        open: true,
        message: `Position closed successfully!`,
        severity: 'success'
      });
      
      // Refresh positions data
      await fetchPositionsData();
      setCloseDialog({ open: false, position: null });
      
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to close position. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const getTotalPnl = () => {
    return positions.reduce((total, pos) => total + pos.pnl, 0);
  };

  const getTotalExposure = () => {
    return positions.reduce((total, pos) => total + (pos.currentPrice * pos.quantity), 0);
  };

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
        <Button variant="contained" onClick={fetchPositionsData}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Positions
        </Typography>
        <Button
          variant="outlined"
          startIcon={<TrendingUp />}
          onClick={fetchPositionsData}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh Data'}
        </Button>
      </Box>

      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 3, mb: 3 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Total P&L
            </Typography>
            <Typography variant="h4" color={getTotalPnl() >= 0 ? 'success.main' : 'error.main'}>
              ₹{getTotalPnl().toLocaleString()}
            </Typography>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Open Positions
            </Typography>
            <Typography variant="h4" color="primary.main">
              {positions.length}
            </Typography>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Total Exposure
            </Typography>
            <Typography variant="h4" color="info.main">
              ₹{getTotalExposure().toLocaleString()}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Positions Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Open Positions
          </Typography>
          {positions.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No open positions found
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell>Quantity</TableCell>
                    <TableCell>Entry Price</TableCell>
                    <TableCell>Current Price</TableCell>
                    <TableCell>P&L</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {positions.map((position) => (
                    <TableRow key={position.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {position.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={position.side}
                          color={position.side === 'LONG' ? 'success' : 'error'}
                          size="small"
                          icon={position.side === 'LONG' ? <TrendingUp /> : <TrendingDown />}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {position.quantity.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          ₹{position.entryPrice.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          ₹{position.currentPrice.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography
                            variant="body2"
                            color={position.pnl >= 0 ? 'success.main' : 'error.main'}
                            fontWeight="bold"
                          >
                            ₹{position.pnl.toLocaleString()}
                          </Typography>
                          <Typography
                            variant="caption"
                            color={position.pnl >= 0 ? 'success.main' : 'error.main'}
                            sx={{ ml: 1 }}
                          >
                            ({position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(2)}%)
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={position.status}
                          color={position.status === 'OPEN' ? 'success' : 'warning'}
                          size="small"
                          icon={position.status === 'OPEN' ? <CheckCircle /> : <Warning />}
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outlined"
                          size="small"
                          color="warning"
                          onClick={() => handleClosePosition(position)}
                          disabled={position.status !== 'OPEN'}
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
      </Card>

      {/* Close Position Dialog */}
      <Dialog open={closeDialog.open} onClose={() => setCloseDialog({ open: false, position: null })} maxWidth="sm" fullWidth>
        <DialogTitle>
          Close Position - {closeDialog.position?.symbol}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Box sx={{ display: 'grid', gap: 2 }}>
              <TextField
                fullWidth
                label="Quantity to Close"
                type="number"
                value={closeForm.quantity}
                onChange={(e) => setCloseForm(prev => ({ ...prev, quantity: parseInt(e.target.value) || 0 }))}
                inputProps={{ min: 1, max: closeDialog.position?.quantity || 0 }}
              />
              
              <FormControl fullWidth>
                <InputLabel>Reason</InputLabel>
                <Select
                  value={closeForm.reason}
                  label="Reason"
                  onChange={(e) => setCloseForm(prev => ({ ...prev, reason: e.target.value }))}
                >
                  <MenuItem value="profit-taking">Profit Taking</MenuItem>
                  <MenuItem value="stop-loss">Stop Loss</MenuItem>
                  <MenuItem value="risk-management">Risk Management</MenuItem>
                  <MenuItem value="strategy-exit">Strategy Exit</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCloseDialog({ open: false, position: null })}>
            Cancel
          </Button>
          <Button
            onClick={handleCloseConfirm}
            variant="contained"
            color="warning"
            disabled={loading || closeForm.quantity <= 0}
          >
            {loading ? 'Closing...' : 'Close Position'}
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

export default Positions; 