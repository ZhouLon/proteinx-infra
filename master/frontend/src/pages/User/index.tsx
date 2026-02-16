import React, { useEffect, useState } from 'react';
import { Card, Avatar, Typography, Button, Space } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { getCurrentUser } from '../../api/auth';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const UserPage: React.FC = () => {
  const [username, setUsername] = useState<string>('用户');
  const navigate = useNavigate();
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
    <Card>
      <Space align="center" size={16}>
        <Avatar size={64} icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
        <div>
          <Title level={4} style={{ margin: 0 }}>{username}</Title>
          <Text type="secondary">管理员</Text>
        </div>
      </Space>
      <div style={{ marginTop: 24 }}>
        <Button
          danger
          onClick={() => {
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('refresh_token');
            navigate('/login');
          }}
        >
          退出登录
        </Button>
      </div>
    </Card>
  );
};

export default UserPage;
