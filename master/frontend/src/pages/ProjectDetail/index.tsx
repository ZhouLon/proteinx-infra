import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Card, Button, Space, Typography, Input, Form, message, Modal, Select, Row, Col, Statistic, Table, Divider } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../../api/client';
import { listColumns, ColumnInfo, FilterItem, queryRecords } from '../../api/metadata';

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

export const ProjectDataBuild: React.FC = () => {
  const { pid } = useParams<{ pid: string }>();
  const [columnsMeta, setColumnsMeta] = useState<ColumnInfo[]>([]);
  const [filters, setFilters] = useState<FilterItem[]>([{ column: '', operator: '=', value: '' }]);
  const [datasetName, setDatasetName] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [total, setTotal] = useState(0);
  const [rows, setRows] = useState<Record<string, any>[]>([]);
  const [durationMs, setDurationMs] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [tableHeight, setTableHeight] = useState<number>(480);
  const [displayColumns, setDisplayColumns] = useState<string[]>([]);
  const isFetchingRef = useRef<boolean>(false);
  const [datasetNames, setDatasetNames] = useState<string[]>([]);
  const [saveConfirmOpen, setSaveConfirmOpen] = useState(false);
  const [pendingRowsCount, setPendingRowsCount] = useState<number | null>(null);
  const [pendingCountLoading, setPendingCountLoading] = useState<boolean>(false);

  useEffect(() => {
    (async () => {
      try {
        const cols = await listColumns();
        setColumnsMeta(cols);
      } catch {}
    })();
  }, [pid]);

  useEffect(() => {
    const loadNames = async () => {
      try {
        const res = await client.get(`/projects/${pid}/datasets`, { params: { page: 1, per_page: 10000 } });
        const items = (res.data?.items || []) as Array<{ name: string }>;
        setDatasetNames(items.map(i => String(i.name || '')) || []);
      } catch {
        setDatasetNames([]);
      }
    };
    loadNames();
  }, [pid]);

  useEffect(() => {
    const computeHeight = () => {
      const h = window.innerHeight;
      const headerAndControls = 260;
      const paginationArea = 64;
      const available = Math.max(320, h - headerAndControls - paginationArea);
      setTableHeight(available);
    };
    computeHeight();
    window.addEventListener('resize', computeHeight);
    return () => window.removeEventListener('resize', computeHeight);
  }, []);

  useEffect(() => {
    const acc = new Set<string>(columnsMeta.map(c => c.name));
    for (const r of rows) {
      for (const k of Object.keys(r)) {
        acc.add(k);
      }
    }
    setDisplayColumns(Array.from(acc));
  }, [columnsMeta, rows]);

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
    setFilters(prev => {
      if (prev.length > 1) {
        return prev.filter((_, i) => i !== idx);
      }
      return [{ column: '', operator: '=', value: '' }];
    });
    runQuery(1, undefined, []);
  };

  const operatorsFor = (col?: string) => {
    const type = (columnsMeta.find(c => c.name === col)?.type || '').toUpperCase();
    return type.match(/INT|REAL|NUM/) ? numericOperators : textOperators;
  };

  const opLabel = (op: string) => {
    if (op === 'like') return '包含';
    if (op === '=') return '=';
    if (op === '!=') return '!=';
    if (op === '>') return '>';
    if (op === '<') return '<';
    if (op === '>=') return '>=';
    if (op === '<=') return '<=';
    return op;
  };

  const saveDataset = async () => {
    if (!datasetName.trim()) {
      message.warning('请输入数据集名称');
      return;
    }
    const norm = (s: string) => s.trim().toLowerCase();
    const newNameNorm = norm(datasetName);
    const conflict = datasetNames.some(n => norm(n) === newNameNorm);
    if (conflict) {
      Modal.warning({
        title: '数据集名称重复',
        content: '与已有数据集名称冲突，请更换名称后再试。',
      });
      return;
    }
    setPendingRowsCount(null);
    setPendingCountLoading(true);
    setSaveConfirmOpen(true);
    try {
      const cleanFilters = filters.filter(f => f.column && (f.value !== '' && f.value !== undefined));
      const res = await queryRecords(undefined, 1, 1, cleanFilters);
      setPendingRowsCount(res.total);
    } catch {
      setPendingRowsCount(null);
    } finally {
      setPendingCountLoading(false);
    }
  };

  const doSaveDataset = async () => {
    const cleanFilters = filters.filter(f => f.column && (f.value !== '' && f.value !== undefined));
    try {
      const res = await client.post<DatasetInfo>(`/projects/${pid}/datasets`, { name: datasetName.trim(), filters: cleanFilters });
      message.success(`已保存数据集：${res.data.name}（${res.data.rows_count} 条）`);
      setDatasetName('');
      setDatasetNames(prev => [...prev, res.data.name]);
      setSaveConfirmOpen(false);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '保存数据集失败');
    }
  };

  const runQuery = async (overridePage?: number, overridePerPage?: number, overrideFilters?: FilterItem[]) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    setLoading(true);
    try {
      const currentPage = overridePage ?? page;
      const currentPerPage = overridePerPage ?? perPage;
      const baseFilters = overrideFilters ?? filters;
      const cleanFilters = baseFilters.filter(f => f.column && (f.value !== '' && f.value !== undefined));
      const res = await queryRecords(undefined, currentPage, currentPerPage, cleanFilters);
      setRows(res.rows);
      setTotal(res.total);
      setDurationMs(res.duration_ms);
      if (overridePage) setPage(overridePage);
      if (overridePerPage) setPerPage(overridePerPage);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '查询失败');
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  };

  useEffect(() => {
    runQuery(1);
  }, []);

  const tableColumns = useMemo(() => {
    const cols = displayColumns.map(name => {
      const col: any = {
        title: name,
        dataIndex: name,
        key: name,
        ellipsis: true,
      };
      if (name === 'id') col.width = 80;
      if (name === 'mut_num') col.width = 80;
      if (name === 'DMS_score_bin') col.width = 100;
      if (name === 'DMS_score') {
        col.render = (value: any) => {
          const num = typeof value === 'number' ? value : (value == null ? null : parseFloat(value));
          return typeof num === 'number' && !Number.isNaN(num) ? num.toFixed(4) : value;
        };
      }
      if (name === 'sequence' || name === 'source') {
        col.render = (text: any) => {
          const str = String(text ?? '');
          const onEnter = (e: React.MouseEvent<HTMLSpanElement>) => {
            const el = e.currentTarget;
            el.style.background = '#e6f7ff';
            el.style.boxShadow = '0 0 0 2px #bae7ff inset';
            el.style.borderRadius = '6px';
            el.style.transition = 'all .2s';
          };
          const onLeave = (e: React.MouseEvent<HTMLSpanElement>) => {
            const el = e.currentTarget;
            el.style.background = 'transparent';
            el.style.boxShadow = 'none';
          };
          const copyText = async (s: string) => {
            try {
              if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(s);
                return true;
              }
            } catch {}
            const ta = document.createElement('textarea');
            ta.value = s;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.focus();
            ta.select();
            let ok = false;
            try {
              ok = document.execCommand('copy');
            } catch {}
            document.body.removeChild(ta);
            return ok;
          };
          const onClick = async (e: React.MouseEvent<HTMLSpanElement>) => {
            const el = e.currentTarget;
            const ok = await copyText(str);
            if (ok) {
              el.style.background = '#f6ffed';
              el.style.boxShadow = '0 0 0 2px #b7eb8f inset';
              message.success('已复制');
              setTimeout(() => {
                el.style.background = 'transparent';
                el.style.boxShadow = 'none';
              }, 600);
            } else {
              message.error('复制失败');
            }
          };
          return (
            <span
              onMouseEnter={onEnter}
              onMouseLeave={onLeave}
              onClick={onClick}
              style={{
                display: 'inline-block',
                maxWidth: 480,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                cursor: 'pointer',
                padding: '0 6px'
              }}
            >
              {str}
            </span>
          );
        };
      }
      return col;
    });
    return cols;
  }, [displayColumns]);

  return (
    <div>
      <Title level={3}>数据构建</Title>
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space align="center">
            <Text strong>筛选条件</Text>
            <Button type="dashed" onClick={onAddFilter}>添加条件</Button>
            <Button type="primary" onClick={() => runQuery(1)}>查询</Button>
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
              <Button danger onClick={() => onRemoveFilter(idx)}>{filters.length > 1 ? '移除' : '清除'}</Button>
            </Space>
          ))}
          <Space>
            <Input placeholder="数据集名称" value={datasetName} onChange={(e) => setDatasetName(e.target.value)} style={{ minWidth: 240 }} />
            <Button type="primary" onClick={saveDataset}>保存为数据集</Button>
          </Space>
        </Space>
      </Card>
      <Modal
        title="确认保存数据集"
        open={saveConfirmOpen}
        onOk={doSaveDataset}
        onCancel={() => setSaveConfirmOpen(false)}
        okText="保存"
        cancelText="取消"
        okButtonProps={{ disabled: pendingCountLoading }}
      >
        <div style={{ background: 'linear-gradient(135deg, #f7faff 0%, #ffffff 100%)', border: '1px solid #e6f7ff', borderRadius: 8, padding: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ padding: '8px 12px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
              <Text strong>数据集名称：</Text>
              <Text>{datasetName || '(未填写)'}</Text>
            </div>
            <Divider style={{ margin: '12px 0' }} />
            <div style={{ padding: '8px 12px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
              <Text strong>筛选条件：</Text>
              <div style={{ marginTop: 8 }}>
                {filters.filter(f => f.column && (f.value !== '' && f.value !== undefined)).length === 0 ? (
                  <div>空查询</div>
                ) : (
                  filters
                    .filter(f => f.column && (f.value !== '' && f.value !== undefined))
                    .map((f, i) => (
                      <div key={i}>{`${f.column} ${opLabel(String(f.operator || ''))} ${String(f.value ?? '')}`}</div>
                    ))
                )}
              </div>
            </div>
            <Divider style={{ margin: '12px 0' }} />
            <div style={{ padding: '8px 12px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
              <Text strong>待保存数据量：</Text>
              {pendingCountLoading ? (
                <Text type="secondary">正在计算数据量...</Text>
              ) : (
                <Text>{pendingRowsCount != null ? pendingRowsCount : '—'}</Text>
              )}
            </div>
          </Space>
        </div>
      </Modal>
      <Card title="查询结果">
        <div style={{ marginBottom: 12 }}>
          <Space>
            <Text>找到 {total} 条记录</Text>
            {durationMs !== undefined && <Text type="secondary">本次查询耗时 {durationMs} ms</Text>}
          </Space>
        </div>
        <Table
          dataSource={rows}
          rowKey={(r) => r.id ?? r.__rowid__ ?? JSON.stringify(r).length}
          loading={loading}
          columns={tableColumns}
          scroll={{ y: tableHeight }}
          pagination={{
            current: page,
            pageSize: perPage,
            total,
            showSizeChanger: true,
            pageSizeOptions: ['10', '25', '50', '100'],
            onChange: (p, ps) => runQuery(p, ps),
          }}
        />
      </Card>
    </div>
  );
};

export const ProjectDatasets: React.FC = () => {
  const { pid } = useParams<{ pid: string }>();
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
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
    loadDatasets(1, perPage);
  }, [pid]);

  const formatDateOnly = (s: string) => {
    if (!s) return s;
    const idx = s.indexOf('T');
    return idx > 0 ? s.slice(0, idx) : s;
  };
  const opLabel = (op: string) => {
    if (op === 'like') return '包含';
    if (op === '=') return '=';
    if (op === '!=') return '!=';
    if (op === '>') return '>';
    if (op === '<') return '<';
    if (op === '>=') return '>=';
    if (op === '<=') return '<=';
    return op;
  };

  return (
    <div>
      <Title level={3}>数据集</Title>
      <Card>
        <Table
          dataSource={datasets}
          rowKey={(r) => r.id}
          loading={loading}
          columns={[
            { title: '名称', dataIndex: 'name' },
            { title: '数据量', dataIndex: 'rows_count' },
            { title: '创建时间', dataIndex: 'created_at', render: (t: string) => formatDateOnly(t) },
            { 
              title: '筛选条件', 
              dataIndex: 'filters', 
              render: (fs: FilterItem[]) => {
                const items = (fs || []);
                if (items.length === 0) return '空查询';
                return (
                  <div>
                    {items.map((f, i) => (
                      <div key={i}>
                        {`${f.column} ${opLabel(String(f.operator || ''))} ${String(f.value ?? '')}`}
                      </div>
                    ))}
                  </div>
                );
              }
            },
            { title: '操作', render: (_: any, r: DatasetInfo) => (<Button type="link" onClick={() => navigate(`/dashboard/projects/${pid}/datasets/${r.id}`)}>查看详情</Button>) }
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

export const ProjectDatasetDetail: React.FC = () => {
  const { pid, did } = useParams<{ pid: string; did: string }>();
  return (
    <div>
      <Title level={3}>数据集详情</Title>
      <Card>
        <Space direction="vertical">
          <Text>目标项目：{pid}</Text>
          <Text>数据集ID：{did}</Text>
          <Text strong>突变位点呈现（频率，活性加权）</Text>
          <Text strong>上位效应计算</Text>
          <Text strong>突变位点数比例</Text>
        </Space>
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
