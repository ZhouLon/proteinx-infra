import React from 'react';
import { Card, Row, Col, Progress, Statistic } from 'antd';
// Note: In a real app, use a charting library like @ant-design/plots or recharts
// For now, using placeholders

const TrainingMonitor: React.FC = () => {
  return (
    <div>
      <h2>训练监控</h2>
      <Row gutter={16}>
        <Col span={12}>
          <Card title="实时 Loss">
             <div style={{ height: 200, background: '#f0f2f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               Loss Chart Placeholder
             </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="实时 Accuracy">
            <div style={{ height: 200, background: '#f0f2f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               Accuracy Chart Placeholder
             </div>
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="当前 Epoch" value={45} suffix="/ 100" />
            <Progress percent={45} status="active" />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="GPU 利用率" value={92} suffix="%" />
            <Progress percent={92} status="active" strokeColor="orange" />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="显存使用" value={14.5} suffix="GB / 24 GB" />
            <Progress percent={60} status="normal" />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default TrainingMonitor;
