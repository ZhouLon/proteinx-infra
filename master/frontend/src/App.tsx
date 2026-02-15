import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import MainLayout from './layouts/MainLayout';
import DashboardHome from './pages/DashboardHome';
import ProjectList from './pages/ProjectList';
import { ProjectOverview, ProjectBuild, ProjectModelBuild, ProjectTrain, ProjectCompare } from './pages/ProjectDetail';
import DataManagement from './pages/DataManagement';
import TrainingMonitor from './pages/TrainingMonitor';
import Docs from './pages/Docs';
import Recycle from './pages/Recycle';
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
          <Route index element={<DashboardHome />} />
          <Route path="projects" element={<ProjectList />} />
          <Route path="projects/:pid">
            <Route index element={<Navigate to="overview" replace />} />
            <Route path="overview" element={<ProjectOverview />} />
            <Route path="build" element={<ProjectBuild />} />
            <Route path="model-build" element={<ProjectModelBuild />} />
            <Route path="train" element={<ProjectTrain />} />
            <Route path="compare" element={<ProjectCompare />} />
          </Route>
          <Route path="data" element={<DataManagement />} />
          <Route path="monitor" element={<TrainingMonitor />} />
          <Route path="docs" element={<Docs />} />
          <Route path="recycle" element={<Recycle />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
