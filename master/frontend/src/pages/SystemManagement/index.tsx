import React from 'react';
import { Table, Tag, Card, Row, Col, Statistic } from 'antd';

const SystemManagement: React.FC = () => {
  const nodeColumns = [
    { title: '节点名称', dataIndex: 'name', key: 'name' },
    { title: 'IP 地址', dataIndex: 'ip', key: 'ip' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status: string) => (
      <Tag color={status === 'Online' ? 'green' : 'red'}>{status}</Tag>
    )},
    { title: 'CPU 使用率', dataIndex: 'cpu', key: 'cpu' },
    { title: 'GPU 使用率', dataIndex: 'gpu', key: 'gpu' },
  ];

  const nodeData = [
    { key: '1', name: 'Worker-01', ip: '192.168.1.101', status: 'Online', cpu: '45%', gpu: '80%' },
    { key: '2', name: 'Worker-02', ip: '192.168.1.102', status: 'Busy', cpu: '90%', gpu: '99%' },
    { key: '3', name: 'Worker-03', ip: '192.168.1.103', status: 'Offline', cpu: '-', gpu: '-' },
  ];

  return (
    <div>
      <h2>系统管理</h2>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="在线节点" value={2} suffix="/ 3" valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="总算力 (TFLOPS)" value={150} />
          </Card>
        </Col>
      </Row>
      <Card title="计算节点池">
        <Table dataSource={nodeData} columns={nodeColumns} />
      </Card>
    </div>
  );
};

export default SystemManagement;
