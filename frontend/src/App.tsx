import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import Login from './pages/Login/Login';
import SetupWorkDir from './pages/Setup/SetupWorkDir';
import Dashboard from './pages/Dashboard';
import { getSystemStatus } from './api/system';

const App: React.FC = () => {
  const [initializing, setInitializing] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);

  useEffect(() => {
    // Check system status on load
    const checkStatus = async () => {
      try {
        const status = await getSystemStatus();
        // If workdir is not set, we need setup
        if (!status.initialized) {
          setNeedsSetup(true);
        }
      } catch (error) {
        // Fallback for demo/dev without backend: 
        // Assume needs setup for first time demo
        console.log("Backend not reachable, defaulting to Setup mode for demo");
        setNeedsSetup(true);
      } finally {
        setInitializing(false);
      }
    };
    checkStatus();
  }, []);

  if (initializing) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="正在连接管理节点..." />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/" 
          element={needsSetup ? <Navigate to="/setup" replace /> : <Navigate to="/login" replace />} 
        />
        <Route path="/setup" element={<SetupWorkDir />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
