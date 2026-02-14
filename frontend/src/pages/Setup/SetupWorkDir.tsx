import React, { useState } from 'react';
import { Card, Form, Input, Button, Typography, message, Steps } from 'antd';
import { FolderOpenOutlined, CloudServerOutlined } from '@ant-design/icons';
import { setupWorkDir } from '../../api/system';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph, Text } = Typography;

const SetupWorkDir: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { workdir: string }) => {
    setLoading(true);
    try {
      await setupWorkDir(values.workdir);
      message.success('系统初始化成功！工作目录已创建。');
      // Navigate to login after successful setup
      navigate('/login');
    } catch (error) {
      console.error(error);
      // In a real scenario, we would show the error from backend
      message.error('初始化失败，请检查路径权限或后端连接。');
      
      // MOCK: For demo purposes if backend is missing, let's simulate success after 1s
      // setTimeout(() => {
      //   message.success('（模拟）初始化成功！');
      //   navigate('/login');
      // }, 1000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      backgroundColor: '#f0f2f5' 
    }}>
      <Card style={{ width: 600, padding: 24 }} bordered={false} hoverable>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <CloudServerOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          <Title level={2} style={{ margin: '16px 0' }}>ProteinX Infra Master 初始化</Title>
          <Paragraph type="secondary">
            这是您第一次启动管理节点。请配置数据存储位置。
          </Paragraph>
        </div>

        <Steps 
          current={0} 
          items={[
            { title: '配置存储', description: '设置工作目录' },
            { title: '管理员设置', description: '即将进行' },
            { title: '完成', description: '开始使用' },
          ]}
          style={{ marginBottom: 40 }}
        />

        <Form
          name="setup_workdir"
          layout="vertical"
          onFinish={onFinish}
          initialValues={{ workdir: '/data/proteinx' }}
        >
          <Form.Item
            label="工作目录 (WorkDir)"
            name="workdir"
            tooltip="服务器上的绝对路径。系统将在此目录下创建 proteinx_infra_master 文件夹以存储所有持久化数据。"
            rules={[
              { required: true, message: '请输入服务器上的工作目录路径' },
              { pattern: /^(\/|[a-zA-Z]:\\)/, message: '请输入有效的绝对路径' }
            ]}
          >
            <Input 
              prefix={<FolderOpenOutlined />} 
              placeholder="/data/proteinx 或 D:\ProteinXWorkdir" 
              size="large" 
            />
          </Form.Item>

          <div style={{ backgroundColor: '#e6f7ff', padding: '12px', borderRadius: '4px', marginBottom: '24px' }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              <span style={{ fontWeight: 'bold' }}>注意：</span> 
              系统会自动在该路径下创建 <code>proteinx_infra_master</code> 子目录。
              所有上传的原始数据、训练日志、模型产物都将保存在此，不会占用 Docker 容器空间。
            </Text>
          </div>

          <Form.Item>
            <Button type="primary" htmlType="submit" size="large" block loading={loading}>
              初始化并创建目录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default SetupWorkDir;
