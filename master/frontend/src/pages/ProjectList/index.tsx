import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Button, message, Modal, Input, Typography, Space } from 'antd';
import { PlusOutlined, PushpinOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import client from '../../api/client';

interface ProjectInfo {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  models_count: number;
  pinned_at?: string | null;
}

const ProjectList: React.FC = () => {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [creating, setCreating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);
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

  const normalizeName = (s: string) => {
    try {
      return s.normalize('NFKC').trim().replace(/\s+/g, ' ');
    } catch {
      return s.trim().replace(/\s+/g, ' ');
    }
  };

  const validateName = (raw: string) => {
    const n = normalizeName(raw);
    if (!n) {
      setNameError('请输入项目名称');
      return false;
    }
    const dup = projects.some(p => normalizeName(p.name) === n);
    if (dup) {
      setNameError('项目名重复，请更换名字');
      return false;
    }
    setNameError(null);
    return true;
  };

  const onCreate = async () => {
    if (!name.trim()) {
      message.warning('请输入项目名称');
      return;
    }
    if (!validateName(name)) {
      return;
    }
    setCreating(true);
    try {
      await client.post<ProjectInfo>('/projects', { name: normalizeName(name), description: desc.trim() });
      setName('');
      setDesc('');
      setCreateOpen(false);
      await loadProjects();
      message.success('项目创建成功');
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail === '项目名重复，请更换名字') {
        setNameError(detail);
      }
      message.error(detail || '创建项目失败');
    } finally {
      setCreating(false);
    }
  };

  const formatDate = (s: string) => {
    try {
      return s.split('T')[0];
    } catch {
      return s;
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ 
        marginBottom: 16, 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Typography.Title level={3} style={{ margin: 0, color: '#1890ff' }}>项目列表</Typography.Title>
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
        okButtonProps={{ loading: creating, disabled: !!nameError || !name.trim() }}
      >
        <div style={{ marginTop: 8 }}>
          <Input 
            placeholder="项目名称" 
            value={name} 
            onChange={(e) => {
              setName(e.target.value);
              validateName(e.target.value);
            }} 
            style={{ marginBottom: 8 }} 
          />
          {nameError && (
            <Typography.Text type="danger" style={{ display: 'block', marginBottom: 8 }}>
              {nameError}
            </Typography.Text>
          )}
          <Input.TextArea placeholder="项目介绍（可选）" value={desc} onChange={(e) => setDesc(e.target.value)} rows={3} />
        </div>
      </Modal>
      <Row gutter={[24, 24]} justify="center">
        {projects.map(project => (
          <Col xs={24} md={12} key={project.id} style={{ display: 'flex' }}>
            <Card
              hoverable
              title={<span style={{ fontWeight: 600 }}>{project.name}</span>}
              extra={
                <Space>
                  {project.pinned_at ? (
                    <Button 
                      shape="round" 
                      icon={<PushpinOutlined />} 
                      onClick={async () => {
                        try {
                          await client.post(`/projects/${project.id}/unpin`);
                          await loadProjects();
                          message.success('已取消置顶');
                        } catch (e: any) {
                          message.error(e?.response?.data?.detail || '取消置顶失败');
                        }
                      }}
                    >
                      取消置顶
                    </Button>
                  ) : (
                    <Button 
                      ghost 
                      shape="round" 
                      icon={<PushpinOutlined />} 
                      onClick={async () => {
                        try {
                          await client.post(`/projects/${project.id}/pin`);
                          await loadProjects();
                          message.success('已置顶');
                        } catch (e: any) {
                          message.error(e?.response?.data?.detail || '置顶失败');
                        }
                      }}
                    >
                      置顶
                    </Button>
                  )}
                  <Button 
                    type="primary" 
                    shape="round" 
                    icon={<ArrowRightOutlined />} 
                    onClick={() => navigate(`/dashboard/projects/${project.id}/overview`)}
                  >
                    进入项目
                  </Button>
                </Space>
              }
              style={{ 
                width: '100%',
                borderRadius: 16,
                boxShadow: '0 6px 16px rgba(0,0,0,0.08)',
                transition: 'box-shadow 0.2s',
              }}
              bodyStyle={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: 180 }}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  {project.description || '暂无介绍'}
                </Typography.Paragraph>
                <Statistic title="模型数量" value={project.models_count} />
                <div style={{ color: '#8c8c8c' }}>创建于: {formatDate(project.created_at)}</div>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ProjectList;
