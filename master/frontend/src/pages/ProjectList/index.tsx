import React from 'react';
import { Card, Col, Row, Statistic, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const ProjectList: React.FC = () => {
  // Mock data
  const projects = [
    { key: '1', name: 'AlphaFold-P1', description: 'Protein Structure Prediction v1', createdAt: '2025-01-01', dataSize: '1.2 GB' },
    { key: '2', name: 'BioBert-Finetune', description: 'NLP for Biomedical Text', createdAt: '2025-02-10', dataSize: '500 MB' },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>项目列表</h2>
        <Button type="primary" icon={<PlusOutlined />}>新建项目</Button>
      </div>
      <Row gutter={[16, 16]}>
        {projects.map(project => (
          <Col span={8} key={project.key}>
            <Card title={project.name} extra={<a href="#">详情</a>}>
              <p>{project.description}</p>
              <Statistic title="数据量" value={project.dataSize} />
              <div style={{ marginTop: 8, color: '#999' }}>创建于: {project.createdAt}</div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ProjectList;
