import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';
import Dashboard from './components/Dashboard';
import Trading from './components/Trading';
import Positions from './components/Positions';
import Orders from './components/Orders';
import Strategies from './components/Strategies';
import RiskManagement from './components/RiskManagement';
import Analytics from './components/Analytics';
import Settings from './components/Settings';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import MarketScanner from './components/MarketScanner';
import PaperTrading from './components/PaperTrading';
import StrategyTesting from './components/StrategyTesting';
import './App.css';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00c853',
    },
    secondary: {
      main: '#ff6f00',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', height: '100vh' }}>
          <Sidebar />
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
            <Header />
            <Box component="main" sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/trading" element={<Trading />} />
                <Route path="/positions" element={<Positions />} />
                <Route path="/orders" element={<Orders />} />
                <Route path="/strategies" element={<Strategies />} />
                <Route path="/risk" element={<RiskManagement />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/market-scanner" element={<MarketScanner />} />
                <Route path="/paper-trading" element={<PaperTrading />} />
        <Route path="/strategy-testing" element={<StrategyTesting />} />
              </Routes>
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
