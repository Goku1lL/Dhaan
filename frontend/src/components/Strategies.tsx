import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, Snackbar, IconButton, Tooltip, Switch, FormControlLabel, CircularProgress
} from '@mui/material';
import {
  PlayArrow, Stop, Add, Edit, Delete, TrendingUp, TrendingDown,
  Warning, CheckCircle, Error, Settings, Analytics, Refresh
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface Strategy {
  id: string;
  name: string;
  description: string;
  type: 'MOMENTUM' | 'MEAN_REVERSION' | 'ARBITRAGE' | 'GRID_TRADING' | 'CUSTOM';
  status: 'ACTIVE' | 'PAUSED' | 'STOPPED' | 'ERROR';
  symbols: string[];
  performance: {
    totalPnL: number;
    winRate: number;
    totalTrades: number;
    sharpeRatio: number;
    maxDrawdown: number;
  };
  risk: {
    maxPositionSize: number;
    stopLoss: number;
    takeProfit: number;
    maxDailyLoss: number;
  };
  createdAt: string;
  lastModified: string;
}

const Strategies: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [createDialog, setCreateDialog] = useState(false);
  const [editDialog, setEditDialog] = useState<{ open: boolean; strategy: Strategy | null }>({
    open: false,
    strategy: null
  });
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; strategy: Strategy | null }>({
    open: false,
    strategy: null
  });
  const [loading, setLoading] = useState(true);
  const [operationLoading, setOperationLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Form states
  const [strategyForm, setStrategyForm] = useState({
    name: '',
    description: '',
    type: 'MOMENTUM' as Strategy['type'],
    symbols: '',
    maxPositionSize: 1000,
    stopLoss: 5,
    takeProfit: 10,
    maxDailyLoss: 5000
  });

  // Fetch strategies data from API
  useEffect(() => {
    fetchStrategiesData();
  }, []);

  const fetchStrategiesData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await tradingAPI.getStrategies();
      if (response.data && Array.isArray(response.data)) {
        setStrategies(response.data);
      } else {
        // API returned unexpected format, set empty data
        setStrategies([]);
        setError('Invalid data format received from server');
      }
    } catch (error) {
      console.error('Error fetching strategies:', error);
      setError('Failed to fetch strategies. Please try again later.');
      
      // Set empty data instead of mock data
      setStrategies([]);
    } finally {
      // Always set loading to false regardless of success or error
      setLoading(false);
    }
  };

  const handleRefreshData = () => {
    fetchStrategiesData();
  };

  const handleCreateStrategy = async () => {
    if (!strategyForm.name || !strategyForm.description) {
      setSnackbar({
        open: true,
        message: 'Please fill in all required fields',
        severity: 'error'
      });
      return;
    }

    setOperationLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newStrategy: Strategy = {
        id: `STRAT${Date.now()}`,
        name: strategyForm.name,
        description: strategyForm.description,
        type: strategyForm.type,
        status: 'PAUSED',
        symbols: strategyForm.symbols.split(',').map(s => s.trim()).filter(s => s),
        performance: {
          totalPnL: 0,
          winRate: 0,
          totalTrades: 0,
          sharpeRatio: 0,
          maxDrawdown: 0
        },
        risk: {
          maxPositionSize: strategyForm.maxPositionSize,
          stopLoss: strategyForm.stopLoss,
          takeProfit: strategyForm.takeProfit,
          maxDailyLoss: strategyForm.maxDailyLoss
        },
        createdAt: new Date().toISOString(),
        lastModified: new Date().toISOString()
      };

      // Create strategy logic here
      await tradingAPI.createStrategy(newStrategy);

      setStrategies(prev => [...prev, newStrategy]);
      setCreateDialog(false);
      resetForm();

      setSnackbar({
        open: true,
        message: 'Strategy created successfully!',
        severity: 'success'
      });

    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to create strategy. Please try again.',
        severity: 'error'
      });
    } finally {
      setOperationLoading(false);
    }
  };

  const handleEditStrategy = async () => {
    if (!editDialog.strategy) return;

    setOperationLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const updatedStrategy = {
        ...editDialog.strategy,
        name: strategyForm.name,
        description: strategyForm.description,
        type: strategyForm.type,
        symbols: strategyForm.symbols.split(',').map(s => s.trim()).filter(s => s),
        risk: {
          maxPositionSize: strategyForm.maxPositionSize,
          stopLoss: strategyForm.stopLoss,
          takeProfit: strategyForm.takeProfit,
          maxDailyLoss: strategyForm.maxDailyLoss
        },
        lastModified: new Date().toISOString()
      };

      // Update strategy logic here
      await tradingAPI.updateStrategy(editDialog.strategy.id, updatedStrategy);

      setStrategies(prev => prev.map(s => 
        s.id === editDialog.strategy!.id ? updatedStrategy : s
      ));

      setEditDialog({ open: false, strategy: null });
      resetForm();

      setSnackbar({
        open: true,
        message: 'Strategy updated successfully!',
        severity: 'success'
      });

    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to update strategy. Please try again.',
        severity: 'error'
      });
    } finally {
      setOperationLoading(false);
    }
  };

  const handleDeleteStrategy = async () => {
    if (!deleteDialog.strategy) return;

    setOperationLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Delete strategy logic here
      await tradingAPI.deleteStrategy(deleteDialog.strategy.id);

      setStrategies(prev => prev.filter(s => s.id !== deleteDialog.strategy!.id));
      setDeleteDialog({ open: false, strategy: null });

      setSnackbar({
        open: true,
        message: 'Strategy deleted successfully!',
        severity: 'success'
      });

    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to delete strategy. Please try again.',
        severity: 'error'
      });
    } finally {
      setOperationLoading(false);
    }
  };

  const handleToggleStrategy = async (strategy: Strategy) => {
    setOperationLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newStatus = strategy.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
      
      if (newStatus === 'ACTIVE') {
        await tradingAPI.enableStrategy(strategy.id);
      } else {
        await tradingAPI.disableStrategy(strategy.id);
      }

      setStrategies(prev => prev.map(s => 
        s.id === strategy.id ? { ...s, status: newStatus } : s
      ));

      setSnackbar({
        open: true,
        message: `Strategy ${newStatus === 'ACTIVE' ? 'enabled' : 'paused'} successfully!`,
        severity: 'success'
      });

    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to toggle strategy. Please try again.',
        severity: 'error'
      });
    } finally {
      setOperationLoading(false);
    }
  };

  const resetForm = () => {
    setStrategyForm({
      name: '',
      description: '',
      type: 'MOMENTUM',
      symbols: '',
      maxPositionSize: 1000,
      stopLoss: 5,
      takeProfit: 10,
      maxDailyLoss: 5000
    });
  };

  const openEditDialog = (strategy: Strategy) => {
    setStrategyForm({
      name: strategy.name,
      description: strategy.description,
      type: strategy.type,
      symbols: strategy.symbols.join(', '),
      maxPositionSize: strategy.risk.maxPositionSize,
      stopLoss: strategy.risk.stopLoss,
      takeProfit: strategy.risk.takeProfit,
      maxDailyLoss: strategy.risk.maxDailyLoss
    });
    setEditDialog({ open: true, strategy });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'success';
      case 'PAUSED': return 'warning';
      case 'STOPPED': return 'default';
      case 'ERROR': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ACTIVE': return <PlayArrow />;
      case 'PAUSED': return <Stop />;
      case 'STOPPED': return <Stop />;
      case 'ERROR': return <Error />;
      default: return <Warning />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'MOMENTUM': return 'primary';
      case 'MEAN_REVERSION': return 'secondary';
      case 'ARBITRAGE': return 'info';
      case 'GRID_TRADING': return 'warning';
      case 'CUSTOM': return 'default';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Trading Strategies
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefreshData}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh Data'}
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialog(true)}
          >
            Create Strategy
          </Button>
        </Box>
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
        <>
          {/* Strategies Table */}
          <Card>
            <CardContent>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Symbols</TableCell>
                      <TableCell>Performance</TableCell>
                      <TableCell>Risk</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {strategies.map((strategy) => (
                      <TableRow key={strategy.id} hover>
                        <TableCell>
                          <Box>
                            <Typography variant="subtitle2" fontWeight="bold">
                              {strategy.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {strategy.description}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={strategy.type.replace('_', ' ')}
                            color={getTypeColor(strategy.type) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={strategy.status}
                            color={getStatusColor(strategy.status) as any}
                            size="small"
                            icon={getStatusIcon(strategy.status)}
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {strategy.symbols.map((symbol) => (
                              <Chip
                                key={symbol}
                                label={symbol}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" color={strategy.performance.totalPnL >= 0 ? 'success.main' : 'error.main'}>
                              ₹{strategy.performance.totalPnL.toLocaleString()}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {strategy.performance.winRate.toFixed(1)}% win rate
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2">
                              Max: ₹{strategy.risk.maxPositionSize.toLocaleString()}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              SL: {strategy.risk.stopLoss}% | TP: {strategy.risk.takeProfit}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                                                         <Tooltip title={strategy.status === 'ACTIVE' ? 'Pause Strategy' : 'Enable Strategy'}>
                               <IconButton
                                 size="small"
                                 color={strategy.status === 'ACTIVE' ? 'warning' : 'success'}
                                 onClick={() => handleToggleStrategy(strategy)}
                                 disabled={operationLoading}
                               >
                                 {strategy.status === 'ACTIVE' ? <Stop /> : <PlayArrow />}
                               </IconButton>
                             </Tooltip>
                            <Tooltip title="Edit Strategy">
                              <IconButton
                                size="small"
                                color="primary"
                                onClick={() => openEditDialog(strategy)}
                              >
                                <Edit />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete Strategy">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => setDeleteDialog({ open: true, strategy })}
                              >
                                <Delete />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Create Strategy Dialog */}
          <Dialog open={createDialog} onClose={() => setCreateDialog(false)} maxWidth="md" fullWidth>
            <DialogTitle>Create New Strategy</DialogTitle>
            <DialogContent>
              <Box sx={{ pt: 2 }}>
                <Box sx={{ display: 'grid', gap: 2 }}>
                  <TextField
                    fullWidth
                    label="Strategy Name"
                    value={strategyForm.name}
                    onChange={(e) => setStrategyForm(prev => ({ ...prev, name: e.target.value }))}
                    required
                  />
                  <TextField
                    fullWidth
                    label="Description"
                    multiline
                    rows={3}
                    value={strategyForm.description}
                    onChange={(e) => setStrategyForm(prev => ({ ...prev, description: e.target.value }))}
                    required
                  />
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>Strategy Type</InputLabel>
                      <Select
                        value={strategyForm.type}
                        label="Strategy Type"
                        onChange={(e) => setStrategyForm(prev => ({ ...prev, type: e.target.value as Strategy['type'] }))}
                      >
                        <MenuItem value="MOMENTUM">Momentum</MenuItem>
                        <MenuItem value="MEAN_REVERSION">Mean Reversion</MenuItem>
                        <MenuItem value="ARBITRAGE">Arbitrage</MenuItem>
                        <MenuItem value="GRID_TRADING">Grid Trading</MenuItem>
                        <MenuItem value="CUSTOM">Custom</MenuItem>
                      </Select>
                    </FormControl>
                    <TextField
                      fullWidth
                      label="Symbols (comma-separated)"
                      placeholder="RELIANCE, TCS, INFY"
                      value={strategyForm.symbols}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, symbols: e.target.value }))}
                    />
                  </Box>
                  <Typography variant="h6" sx={{ mt: 2 }}>Risk Parameters</Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                    <TextField
                      fullWidth
                      label="Max Position Size (₹)"
                      type="number"
                      value={strategyForm.maxPositionSize}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, maxPositionSize: parseInt(e.target.value) || 0 }))}
                      inputProps={{ min: 100 }}
                    />
                    <TextField
                      fullWidth
                      label="Stop Loss (%)"
                      type="number"
                      value={strategyForm.stopLoss}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, stopLoss: parseFloat(e.target.value) || 0 }))}
                      inputProps={{ min: 0.1, max: 20, step: 0.1 }}
                    />
                    <TextField
                      fullWidth
                      label="Take Profit (%)"
                      type="number"
                      value={strategyForm.takeProfit}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, takeProfit: parseFloat(e.target.value) || 0 }))}
                      inputProps={{ min: 0.1, max: 50, step: 0.1 }}
                    />
                    <TextField
                      fullWidth
                      label="Max Daily Loss (₹)"
                      type="number"
                      value={strategyForm.maxDailyLoss}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, maxDailyLoss: parseInt(e.target.value) || 0 }))}
                      inputProps={{ min: 100 }}
                    />
                  </Box>
                </Box>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setCreateDialog(false)}>
                Cancel
              </Button>
                             <Button
                 onClick={handleCreateStrategy}
                 variant="contained"
                 disabled={operationLoading || !strategyForm.name || !strategyForm.description}
               >
                 {operationLoading ? 'Creating...' : 'Create Strategy'}
               </Button>
            </DialogActions>
          </Dialog>

          {/* Edit Strategy Dialog */}
          <Dialog open={editDialog.open} onClose={() => setEditDialog({ open: false, strategy: null })} maxWidth="md" fullWidth>
            <DialogTitle>Edit Strategy</DialogTitle>
            <DialogContent>
              <Box sx={{ pt: 2 }}>
                <Box sx={{ display: 'grid', gap: 2 }}>
                  <TextField
                    fullWidth
                    label="Strategy Name"
                    value={strategyForm.name}
                    onChange={(e) => setStrategyForm(prev => ({ ...prev, name: e.target.value }))}
                    required
                  />
                  <TextField
                    fullWidth
                    label="Description"
                    multiline
                    rows={3}
                    value={strategyForm.description}
                    onChange={(e) => setStrategyForm(prev => ({ ...prev, description: e.target.value }))}
                    required
                  />
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>Strategy Type</InputLabel>
                      <Select
                        value={strategyForm.type}
                        label="Strategy Type"
                        onChange={(e) => setStrategyForm(prev => ({ ...prev, type: e.target.value as Strategy['type'] }))}
                      >
                        <MenuItem value="MOMENTUM">Momentum</MenuItem>
                        <MenuItem value="MEAN_REVERSION">Mean Reversion</MenuItem>
                        <MenuItem value="ARBITRAGE">Arbitrage</MenuItem>
                        <MenuItem value="GRID_TRADING">Grid Trading</MenuItem>
                        <MenuItem value="CUSTOM">Custom</MenuItem>
                      </Select>
                    </FormControl>
                    <TextField
                      fullWidth
                      label="Symbols (comma-separated)"
                      placeholder="RELIANCE, TCS, INFY"
                      value={strategyForm.symbols}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, symbols: e.target.value }))}
                    />
                  </Box>
                  <Typography variant="h6" sx={{ mt: 2 }}>Risk Parameters</Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                    <TextField
                      fullWidth
                      label="Max Position Size (₹)"
                      type="number"
                      value={strategyForm.maxPositionSize}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, maxPositionSize: parseInt(e.target.value) || 0 }))}
                      inputProps={{ min: 100 }}
                    />
                    <TextField
                      fullWidth
                      label="Stop Loss (%)"
                      type="number"
                      value={strategyForm.stopLoss}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, stopLoss: parseFloat(e.target.value) || 0 }))}
                      inputProps={{ min: 0.1, max: 20, step: 0.1 }}
                    />
                    <TextField
                      fullWidth
                      label="Take Profit (%)"
                      type="number"
                      value={strategyForm.takeProfit}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, takeProfit: parseFloat(e.target.value) || 0 }))}
                      inputProps={{ min: 0.1, max: 50, step: 0.1 }}
                    />
                    <TextField
                      fullWidth
                      label="Max Daily Loss (₹)"
                      type="number"
                      value={strategyForm.maxDailyLoss}
                      onChange={(e) => setStrategyForm(prev => ({ ...prev, maxDailyLoss: parseInt(e.target.value) || 0 }))}
                      inputProps={{ min: 100 }}
                    />
                  </Box>
                </Box>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setEditDialog({ open: false, strategy: null })}>
                Cancel
              </Button>
                             <Button
                 onClick={handleEditStrategy}
                 variant="contained"
                 disabled={operationLoading || !strategyForm.name || !strategyForm.description}
               >
                 {operationLoading ? 'Updating...' : 'Update Strategy'}
               </Button>
            </DialogActions>
          </Dialog>

          {/* Delete Strategy Dialog */}
          <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false, strategy: null })} maxWidth="sm" fullWidth>
            <DialogTitle>Delete Strategy</DialogTitle>
            <DialogContent>
              <Box sx={{ pt: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Are you sure you want to delete this strategy? This action cannot be undone.
                </Typography>
                {deleteDialog.strategy && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      <strong>Strategy:</strong> {deleteDialog.strategy.name}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Type:</strong> {deleteDialog.strategy.type.replace('_', ' ')}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Status:</strong> {deleteDialog.strategy.status}
                    </Typography>
                  </Box>
                )}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDeleteDialog({ open: false, strategy: null })}>
                Cancel
              </Button>
                             <Button
                 onClick={handleDeleteStrategy}
                 variant="contained"
                 color="error"
                 disabled={operationLoading}
               >
                 {operationLoading ? 'Deleting...' : 'Delete Strategy'}
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
        </>
      )}
    </Box>
  );
};

export default Strategies; 