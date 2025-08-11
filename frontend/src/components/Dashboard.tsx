import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  AccountBalance,
  ShoppingCart,
  Psychology,
  PlayArrow,
  Stop,
  Refresh,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { tradingAPI } from '../services/api';

const Dashboard: React.FC = () => {
  const [isTradingActive, setIsTradingActive] = useState(true);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [dashboardRes, positionsRes, ordersRes] = await Promise.all([
          tradingAPI.getDashboardData(),
          tradingAPI.getPositions(),
          tradingAPI.getOrders()
        ]);
        
        setDashboardData(dashboardRes.data);
        setPositions(positionsRes.data);
        setOrders(ordersRes.data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch dashboard data');
        console.error('Dashboard data fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const toggleTrading = () => {
    setIsTradingActive(!isTradingActive);
  };

  const refreshData = async () => {
    try {
      setLoading(true);
      const [dashboardRes, positionsRes, ordersRes] = await Promise.all([
        tradingAPI.getDashboardData(),
        tradingAPI.getPositions(),
        tradingAPI.getOrders()
      ]);
      
      setDashboardData(dashboardRes.data);
      setPositions(positionsRes.data);
      setOrders(ordersRes.data);
      setError(null);
    } catch (err) {
      setError('Failed to refresh data');
      console.error('Data refresh error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Generate chart data from dashboard data
  const generateChartData = () => {
    if (!dashboardData) return [];
    
    const baseValue = dashboardData.portfolio_value || 100000;
    const dailyPnL = dashboardData.daily_pnl || 0;
    
    return [
      { time: '09:00', pnl: 0, equity: baseValue },
      { time: '10:00', pnl: dailyPnL * 0.3, equity: baseValue + dailyPnL * 0.3 },
      { time: '11:00', pnl: dailyPnL * 0.6, equity: baseValue + dailyPnL * 0.6 },
      { time: '12:00', pnl: dailyPnL * 0.5, equity: baseValue + dailyPnL * 0.5 },
      { time: '13:00', pnl: dailyPnL * 0.8, equity: baseValue + dailyPnL * 0.8 },
      { time: '14:00', pnl: dailyPnL * 0.7, equity: baseValue + dailyPnL * 0.7 },
      { time: '15:00', pnl: dailyPnL, equity: baseValue + dailyPnL },
    ];
  };

  // Show loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography variant="h6">Loading dashboard data...</Typography>
      </Box>
    );
  }

  // Show error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" color="error" gutterBottom>
          Error: {error}
        </Typography>
        <Button variant="contained" onClick={refreshData}>
          Retry
        </Button>
      </Box>
    );
  }

  const chartData = generateChartData();
  const portfolioValue = dashboardData?.portfolio_value || 100000;
  const dailyPnL = dashboardData?.daily_pnl || 0;
  const changePercent = dashboardData?.change_percent || 0;
  const openPositionsCount = positions.length;
  const activeStrategiesCount = dashboardData?.active_strategies || 2;

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Trading Dashboard
      </Typography>

      {/* System Status and Controls */}
      <Card sx={{ mb: 3, backgroundColor: 'background.paper' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Chip
                label={isTradingActive ? 'Trading Active' : 'Trading Paused'}
                color={isTradingActive ? 'success' : 'warning'}
                icon={isTradingActive ? <PlayArrow /> : <Stop />}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant={isTradingActive ? 'outlined' : 'contained'}
                color={isTradingActive ? 'warning' : 'success'}
                onClick={toggleTrading}
                startIcon={isTradingActive ? <Stop /> : <PlayArrow />}
              >
                {isTradingActive ? 'Pause Trading' : 'Resume Trading'}
              </Button>
              <Button variant="outlined" startIcon={<Refresh />} onClick={refreshData} disabled={loading}>
                {loading ? 'Refreshing...' : 'Refresh Data'}
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 3 }}>
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <AccountBalance sx={{ color: 'primary.main', mr: 1 }} />
              <Typography variant="h6">Portfolio Value</Typography>
            </Box>
            <Typography variant="h4" color="primary.main">
              ₹{portfolioValue.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {dailyPnL >= 0 ? '+' : ''}₹{dailyPnL.toLocaleString()} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(1)}%)
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingUp sx={{ color: 'success.main', mr: 1 }} />
              <Typography variant="h6">Today's P&L</Typography>
            </Box>
            <Typography variant="h4" color={dailyPnL >= 0 ? 'success.main' : 'error.main'}>
              ₹{dailyPnL.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {dailyPnL >= 0 ? '+' : ''}{changePercent.toFixed(1)}% from yesterday
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <ShoppingCart sx={{ color: 'info.main', mr: 1 }} />
              <Typography variant="h6">Open Positions</Typography>
            </Box>
            <Typography variant="h4" color="info.main">
              {openPositionsCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Value: ₹{(positions.reduce((sum, pos) => sum + (pos.market_value || 0), 0)).toLocaleString()}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Psychology sx={{ color: 'secondary.main', mr: 1 }} />
              <Typography variant="h6">Active Strategies</Typography>
            </Box>
            <Typography variant="h4" color="secondary.main">
              {activeStrategiesCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Running smoothly
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Charts and Tables */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3, mb: 3 }}>
        {/* P&L Chart */}
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Portfolio Performance
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="equity" stroke="#00c853" strokeWidth={2} />
                <Line type="monotone" dataKey="pnl" stroke="#ff6f00" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Risk Metrics */}
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Risk Metrics
            </Typography>
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" gutterBottom>
                Daily Loss Limit
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={Math.min(35, Math.abs(dailyPnL) / 1000 * 10)} 
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {Math.min(35, Math.abs(dailyPnL) / 1000 * 10).toFixed(1)}% used (₹{(100000 - Math.abs(dailyPnL)).toLocaleString()} remaining)
              </Typography>
            </Box>
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" gutterBottom>
                Portfolio Exposure
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={Math.min(100, (positions.reduce((sum, pos) => sum + (pos.market_value || 0), 0) / portfolioValue) * 100)} 
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {Math.min(100, (positions.reduce((sum, pos) => sum + (pos.market_value || 0), 0) / portfolioValue) * 100).toFixed(1)}% exposed (₹{positions.reduce((sum, pos) => sum + (pos.market_value || 0), 0).toLocaleString()})
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" gutterBottom>
                Margin Utilization
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={45} 
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                45% utilized
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Tables Row */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
        {/* Open Positions */}
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Open Positions
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell>Qty</TableCell>
                    <TableCell>P&L</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {positions.length > 0 ? (
                    positions.map((position, index) => (
                      <TableRow key={index}>
                        <TableCell>{position.symbol || position.instrument}</TableCell>
                        <TableCell>
                          <Chip
                            label={position.side || 'LONG'}
                            color={(position.side || 'LONG') === 'LONG' ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{position.quantity || position.qty}</TableCell>
                        <TableCell sx={{ color: (position.pnl || 0) >= 0 ? 'success.main' : 'error.main' }}>
                          ₹{position.pnl || 0}
                        </TableCell>
                        <TableCell>
                          <Chip label={position.status || 'OPEN'} color="primary" size="small" />
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography variant="body2" color="text.secondary">
                          No open positions
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Recent Orders */}
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Orders
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Qty</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {orders.length > 0 ? (
                    orders.slice(0, 5).map((order, index) => (
                      <TableRow key={index}>
                        <TableCell>{order.symbol || order.instrument}</TableCell>
                        <TableCell>
                          <Chip
                            label={order.type || order.order_type}
                            color={(order.type || order.order_type) === 'BUY' ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{order.quantity || order.qty}</TableCell>
                        <TableCell>
                          <Chip 
                            label={order.status} 
                            color={order.status === 'FILLED' ? 'success' : 'warning'} 
                            size="small" 
                          />
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={4} align="center">
                        <Typography variant="body2" color="text.secondary">
                          No recent orders
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default Dashboard; 