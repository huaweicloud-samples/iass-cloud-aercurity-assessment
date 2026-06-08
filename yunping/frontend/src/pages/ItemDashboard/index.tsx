import { useState, useEffect } from 'react';
import { Card, Select, Progress, Row, Col, Typography, Tag, Spin, Statistic } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import { getProgressOverview, getBases, type BaseProgress, type ProgressOverview } from '../../api';
import { useAppStore } from '../../store';

const { Title, Text } = Typography;

const ItemDashboard = () => {
  const { userInfo, currentBaseId } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [progressData, setProgressData] = useState<ProgressOverview | null>(null);
  const [selectedBaseId, setSelectedBaseId] = useState<string>('');
  const [bases, setBases] = useState<any[]>([]);

  const isAdmin = userInfo?.role === 'sys_admin' || userInfo?.role === 'eval_admin' || userInfo?.role === 'auditor';
  const isBaseUser = userInfo?.role === 'base_user';

  // 获取基地列表
  useEffect(() => {
    getBases().then((r: any) => setBases(r.bases || [])).catch(() => {});
  }, []);

  // 获取进度数据
  const fetchProgress = async (baseId?: string) => {
    setLoading(true);
    try {
      const res = await getProgressOverview(baseId);
      setProgressData(res.data);
    } catch (e: any) {
      console.error('获取进度失败:', e);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    if (isBaseUser && currentBaseId) {
      setSelectedBaseId(currentBaseId);
      fetchProgress(currentBaseId);
    } else if (isAdmin) {
      fetchProgress();
    }
  }, [userInfo, currentBaseId]);

  // 管理员切换基地
  const handleBaseChange = (baseId: string) => {
    setSelectedBaseId(baseId);
    fetchProgress(baseId || undefined);
  };

  // 计算整体进度
  const calculateOverallProgress = (baseProgress: BaseProgress) => {
    const declarationTotal = baseProgress.declaration_progress.reduce((sum, item) => sum + item.total, 0);
    const declarationEdited = baseProgress.declaration_progress.reduce((sum, item) => sum + item.edited, 0);
    const standardProgress = baseProgress.standard_progress.progress;
    const evidenceProgress = baseProgress.evidence_progress.progress;

    // 整体进度 = (01-06文档进度 + 标准项进度 + 举证材料进度) / 3
    const declarationProgress = declarationTotal > 0 ? (declarationEdited / declarationTotal) * 100 : 0;
    const overallProgress = (declarationProgress + standardProgress + evidenceProgress) / 3;

    return {
      declarationProgress,
      standardProgress,
      evidenceProgress,
      overallProgress
    };
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  // 基地用户端 - 显示整体进展看板
  if (isBaseUser && progressData && progressData.bases.length > 0) {
    const baseProgress = progressData.bases[0];
    const categoryNames: Record<string, string> = {
      '01': '01申报书',
      '02': '02系统安全计划',
      '03': '03业务连续性和供应链报告',
      '04': '04可迁移性报告',
      '05': '05标准符合性证明',
      '06': '06统一规范落实情况'
    };

    const { declarationProgress, standardProgress, evidenceProgress, overallProgress } = calculateOverallProgress(baseProgress);

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <Title level={4}>整体进展看板 - {baseProgress.base_name}</Title>
          <Tag color="blue" icon={<CheckCircleOutlined />}>
            基地用户
          </Tag>
        </div>

        {/* 上方：整体进度条 */}
        <Card>
          <div className="mb-4">
            <Text strong className="text-lg">整体刷新进展</Text>
          </div>
          <Progress
            percent={Math.round(overallProgress)}
            status={overallProgress === 100 ? 'success' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
            strokeWidth={20}
          />
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="text-center">
              <Text type="secondary">01-06文档</Text>
              <div className="text-2xl font-bold text-blue-600">{Math.round(declarationProgress)}%</div>
            </div>
            <div className="text-center">
              <Text type="secondary">标准项刷新</Text>
              <div className="text-2xl font-bold text-green-600">{Math.round(standardProgress)}%</div>
            </div>
            <div className="text-center">
              <Text type="secondary">举证材料</Text>
              <div className="text-2xl font-bold text-orange-600">{Math.round(evidenceProgress)}%</div>
            </div>
          </div>
        </Card>

        {/* 中间：01-06文档名称及进展百分数 */}
        <Card title="01-06文档刷新进展">
          <Row gutter={[16, 16]}>
            {baseProgress.declaration_progress.map((item) => (
              <Col xs={24} sm={12} lg={8} key={item.category}>
                <Card size="small" className="progress-card">
                  <div className="flex justify-between items-center mb-2">
                    <Text strong>{categoryNames[item.category]}</Text>
                    <Tag color={item.edited === item.total ? 'green' : 'blue'}>
                      {Math.round(item.progress)}%
                    </Tag>
                  </div>
                  <Progress
                    percent={Math.round(item.progress)}
                    status={item.edited === item.total ? 'success' : 'active'}
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                  />
                  <div className="mt-2 text-xs text-gray-500">
                    {item.edited === item.total ? '已完成' : `已完成 ${item.edited}/${item.total} 个模板`}
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>

        {/* 下方：标准项刷新进展 */}
        <Card title="标准项刷新进展">
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Statistic
                title="涉及526条标准项"
                value={baseProgress.standard_progress.edited}
                suffix={`/ ${baseProgress.standard_progress.total} 条`}
                valueStyle={{ color: baseProgress.standard_progress.edited === baseProgress.standard_progress.total ? '#3f8600' : '#1890ff' }}
              />
            </Col>
            <Col xs={24} md={12}>
              <Progress
                type="circle"
                percent={Math.round(baseProgress.standard_progress.progress)}
                status={baseProgress.standard_progress.edited === baseProgress.standard_progress.total ? 'success' : 'active'}
                width={120}
              />
            </Col>
          </Row>
        </Card>

        {/* 下方：举证材料进展 */}
        <Card title="举证材料进展">
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Statistic
                title="共涉及举证材料"
                value={baseProgress.evidence_progress.passed}
                suffix={`/ ${baseProgress.evidence_progress.total} 条`}
                valueStyle={{ color: baseProgress.evidence_progress.passed === baseProgress.evidence_progress.total ? '#3f8600' : '#1890ff' }}
              />
            </Col>
            <Col xs={24} md={12}>
              <Progress
                type="circle"
                percent={Math.round(baseProgress.evidence_progress.progress)}
                status={baseProgress.evidence_progress.passed === baseProgress.evidence_progress.total ? 'success' : 'active'}
                width={120}
              />
            </Col>
          </Row>
        </Card>
      </div>
    );
  }

  // 管理员端 - 显示所有基地进度或选中的基地进度
  if (isAdmin) {
    const categoryNames: Record<string, string> = {
      '01': '01申报书',
      '02': '02系统安全计划',
      '03': '03业务连续性和供应链报告',
      '04': '04可迁移性报告',
      '05': '05标准符合性证明',
      '06': '06统一规范落实情况'
    };

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <Title level={4}>整体进展看板</Title>
          <Select
            value={selectedBaseId}
            placeholder="选择基地"
            style={{ width: 200 }}
            onChange={handleBaseChange}
            allowClear
            options={[
              { label: '全部基地', value: '' },
              ...bases.map(b => ({ label: b.name, value: b.id }))
            ]}
          />
        </div>

        {selectedBaseId && progressData && progressData.bases.length > 0 ? (
          // 显示单个基地的整体进展
          <>
            {(() => {
              const baseProgress = progressData.bases[0];
              const { declarationProgress, standardProgress, evidenceProgress, overallProgress } = calculateOverallProgress(baseProgress);

              return (
                <>
                  {/* 上方：整体进度条 */}
                  <Card>
                    <div className="mb-4">
                      <Text strong className="text-lg">整体刷新进展 - {baseProgress.base_name}</Text>
                    </div>
                    <Progress
                      percent={Math.round(overallProgress)}
                      status={overallProgress === 100 ? 'success' : 'active'}
                      strokeColor={{
                        '0%': '#108ee9',
                        '100%': '#87d068',
                      }}
                      strokeWidth={20}
                    />
                    <div className="mt-4 grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <Text type="secondary">01-06文档</Text>
                        <div className="text-2xl font-bold text-blue-600">{Math.round(declarationProgress)}%</div>
                      </div>
                      <div className="text-center">
                        <Text type="secondary">标准项刷新</Text>
                        <div className="text-2xl font-bold text-green-600">{Math.round(standardProgress)}%</div>
                      </div>
                      <div className="text-center">
                        <Text type="secondary">举证材料</Text>
                        <div className="text-2xl font-bold text-orange-600">{Math.round(evidenceProgress)}%</div>
                      </div>
                    </div>
                  </Card>

                  {/* 中间：01-06文档名称及进展百分数 */}
                  <Card title="01-06文档刷新进展">
                    <Row gutter={[16, 16]}>
                      {baseProgress.declaration_progress.map((item) => (
                        <Col xs={24} sm={12} lg={8} key={item.category}>
                          <Card size="small" className="progress-card">
                            <div className="flex justify-between items-center mb-2">
                              <Text strong>{categoryNames[item.category]}</Text>
                              <Tag color={item.edited === item.total ? 'green' : 'blue'}>
                                {Math.round(item.progress)}%
                              </Tag>
                            </div>
                            <Progress
                              percent={Math.round(item.progress)}
                              status={item.edited === item.total ? 'success' : 'active'}
                              strokeColor={{
                                '0%': '#108ee9',
                                '100%': '#87d068',
                              }}
                            />
                            <div className="mt-2 text-xs text-gray-500">
                              {item.edited === item.total ? '已完成' : `已完成 ${item.edited}/${item.total} 个模板`}
                            </div>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  </Card>

                  {/* 下方：标准项刷新进展 */}
                  <Card title="标准项刷新进展">
                    <Row gutter={[16, 16]}>
                      <Col xs={24} md={12}>
                        <Statistic
                          title="涉及526条标准项"
                          value={baseProgress.standard_progress.edited}
                          suffix={`/ ${baseProgress.standard_progress.total} 条`}
                          valueStyle={{ color: baseProgress.standard_progress.edited === baseProgress.standard_progress.total ? '#3f8600' : '#1890ff' }}
                        />
                      </Col>
                      <Col xs={24} md={12}>
                        <Progress
                          type="circle"
                          percent={Math.round(baseProgress.standard_progress.progress)}
                          status={baseProgress.standard_progress.edited === baseProgress.standard_progress.total ? 'success' : 'active'}
                          width={120}
                        />
                      </Col>
                    </Row>
                  </Card>

                  {/* 下方：举证材料进展 */}
                  <Card title="举证材料进展">
                    <Row gutter={[16, 16]}>
                      <Col xs={24} md={12}>
                        <Statistic
                          title="共涉及举证材料"
                          value={baseProgress.evidence_progress.passed}
                          suffix={`/ ${baseProgress.evidence_progress.total} 条`}
                          valueStyle={{ color: baseProgress.evidence_progress.passed === baseProgress.evidence_progress.total ? '#3f8600' : '#1890ff' }}
                        />
                      </Col>
                      <Col xs={24} md={12}>
                        <Progress
                          type="circle"
                          percent={Math.round(baseProgress.evidence_progress.progress)}
                          status={baseProgress.evidence_progress.passed === baseProgress.evidence_progress.total ? 'success' : 'active'}
                          width={120}
                        />
                      </Col>
                    </Row>
                  </Card>
                </>
              );
            })()}
          </>
        ) : progressData && progressData.bases.length > 0 ? (
          // 显示所有基地的概览
          <Row gutter={[16, 16]}>
            {progressData?.bases.map((baseProgress) => {
              const { declarationProgress, standardProgress, evidenceProgress, overallProgress } = calculateOverallProgress(baseProgress);

              return (
                <Col xs={24} xl={12} key={baseProgress.base_id}>
                  <Card
                    title={
                      <div className="flex justify-between items-center">
                        <span>{baseProgress.base_name}</span>
                        <Tag color="blue">{baseProgress.base_code}</Tag>
                      </div>
                    }
                    className="h-full"
                  >
                    {/* 整体进度 */}
                    <div className="mb-4">
                      <Text strong className="text-sm">整体刷新进展</Text>
                      <Progress
                        percent={Math.round(overallProgress)}
                        size="small"
                        status={overallProgress === 100 ? 'success' : 'active'}
                      />
                    </div>

                    {/* 01-06文档进度 */}
                    <Text strong className="block mb-2 text-sm">01-06文档刷新进度</Text>
                    <Row gutter={[8, 8]} className="mb-4">
                      {baseProgress.declaration_progress.map((item) => (
                        <Col xs={12} sm={8} key={item.category}>
                          <div className="text-center p-2 bg-gray-50 rounded">
                            <div className="text-xs text-gray-500 mb-1">{item.category}</div>
                            <Progress
                              percent={Math.round(item.progress)}
                              size="small"
                              showInfo={false}
                              strokeColor={item.edited === item.total ? '#52c41a' : '#1890ff'}
                            />
                            <div className="text-xs mt-1">
                              <Tag color={item.edited === item.total ? 'success' : 'processing'}>
                                {item.edited === item.total ? '完成' : `${Math.round(item.progress)}%`}
                              </Tag>
                            </div>
                          </div>
                        </Col>
                      ))}
                    </Row>

                    {/* 标准项和举证材料进度 */}
                    <Row gutter={16}>
                      <Col span={12}>
                        <Text strong className="block mb-2 text-sm">标准项刷新</Text>
                        <div className="text-center">
                          <div className="text-lg font-bold">{baseProgress.standard_progress.edited}/{baseProgress.standard_progress.total}</div>
                          <Progress
                            type="circle"
                            percent={Math.round(baseProgress.standard_progress.progress)}
                            size={60}
                            strokeWidth={6}
                          />
                        </div>
                      </Col>
                      <Col span={12}>
                        <Text strong className="block mb-2 text-sm">举证材料</Text>
                        <div className="text-center">
                          <div className="text-lg font-bold">{baseProgress.evidence_progress.passed}/{baseProgress.evidence_progress.total}</div>
                          <Progress
                            type="circle"
                            percent={Math.round(baseProgress.evidence_progress.progress)}
                            size={60}
                            strokeWidth={6}
                          />
                        </div>
                      </Col>
                    </Row>
                  </Card>
                </Col>
              );
            })}
          </Row>
        ) : (
          <div className="text-center text-gray-500 py-12">
            暂无进度数据
          </div>
        )}
      </div>
    );
  }

  return null;
};

export default ItemDashboard;
