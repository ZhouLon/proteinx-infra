import client from './client';

export interface ColumnInfo {
  cid: number;
  name: string;
  type: string;
  notnull: number;
  pk: number;
}

export interface QueryResponse {
  page: number;
  per_page: number;
  total: number;
  rows: Record<string, any>[];
  duration_ms?: number;
}

export interface FilterItem {
  column: string;
  operator: string;
  value: string | number;
}

export const listTables = async (): Promise<string[]> => {
  const res = await client.get<{ tables: string[] }>('/metadata/tables');
  return res.data.tables;
};

export const listColumns = async (table?: string): Promise<ColumnInfo[]> => {
  const params: Record<string, any> = {};
  if (table) params.table = table;
  const res = await client.get<{ columns: ColumnInfo[] }>('/metadata/columns', { params });
  return res.data.columns;
};

export const queryRecords = async (table: string | undefined, page: number, perPage: number, filters: FilterItem[]): Promise<QueryResponse> => {
  const params: Record<string, any> = {
    page,
    per_page: perPage,
    pageSize: perPage,
    filters: JSON.stringify(filters || []),
  };
  if (table) params.table = table;
  const res = await client.get<QueryResponse>('/metadata/query', { params });
  return res.data;
};

export const uploadCSV = async (table: string, file: File) => {
  const formData = new FormData();
  formData.append('table', table);
  formData.append('file', file);
  await client.post('/metadata/upload_csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const deleteRecords = async (table: string, ids: number[]) => {
  await client.post('/metadata/delete', { table, ids });
};
