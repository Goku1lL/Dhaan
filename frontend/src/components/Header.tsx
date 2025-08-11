import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Badge,
  Avatar,
  Chip,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  AccountCircle,
  TrendingUp,
  Warning,
} from '@mui/icons-material';

const Header: React.FC = () => {
  const [systemStatus] = React.useState<'online' | 'offline'>('online');
  const [unreadNotifications] = React.useState(3);

  return (
    <AppBar position="static" elevation={0} sx={{ backgroundColor: 'background.paper' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <TrendingUp sx={{ color: 'primary.main', mr: 2, fontSize: 32 }} />
          <Typography variant="h6" component="div" sx={{ color: 'text.primary', fontWeight: 600 }}>
            Dhan Advanced Algo Trading
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* System Status */}
          <Chip
            label={systemStatus === 'online' ? 'System Online' : 'System Offline'}
            color={systemStatus === 'online' ? 'success' : 'error'}
            size="small"
            icon={systemStatus === 'online' ? <TrendingUp /> : <Warning />}
          />

          {/* Notifications */}
          <IconButton color="inherit" size="large">
            <Badge badgeContent={unreadNotifications} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          {/* User Profile */}
          <IconButton color="inherit" size="large">
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
              <AccountCircle />
            </Avatar>
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header; 