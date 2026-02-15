import React from 'react';
import { Typography, Card, Space } from 'antd';

const { Title, Text } = Typography;

const Docs: React.FC = () => {
  return (
    <div>
      <Title level={3} style={{ margin: 0, color: '#1890ff' }}>文档查看</Title>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>在此浏览项目相关文档与说明。</Text>
          <Text type="secondary">后续接入文档列表、搜索与预览功能。</Text>
        </Space>
      </Card>
    </div>
  );
};

export default Docs;
