import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login/Login';
import Dashboard from './pages/Dashboard';
import Register from './pages/Register/Register';
import { existsUser } from './api/auth';
import { Spin } from 'antd';

const App: React.FC = () => {
  const [checking, setChecking] = useState(true);
  const [hasUser, setHasUser] = useState<boolean | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const res = await existsUser();
        setHasUser(res.exists);
      } catch {
        setHasUser(true);
      } finally {
        setChecking(false);
      }
    };
    run();
  }, []);

  if (checking) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="正在检查用户状态..." />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to={hasUser ? "/login" : "/register"} replace />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
