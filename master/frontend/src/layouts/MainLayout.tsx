import React, { useState } from 'react';
import { Layout, Menu, theme, Breadcrumb } from 'antd';
import {
  DesktopOutlined,
  FileOutlined,
  TeamOutlined,
  ExperimentOutlined,
  LineChartOutlined,
  AreaChartOutlined,
  RadarChartOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';

const { Header, Content, Footer, Sider } = Layout;

const MainLayout: React.FC = () => {
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const items = [
    { key: '/dashboard/projects', icon: <DesktopOutlined />, label: '项目首页' },
    { key: '/dashboard/data', icon: <FileOutlined />, label: '数据管理' },
    { key: '/dashboard/training', icon: <ExperimentOutlined />, label: '训练配置' },
    { key: '/dashboard/monitor', icon: <LineChartOutlined />, label: '训练监控' },
    { key: '/dashboard/evaluation', icon: <RadarChartOutlined />, label: '模型评估' },
    { key: '/dashboard/visualization', icon: <AreaChartOutlined />, label: '可视化' },
    { key: '/dashboard/system', icon: <TeamOutlined />, label: '系统管理' },
  ];

  const handleMenuClick = (e: { key: string }) => {
    navigate(e.key);
  };

  const breadcrumbItems = location.pathname.split('/').filter(i => i).map((item, index, arr) => {
    const url = `/${arr.slice(0, index + 1).join('/')}`;
    const menuItem = items.find(i => i.key === url);
    return { title: menuItem ? menuItem.label : item };
  });

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
        <div className="demo-logo-vertical" style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)' }} />
        <Menu 
          theme="dark" 
          defaultSelectedKeys={['/dashboard/projects']} 
          selectedKeys={[location.pathname]}
          mode="inline" 
          items={items} 
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }} />
        <Content style={{ margin: '0 16px' }}>
          <Breadcrumb style={{ margin: '16px 0' }} items={breadcrumbItems} />
          <div style={{ padding: 24, minHeight: 360, background: colorBgContainer, borderRadius: borderRadiusLG }}>
            <Outlet />
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          ProteinX Infra Master ©2026 Created by Research Team
        </Footer>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
