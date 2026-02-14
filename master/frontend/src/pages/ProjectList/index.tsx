import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Button, message, Modal, Input } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import client from '../../api/client';

interface ProjectInfo {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  models_count: number;
}

const ProjectList: React.FC = () => {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [creating, setCreating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const navigate = useNavigate();

  const loadProjects = async () => {
    try {
      const res = await client.get<ProjectInfo[]>('/projects');
      setProjects(res.data);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载项目列表失败');
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const onCreate = async () => {
    if (!name.trim()) {
      message.warning('请输入项目名称');
      return;
    }
    setCreating(true);
    try {
      await client.post<ProjectInfo>('/projects', { name: name.trim(), description: desc.trim() });
      setName('');
      setDesc('');
      setCreateOpen(false);
      await loadProjects();
      message.success('项目创建成功');
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '创建项目失败');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>项目列表</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建项目</Button>
      </div>
      <Modal
        title="新建项目"
        open={createOpen}
        onOk={onCreate}
        onCancel={() => {
          setCreateOpen(false);
        }}
        okText="创建"
        cancelText="取消"
        okButtonProps={{ loading: creating }}
      >
        <div style={{ marginTop: 8 }}>
          <Input placeholder="项目名称" value={name} onChange={(e) => setName(e.target.value)} style={{ marginBottom: 8 }} />
          <Input.TextArea placeholder="项目介绍（可选）" value={desc} onChange={(e) => setDesc(e.target.value)} rows={3} />
        </div>
      </Modal>
      <Row gutter={[16, 16]}>
        {projects.map(project => (
          <Col span={8} key={project.id}>
            <Card title={project.name} extra={<a onClick={() => navigate(`/dashboard/projects/${project.id}`)}>详情</a>}>
              <p>{project.description || '暂无介绍'}</p>
              <Statistic title="模型数量" value={project.models_count} />
              <div style={{ marginTop: 8, color: '#999' }}>创建于: {project.created_at}</div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ProjectList;
