import React, { useEffect, useState } from 'react';
import { Card, Button, Space, Typography, Input, Form, message, Modal, Select, Row, Col, Statistic, Table } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../../api/client';
import { listColumns, ColumnInfo, FilterItem } from '../../api/metadata';

const { Title, Text } = Typography;

interface ProjectInfo {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  models_count: number;
}

interface DatasetInfo {
  id: string;
  name: string;
  filters: FilterItem[];
  table?: string;
  created_at: string;
  rows_count: number;
}

const textOperators = [
  { label: '= 等于', value: '=' },
  { label: '包含', value: 'like' },
  { label: '!= 不等于', value: '!=' },
];
const numericOperators = [
  { label: '= 等于', value: '=' },
  { label: '> 大于', value: '>' },
  { label: '< 小于', value: '<' },
  { label: '>= 大于等于', value: '>=' },
  { label: '<= 小于等于', value: '<=' },
  { label: '!= 不等于', value: '!=' },
];

export const ProjectOverview: React.FC = () => {
  const { pid } = useParams<{ pid: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [password, setPassword] = useState('');
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [experimentsTotal, setExperimentsTotal] = useState(0);
  const [confirmPhase, setConfirmPhase] = useState(false);

  const loadProject = async () => {
    try {
      const res = await client.get<ProjectInfo>(`/projects/${pid}`);
      setProject(res.data);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载项目失败');
    }
  };

  useEffect(() => {
    loadProject();
    (async () => {
      try {
        const res = await client.get(`/projects/${pid}/datasets`, { params: { page: 1, per_page: 1 } });
        setExperimentsTotal(res.data.total || 0);
      } catch {
        setExperimentsTotal(0);
      }
    })();
  }, [pid]);

  const onUpdate = async (values: { name?: string; description?: string }) => {
    setLoading(true);
    try {
      const res = await client.patch<ProjectInfo>(`/projects/${pid}`, values);
      setProject(res.data);
      message.success('项目已更新');
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '更新项目失败');
    } finally {
      setLoading(false);
    }
  };

  const onDelete = async () => {
    if (!password.trim()) {
      message.warning('请输入密码以确认删除');
      return;
    }
    setLoading(true);
    try {
      await client.delete(`/projects/${pid}`, { data: { password } });
      message.success('项目已删除');
      navigate('/dashboard/projects');
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '删除项目失败');
    } finally {
      setLoading(false);
    }
  };
  const onOpenDelete = () => {
    setPassword('');
    setConfirmPhase(false);
    setDeleteOpen(true);
  };
  const onOkDelete = async () => {
    if (!confirmPhase) {
      setConfirmPhase(true);
      return;
    }
    await onDelete();
  };

  return (
    <div>
      <div style={{ 
        marginBottom: 16, 
        padding: '24px', 
        background: 'linear-gradient(135deg, #e6f7ff 0%, #ffffff 100%)', 
        borderRadius: 12, 
        border: '1px solid #bae7ff'
      }}>
        <Title level={3} style={{ color: '#1890ff', margin: 0 }}>项目概览</Title>
        <Text type="secondary">管理模型与实验，快速进入构建与训练流程</Text>
      </div>
      {project && (
        <Card>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic title="项目名称" value={project.name} />
              </Col>
              <Col span={12}>
                <Statistic title="模型数量" value={project.models_count} />
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic title="实验数量" value={experimentsTotal} />
              </Col>
              <Col span={12}>
                <Text type="secondary">更新于：{project.updated_at}</Text>
              </Col>
            </Row>
            {!editOpen && (
              <Button onClick={() => setEditOpen(true)}>更改项目</Button>
            )}
            {editOpen && (
              <Form
                layout="vertical"
                initialValues={{ name: project.name, description: project.description }}
                onFinish={onUpdate}
              >
                <Form.Item label="项目名称" name="name">
                  <Input />
                </Form.Item>
                <Form.Item label="项目介绍" name="description">
                  <Input.TextArea rows={3} />
                </Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={loading}>保存修改</Button>
                  <Button danger onClick={onOpenDelete}>删除项目</Button>
                </Space>
              </Form>
            )}
          </Space>
        </Card>
      )}
      <Modal
        title="删除项目"
        open={deleteOpen}
        onOk={onOkDelete}
        onCancel={() => {
          setDeleteOpen(false);
          setConfirmPhase(false);
        }}
        okText={confirmPhase ? "删除" : "确定"}
        cancelText="取消"
        okButtonProps={{ danger: true, loading }}
        cancelButtonProps={{ type: 'primary' }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>请输入密码以确认删除：</Text>
          <Input.Password value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" />
          {confirmPhase && (
            <Text type="danger">确定要删除吗？数据无法找回。</Text>
          )}
        </Space>
      </Modal>
    </div>
  );
};

export const ProjectBuild: React.FC = () => {
  const { pid } = useParams<{ pid: string }>();
  const [columnsMeta, setColumnsMeta] = useState<ColumnInfo[]>([]);
  const [filters, setFilters] = useState<FilterItem[]>([{ column: '', operator: '=', value: '' }]);
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [datasetName, setDatasetName] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const loadDatasets = async (overridePage?: number, overridePerPage?: number) => {
    setLoading(true);
    try {
      const currentPage = overridePage ?? page;
      const currentPerPage = overridePerPage ?? perPage;
      const res = await client.get(`/projects/${pid}/datasets`, { params: { page: currentPage, per_page: currentPerPage } });
      setDatasets(res.data.items || []);
      setTotal(res.data.total || 0);
      if (overridePage) setPage(overridePage);
      if (overridePerPage) setPerPage(overridePerPage);
    } catch {
      setDatasets([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const cols = await listColumns();
        setColumnsMeta(cols);
      } catch {}
    })();
    loadDatasets();
  }, [pid]);

  const onAddFilter = () => {
    setFilters(prev => [...prev, { column: '', operator: '=', value: '' }]);
  };
  const onChangeFilter = (idx: number, patch: Partial<FilterItem>) => {
    setFilters(prev => {
      const next = [...prev];
      next[idx] = { ...next[idx], ...patch };
      return next;
    });
  };
  const onRemoveFilter = (idx: number) => {
    setFilters(prev => (prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev));
  };

  const operatorsFor = (col?: string) => {
    const type = (columnsMeta.find(c => c.name === col)?.type || '').toUpperCase();
    return type.match(/INT|REAL|NUM/) ? numericOperators : textOperators;
  };

  const saveDataset = async () => {
    if (!datasetName.trim()) {
      message.warning('请输入数据集名称');
      return;
    }
    const cleanFilters = filters.filter(f => f.column && (f.value !== '' && f.value !== undefined));
    try {
      const res = await client.post<DatasetInfo>(`/projects/${pid}/datasets`, { name: datasetName.trim(), filters: cleanFilters });
      message.success(`已保存数据集：${res.data.name}（${res.data.rows_count} 条）`);
      setDatasetName('');
      await loadDatasets(1, perPage);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '保存数据集失败');
    }
  };

  return (
    <div>
      <Title level={3}>数据构建</Title>
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space align="center">
            <Text strong>筛选条件</Text>
            <Button type="dashed" onClick={onAddFilter}>添加条件</Button>
          </Space>
          {filters.map((f, idx) => (
            <Space key={idx} style={{ width: '100%' }}>
              <Select
                placeholder="选择列"
                value={f.column || undefined}
                onChange={(v) => onChangeFilter(idx, { column: v })}
                style={{ minWidth: 200 }}
                options={columnsMeta.map(c => ({ label: `${c.name} (${c.type})`, value: c.name }))}
              />
              <Select
                placeholder="运算符"
                value={f.operator}
                onChange={(v) => onChangeFilter(idx, { operator: v })}
                style={{ minWidth: 140 }}
                options={operatorsFor(f.column)}
              />
              <Input
                placeholder="输入筛选值"
                value={String(f.value ?? '')}
                onChange={(e) => onChangeFilter(idx, { value: e.target.value })}
                style={{ minWidth: 240 }}
              />
              <Button danger onClick={() => onRemoveFilter(idx)}>移除</Button>
            </Space>
          ))}
          <Space>
            <Input placeholder="数据集名称" value={datasetName} onChange={(e) => setDatasetName(e.target.value)} style={{ minWidth: 240 }} />
            <Button type="primary" onClick={saveDataset}>保存为数据集</Button>
          </Space>
        </Space>
      </Card>
      <Card title="已保存数据集">
        <Table
          dataSource={datasets}
          rowKey={(r) => r.id}
          loading={loading}
          columns={[
            { title: '数据集名称', dataIndex: 'name' },
            { title: '行数', dataIndex: 'rows_count' },
            { title: '创建时间', dataIndex: 'created_at' },
          ]}
          pagination={{
            current: page,
            pageSize: perPage,
            total,
            showSizeChanger: true,
            pageSizeOptions: ['10', '25', '50', '100'],
            onChange: (p, ps) => loadDatasets(p, ps),
          }}
        />
      </Card>
    </div>
  );
};

export const ProjectTrain: React.FC = () => {
  return (
    <div>
      <Title level={3}>运行训练</Title>
      <Card>
        <Text>后续接入训练配置与调度。</Text>
      </Card>
    </div>
  );
};

export const ProjectModelBuild: React.FC = () => {
  return (
    <div>
      <Title level={3}>模型构建</Title>
      <Card>
        <Text>在此配置与管理模型结构、特征选择与训练计划。</Text>
      </Card>
    </div>
  );
};

export const ProjectCompare: React.FC = () => {
  return (
    <div>
      <Title level={3}>结果对比</Title>
      <Card>
        <Text>后续接入评估结果展示与对比。</Text>
      </Card>
    </div>
  );
};

export default ProjectOverview;
