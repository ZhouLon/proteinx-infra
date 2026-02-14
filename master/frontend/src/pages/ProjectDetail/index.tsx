import React, { useEffect, useState } from 'react';
import { Card, Button, Space, Typography, Input, Form, message, List, Modal, Select } from 'antd';
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

const ProjectDetail: React.FC = () => {
  const { pid } = useParams<{ pid: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [password, setPassword] = useState('');

  const [columnsMeta, setColumnsMeta] = useState<ColumnInfo[]>([]);
  const [filters, setFilters] = useState<FilterItem[]>([{ column: '', operator: '=', value: '' }]);
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [datasetName, setDatasetName] = useState('');

  const loadProject = async () => {
    try {
      const res = await client.get<ProjectInfo>(`/projects/${pid}`);
      setProject(res.data);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载项目失败');
    }
  };

  const loadDatasets = async () => {
    try {
      const res = await client.get<DatasetInfo[]>(`/projects/${pid}/datasets`);
      setDatasets(res.data);
    } catch {
      setDatasets([]);
    }
  };

  useEffect(() => {
    loadProject();
    loadDatasets();
    (async () => {
      try {
        const cols = await listColumns();
        setColumnsMeta(cols);
      } catch {}
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
      await loadDatasets();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '保存数据集失败');
    }
  };

  const menu = (
    <Card style={{ width: 240 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Button type="link" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>概览</Button>
        <Button type="link" onClick={() => document.getElementById('dataset')?.scrollIntoView({ behavior: 'smooth' })}>数据构建</Button>
        <Button type="link" onClick={() => document.getElementById('train')?.scrollIntoView({ behavior: 'smooth' })}>运行训练</Button>
        <Button type="link" onClick={() => document.getElementById('compare')?.scrollIntoView({ behavior: 'smooth' })}>结果对比</Button>
      </Space>
    </Card>
  );

  const operatorsFor = (col?: string) => {
    const type = (columnsMeta.find(c => c.name === col)?.type || '').toUpperCase();
    return type.match(/INT|REAL|NUM/) ? numericOperators : textOperators;
  };

  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <div>{menu}</div>
      <div style={{ flex: 1 }}>
        <Title level={3}>项目特别页</Title>
        {project && (
          <Card style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text>项目ID：{project.id}</Text>
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
                  <Button danger onClick={() => Modal.confirm({
                    title: '删除项目',
                    content: (
                      <div>
                        <Text>请输入密码以确认删除：</Text>
                        <Input.Password value={password} onChange={(e) => setPassword(e.target.value)} />
                      </div>
                    ),
                    okText: '删除',
                    cancelText: '取消',
                    onOk: onDelete,
                    okButtonProps: { danger: true, loading },
                  })}>删除项目</Button>
                </Space>
              </Form>
            </Space>
          </Card>
        )}

        <div id="dataset">
          <Card title="数据构建" style={{ marginBottom: 16 }}>
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
              <List
                header="已保存数据集"
                dataSource={datasets}
                renderItem={(item) => (
                  <List.Item>
                    <Space direction="vertical">
                      <Text>{item.name}（{item.rows_count} 条）</Text>
                      <Text type="secondary">创建于 {item.created_at}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            </Space>
          </Card>
        </div>

        <div id="train">
          <Card title="运行训练（占位）" style={{ marginBottom: 16 }}>
            <Text>后续接入训练配置与调度。</Text>
          </Card>
        </div>

        <div id="compare">
          <Card title="结果对比（占位）">
            <Text>后续接入评估结果展示与对比。</Text>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail;
