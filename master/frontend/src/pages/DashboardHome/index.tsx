import React, { useEffect, useState } from 'react';
import { Card, Typography, Row, Col, Button, Space, Divider } from 'antd';
import { 
  RocketOutlined, 
  CloudUploadOutlined, 
  MonitorOutlined, 
  ReadOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser } from '../../api/auth';

const { Title, Paragraph, Text } = Typography;

const DashboardHome: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>('研究员');

  useEffect(() => {
    const run = async () => {
      try {
        const me = await getCurrentUser();
        setUsername(me.username || '研究员');
      } catch {
        setUsername('研究员');
      }
    };
    run();
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 6) return '夜深了，注意休息';
    if (hour < 12) return '早上好';
    if (hour < 18) return '下午好';
    return '晚上好';
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* Hero Section */}
      <div style={{ 
        marginBottom: 48, 
        textAlign: 'center', 
        padding: '48px 24px', 
        background: 'linear-gradient(135deg, #e6f7ff 0%, #ffffff 100%)', 
        borderRadius: 16,
        border: '1px solid #bae7ff'
      }}>
        <Title level={2} style={{ color: '#1890ff', marginBottom: 16 }}>
          {getGreeting()}，{username}
        </Title>
        <Paragraph style={{ fontSize: 18, color: '#595959', maxWidth: 800, margin: '0 auto 32px' }}>
          欢迎回到 <Text strong style={{ color: '#1890ff' }}>ProteinX Infra</Text>。
          这是一个专为生物数据 AI 训练设计的分布式计算平台。
          在这里，您可以轻松管理海量数据，调度高性能计算节点，加速您的科学探索。
        </Paragraph>
        <Space size="large">
          <Button type="primary" size="large" icon={<RocketOutlined />} onClick={() => navigate('/dashboard/projects')}>
            开始新项目
          </Button>
          <Button size="large" icon={<ReadOutlined />} onClick={() => window.open('https://github.com/your-repo/docs', '_blank')}>
            查看文档
          </Button>
        </Space>
      </div>

      {/* Quick Access Cards */}
      <Row gutter={[24, 24]}>
        <Col xs={24} md={8}>
          <Card 
            hoverable 
            style={{ height: '100%', borderRadius: 12 }}
            onClick={() => navigate('/dashboard/projects')}
          >
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <ExperimentOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
              <Title level={4}>项目管理</Title>
              <Paragraph type="secondary">
                创建和管理您的生物信息学研究项目，追踪实验进度。
              </Paragraph>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card 
            hoverable 
            style={{ height: '100%', borderRadius: 12 }}
            onClick={() => navigate('/dashboard/data')}
          >
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <CloudUploadOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
              <Title level={4}>数据中心</Title>
              <Paragraph type="secondary">
                上传序列与结构数据，支持 FASTA, PDB 等多种格式的预览与管理。
              </Paragraph>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card 
            hoverable 
            style={{ height: '100%', borderRadius: 12 }}
            onClick={() => navigate('/dashboard/monitor')}
          >
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <MonitorOutlined style={{ fontSize: 48, color: '#faad14', marginBottom: 16 }} />
              <Title level={4}>训练监控</Title>
              <Paragraph type="secondary">
                实时监控计算节点资源状态，可视化模型训练 Loss 与 Accuracy 曲线。
              </Paragraph>
            </div>
          </Card>
        </Col>
      </Row>

      <Divider style={{ margin: '48px 0' }} />

      {/* System Status Summary (Mock) */}
      <Row gutter={[24, 24]}>
        <Col xs={24} md={24}>
          <Card title="最新公告" bordered={false} style={{ borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
             <ul style={{ paddingLeft: 20, margin: 0 }}>
               <li style={{ marginBottom: 8 }}><Text type="secondary">[2026-02-18]</Text> 本系统正在添加队列功能。</li>
               <li><Text type="secondary">[2026-01-30]</Text> 欢迎使用 ProteinX Infra v1.0！</li>
             </ul>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardHome;
