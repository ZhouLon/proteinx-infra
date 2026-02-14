import React, { useState } from 'react';
import { Card, Form, Input, Button, Typography, message, Checkbox } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);
    console.log('Login values:', values);
    
    // Simulate Login API Call
    setTimeout(() => {
      setLoading(false);
      // Mock validation
      if (values.username === 'admin' && values.password === 'admin') {
         message.success('登录成功');
         navigate('/dashboard');
      } else {
         message.error('用户名或密码错误 (默认 admin/admin)');
      }
    }, 1000);
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1890ff 0%, #001529 100%)' 
    }}>
      <Card 
        style={{ width: 400, borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }} 
        bordered={false}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          {/* Logo placeholder */}
          <div style={{ 
            width: 48, height: 48, background: '#1890ff', borderRadius: '50%', 
            margin: '0 auto 16px', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white', fontWeight: 'bold', fontSize: 24
          }}>P</div>
          <Title level={3}>ProteinX Infra Master</Title>
          <Text type="secondary">生物数据分布式训练平台</Text>
        </div>

        <Form
          name="login"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>记住我</Checkbox>
            </Form.Item>
            <a style={{ float: 'right' }} href="">忘记密码</a>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登录
            </Button>
          </Form.Item>
          
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>v1.0.0 (Master Node)</Text>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Login;
