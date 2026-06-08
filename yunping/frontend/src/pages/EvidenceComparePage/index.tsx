import { useState, useEffect } from 'react';
import { Card, Button, Upload, Tag, Space, message, Empty, Table, Row, Col, Modal, Image, Statistic } from 'antd';
import { UploadOutlined, FileOutlined, EyeOutlined, FileExcelOutlined, FilePdfOutlined, FileWordOutlined, RobotOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import { useAppStore } from '../../store';
import { uploadEvidenceList, getEvidenceList, uploadEvidenceMaterial, getSampleFileInfo, compareEvidence } from '../../api';

interface EvidenceItem {
  id: string;
  序号: number;
  章节名称: string;
  举证名称: string;
  样例举证: string;
  局点上传举证材料?: string;
  审核结果?: '满足' | '不满足' | '待审核';
  样例举证文件?: string;
  局点上传文件?: string;
  举证诊断结果?: string;
  [key: string]: any; // 支持动态属性
}

interface ExcelData {
  columns: string[];
  data: any[];
}

const EvidenceComparePage = () => {
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<EvidenceItem | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadingItem, setUploadingItem] = useState<EvidenceItem | null>(null);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [excelData, setExcelData] = useState<ExcelData | null>(null);
  const [excelColumns, setExcelColumns] = useState<string[]>([]);
  const [previewSample, setPreviewSample] = useState<{ name: string; url: string; type: string } | null>(null);
  const [auditing, setAuditing] = useState(false);

  const { userInfo, currentBaseId } = useAppStore();
  const isAdmin = userInfo?.role === 'sys_admin' || userInfo?.role === 'eval_admin';
  
  // 根据文件名判断文件类型
  const getFileType = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(ext)) {
      return 'image';
    } else if (ext === 'pdf') {
      return 'pdf';
    } else if (['doc', 'docx'].includes(ext)) {
      return 'word';
    }
    return 'other';
  };

  // 统计数据
  const totalCount = evidenceList.length;
  const uploadedCount = evidenceList.filter(item => item.局点上传举证材料).length;
  const satisfiedCount = evidenceList.filter(item => item.审核结果 === '满足').length;

  // 获取证据清单数据
  const fetchEvidenceList = async () => {
    setLoading(true);
    try {
      const res = await getEvidenceList() as any;
      const items = res.items || [];
      setEvidenceList(items);
      
      // 提取Excel列名（从第一条数据的所有key中获取）
      if (items.length > 0) {
        const allKeys = Object.keys(items[0]).filter(key => 
          key !== 'id' && key !== '局点上传举证材料' && key !== '审核结果' && 
          key !== '样例举证文件' && key !== '局点上传文件' && key !== '举证诊断结果'
        );
        setExcelColumns(allKeys);
        setExcelData({
          columns: allKeys,
          data: items
        });
      } else {
        setExcelData(null);
        setExcelColumns([]);
      }
    } catch (e: any) {
      message.error(e.message || '获取证据清单失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidenceList();
  }, [currentBaseId]);

  // 上传证据清单（管理员）
  const handleUploadEvidenceList = async (file: File) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await uploadEvidenceList(formData) as any;
      message.success('证据清单上传成功');
      
      // 直接使用返回的数据更新状态
      const items = res.items || [];
      setEvidenceList(items);
      
      // 提取Excel列名
      if (items.length > 0) {
        const allKeys = Object.keys(items[0]).filter(key => 
          key !== 'id' && key !== '局点上传举证材料' && key !== '审核结果' && 
          key !== '样例举证文件' && key !== '局点上传文件' && key !== '举证诊断结果'
        );
        setExcelColumns(allKeys);
        setExcelData({
          columns: allKeys,
          data: items
        });
      }
    } catch (e: any) {
      message.error(e.message || '上传失败');
    } finally {
      setLoading(false);
    }
  };

  // 上传举证材料（用户）
  const handleUploadEvidence = async () => {
    if (!uploadingItem || !fileList.length) {
      message.warning('请选择要上传的文件');
      return;
    }
    try {
      const formData = new FormData();
      formData.append('file', fileList[0] as any);
      await uploadEvidenceMaterial(uploadingItem.id, formData);
      message.success('举证材料上传成功');
      setUploadModalOpen(false);
      setFileList([]);
      fetchEvidenceList();
    } catch (e: any) {
      message.error(e.message || '上传失败');
    }
  };

  // 自动审核
  const handleAutoAudit = async (item: EvidenceItem) => {
    if (!item.局点上传文件) {
      message.warning('请先上传举证材料');
      return;
    }
    setAuditing(true);
    try {
      console.log('开始智能审核，itemId:', item.id);
      const baseInfo = currentBaseId ? { base_id: currentBaseId } : undefined;
      console.log('baseInfo:', baseInfo);
      const res = await compareEvidence(item.id, baseInfo) as any;
      console.log('审核结果:', res);
      message.success('审核完成');
      fetchEvidenceList();
      // 更新右侧预览
      if (selectedItem?.id === item.id) {
        setSelectedItem({ ...item, 审核结果: res.audit_result, 举证诊断结果: res.diagnosis });
      }
    } catch (e: any) {
      console.error('审核失败:', e);
      message.error(e.message || '审核失败');
    } finally {
      setAuditing(false);
    }
  };

  // 渲染审核结果标签
  const renderAuditResult = (result?: string) => {
    if (!result || result === '待审核') {
      return <Tag color="default">待审核</Tag>;
    }
    if (result === '满足') {
      return <Tag color="success" icon={<CheckCircleOutlined />}>满足</Tag>;
    }
    return <Tag color="error" icon={<CloseCircleOutlined />}>不满足</Tag>;
  };

  // 动态生成表格列
  const generateColumns = () => {
    if (!excelColumns.length) return [];
    
    const cols: any[] = excelColumns.map(col => ({
      title: col,
      dataIndex: col,
      key: col,
      width: col === '序号' ? 60 : 120,
      ellipsis: true,
    }));
    
    // 添加样例举证列
    cols.push({
      title: '样例举证',
      dataIndex: '样例举证',
      key: '样例举证',
      width: 150,
      render: (text: string, record: EvidenceItem) => {
        // 从举证名称中提取样例名称
        const sampleName = text || record.举证名称 || record['样例举证'] || '';
        
        // 点击预览按钮的处理函数
        const handlePreview = async () => {
          if (sampleName) {
            try {
              // 调用API获取文件信息
              const res = await getSampleFileInfo(sampleName) as any;
              const fileInfo = res || {};
              
              setPreviewSample({ 
                name: fileInfo.filename || sampleName, 
                url: fileInfo.url || `/api/v1/evidence/sample/${encodeURIComponent(sampleName)}`, 
                type: fileInfo.type || 'other' 
              });
              setSelectedItem(record);
            } catch (error) {
              // 如果API调用失败，使用默认值
              const sampleUrl = `/api/v1/evidence/sample/${encodeURIComponent(sampleName)}`;
              setPreviewSample({ name: sampleName, url: sampleUrl, type: 'other' });
              setSelectedItem(record);
            }
          }
        };
        
        return sampleName ? (
          <Space direction="vertical" size={0}>
            <span className="text-sm">{sampleName}</span>
            <Button type="link" size="small" icon={<EyeOutlined />} onClick={handlePreview}>
              预览
            </Button>
          </Space>
        ) : (
          <span className="text-gray-400">-</span>
        );
      }
    });
    
    // 添加局点上传举证材料列
    cols.push({
      title: '局点上传举证材料',
      dataIndex: '局点上传举证材料',
      key: '局点上传举证材料',
      width: 220,
      render: (text: string, record: EvidenceItem) => (
        <Space>
          {text ? (
            <>
              <Button type="link" size="small" icon={<EyeOutlined />}>{text}</Button>
              <Button type="link" size="small" onClick={() => { setUploadingItem(record); setUploadModalOpen(true); }}>
                更换
              </Button>
              <Button 
                type="link" 
                size="small" 
                icon={<RobotOutlined />} 
                onClick={() => handleAutoAudit(record)}
                loading={auditing && selectedItem?.id === record.id}
              >
                智能审核
              </Button>
            </>
          ) : (
            <Button type="primary" size="small" icon={<UploadOutlined />} onClick={() => { setUploadingItem(record); setUploadModalOpen(true); }}>
              上传
            </Button>
          )}
        </Space>
      )
    });
    
    // 添加审核结果列
    cols.push({
      title: '审核结果',
      dataIndex: '审核结果',
      key: '审核结果',
      width: 100,
      render: (result: string) => renderAuditResult(result)
    });
    
    return cols;
  };

  // 右侧预览区域
  const renderPreviewArea = () => {
    if (!selectedItem) {
      return (
        <div className="h-full flex items-center justify-center text-gray-400">
          请从左侧列表选择一项查看详情
        </div>
      );
    }

    // 渲染样例预览内容
    const renderSamplePreview = () => {
      if (!previewSample) {
        const sampleName = selectedItem.样例举证 || selectedItem.举证名称 || '';
        if (sampleName) {
          return (
            <div className="flex items-center gap-2">
              <FileOutlined className="text-blue-500" />
              <span>{sampleName}</span>
              <Button type="link" size="small" icon={<EyeOutlined />}>点击左侧预览按钮查看</Button>
            </div>
          );
        }
        return <Empty description="暂无样例" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
      }

      // 根据文件类型渲染不同的预览内容
      if (previewSample.type === 'image') {
        return (
          <div className="text-center h-full flex flex-col justify-center overflow-hidden" style={{ height: '100%' }}>
            <div className="flex-1 flex items-center justify-center overflow-hidden">
              <Image 
                src={previewSample.url} 
                alt={previewSample.name}
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
              />
            </div>
            <div className="mt-2 text-sm text-gray-500">{previewSample.name}</div>
          </div>
        );
      } else if (previewSample.type === 'pdf') {
        return (
          <div className="flex flex-col items-center gap-2 justify-center h-full">
            <FilePdfOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
            <span className="text-sm">{previewSample.name}</span>
            <Button type="primary" size="small" href={previewSample.url} target="_blank">
              下载查看
            </Button>
          </div>
        );
      } else if (previewSample.type === 'word') {
        return (
          <div className="flex flex-col items-center gap-2 justify-center h-full">
            <FileWordOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            <span className="text-sm">{previewSample.name}</span>
            <Button type="primary" size="small" href={previewSample.url} target="_blank">
              下载查看
            </Button>
          </div>
        );
      } else {
        return (
          <div className="flex flex-col items-center gap-2 justify-center h-full">
            <FileOutlined style={{ fontSize: 48, color: '#666' }} />
            <span className="text-sm">{previewSample.name}</span>
            <Button type="primary" size="small" href={previewSample.url} target="_blank">
              下载查看
            </Button>
          </div>
        );
      }
    };

    // 渲染局点上传举证预览内容
    const renderUploadPreview = () => {
      const uploadName = selectedItem.局点上传举证材料 || selectedItem.局点上传文件;
      if (!uploadName) {
        return <Empty description="暂未上传" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
      }

      // 构建文件URL
      const uploadUrl = `/api/v1/evidence/material/${selectedItem.id}`;
      const fileType = getFileType(uploadName);

      // 根据文件类型渲染不同的预览内容
      if (fileType === 'image') {
        return (
          <div className="text-center h-full flex flex-col justify-center overflow-hidden" style={{ height: '100%' }}>
            <div className="flex-1 flex items-center justify-center overflow-hidden">
              <Image 
                src={uploadUrl} 
                alt={uploadName}
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
              />
            </div>
            <div className="mt-2 text-sm text-gray-500">{uploadName}</div>
          </div>
        );
      } else if (fileType === 'pdf') {
        return (
          <div className="flex flex-col items-center gap-2 justify-center h-full">
            <FilePdfOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
            <span className="text-sm">{uploadName}</span>
            <Button type="primary" size="small" href={uploadUrl} target="_blank">
              下载查看
            </Button>
          </div>
        );
      } else if (fileType === 'word') {
        return (
          <div className="flex flex-col items-center gap-2 justify-center h-full">
            <FileWordOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            <span className="text-sm">{uploadName}</span>
            <Button type="primary" size="small" href={uploadUrl} target="_blank">
              下载查看
            </Button>
          </div>
        );
      } else {
        return (
          <div className="flex flex-col items-center gap-2 justify-center h-full">
            <FileOutlined style={{ fontSize: 48, color: '#666' }} />
            <span className="text-sm">{uploadName}</span>
            <Button type="primary" size="small" href={uploadUrl} target="_blank">
              下载查看
            </Button>
          </div>
        );
      }
    };

    return (
      <div className="h-full flex flex-col">
        {/* 样例举证预览 */}
        <Card size="small" title="样例举证预览" className="mb-2 flex-shrink-0" style={{ height: '33%', overflow: 'auto' }}>
          {renderSamplePreview()}
        </Card>

        {/* 局点上传举证预览 */}
        <Card size="small" title="局点上传举证预览" className="mb-2 flex-shrink-0" style={{ height: '33%', overflow: 'auto' }}>
          {renderUploadPreview()}
        </Card>

        {/* 举证诊断结果 */}
        <Card size="small" title="举证诊断结果" className="flex-shrink-0" style={{ height: '34%', overflow: 'auto' }}>
          {selectedItem.举证诊断结果 ? (
            <div className="text-sm text-gray-700 whitespace-pre-wrap">{selectedItem.举证诊断结果}</div>
          ) : (
            <Empty description="暂无诊断结果" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </Card>
      </div>
    );
  };

  const uploadProps = {
    beforeUpload: (file: File) => {
      handleUploadEvidenceList(file);
      return false;
    },
    showUploadList: false as const,
    accept: '.xlsx,.xls',
  };

  return (
    <div className="space-y-4">
      {/* 统计信息行 */}
      <Card>
        <Row gutter={24}>
          <Col span={6}>
            <Statistic title="总共涉及" value={totalCount} suffix="项" />
          </Col>
          <Col span={6}>
            <Statistic title="用户上传" value={uploadedCount} suffix="项" valueStyle={{ color: uploadedCount > 0 ? '#3f8600' : undefined }} />
          </Col>
          <Col span={6}>
            <Statistic title="满足" value={satisfiedCount} suffix="项" valueStyle={{ color: satisfiedCount > 0 ? '#3f8600' : undefined }} />
          </Col>
          <Col span={6}>
            {isAdmin && (
              <Upload {...uploadProps}>
                <Button type="primary" icon={<UploadOutlined />} loading={loading}>
                  上传证据清单
                </Button>
              </Upload>
            )}
          </Col>
        </Row>
      </Card>

      {/* 证据材料列表 - 左右布局 6:4 */}
      <Card title="证据材料列表">
        {excelData ? (
          <div style={{ display: 'flex', gap: 16, height: 500 }}>
            {/* 左侧列表 60% */}
            <div style={{ width: '60%', overflow: 'auto' }}>
              <Table
                columns={generateColumns()}
                dataSource={evidenceList}
                rowKey="id"
                size="small"
                pagination={false}
                scroll={{ x: 'max-content' }}
                onRow={(record) => ({
                  onClick: () => setSelectedItem(record),
                  style: { cursor: 'pointer', backgroundColor: selectedItem?.id === record.id ? '#e6f7ff' : undefined }
                })}
              />
            </div>
            
            {/* 右侧预览 40% */}
            <div style={{ width: '40%', borderLeft: '1px solid #f0f0f0', paddingLeft: 16 }}>
              {renderPreviewArea()}
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <FileExcelOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <p>暂无证据清单数据</p>
            {isAdmin && <p>请点击上方"上传证据清单"按钮上传Excel文件</p>}
          </div>
        )}
      </Card>

      {/* 上传举证材料弹窗 */}
      <Modal
        title={`上传举证材料 - ${uploadingItem?.举证名称 || ''}`}
        open={uploadModalOpen}
        onCancel={() => { setUploadModalOpen(false); setFileList([]); }}
        onOk={handleUploadEvidence}
        okText="上传"
      >
        <div className="mb-4">
          <Upload
            beforeUpload={(file) => { setFileList([file]); return false; }}
            onRemove={() => setFileList([])}
            fileList={fileList}
            maxCount={1}
            accept=".pdf,.docx,.doc,.png,.jpg,.jpeg"
          >
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
        </div>
        <div className="text-gray-500 text-sm">
          支持格式：PDF、Word、图片（PNG、JPG）
        </div>
      </Modal>
    </div>
  );
};

export default EvidenceComparePage;
