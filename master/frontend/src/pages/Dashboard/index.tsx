import React, { useEffect, useMemo, useState } from 'react';
import { Layout, Menu, Breadcrumb, theme, Card, Row, Col, Table, Tag, Statistic, Spin, message } from 'antd';
import { DesktopOutlined, FileOutlined, PieChartOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons';
import client from '../../api/client';
import { Job } from '../../api/job';
import { NodeInfo } from '../../api/node';
import { FileInfo } from '../../api/file';

const { Header, Content, Footer, Sider } = Layout;

const items = [
  { key: '1', icon: <PieChartOutlined />, label: '概览' },
  { key: '2', icon: <DesktopOutlined />, label: '项目管理' },
  { key: '3', icon: <UserOutlined />, label: '计算节点池' },
  { key: '4', icon: <TeamOutlined />, label: '用户管理' },
  { key: '9', icon: <FileOutlined />, label: '数据中心' },
];

interface OverviewData {
  nodes_total: number;
  nodes_by_status: Record<string, number>;
  jobs_total: number;
  jobs_by_status: Record<string, number>;
  files_total: number;
  files_size_total: number;
  nodes: NodeInfo[];
  jobs: Job[];
  files: FileInfo[];
}

const Dashboard: React.FC = () => {
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<OverviewData | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const res = await client.get<OverviewData>('/overview');
        setOverview(res.data);
      } catch (error: any) {
        message.error(error?.response?.data?.detail || '加载概览数据失败');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  const nodes = overview?.nodes ?? [];
  const jobs = overview?.jobs ?? [];
  const files = overview?.files ?? [];

  const jobColumns = useMemo(() => [
    { title: '任务名称', dataIndex: 'name' },
    { title: '状态', dataIndex: 'status', render: (value: Job['status']) => {
      const color = value === 'running' ? 'processing' : value === 'completed' ? 'success' : value === 'failed' ? 'error' : value === 'cancelled' ? 'default' : 'warning';
      return <Tag color={color}>{value}</Tag>;
    }},
    { title: '节点', dataIndex: 'node_id', render: (value?: string) => value || '-' },
    { title: '创建时间', dataIndex: 'created_at' },
  ], []);

  const nodeColumns = useMemo(() => [
    { title: '节点', dataIndex: 'hostname' },
    { title: 'IP', dataIndex: 'ip' },
    { title: '状态', dataIndex: 'status', render: (value: NodeInfo['status']) => {
      const color = value === 'idle' ? 'success' : value === 'busy' ? 'processing' : 'default';
      return <Tag color={color}>{value}</Tag>;
    }},
    { title: 'CPU', render: (_: any, record: NodeInfo) => `${record.resources.cpu_usage}%` },
    { title: '内存', render: (_: any, record: NodeInfo) => `${record.resources.memory_usage}%` },
    { title: 'GPU', render: (_: any, record: NodeInfo) => record.resources.gpu_info || '-' },
  ], []);

  const fileColumns = useMemo(() => [
    { title: '文件名', dataIndex: 'name' },
    { title: '路径', dataIndex: 'path' },
    { title: '大小', dataIndex: 'size', render: (value: number) => `${(value / 1024).toFixed(2)} KB` },
    { title: '更新时间', dataIndex: 'updated_at' },
  ], []);

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
          <div style={{ padding: 24, minHeight: 360, background: colorBgContainer, borderRadius: borderRadiusLG }}>
            {loading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
                <Spin size="large" tip="加载概览数据..." />
              </div>
            ) : (
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} lg={6}>
                  <Card bordered={false}>
                    <Statistic title="计算节点总数" value={overview?.nodes_total ?? 0} />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card bordered={false}>
                    <Statistic title="任务总数" value={overview?.jobs_total ?? 0} />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card bordered={false}>
                    <Statistic title="数据文件数" value={overview?.files_total ?? 0} />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card bordered={false}>
                    <Statistic title="数据总大小 (KB)" value={(overview?.files_size_total ?? 0) / 1024} precision={2} />
                  </Card>
                </Col>

                <Col span={24}>
                  <Card title="最近任务" bordered={false}>
                    <Table dataSource={jobs} columns={jobColumns} rowKey="id" pagination={{ pageSize: 5 }} />
                  </Card>
                </Col>

                <Col span={24}>
                  <Card title="计算节点" bordered={false}>
                    <Table dataSource={nodes} columns={nodeColumns} rowKey="id" pagination={{ pageSize: 5 }} />
                  </Card>
                </Col>

                <Col span={24}>
                  <Card title="数据中心" bordered={false}>
                    <Table dataSource={files} columns={fileColumns} rowKey="path" pagination={{ pageSize: 5 }} />
                  </Card>
                </Col>
              </Row>
            )}
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
