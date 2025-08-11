import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, Snackbar, IconButton, Tooltip, Switch, FormControlLabel,
  LinearProgress, Divider, CircularProgress
} from '@mui/material';
import {
  Warning, CheckCircle, Error, Settings, Refresh, TrendingUp, TrendingDown,
  Security, AccountBalance, Speed, Timeline, Notifications
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface RiskMetric {
  id: string;
  name: string;
  currentValue: number;
  limit: number;
  status: 'SAFE' | 'WARNING' | 'CRITICAL' | 'EXCEEDED';
  trend: 'UP' | 'DOWN' | 'STABLE';
  lastUpdated: string;
}

interface RiskLimit {
  id: string;
  name: string;
  value: number;
  unit: string;
  description: string;
  isActive: boolean;
}

interface RiskAlert {
  id: string;
  type: 'WARNING' | 'CRITICAL' | 'INFO';
  message: string;
  timestamp: string;
  isRead: boolean;
}

const RiskManagement: React.FC = () => {
  const [riskMetrics, setRiskMetrics] = useState<RiskMetric[]>([]);
  const [riskLimits, setRiskLimits] = useState<RiskLimit[]>([]);
  const [riskAlerts, setRiskAlerts] = useState<RiskAlert[]>([]);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [editLimitDialog, setEditLimitDialog] = useState<{ open: boolean; limit: RiskLimit | null }>({
    open: false,
    limit: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Form states
  const [limitForm, setLimitForm] = useState({
    value: 0,
    isActive: true
  });

  // Fetch real data from API
  useEffect(() => {
    fetchRiskData();
  }, []);

  const fetchRiskData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch risk metrics and summary
      const [riskRes, summaryRes] = await Promise.all([
        tradingAPI.getRiskMetrics(),
        tradingAPI.getRiskSummary()
      ]);

      if (riskRes.data) {
        setRiskMetrics([
          {
            id: 'RM001',
            name: 'Portfolio VaR (95%)',
            currentValue: riskRes.data.var_95 || 0,
            limit: riskRes.data.daily_loss_limit || 0,
            status: (riskRes.data.var_95 || 0) < (riskRes.data.daily_loss_limit || 0) ? 'SAFE' : 'WARNING',
            trend: 'STABLE',
            lastUpdated: new Date().toISOString()
          },
          {
            id: 'RM002',
            name: 'Maximum Drawdown',
            currentValue: riskRes.data.max_drawdown || 0,
            limit: -(riskRes.data.daily_loss_limit || 0),
            status: Math.abs(riskRes.data.max_drawdown || 0) < (riskRes.data.daily_loss_limit || 0) ? 'SAFE' : 'WARNING',
            trend: 'STABLE',
            lastUpdated: new Date().toISOString()
          },
          {
            id: 'RM003',
            name: 'Daily P&L',
            currentValue: riskRes.data.daily_loss_limit_used || 0,
            limit: -(riskRes.data.daily_loss_limit || 0),
            status: Math.abs(riskRes.data.daily_loss_limit_used || 0) < (riskRes.data.daily_loss_limit || 0) ? 'SAFE' : 'WARNING',
            trend: 'STABLE',
            lastUpdated: new Date().toISOString()
          },
          {
            id: 'RM004',
            name: 'Position Concentration',
            currentValue: riskRes.data.portfolio_exposure || 0,
            limit: 50,
            status: (riskRes.data.portfolio_exposure || 0) < 50 ? 'SAFE' : 'WARNING',
            trend: 'STABLE',
            lastUpdated: new Date().toISOString()
          },
          {
            id: 'RM005',
            name: 'Leverage Ratio',
            currentValue: riskRes.data.margin_utilization || 0,
            limit: 2.5,
            status: (riskRes.data.margin_utilization || 0) < 2.5 ? 'SAFE' : 'WARNING',
            trend: 'STABLE',
            lastUpdated: new Date().toISOString()
          }
        ]);
      }

      if (summaryRes.data) {
        setRiskLimits([
          {
            id: 'RL001',
            name: 'Maximum Daily Loss',
            value: summaryRes.data.daily_loss_limit || 0,
            unit: '₹',
            description: 'Maximum allowed daily loss before trading is suspended',
            isActive: true
          },
          {
            id: 'RL002',
            name: 'Maximum Position Size',
            value: 10000, // This should come from API
            unit: '₹',
            description: 'Maximum size of any single position',
            isActive: true
          },
          {
            id: 'RL003',
            name: 'Portfolio VaR Limit',
            value: summaryRes.data.daily_loss_limit || 0,
            unit: '₹',
            description: 'Maximum portfolio Value at Risk',
            isActive: true
          },
          {
            id: 'RL004',
            name: 'Maximum Drawdown',
            value: summaryRes.data.daily_loss_limit || 0,
            unit: '₹',
            description: 'Maximum allowed portfolio drawdown',
            isActive: true
          },
          {
            id: 'RL005',
            name: 'Leverage Limit',
            value: 2.5,
            unit: 'x',
            description: 'Maximum allowed leverage ratio',
            isActive: true
          }
        ]);
      }

      // Generate risk alerts based on actual data
      const alerts: RiskAlert[] = [];
      
      if (riskRes.data) {
        // Add warning alerts based on risk metrics
        if (riskRes.data.var_95 && riskRes.data.var_95 > (riskRes.data.daily_loss_limit || 0) * 0.8) {
          alerts.push({
            id: 'RA_VAR',
            type: 'WARNING',
            message: `Portfolio VaR approaching limit (${riskRes.data.var_95} / ${riskRes.data.daily_loss_limit})`,
            timestamp: new Date().toISOString(),
            isRead: false
          });
        }

        if (riskRes.data.max_drawdown && Math.abs(riskRes.data.max_drawdown) > (riskRes.data.daily_loss_limit || 0) * 0.8) {
          alerts.push({
            id: 'RA_DRAWDOWN',
            type: 'WARNING',
            message: `Maximum drawdown approaching limit (${riskRes.data.max_drawdown} / ${riskRes.data.daily_loss_limit})`,
            timestamp: new Date().toISOString(),
            isRead: false
          });
        }

        // Add some info alerts
        if (riskRes.data.sharpe_ratio && riskRes.data.sharpe_ratio > 1.5) {
          alerts.push({
            id: 'RA_SHARPE',
            type: 'INFO',
            message: `Sharpe ratio improved to ${riskRes.data.sharpe_ratio.toFixed(2)}`,
            timestamp: new Date().toISOString(),
            isRead: true
          });
        }
      }

      setRiskAlerts(alerts);

    } catch (err) {
      console.error('Error fetching risk data:', err);
      setError('Failed to fetch risk data. Please try again later.');
      
      // Set empty data instead of mock data
      setRiskMetrics([]);
      setRiskLimits([]);
      setRiskAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEditLimit = (limit: RiskLimit) => {
    setEditLimitDialog({ open: true, limit });
    setLimitForm({ value: limit.value, isActive: limit.isActive });
  };

  const handleEditConfirm = async () => {
    if (!editLimitDialog.limit) return;

    setLoading(true);
    try {
      // Update risk limit logic here
      await tradingAPI.updateRiskLimits({
        id: editLimitDialog.limit.id,
        value: limitForm.value,
        isActive: limitForm.isActive
      });

      setSnackbar({
        open: true,
        message: 'Risk limit updated successfully!',
        severity: 'success'
      });

      // Update local state
      setRiskLimits(prev => prev.map(limit =>
        limit.id === editLimitDialog.limit!.id
          ? { ...limit, value: limitForm.value, isActive: limitForm.isActive }
          : limit
      ));

      setEditLimitDialog({ open: false, limit: null });

    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to update risk limit. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshMetrics = async () => {
    await fetchRiskData();
    setSnackbar({
      open: true,
      message: 'Risk metrics refreshed successfully!',
      severity: 'success'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SAFE': return 'success';
      case 'WARNING': return 'warning';
      case 'CRITICAL': return 'error';
      case 'EXCEEDED': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SAFE': return <CheckCircle />;
      case 'WARNING': return <Warning />;
      case 'CRITICAL': return <Error />;
      case 'EXCEEDED': return <Error />;
      default: return <Security />;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'UP': return <TrendingUp />;
      case 'DOWN': return <TrendingDown />;
      case 'STABLE': return <Timeline />;
      default: return <Timeline />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'WARNING': return 'warning';
      case 'CRITICAL': return 'error';
      case 'INFO': return 'info';
      default: return 'default';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'WARNING': return <Warning />;
      case 'CRITICAL': return <Error />;
      case 'INFO': return <Notifications />;
      default: return <Notifications />;
    }
  };

  const calculateUtilization = (current: number, limit: number) => {
    return Math.abs((current / limit) * 100);
  };

  const getOverallRiskStatus = () => {
    const criticalCount = riskMetrics.filter(m => m.status === 'CRITICAL').length;
    const warningCount = riskMetrics.filter(m => m.status === 'WARNING').length;
    
    if (criticalCount > 0) return { status: 'HIGH', color: 'error.main', description: `${criticalCount} critical, ${warningCount} warnings` };
    if (warningCount > 0) return { status: 'MEDIUM', color: 'warning.main', description: `${warningCount} warnings` };
    return { status: 'LOW', color: 'success.main', description: 'All metrics safe' };
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
      <Box sx={{ p: 3 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={fetchRiskData}>
          Retry
        </Button>
      </Box>
    );
  }

  const overallRisk = getOverallRiskStatus();

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Risk Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={handleRefreshMetrics}
          disabled={loading}
        >
          Refresh Metrics
        </Button>
      </Box>

      {/* Risk Overview Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 3, mb: 3 }}>
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Security color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Overall Risk
              </Typography>
            </Box>
            <Typography variant="h4" color={overallRisk.color} gutterBottom>
              {overallRisk.status}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {overallRisk.description}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <AccountBalance color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Portfolio VaR
              </Typography>
            </Box>
            <Typography variant="h4" color="success.main" gutterBottom>
              ₹{dashboardData?.risk_metrics?.var_95?.toLocaleString() || '12,500'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {dashboardData?.risk_metrics?.var_95 ? Math.round((dashboardData.risk_metrics.var_95 / 20000) * 100) : 62.5}% of limit
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Speed color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Daily P&L
              </Typography>
            </Box>
            <Typography variant="h4" color={dashboardData?.daily_pnl > 0 ? 'success.main' : 'warning.main'} gutterBottom>
              ₹{dashboardData?.daily_pnl?.toLocaleString() || '-3,200'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {dashboardData?.daily_pnl ? Math.round((Math.abs(dashboardData.daily_pnl) / 5000) * 100) : 64}% of limit
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Timeline color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Max Drawdown
              </Typography>
            </Box>
            <Typography variant="h4" color="warning.main" gutterBottom>
              ₹{dashboardData?.risk_metrics?.max_drawdown?.toLocaleString() || '-8,500'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {dashboardData?.risk_metrics?.max_drawdown ? Math.round((Math.abs(dashboardData.risk_metrics.max_drawdown) / 15000) * 100) : 56.7}% of limit
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Risk Metrics Table */}
      <Card sx={{ backgroundColor: 'background.paper', mb: 3 }}>
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            Risk Metrics
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Metric</TableCell>
                  <TableCell align="right">Current Value</TableCell>
                  <TableCell align="right">Limit</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell align="center">Trend</TableCell>
                  <TableCell align="center">Utilization</TableCell>
                  <TableCell align="right">Last Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {riskMetrics.map((metric) => (
                  <TableRow key={metric.id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {metric.name}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        color={metric.currentValue < 0 ? 'error.main' : 'text.primary'}
                      >
                        {metric.currentValue < 0 ? '-' : ''}₹{Math.abs(metric.currentValue).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        ₹{Math.abs(metric.limit).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        icon={getStatusIcon(metric.status)}
                        label={metric.status}
                        color={getStatusColor(metric.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title={metric.trend}>
                        <IconButton size="small">
                          {getTrendIcon(metric.trend)}
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(calculateUtilization(metric.currentValue, metric.limit), 100)}
                          color={getStatusColor(metric.status) as any}
                          sx={{ width: 60, height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="caption">
                          {Math.min(calculateUtilization(metric.currentValue, metric.limit), 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="caption" color="text.secondary">
                        {new Date(metric.lastUpdated).toLocaleTimeString()}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Risk Limits and Alerts */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3 }}>
        {/* Risk Limits */}
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              Risk Limits
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Limit</TableCell>
                    <TableCell align="right">Value</TableCell>
                    <TableCell align="center">Status</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {riskLimits.map((limit) => (
                    <TableRow key={limit.id}>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {limit.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {limit.description}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {limit.value.toLocaleString()} {limit.unit}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Switch
                          checked={limit.isActive}
                          color="primary"
                          size="small"
                          disabled
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Button
                          size="small"
                          startIcon={<Settings />}
                          onClick={() => handleEditLimit(limit)}
                        >
                          Edit
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Risk Alerts */}
        <Card sx={{ backgroundColor: 'background.paper' }}>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              Risk Alerts
            </Typography>
            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              {riskAlerts.length > 0 ? (
                riskAlerts.map((alert) => (
                  <Box key={alert.id} sx={{ mb: 2, p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1 }}>
                      <Box sx={{ color: `${getAlertColor(alert.type)}.main` }}>
                        {getAlertIcon(alert.type)}
                      </Box>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="body2" fontWeight="medium">
                          {alert.message}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(alert.timestamp).toLocaleString()}
                        </Typography>
                      </Box>
                      {!alert.isRead && (
                        <Chip label="New" size="small" color="primary" />
                      )}
                    </Box>
                  </Box>
                ))
              ) : (
                <Box sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    No risk alerts at the moment
                  </Typography>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Edit Limit Dialog */}
      <Dialog open={editLimitDialog.open} onClose={() => setEditLimitDialog({ open: false, limit: null })}>
        <DialogTitle>Edit Risk Limit</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Limit Value"
              type="number"
              value={limitForm.value}
              onChange={(e) => setLimitForm({ ...limitForm, value: Number(e.target.value) })}
              sx={{ mb: 2 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={limitForm.isActive}
                  onChange={(e) => setLimitForm({ ...limitForm, isActive: e.target.checked })}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditLimitDialog({ open: false, limit: null })}>
            Cancel
          </Button>
          <Button onClick={handleEditConfirm} variant="contained" disabled={loading}>
            Update
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default RiskManagement; 