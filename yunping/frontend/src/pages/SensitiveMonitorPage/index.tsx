import { useState, useEffect } from 'react';
import { Card, Table, Tag, Space, Button, message, Alert, Typography, Row, Col } from 'antd';
import { ScanOutlined, FolderOutlined, RightOutlined } from '@ant-design/icons';
import { useAppStore } from '../../store';
import { scanSensitiveInfo, getSensitiveResults, type SensitiveScanResult } from '../../api';

const { Title, Text } = Typography;

// 不再需要这些接口，使用从API导入的SensitiveScanResult和SensitiveItem

const SensitiveMonitorPage = () => {
  const [scanResults, setScanResults] = useState<SensitiveScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const { currentBaseId, currentBaseName } = useAppStore();
  
  // 目录列表
  const directoryItems = [
    { id: '1', name: '01申报书' },
    { id: '2', name: '02系统安全计划' },
    { id: '3', name: '03业务连续性和供应链报告' },
    { id: '4', name: '04可迁移性报告' },
    { id: '5', name: '05标准符合性证明' },
    { id: '6', name: '06统一规范落实情况' },
    { id: '7', name: '标准项刷新' },
  ];
  
  // 统计信息
  const totalSensitiveCount = scanResults?.total_sensitive_count || 0;
  const micronCount = scanResults?.category_counts?.['美光'] || 0;
  const mysqlCount = scanResults?.category_counts?.['mysql5.7'] || 0;
  const lastScanTime = scanResults?.scan_time ? new Date(scanResults.scan_time).toLocaleString('zh-CN') : '2026/5/26 17:38:44';

  const fetchResults = async () => {
    if (!currentBaseId) return;
    
    setLoading(true);
    try {
      const response = await getSensitiveResults(currentBaseId);
      setScanResults(response.data);
    } catch (error) {
      console.error('获取扫描结果失败:', error);
      // 如果API未实现或出错，使用空数据
      setScanResults({
        base_id: currentBaseId,
        base_name: currentBaseName || '',
        total_sensitive_count: 0,
        category_counts: { '美光': 0, '镁光': 0, 'mysql5.7': 0 },
        sensitive_items: [],
        scan_time: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { 
    if (currentBaseId) {
      fetchResults(); 
    }
  }, [currentBaseId]);

  const handleScan = async () => {
    if (!currentBaseId) { 
      message.warning('请先选择基地'); 
      return; 
    }
    
    setScanning(true);
    try {
      const response = await scanSensitiveInfo(currentBaseId);
      setScanResults(response.data);
      message.success('敏感信息扫描完成');
    } catch (error: any) {
      console.error('扫描失败:', error);
      message.error(error.message || '扫描失败，请重试');
    } finally {
      setScanning(false);
    }
  };

  // 敏感信息详情表格列定义
  const sensitiveColumns = [
    { title: '文档名称', dataIndex: 'document_name', key: 'document_name' },
    { title: '分类', dataIndex: 'category', key: 'category', width: 120 },
    { title: '敏感类型', dataIndex: 'sensitive_type', key: 'sensitive_type', width: 100 },
    { title: '关键字', dataIndex: 'keywords', key: 'keywords', width: 150,
      render: (keywords: string[]) => (
        <Space size={4} wrap>
          {keywords.map((kw, idx) => (
            <Tag key={idx} color="orange">{kw}</Tag>
          ))}
        </Space>
      ),
    },
    { title: '出现次数', dataIndex: 'total_count', key: 'total_count', width: 100,
      render: (count: number) => <Tag color="red">{count}次</Tag>
    },
    { title: '内容预览', dataIndex: 'content_preview', key: 'content_preview', 
      render: (text: string) => <span className="text-gray-600">{text.length > 50 ? text.substring(0, 50) + '...' : text}</span>
    },
  ];

  return (
    <div className="space-y-6">
      {/* 顶部区域 - 统计概览 */}
      <Card>
        <div className="flex justify-between items-center mb-6">
          <Title level={4} style={{ margin: 0 }}>敏感信息监测</Title>
          <Space>
            <Text type="secondary">最近扫描：{lastScanTime}</Text>
            <Button type="primary" icon={<ScanOutlined />} loading={scanning} onClick={handleScan}>
              重新扫描
            </Button>
          </Space>
        </div>
        
        {/* 统计卡片 */}
        <Row gutter={16} className="mb-4">
          <Col span={8}>
            <Card size="small" className="text-center">
              <div className="text-gray-500 text-sm mb-2">涉及敏感信息总数</div>
              <div className={`text-2xl font-bold ${totalSensitiveCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {totalSensitiveCount > 0 ? `△${totalSensitiveCount}处` : '△0处'}
              </div>
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small" className="text-center">
              <div className="text-gray-500 text-sm mb-2">美光/镁光</div>
              <div className={`text-2xl font-bold ${micronCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {micronCount}处
              </div>
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small" className="text-center">
              <div className="text-gray-500 text-sm mb-2">Mysql5.7</div>
              <div className={`text-2xl font-bold ${mysqlCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {mysqlCount}处
              </div>
            </Card>
          </Col>
        </Row>
        
        {/* 统计说明 */}
        <Text type="secondary" className="text-sm">
          共涉及{totalSensitiveCount}个敏感信息，其中美光/镁光{micronCount}个，Mysql5.7{mysqlCount}个
        </Text>
      </Card>
      
      {/* 下方区域 - 详细目录列表 */}
      <Card>
        <Title level={4} style={{ marginBottom: 16 }}>涉及敏感信息具体目录</Title>
        
        <div className="space-y-2">
          {directoryItems.map((item) => {
            // 检查该目录是否有敏感信息
            const hasSensitiveInfo = scanResults?.sensitive_items?.some(
              sensitiveItem => sensitiveItem.category.includes(item.name.replace(/\d+\s*/, ''))
            );
            
            return (
              <div 
                key={item.id} 
                className="flex items-center justify-between p-3 border border-gray-200 rounded hover:bg-gray-50 cursor-pointer"
              >
                <div className="flex items-center space-x-3">
                  <RightOutlined className="text-gray-400" />
                  <FolderOutlined className="text-blue-500" />
                  <span className="font-medium">{item.name}</span>
                </div>
                <Tag color={hasSensitiveInfo ? "red" : "green"}>
                  {hasSensitiveInfo ? "发现敏感信息" : "无异常"}
                </Tag>
              </div>
            );
          })}
        </div>
      </Card>
      
      {/* 敏感信息详情表格 */}
      {scanResults?.sensitive_items && scanResults.sensitive_items.length > 0 && (
        <Card title="敏感信息详情">
          <Alert 
            type="warning" 
            message={`共发现 ${totalSensitiveCount} 处敏感信息，请及时处理`} 
            showIcon 
            className="mb-4" 
          />
          <Table 
            columns={sensitiveColumns} 
            dataSource={scanResults.sensitive_items} 
            rowKey={(record, index) => `${record.document_name}-${record.sensitive_type}-${index}`}
            loading={loading} 
            pagination={false} 
          />
        </Card>
      )}
    </div>
  );
};

export default SensitiveMonitorPage;
