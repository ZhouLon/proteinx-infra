import React, { useEffect, useState } from 'react';
import { Upload, Table, message, Button, Popconfirm } from 'antd';
import { InboxOutlined, DeleteOutlined, FileOutlined, FolderOutlined } from '@ant-design/icons';
import { listFiles, deleteFile, FileInfo } from '../../api/file';

const { Dragger } = Upload;

const DataManagement: React.FC = () => {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState('/');

  const fetchFiles = async (path: string) => {
    setLoading(true);
    try {
      const data = await listFiles(path);
      setFiles(data);
    } catch (error) {
      message.error('加载文件列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles(currentPath);
  }, [currentPath]);

  const handleDelete = async (path: string) => {
    try {
      await deleteFile(path);
      message.success('文件删除成功');
      fetchFiles(currentPath);
    } catch (error) {
      message.error('文件删除失败');
    }
  };

  const uploadProps = {
    name: 'file',
    multiple: true,
    action: '/api/files/upload',
    data: { path: currentPath },
    onChange(info: any) {
      const { status } = info.file;
      if (status === 'done') {
        message.success(`${info.file.name} 上传成功`);
        fetchFiles(currentPath);
      } else if (status === 'error') {
        message.error(`${info.file.name} 上传失败`);
      }
    },
    showUploadList: false, // 不显示默认的上传列表，因为我们有自己的文件表格
  };

  const formatSize = (size: number) => {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`;
    if (size < 1024 * 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`;
    return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`;
  };

  const columns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 60,
      render: (type: string) => type === 'directory' ? <FolderOutlined /> : <FileOutlined />,
    },
    { 
      title: '文件名', 
      dataIndex: 'name', 
      key: 'name',
      render: (text: string, record: FileInfo) => (
        record.type === 'directory' ? (
          <a onClick={() => setCurrentPath(`${currentPath}${text}/`)}>{text}</a>
        ) : text
      )
    },
    { 
      title: '大小', 
      dataIndex: 'size', 
      key: 'size', 
      render: (size: number, record: FileInfo) => record.type === 'directory' ? '-' : formatSize(size) 
    },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at' },
    { 
      title: '操作', 
      key: 'action', 
      render: (_: any, record: FileInfo) => (
        <Popconfirm title="确定删除吗？" onConfirm={() => handleDelete(record.path)}>
          <Button type="link" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ) 
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>数据管理</h2>
        {currentPath !== '/' && (
           <Button onClick={() => {
             const parent = currentPath.split('/').slice(0, -2).join('/') + '/';
             setCurrentPath(parent || '/');
           }}>返回上级目录</Button>
        )}
      </div>
      
      <div style={{ marginBottom: 24 }}>
        <Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            当前路径: {currentPath} (支持批量上传)
          </p>
        </Dragger>
      </div>

      <Table 
        dataSource={files} 
        columns={columns} 
        rowKey="path"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default DataManagement;
