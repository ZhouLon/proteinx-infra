import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import MainLayout from './layouts/MainLayout';
import DashboardHome from './pages/DashboardHome';
import ProjectList from './pages/ProjectList';
import { ProjectOverview, ProjectDataBuild, ProjectModelBuild, ProjectTrain, ProjectCompare, ProjectDatasets, ProjectDatasetDetail, ProjectExperiments, ProjectExperimentDetail } from './pages/ProjectDetail';
import DataManagement from './pages/DataManagement';
import TrainingMonitor from './pages/TrainingMonitor';
import Docs from './pages/Docs';
import Recycle from './pages/Recycle';
import { existsUser } from './api/auth';
import { Spin } from 'antd';
import UserPage from './pages/User';

const App: React.FC = () => {
  const [checking, setChecking] = useState(true);
  const [hasUser, setHasUser] = useState<boolean | null>(null);
  const [authed, setAuthed] = useState<boolean>(!!sessionStorage.getItem('access_token'));

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

  useEffect(() => {
    const handler = () => {
      setAuthed(!!sessionStorage.getItem('access_token'));
    };
    window.addEventListener('px-auth', handler as any);
    return () => {
      window.removeEventListener('px-auth', handler as any);
    };
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
        <Route path="/" element={<Navigate to={authed ? "/dashboard" : (hasUser ? "/login" : "/register")} replace />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={authed ? <MainLayout /> : <Navigate to="/login" replace />}>
          <Route index element={<DashboardHome />} />
          <Route path="projects" element={<ProjectList />} />
          <Route path="user" element={<UserPage />} />
          <Route path="projects/:pid">
            <Route index element={<Navigate to="overview" replace />} />
            <Route path="overview" element={<ProjectOverview />} />
            <Route path="data-build" element={<ProjectDataBuild />} />
            <Route path="datasets" element={<ProjectDatasets />} />
            <Route path="datasets/:did" element={<ProjectDatasetDetail />} />
            <Route path="model-build" element={<ProjectModelBuild />} />
            <Route path="train" element={<ProjectTrain />} />
            <Route path="experiments" element={<ProjectExperiments />} />
            <Route path="experiments/:experimentId" element={<ProjectExperimentDetail />} />
            <Route path="compare" element={<ProjectCompare />} />
          </Route>
          <Route path="data" element={<DataManagement />} />
          <Route path="monitor" element={<TrainingMonitor />} />
          <Route path="docs" element={<Docs />} />
          <Route path="recycle" element={<Recycle />} />
        </Route>
        <Route path="*" element={<Navigate to={authed ? "/dashboard" : "/login"} replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
