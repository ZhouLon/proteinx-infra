import React, { useEffect, useState } from 'react';
import { Typography, Card, Space, Table, Button, message, Popconfirm } from 'antd';
import client from '../../api/client';

const { Title } = Typography;

const Recycle: React.FC = () => {
  const [items, setItems] = useState<Array<{ id: string; name: string; deleted_at: string }>>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await client.get('/recycle/projects');
      setItems(res.data.items || []);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载回收站失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const restore = async (id: string) => {
    try {
      await client.post(`/recycle/projects/${id}/restore`);
      message.success('已还原');
      await load();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '还原失败');
    }
  };
  const remove = async (id: string) => {
    try {
      await client.delete(`/recycle/projects/${id}`);
      message.success('已永久删除');
      await load();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '删除失败');
    }
  };

  return (
    <div>
      <Title level={3} style={{ margin: 0, color: '#1890ff' }}>回收站</Title>
      <Card title="已删除项目">
        <Table
          dataSource={items}
          loading={loading}
          rowKey={(r) => r.id}
          columns={[
            { title: '项目名称', dataIndex: 'name' },
            { title: '删除时间', dataIndex: 'deleted_at' },
            {
              title: '操作',
              render: (_, r) => (
                <Space>
                  <Button type="primary" onClick={() => restore(r.id)}>还原</Button>
                  <Popconfirm title="确认永久删除？此操作不可恢复" onConfirm={() => remove(r.id)}>
                    <Button danger>永久删除</Button>
                  </Popconfirm>
                </Space>
              )
            }
          ]}
        />
      </Card>
    </div>
  );
};

export default Recycle;
