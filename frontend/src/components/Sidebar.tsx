import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  AccountBalance as PositionsIcon,
  ShoppingCart as OrdersIcon,
  Psychology as StrategiesIcon,
  Security as RiskIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  TrendingUp as TradingIcon,
  Search as SearchIcon,
  Assignment as PaperTradingIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Trading', icon: <TradingIcon />, path: '/trading' },
  { text: 'Market Scanner', icon: <SearchIcon />, path: '/market-scanner' },
  { text: 'Positions', icon: <PositionsIcon />, path: '/positions' },
  { text: 'Orders', icon: <OrdersIcon />, path: '/orders' },
  { text: 'Strategies', icon: <StrategiesIcon />, path: '/strategies' },
  { text: 'Risk Management', icon: <RiskIcon />, path: '/risk' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  { text: 'Paper Trading', icon: <PaperTradingIcon />, path: '/paper-trading' },
  { text: 'Strategy Testing', icon: <AssessmentIcon />, path: '/strategy-testing' },
];

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: 'background.paper',
          borderRight: '1px solid rgba(255, 255, 255, 0.12)',
        },
      }}
    >
      <Box sx={{ overflow: 'auto', mt: 8 }}>
        <Box sx={{ p: 2 }}>
          <Typography variant="caption" color="text.secondary">
            NAVIGATION
          </Typography>
        </Box>
        
        <List>
          {menuItems.map((item, index) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
                sx={{
                  mx: 1,
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: location.pathname === item.path ? 'white' : 'inherit',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        <Divider sx={{ my: 2 }} />
        
        <Box sx={{ p: 2 }}>
          <Typography variant="caption" color="text.secondary">
            QUICK ACTIONS
          </Typography>
        </Box>
        
        <List>
          <ListItem disablePadding>
            <ListItemButton sx={{ mx: 1, borderRadius: 1 }}>
              <ListItemText 
                primary="New Order" 
                primaryTypographyProps={{ variant: 'body2' }}
              />
            </ListItemButton>
          </ListItem>
          <ListItem disablePadding>
            <ListItemButton sx={{ mx: 1, borderRadius: 1 }}>
              <ListItemText 
                primary="Emergency Stop" 
                primaryTypographyProps={{ variant: 'body2' }}
              />
            </ListItemButton>
          </ListItem>
        </List>
      </Box>
    </Drawer>
  );
};

export default Sidebar; 