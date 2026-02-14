import React from 'react';
import { Card, Row, Col, Table } from 'antd';

const ModelEvaluation: React.FC = () => {
  const columns = [
    { title: '模型名称', dataIndex: 'name', key: 'name' },
    { title: 'Accuracy', dataIndex: 'accuracy', key: 'accuracy' },
    { title: 'Precision', dataIndex: 'precision', key: 'precision' },
    { title: 'Recall', dataIndex: 'recall', key: 'recall' },
    { title: 'F1 Score', dataIndex: 'f1', key: 'f1' },
  ];

  const data = [
    { key: '1', name: 'Model-v1.0', accuracy: '94.5%', precision: '0.92', recall: '0.95', f1: '0.93' },
    { key: '2', name: 'Model-v1.1', accuracy: '96.2%', precision: '0.95', recall: '0.96', f1: '0.95' },
  ];

  return (
    <div>
      <h2>模型评估</h2>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="性能对比 (Radar Chart)">
             <div style={{ height: 300, background: '#f0f2f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               Radar Chart Placeholder
             </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="混淆矩阵 (Confusion Matrix)">
             <div style={{ height: 300, background: '#f0f2f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               Confusion Matrix Placeholder
             </div>
          </Card>
        </Col>
      </Row>
      <Table dataSource={data} columns={columns} />
    </div>
  );
};

export default ModelEvaluation;
