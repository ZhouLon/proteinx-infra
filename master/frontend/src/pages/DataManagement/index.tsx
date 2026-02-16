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
  const [displayColumns, setDisplayColumns] = useState<string[]>([]);

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

  useEffect(() => {
    const acc = new Set<string>(columnsMeta.map(c => c.name));
    for (const r of rows) {
      for (const k of Object.keys(r)) {
        acc.add(k);
      }
    }
    setDisplayColumns(Array.from(acc));
  }, [columnsMeta, rows]);

  const fetchData = async (overridePage?: number, overridePerPage?: number, overrideFilters?: FilterItem[]) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    setLoading(true);
    try {
      const baseFilters = overrideFilters ?? filters;
      const cleanFilters = baseFilters.filter(f => f.column && (f.value !== '' && f.value !== undefined));
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

  useEffect(() => {
    fetchData(1);
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
    setFilters(prev => {
      if (prev.length > 1) {
        return prev.filter((_, i) => i !== idx);
      }
      return [{ column: '', operator: '=', value: '' }];
    });
    fetchData(1, undefined, []);
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
              <Button danger onClick={() => onRemoveFilter(idx)}>{filters.length > 1 ? '移除' : '清除'}</Button>
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
