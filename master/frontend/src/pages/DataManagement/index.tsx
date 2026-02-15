import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Table, message, Button, Select, Input, Space, Typography } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { listColumns, queryRecords, ColumnInfo, FilterItem } from '../../api/metadata';

const { Title, Text } = Typography;

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

const DataManagement: React.FC = () => {
  const [columnsMeta, setColumnsMeta] = useState<ColumnInfo[]>([]);
  const [filters, setFilters] = useState<FilterItem[]>([{ column: '', operator: '=', value: '' }]);
  const [rows, setRows] = useState<Record<string, any>[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [total, setTotal] = useState(0);
  const [durationMs, setDurationMs] = useState<number | undefined>(undefined);
  const [tableHeight, setTableHeight] = useState<number>(480);

  const isFetchingRef = useRef<boolean>(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const cols = await listColumns();
        setColumnsMeta(cols);
      } catch (e) {
        const err: any = e;
        message.error(err?.response?.data?.detail || '加载列信息失败');
      }
    })();
  }, []);

  useEffect(() => {
    const computeHeight = () => {
      const h = window.innerHeight;
      const headerAndControls = 260; // 估算顶部控件与边距高度
      const paginationArea = 64;
      const available = Math.max(320, h - headerAndControls - paginationArea);
      setTableHeight(available);
    };
    computeHeight();
    window.addEventListener('resize', computeHeight);
    return () => window.removeEventListener('resize', computeHeight);
  }, []);

  const fetchData = async (overridePage?: number, overridePerPage?: number) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    setLoading(true);
    try {
      const cleanFilters = filters.filter(f => f.column && (f.value !== '' && f.value !== undefined));
      const currentPage = overridePage ?? page;
      const currentPerPage = overridePerPage ?? perPage;
      const res = await queryRecords(undefined, currentPage, currentPerPage, cleanFilters);
      setRows(res.rows);
      setTotal(res.total);
      setDurationMs(res.duration_ms);
      if (overridePage) setPage(overridePage);
      if (overridePerPage) setPerPage(overridePerPage);
    } catch (e) {
      const err: any = e;
      message.error(err?.response?.data?.detail || '查询数据失败');
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  };

  // 不自动查询；仅在点击按钮或分页交互时触发
  useEffect(() => {
    // 初始化不查询，避免按钮在刷新后灰色
    return;
  }, []);

  const tableColumns = useMemo(() => {
    const cols = columnsMeta.map(c => ({
      title: c.name,
      dataIndex: c.name,
      key: c.name,
      ellipsis: true,
    }));
    return cols;
  }, [columnsMeta]);

  const rowKeySelector = (record: any) => record.id ?? record.__rowid__ ?? JSON.stringify(record).length;

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

  return (
    <div ref={containerRef}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0, color: '#1890ff' }}>数据管理</Title>
      </div>

      <div style={{ padding: 16, background: '#fff', borderRadius: 8, marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space align="center">
            <Text strong>条件查询</Text>
            <Button type="dashed" icon={<PlusOutlined />} onClick={onAddFilter}>添加条件</Button>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={() => fetchData(1)}
              disabled={loading || isFetchingRef.current}
            >
              查询
            </Button>
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
                options={
                  (columnsMeta.find(c => c.name === f.column)?.type || '').toUpperCase().match(/INT|REAL|NUM/)
                    ? numericOperators
                    : textOperators
                }
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
        </Space>
      </div>

      <div style={{ marginBottom: 12 }}>
        <Space>
          <Text>找到 {total} 条记录</Text>
          {durationMs !== undefined && <Text type="secondary">本次查询耗时 {durationMs} ms</Text>}
        </Space>
      </div>

      <Table
        dataSource={rows}
        columns={tableColumns}
        rowKey={rowKeySelector}
        loading={loading}
        scroll={{ y: tableHeight }}
        pagination={{
          current: page,
          pageSize: perPage,
          total,
          showSizeChanger: true,
          pageSizeOptions: ['10', '25', '50', '100'],
          onChange: (p, ps) => {
            fetchData(p, ps);
          },
        }}
      />
    </div>
  );
};

export default DataManagement;
