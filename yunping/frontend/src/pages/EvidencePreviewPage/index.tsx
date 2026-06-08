import { useState, useEffect } from 'react';
import { Card, Table, Tag, Space, Button, Upload, Empty } from 'antd';
import { UploadOutlined, FileWordOutlined, FileExcelOutlined, FilePdfOutlined, FileImageOutlined, FileOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd';
import { useAppStore } from '../../store';

interface EvidenceFile {
  id: string;
  name: string;
  file_type: string;
  file_path: string;
  item_id: string;
  base_id: string;
  uploaded_at: string;
}

const EvidencePreviewPage = () => {
  const [files, setFiles] = useState<EvidenceFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const { currentBaseId, currentBaseName } = useAppStore();

  const fetchFiles = async () => {
    setLoading(true);
    // TODO: 对接后端证据文件API
    setFiles([]);
    setLoading(false);
  };

  useEffect(() => { fetchFiles(); }, [currentBaseId]);

  const getFileIcon = (type: string) => {
    if (type.includes('word') || type.endsWith('.docx')) return <FileWordOutlined className="text-blue-500" />;
    if (type.includes('excel') || type.endsWith('.xlsx')) return <FileExcelOutlined className="text-green-500" />;
    if (type.includes('pdf') || type.endsWith('.pdf')) return <FilePdfOutlined className="text-red-500" />;
    if (type.includes('image')) return <FileImageOutlined className="text-purple-500" />;
    return <FileOutlined className="text-gray-500" />;
  };

  const columns = [
    { title: '文件名', dataIndex: 'name', key: 'name', render: (name: string, r: EvidenceFile) => <Space>{getFileIcon(r.file_type)}{name}</Space> },
    { title: '文件类型', dataIndex: 'file_type', key: 'file_type', width: 120, render: (t: string) => <Tag>{t}</Tag> },
    { title: '关联条目', dataIndex: 'item_id', key: 'item_id', width: 100 },
    { title: '上传时间', dataIndex: 'uploaded_at', key: 'uploaded_at', width: 180, render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
  ];

  return (
    <Card title="证据预览" extra={
      <Space>
        <Upload beforeUpload={(file) => { setFileList([file]); return false; }} onRemove={() => setFileList([])} fileList={fileList} maxCount={1}>
          <Button icon={<UploadOutlined />}>上传证据文件</Button>
        </Upload>
        <span className="text-gray-400 text-sm">{currentBaseName ? `基地: ${currentBaseName}` : '请选择基地'}</span>
      </Space>
    }>
      {files.length > 0 ? (
        <Table columns={columns} dataSource={files} rowKey="id" loading={loading} pagination={false} />
      ) : (
        <Empty description="暂无证据文件，请上传相关证据材料" />
      )}
    </Card>
  );
};

export default EvidencePreviewPage;
