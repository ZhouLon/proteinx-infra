import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import MainLayout from './layouts/MainLayout';
import ProjectList from './pages/ProjectList';
import DataManagement from './pages/DataManagement';
import TrainingConfig from './pages/TrainingConfig';
import TrainingMonitor from './pages/TrainingMonitor';
import ModelEvaluation from './pages/ModelEvaluation';
import Visualization from './pages/Visualization';
import SystemManagement from './pages/SystemManagement';
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
        <Route path="/dashboard" element={<MainLayout />}>
          <Route index element={<Navigate to="projects" replace />} />
          <Route path="projects" element={<ProjectList />} />
          <Route path="data" element={<DataManagement />} />
          <Route path="training" element={<TrainingConfig />} />
          <Route path="monitor" element={<TrainingMonitor />} />
          <Route path="evaluation" element={<ModelEvaluation />} />
          <Route path="visualization" element={<Visualization />} />
          <Route path="system" element={<SystemManagement />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
