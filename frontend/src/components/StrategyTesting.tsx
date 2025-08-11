import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Button,
  Switch,
  FormControlLabel,
  Card,
  CardContent,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Divider,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  CircularProgress
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ShowChart as ShowChartIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface StrategyPerformance {
  name: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_profit_per_trade: number;
  max_drawdown: number;
  active_positions: number;
  last_signal_time: string | null;
}

interface StrategyTrade {
  trade_id: string;
  strategy_id: string;
  symbol: string;
  side: string;
  entry_price: number;
  quantity: number;
  entry_time: string;
  unrealized_pnl: number;
}

interface AutoTradingStatus {
  auto_trading_enabled: boolean;
  max_position_size: number;
  max_positions_per_strategy: number;
  risk_per_trade: number;
  total_strategies: number;
  total_active_trades: number;
}

const StrategyTesting: React.FC = () => {
  const [autoTradingStatus, setAutoTradingStatus] = useState<AutoTradingStatus | null>(null);
  const [strategyPerformance, setStrategyPerformance] = useState<{[key: string]: StrategyPerformance}>({});
  const [activeTrades, setActiveTrades] = useState<StrategyTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Helper functions
  const formatCurrency = (amount: number | null | undefined): string => {
    if (amount == null || isNaN(amount)) return '₹0.00';
    return `₹${amount.toFixed(2)}`;
  };

  const formatPercentage = (percentage: number | null | undefined): string => {
    if (percentage == null || isNaN(percentage)) return '0.00%';
    return `${(percentage * 100).toFixed(2)}%`;
  };

  const getPnLColor = (amount: number | null | undefined): string => {
    if (amount == null || isNaN(amount)) return 'text.primary';
    return amount >= 0 ? 'success.main' : 'error.main';
  };

  const getWinRateColor = (winRate: number): string => {
    if (winRate >= 0.7) return 'success.main';
    if (winRate >= 0.5) return 'warning.main';
    return 'error.main';
  };

  // Load data
  const loadStrategyData = async () => {
    try {
      setLoading(true);
      
      const [statusRes, performanceRes, tradesRes] = await Promise.allSettled([
        tradingAPI.getStrategyTradingStatus(),
        tradingAPI.getStrategyPerformance(),
        tradingAPI.getStrategyActiveTrades()
      ]);

      // Handle status
      if (statusRes.status === 'fulfilled' && statusRes.value?.data?.success) {
        setAutoTradingStatus(statusRes.value.data);
      }

      // Handle performance
      if (performanceRes.status === 'fulfilled' && performanceRes.value?.data?.success) {
        setStrategyPerformance(performanceRes.value.data.performance?.strategies || {});
      }

      // Handle active trades
      if (tradesRes.status === 'fulfilled' && tradesRes.value?.data?.success) {
        setActiveTrades(tradesRes.value.data.trades || []);
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading strategy data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto trading control
  const toggleAutoTrading = async () => {
    try {
      setProcessing(true);
      
      if (autoTradingStatus?.auto_trading_enabled) {
        await tradingAPI.disableStrategyAutoTrading();
      } else {
        await tradingAPI.enableStrategyAutoTrading();
      }
      
      // Reload status
      await loadStrategyData();
    } catch (error) {
      console.error('Error toggling auto trading:', error);
    } finally {
      setProcessing(false);
    }
  };

  // Process opportunities manually
  const processOpportunities = async () => {
    try {
      setProcessing(true);
      const result = await tradingAPI.processStrategyOpportunities();
      console.log('Processing result:', result.data);
      
      // Reload data to see updates
      await loadStrategyData();
    } catch (error) {
      console.error('Error processing opportunities:', error);
    } finally {
      setProcessing(false);
    }
  };

  // Load data on component mount and set up auto-refresh
  useEffect(() => {
    loadStrategyData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadStrategyData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const totalStrategies = Object.keys(strategyPerformance).length;
  const totalPnL = Object.values(strategyPerformance).reduce((sum, perf) => sum + (perf.total_pnl || 0), 0);
  const totalTrades = Object.values(strategyPerformance).reduce((sum, perf) => sum + (perf.total_trades || 0), 0);
  const overallWinRate = totalTrades > 0 ? 
    Object.values(strategyPerformance).reduce((sum, perf) => sum + (perf.winning_trades || 0), 0) / totalTrades : 0;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Strategy Testing & Performance
        </Typography>
        <Box>
          <Tooltip title="Refresh Data">
            <IconButton onClick={loadStrategyData} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton onClick={() => setShowSettingsDialog(true)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Status Alert */}
      {autoTradingStatus && (
        <Alert 
          severity={autoTradingStatus.auto_trading_enabled ? "success" : "warning"} 
          sx={{ mb: 3 }}
          action={
            <FormControlLabel
              control={
                <Switch
                  checked={autoTradingStatus.auto_trading_enabled}
                  onChange={toggleAutoTrading}
                  disabled={processing}
                />
              }
              label="Auto Trading"
            />
          }
        >
          Strategy-based paper trading is {autoTradingStatus.auto_trading_enabled ? 'ENABLED' : 'DISABLED'}. 
          Market opportunities will {autoTradingStatus.auto_trading_enabled ? 'automatically' : 'NOT'} trigger paper trades.
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total Strategies
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {totalStrategies}
                  </Typography>
                </Box>
                <AssessmentIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total P&L
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color={getPnLColor(totalPnL)}>
                    {formatCurrency(totalPnL)}
                  </Typography>
                </Box>
                {totalPnL >= 0 ? 
                  <TrendingUpIcon color="success" sx={{ fontSize: 40 }} /> : 
                  <TrendingDownIcon color="error" sx={{ fontSize: 40 }} />
                }
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Win Rate
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color={getWinRateColor(overallWinRate)}>
                    {formatPercentage(overallWinRate)}
                  </Typography>
                </Box>
                <ShowChartIcon color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Active Trades
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {activeTrades.length}
                  </Typography>
                </Box>
                <TimelineIcon color="secondary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Control Panel */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Strategy Control Panel
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <Button
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={processOpportunities}
            disabled={processing}
          >
            Process Opportunities
          </Button>
          <Typography variant="body2" color="textSecondary">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </Typography>
        </Box>
      </Paper>

      {/* Strategy Performance Table */}
      <Paper sx={{ mb: 4 }}>
        <Box p={2}>
          <Typography variant="h6" gutterBottom>
            Strategy Performance Analysis
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Strategy</TableCell>
                <TableCell align="right">Total Trades</TableCell>
                <TableCell align="right">Win Rate</TableCell>
                <TableCell align="right">Total P&L</TableCell>
                <TableCell align="right">Avg Profit</TableCell>
                <TableCell align="right">Max Drawdown</TableCell>
                <TableCell align="right">Active Positions</TableCell>
                <TableCell align="right">Last Signal</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(strategyPerformance).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography color="textSecondary">
                      No strategy performance data available. Start scanning and auto-trading to see results.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                Object.entries(strategyPerformance).map(([strategyId, performance]) => (
                  <TableRow key={strategyId}>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {performance.name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {strategyId}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={performance.total_trades || 0}
                        size="small"
                        color={performance.total_trades > 0 ? "primary" : "default"}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography color={getWinRateColor(performance.win_rate || 0)}>
                        {formatPercentage(performance.win_rate)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography color={getPnLColor(performance.total_pnl)}>
                        {formatCurrency(performance.total_pnl)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography color={getPnLColor(performance.avg_profit_per_trade)}>
                        {formatCurrency(performance.avg_profit_per_trade)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography color="error.main">
                        {formatCurrency(performance.max_drawdown)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={performance.active_positions || 0}
                        size="small"
                        color={performance.active_positions > 0 ? "success" : "default"}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="caption" color="textSecondary">
                        {performance.last_signal_time ? 
                          new Date(performance.last_signal_time).toLocaleString() : 
                          'Never'
                        }
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Active Trades */}
      <Paper>
        <Box p={2}>
          <Typography variant="h6" gutterBottom>
            Active Strategy Trades ({activeTrades.length})
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Strategy</TableCell>
                <TableCell align="right">Side</TableCell>
                <TableCell align="right">Entry Price</TableCell>
                <TableCell align="right">Quantity</TableCell>
                <TableCell align="right">Unrealized P&L</TableCell>
                <TableCell align="right">Entry Time</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {activeTrades.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="textSecondary">
                      No active strategy trades. Enable auto-trading and wait for market opportunities.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                activeTrades.map((trade) => (
                  <TableRow key={trade.trade_id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {trade.symbol}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" color="textSecondary">
                        {trade.strategy_id}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={trade.side}
                        size="small"
                        color={trade.side === 'BUY' ? "success" : "error"}
                      />
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(trade.entry_price)}
                    </TableCell>
                    <TableCell align="right">
                      {trade.quantity}
                    </TableCell>
                    <TableCell align="right">
                      <Typography color={getPnLColor(trade.unrealized_pnl)}>
                        {formatCurrency(trade.unrealized_pnl)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="caption" color="textSecondary">
                        {new Date(trade.entry_time).toLocaleString()}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Settings Dialog */}
      <Dialog open={showSettingsDialog} onClose={() => setShowSettingsDialog(false)}>
        <DialogTitle>Strategy Trading Settings</DialogTitle>
        <DialogContent>
          {autoTradingStatus && (
            <List>
              <ListItem>
                <ListItemText
                  primary="Max Position Size"
                  secondary={formatCurrency(autoTradingStatus.max_position_size)}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Max Positions per Strategy"
                  secondary={autoTradingStatus.max_positions_per_strategy}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Risk per Trade"
                  secondary={formatPercentage(autoTradingStatus.risk_per_trade)}
                />
              </ListItem>
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettingsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrategyTesting; 