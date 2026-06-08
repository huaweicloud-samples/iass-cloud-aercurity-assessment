import { useState, useEffect } from 'react';
import { Card, Descriptions, Tag, Table, Button, message, Empty, Statistic, Row, Col, Alert, Popconfirm } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, WarningOutlined, DeleteOutlined } from '@ant-design/icons';
import { getMyRiskRecords, getAllRiskRecords, deleteRiskRecord, type RiskRecord } from '../../api';
import { useAppStore } from '../../store';

const AuditPage = () => {
  const [records, setRecords] = useState<RiskRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const { userInfo } = useAppStore();
  const isAdmin = userInfo?.role === 'sys_admin' || userInfo?.role === 'eval_admin';

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = isAdmin ? (await getAllRiskRecords() as any) : (await getMyRiskRecords() as any);
      setRecords(res.records || []);
    } catch (e: any) { message.error(e.message || '获取数据失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleDelete = async (id: string) => {
    try { await deleteRiskRecord(id); message.success('删除成功'); fetchData(); }
    catch (e: any) { message.error(e.message || '删除失败'); }
  };

  const renderRiskTag = (risk?: string) => {
    if (!risk) return <Tag>未知</Tag>;
    const map: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
      high: { color: 'red', icon: <CloseCircleOutlined />, label: '高风险' },
      medium: { color: 'orange', icon: <WarningOutlined />, label: '中风险' },
      low: { color: 'green', icon: <CheckCircleOutlined />, label: '低风险' },
    };
    const info = map[risk] || { color: 'default', icon: null, label: risk };
    return <Tag color={info.color} icon={info.icon}>{info.label}</Tag>;
  };

  const renderYesNo = (val?: string) => {
    if (!val) return <span className="text-gray-400">-</span>;
    return val === 'yes'
      ? <Tag color="green">是</Tag>
      : <Tag color="red">否</Tag>;
  };

  const renderCheckTag = (check?: string) => {
    if (!check) return <span className="text-gray-400">-</span>;
    return check === 'pass'
      ? <Tag color="green" icon={<CheckCircleOutlined />}>达标</Tag>
      : <Tag color="red" icon={<CloseCircleOutlined />}>不达标</Tag>;
  };

  const renderRecordDetail = (record: RiskRecord) => (
    <div className="space-y-4">
      {/* 局点信息 */}
      <Card size="small" title="1) 局点信息" className="border-l-4 border-l-blue-400">
        <Descriptions column={3} size="small">
          <Descriptions.Item label="局点名称">{record.site_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="IP地址">{record.site_ip || '-'}</Descriptions.Item>
          <Descriptions.Item label="Region名称">{record.region_name || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 服务器规模及安可计划 */}
      <Card size="small" title="2) 服务器规模及安可计划" className="border-l-4 border-l-blue-400">
        <Row gutter={16} className="mb-3">
          <Col span={6}><Statistic title="信创服务器" value={record.xinchuang_servers ?? '-'} suffix="台" /></Col>
          <Col span={6}><Statistic title="X86服务器" value={record.x86_servers ?? '-'} suffix="台" /></Col>
          <Col span={6}><Statistic title="物理服务器总数" value={record.total_servers ?? '-'} suffix="台" /></Col>
          <Col span={6}><Statistic title="信创占比" value={record.xinchuang_ratio ?? '-'} suffix="%" /></Col>
        </Row>
        <div className="flex items-center gap-4">
          <span>服务器数量检查：{renderCheckTag(record.server_check)}</span>
          <span>信创占比检查：{renderCheckTag(record.xinchuang_check)}</span>
        </div>
        <div className="bg-red-50 border border-red-200 rounded p-2 mt-2">
          <span className="text-red-600 text-sm font-medium">评估要求：物理服务器不低于100台，信创服务器占比不低于60%</span>
        </div>
      </Card>

      {/* 测评通过情况 */}
      <Card size="small" title="3) 测评通过情况" className="border-l-4 border-l-blue-400">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="等保测评（渗透测试）是否通过并在有效期">{renderYesNo(record.dengbao_passed)}</Descriptions.Item>
          <Descriptions.Item label="密评通过情况">{renderYesNo(record.mipin_passed)}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 运营运维模式 */}
      <Card size="small" title="4) 运营运维模式" className="border-l-4 border-l-blue-400">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="资产归属华为？">{renderYesNo(record.asset_huawei)}</Descriptions.Item>
          <Descriptions.Item label="合同是否与政府客户直签？">{renderYesNo(record.contract_direct)}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 物理机房 */}
      <Card size="small" title="5) 物理机房" className="border-l-4 border-l-blue-400">
        <Descriptions column={1} size="small">
          <Descriptions.Item label="是否独享机房？">{renderYesNo(record.exclusive_room)}</Descriptions.Item>
          <Descriptions.Item label="L1是否是华为供应商">{renderYesNo(record.l1_huawei_supplier)}</Descriptions.Item>
          <Descriptions.Item label="人员进出机房是否符合华为数据中心要求？">{renderYesNo(record.access_compliant)}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 风险评估结果 */}
      <Card size="small" title="综合风险评估" className="border-l-4 border-l-red-400">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-base font-medium">风险等级：</span>
          {renderRiskTag(record.overall_risk)}
        </div>
        {record.risk_items && record.risk_items.length > 0 ? (
          <Alert type="error" message="风险项" description={
            <ul className="list-disc pl-4 mt-1">
              {record.risk_items.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          } showIcon />
        ) : (
          <Alert type="success" message="未发现风险项" showIcon />
        )}
      </Card>
    </div>
  );

  const columns = [
    { title: '基地', dataIndex: 'base_name', key: 'base_name', width: 120 },
    { title: '用户', dataIndex: 'user_name', key: 'user_name', width: 100 },
    { title: '局点', dataIndex: 'site_name', key: 'site_name', width: 120 },
    { title: '服务器总数', dataIndex: 'total_servers', key: 'total_servers', width: 100, render: (v: number) => v ?? '-' },
    { title: '信创占比', dataIndex: 'xinchuang_ratio', key: 'xinchuang_ratio', width: 100, render: (v: number) => v !== undefined ? `${v}%` : '-' },
    { title: '风险等级', dataIndex: 'overall_risk', key: 'overall_risk', width: 100, render: (v: string) => renderRiskTag(v) },
    { title: '状态', dataIndex: 'is_completed', key: 'is_completed', width: 80, render: (v: boolean) => v ? <Tag color="green">已完成</Tag> : <Tag color="orange">填写中</Tag> },
    ...(isAdmin ? [{
      title: '操作', key: 'action', width: 80,
      render: (_: any, record: RiskRecord) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      ),
    }] : []),
  ];

  return (
    <div className="space-y-4">
      <Card title="申报风险识别" extra={
        <span className="text-gray-400 text-sm">{isAdmin ? '所有基地评估结果' : '我的基地评估结果'}</span>
      }>
        {records.length > 0 ? (
          <Table
            columns={columns}
            dataSource={records}
            rowKey="id"
            loading={loading}
            pagination={false}
            expandable={{
              expandedRowRender: renderRecordDetail,
            }}
          />
        ) : (
          <Empty description={loading ? '加载中...' : '暂无风险识别记录，请先填写申报信息'} />
        )}
      </Card>
    </div>
  );
};

export default AuditPage;
