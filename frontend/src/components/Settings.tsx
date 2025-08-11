import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, FormControl, InputLabel, Select, MenuItem,
  Button, Switch, FormControlLabel, TextField, Divider, Alert, Snackbar,
  Tabs, Tab, Chip, IconButton, Tooltip, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Settings as SettingsIcon, Notifications, Security, AccountCircle, Refresh,
  Save, Cancel, ExpandMore, Language, Palette, Speed, Storage, Api
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface UserSettings {
  username: string;
  email: string;
  timezone: string;
  currency: string;
  language: string;
}

interface TradingSettings {
  defaultOrderSize: number;
  maxOrderSize: number;
  enableStopLoss: boolean;
  enableTakeProfit: boolean;
  defaultStopLoss: number;
  defaultTakeProfit: number;
  tradingHours: {
    start: string;
    end: string;
  };
}

interface NotificationSettings {
  emailNotifications: boolean;
  pushNotifications: boolean;
  tradeAlerts: boolean;
  riskAlerts: boolean;
  systemAlerts: boolean;
  dailyReports: boolean;
}

interface SystemSettings {
  theme: 'light' | 'dark' | 'auto';
  refreshInterval: number;
  maxLogRetention: number;
  enableDebugMode: boolean;
  enableTelemetry: boolean;
}

const Settings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Form states
  const [userSettings, setUserSettings] = useState<UserSettings>({
    username: 'trader123',
    email: 'trader@example.com',
    timezone: 'UTC',
    currency: 'USD',
    language: 'en'
  });

  const [tradingSettings, setTradingSettings] = useState<TradingSettings>({
    defaultOrderSize: 1000,
    maxOrderSize: 10000,
    enableStopLoss: true,
    enableTakeProfit: true,
    defaultStopLoss: 5,
    defaultTakeProfit: 10,
    tradingHours: {
      start: '09:00',
      end: '16:00'
    }
  });

  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings>({
    emailNotifications: true,
    pushNotifications: true,
    tradeAlerts: true,
    riskAlerts: true,
    systemAlerts: false,
    dailyReports: true
  });

  const [systemSettings, setSystemSettings] = useState<SystemSettings>({
    theme: 'auto',
    refreshInterval: 30,
    maxLogRetention: 30,
    enableDebugMode: false,
    enableTelemetry: true
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSaveSettings = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Save settings logic here
      // await tradingAPI.updateSettings({
      //   user: userSettings,
      //   trading: tradingSettings,
      //   notifications: notificationSettings,
      //   system: systemSettings
      // });

      setSnackbar({
        open: true,
        message: 'Settings saved successfully!',
        severity: 'success'
      });

    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to save settings. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResetSettings = () => {
    // Reset to default values
    setUserSettings({
      username: 'trader123',
      email: 'trader@example.com',
      timezone: 'UTC',
      currency: 'USD',
      language: 'en'
    });

    setTradingSettings({
      defaultOrderSize: 1000,
      maxOrderSize: 10000,
      enableStopLoss: true,
      enableTakeProfit: true,
      defaultStopLoss: 5,
      defaultTakeProfit: 10,
      tradingHours: {
        start: '09:00',
        end: '16:00'
      }
    });

    setNotificationSettings({
      emailNotifications: true,
      pushNotifications: true,
      tradeAlerts: true,
      riskAlerts: true,
      systemAlerts: false,
      dailyReports: true
    });

    setSystemSettings({
      theme: 'auto',
      refreshInterval: 30,
      maxLogRetention: 30,
      enableDebugMode: false,
      enableTelemetry: true
    });

    setSnackbar({
      open: true,
      message: 'Settings reset to defaults!',
      severity: 'success'
    });
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Cancel />}
            onClick={handleResetSettings}
            disabled={loading}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSaveSettings}
            disabled={loading}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      <Card sx={{ backgroundColor: 'background.paper' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
            <Tab icon={<AccountCircle />} label="User" />
            <Tab icon={<Speed />} label="Trading" />
            <Tab icon={<Notifications />} label="Notifications" />
            <Tab icon={<SettingsIcon />} label="System" />
          </Tabs>
        </Box>

        {/* User Settings Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Username"
                value={userSettings.username}
                onChange={(e) => setUserSettings({ ...userSettings, username: e.target.value })}
                margin="normal"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={userSettings.email}
                onChange={(e) => setUserSettings({ ...userSettings, email: e.target.value })}
                margin="normal"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={userSettings.timezone}
                  label="Timezone"
                  onChange={(e) => setUserSettings({ ...userSettings, timezone: e.target.value })}
                >
                  <MenuItem value="UTC">UTC</MenuItem>
                  <MenuItem value="EST">EST (UTC-5)</MenuItem>
                  <MenuItem value="PST">PST (UTC-8)</MenuItem>
                  <MenuItem value="IST">IST (UTC+5:30)</MenuItem>
                  <MenuItem value="JST">JST (UTC+9)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Currency</InputLabel>
                <Select
                  value={userSettings.currency}
                  label="Currency"
                  onChange={(e) => setUserSettings({ ...userSettings, currency: e.target.value })}
                >
                  <MenuItem value="USD">USD ($)</MenuItem>
                  <MenuItem value="EUR">EUR (€)</MenuItem>
                  <MenuItem value="GBP">GBP (£)</MenuItem>
                  <MenuItem value="INR">INR (₹)</MenuItem>
                  <MenuItem value="JPY">JPY (¥)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Language</InputLabel>
                <Select
                  value={userSettings.language}
                  label="Language"
                  onChange={(e) => setUserSettings({ ...userSettings, language: e.target.value })}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                  <MenuItem value="fr">French</MenuItem>
                  <MenuItem value="de">German</MenuItem>
                  <MenuItem value="hi">Hindi</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Trading Settings Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Default Order Size"
                type="number"
                value={tradingSettings.defaultOrderSize}
                onChange={(e) => setTradingSettings({ ...tradingSettings, defaultOrderSize: Number(e.target.value) })}
                margin="normal"
                InputProps={{
                  endAdornment: <Typography variant="caption">USD</Typography>
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Maximum Order Size"
                type="number"
                value={tradingSettings.maxOrderSize}
                onChange={(e) => setTradingSettings({ ...tradingSettings, maxOrderSize: Number(e.target.value) })}
                margin="normal"
                InputProps={{
                  endAdornment: <Typography variant="caption">USD</Typography>
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Default Stop Loss"
                type="number"
                value={tradingSettings.defaultStopLoss}
                onChange={(e) => setTradingSettings({ ...tradingSettings, defaultStopLoss: Number(e.target.value) })}
                margin="normal"
                InputProps={{
                  endAdornment: <Typography variant="caption">%</Typography>
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Default Take Profit"
                type="number"
                value={tradingSettings.defaultTakeProfit}
                onChange={(e) => setTradingSettings({ ...tradingSettings, defaultTakeProfit: Number(e.target.value) })}
                margin="normal"
                InputProps={{
                  endAdornment: <Typography variant="caption">%</Typography>
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Trading Start Time"
                type="time"
                value={tradingSettings.tradingHours.start}
                onChange={(e) => setTradingSettings({
                  ...tradingSettings,
                  tradingHours: { ...tradingSettings.tradingHours, start: e.target.value }
                })}
                margin="normal"
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Trading End Time"
                type="time"
                value={tradingSettings.tradingHours.end}
                onChange={(e) => setTradingSettings({
                  ...tradingSettings,
                  tradingHours: { ...tradingSettings.tradingHours, end: e.target.value }
                })}
                margin="normal"
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={tradingSettings.enableStopLoss}
                    onChange={(e) => setTradingSettings({ ...tradingSettings, enableStopLoss: e.target.checked })}
                  />
                }
                label="Enable Automatic Stop Loss"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={tradingSettings.enableTakeProfit}
                    onChange={(e) => setTradingSettings({ ...tradingSettings, enableTakeProfit: e.target.checked })}
                  />
                }
                label="Enable Automatic Take Profit"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notification Settings Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Notification Channels
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.emailNotifications}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, emailNotifications: e.target.checked })}
                  />
                }
                label="Email Notifications"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.pushNotifications}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, pushNotifications: e.target.checked })}
                  />
                }
                label="Push Notifications"
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Alert Types
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.tradeAlerts}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, tradeAlerts: e.target.checked })}
                  />
                }
                label="Trade Execution Alerts"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.riskAlerts}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, riskAlerts: e.target.checked })}
                  />
                }
                label="Risk Management Alerts"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.systemAlerts}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, systemAlerts: e.target.checked })}
                  />
                }
                label="System Status Alerts"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.dailyReports}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, dailyReports: e.target.checked })}
                  />
                }
                label="Daily Performance Reports"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* System Settings Tab */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Theme</InputLabel>
                <Select
                  value={systemSettings.theme}
                  label="Theme"
                  onChange={(e) => setSystemSettings({ ...systemSettings, theme: e.target.value as any })}
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="auto">Auto (System)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Data Refresh Interval</InputLabel>
                <Select
                  value={systemSettings.refreshInterval}
                  label="Data Refresh Interval"
                  onChange={(e) => setSystemSettings({ ...systemSettings, refreshInterval: Number(e.target.value) })}
                >
                  <MenuItem value={15}>15 seconds</MenuItem>
                  <MenuItem value={30}>30 seconds</MenuItem>
                  <MenuItem value={60}>1 minute</MenuItem>
                  <MenuItem value={300}>5 minutes</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Log Retention Period"
                type="number"
                value={systemSettings.maxLogRetention}
                onChange={(e) => setSystemSettings({ ...systemSettings, maxLogRetention: Number(e.target.value) })}
                margin="normal"
                InputProps={{
                  endAdornment: <Typography variant="caption">days</Typography>
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={systemSettings.enableDebugMode}
                    onChange={(e) => setSystemSettings({ ...systemSettings, enableDebugMode: e.target.checked })}
                  />
                }
                label="Enable Debug Mode"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={systemSettings.enableTelemetry}
                    onChange={(e) => setSystemSettings({ ...systemSettings, enableTelemetry: e.target.checked })}
                  />
                }
                label="Enable Usage Analytics"
              />
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

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

export default Settings; 