import React, { useEffect, useState } from 'react';
import { Layout, Menu, theme, Typography, Avatar } from 'antd';
import {
  DesktopOutlined,
  FileOutlined,
  LineChartOutlined,
  UserOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { getCurrentUser } from '../api/auth';

const { Header, Content, Footer, Sider } = Layout;
const { Title, Text } = Typography;

const MainLayout: React.FC = () => {
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [username, setUsername] = useState<string>('用户');

  const projectDetail = location.pathname.startsWith('/dashboard/projects/') && location.pathname !== '/dashboard/projects';
  const items = projectDetail ? [
    { key: `/dashboard/projects/${location.pathname.split('/').slice(-1)[0]}`, icon: <DesktopOutlined />, label: '项目特别页' },
    { key: '/dashboard/projects', icon: <FileOutlined />, label: '返回项目首页' },
  ] : [
    { key: '/dashboard/projects', icon: <DesktopOutlined />, label: '项目首页' },
    { key: '/dashboard/data', icon: <FileOutlined />, label: '数据管理' },
    { key: '/dashboard/monitor', icon: <LineChartOutlined />, label: '训练监控' },
  ];

  const handleMenuClick = (e: { key: string }) => {
    navigate(e.key);
  };

  useEffect(() => {
    const run = async () => {
      try {
        const me = await getCurrentUser();
        setUsername(me.username || '用户');
      } catch {
        setUsername('用户');
      }
    };
    run();
  }, []);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: collapsed ? 'center' : 'flex-start',
          gap: 12, 
          padding: '24px 16px',
          transition: 'all 0.2s'
        }}>
          <Avatar size={collapsed ? 32 : 48} icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
          {!collapsed && (
            <Text style={{ color: '#fff', fontSize: '18px', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {username}
            </Text>
          )}
        </div>
        <Menu 
          theme="dark" 
          defaultSelectedKeys={['/dashboard/projects']} 
          selectedKeys={[projectDetail ? `/dashboard/projects/${location.pathname.split('/').slice(-1)[0]}` : location.pathname]}
          mode="inline" 
          items={items} 
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: 0, 
          background: colorBgContainer, 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          boxShadow: '0 2px 8px #f0f1f2',
          zIndex: 1
        }}>
          <Title level={3} style={{ margin: 0, color: '#1890ff', letterSpacing: '1px' }}>
            ProteinX INFRA Master
          </Title>
        </Header>
        <Content style={{ margin: '16px 16px' }}>
          <div style={{ padding: 24, minHeight: 360, background: colorBgContainer, borderRadius: borderRadiusLG }}>
            <Outlet />
          </div>
        </Content>
        <Footer style={{ textAlign: 'center', color: '#8c8c8c' }}>
          ProteinX Infra Master ©2026 Created by Research Team
        </Footer>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
