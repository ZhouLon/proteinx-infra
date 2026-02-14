import React from 'react';
import { Layout, Menu, Breadcrumb, theme } from 'antd';
import { 
  DesktopOutlined, 
  FileOutlined, 
  PieChartOutlined, 
  TeamOutlined, 
  UserOutlined 
} from '@ant-design/icons';

const { Header, Content, Footer, Sider } = Layout;

const items = [
  { key: '1', icon: <PieChartOutlined />, label: '概览' },
  { key: '2', icon: <DesktopOutlined />, label: '项目管理' },
  { key: '3', icon: <UserOutlined />, label: '计算节点池' },
  { key: '4', icon: <TeamOutlined />, label: '用户管理' },
  { key: '9', icon: <FileOutlined />, label: '数据中心' },
];

const Dashboard: React.FC = () => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible breakpoint="lg">
        <div className="demo-logo-vertical" style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)' }} />
        <Menu theme="dark" defaultSelectedKeys={['1']} mode="inline" items={items} />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }} />
        <Content style={{ margin: '0 16px' }}>
          <Breadcrumb style={{ margin: '16px 0' }}>
            <Breadcrumb.Item>首页</Breadcrumb.Item>
            <Breadcrumb.Item>概览</Breadcrumb.Item>
          </Breadcrumb>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            欢迎使用 ProteinX Infra Master 管理平台。
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          ProteinX Infra Master ©2026 Created by Research Team
        </Footer>
      </Layout>
    </Layout>
  );
};

export default Dashboard;
