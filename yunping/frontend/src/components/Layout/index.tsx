import { useState, useEffect } from 'react';
import { Layout, Menu, Select, Typography, Button, Avatar } from 'antd';
import { DashboardOutlined, AuditOutlined, FileTextOutlined, RobotOutlined, SettingOutlined, LogoutOutlined, FolderOutlined, TeamOutlined, BankOutlined, UserOutlined, DiffOutlined, SecurityScanOutlined, ApiOutlined } from '@ant-design/icons';
import ItemDashboard from '../../pages/ItemDashboard';
import AuditPage from '../../pages/AuditPage';
import DeclarationCategoryPage from '../../pages/DeclarationCategoryPage';
import StandardTemplatePage from '../../pages/StandardTemplatePage';
import EvidenceComparePage from '../../pages/EvidenceComparePage';
import SensitiveMonitorPage from '../../pages/SensitiveMonitorPage';
import BaseManagePage from '../../pages/BaseManagePage';
import UserManagePage from '../../pages/UserManagePage';
import LLMConfigPage from '../../pages/LLMConfigPage';
import RiskIdentificationModal from '../../components/RiskIdentificationModal';
import { useAppStore } from '../../store';
import { getBases, checkRiskIdentification } from '../../api';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const AppLayout = () => {
  const [selectedKey, setSelectedKey] = useState('dashboard');
  const { userInfo, currentBaseId, setCurrentBase, logout } = useAppStore();
  const [bases, setBases] = useState<any[]>([]);
  const [riskModalOpen, setRiskModalOpen] = useState(false);
  const [riskChecked, setRiskChecked] = useState(false);

  const isBaseUser = userInfo?.role === 'base_user';

  useEffect(() => {
    getBases().then((r: any) => {
      const basesData = r.bases || [];
      setBases(basesData);
      
      // 基地用户登录后自动选择其关联的基地
      if (isBaseUser && !currentBaseId && basesData.length > 0) {
        // 基地用户只关联一个基地时，自动选中
        if (basesData.length === 1) {
          setCurrentBase(basesData[0].id, basesData[0].name);
        } else if (userInfo?.assigned_bases) {
          // 多个基地时，自动选中第一个关联基地
          try {
            const assignedIds = typeof userInfo.assigned_bases === 'string' 
              ? JSON.parse(userInfo.assigned_bases) 
              : userInfo.assigned_bases;
            if (Array.isArray(assignedIds) && assignedIds.length > 0) {
              const firstBase = basesData.find((b: any) => b.id === assignedIds[0]);
              if (firstBase) {
                setCurrentBase(firstBase.id, firstBase.name);
              }
            }
          } catch { /* 忽略解析错误 */ }
        }
      }
    }).catch(() => {});
  }, [userInfo]);

  // 基地用户首次登录自动弹出风险识别弹窗
  useEffect(() => {
    if (isBaseUser && currentBaseId && !riskChecked) {
      checkRiskIdentification(currentBaseId).then((res: any) => {
        if (!res.exists || !res.is_completed) {
          setRiskModalOpen(true);
        }
        setRiskChecked(true);
      }).catch(() => { setRiskChecked(true); });
    }
  }, [isBaseUser, currentBaseId, riskChecked]);

  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '整体进展看板' },
    { key: 'audit', icon: <AuditOutlined />, label: '申报风险识别' },
    {
      key: 'declaration',
      icon: <FileTextOutlined />,
      label: '申报书刷新',
      children: [
        { key: 'decl-01', icon: <FolderOutlined />, label: '01申报书' },
        { key: 'decl-02', icon: <FolderOutlined />, label: '02系统安全计划' },
        { key: 'decl-03', icon: <FolderOutlined />, label: '03业务连续性和供应链报告' },
        { key: 'decl-04', icon: <FolderOutlined />, label: '04可迁移性报告' },
        { key: 'decl-05', icon: <FolderOutlined />, label: '05标准符合性证明' },
        { key: 'decl-06', icon: <FolderOutlined />, label: '06统一规范落实情况' },
      ],
    },
    { key: 'standard', icon: <RobotOutlined />, label: '标准项刷新' },
    { key: 'evidence', icon: <DiffOutlined />, label: '证据对比' },
    { key: 'sensitive', icon: <SecurityScanOutlined />, label: '敏感信息监测' },
    {
      key: 'account',
      icon: <TeamOutlined />,
      label: '账户管理',
      children: [
        { key: 'base-manage', icon: <BankOutlined />, label: '基地管理' },
        { key: 'user-manage', icon: <UserOutlined />, label: '用户管理' },
      ],
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统配置',
      children: [
        { key: 'llm-config', icon: <ApiOutlined />, label: '大模型配置' },
      ]
    },
  ];

  const renderContent = () => {
    if (selectedKey.startsWith('decl-')) {
      const category = selectedKey.replace('decl-', '');
      return <DeclarationCategoryPage category={category} />;
    }
    switch (selectedKey) {
      case 'dashboard': return <ItemDashboard />;
      case 'audit': return <AuditPage />;
      case 'standard': return <StandardTemplatePage />;
      case 'evidence': return <EvidenceComparePage />;
      case 'sensitive': return <SensitiveMonitorPage />;
      case 'base-manage': return <BaseManagePage />;
      case 'user-manage': return <UserManagePage />;
      case 'llm-config': return <LLMConfigPage />;
      default: return <ItemDashboard />;
    }
  };

  const roleLabel: Record<string, string> = {
    sys_admin: '系统管理员', eval_admin: '评估管理员', base_user: '基地申报人员', auditor: '审核专家'
  };

  return (
    <Layout className="min-h-screen">
      <Header className="flex items-center justify-between bg-white shadow px-4">
        <Title level={4} className="!mb-0 !text-blue-600">智能预审Agent</Title>
        <div className="flex items-center gap-4">
          <span className="text-gray-500">当前基地：</span>
          <Select
            value={currentBaseId || undefined}
            placeholder="选择基地"
            style={{ width: 180 }}
            onChange={(v) => {
              const base = bases.find(b => b.id === v);
              setCurrentBase(v, base?.name || '');
              // 切换基地时重新检查风险识别
              setRiskChecked(false);
            }}
            options={bases.map(b => ({ label: b.name, value: b.id }))}
          />
          <Avatar size="small">{userInfo?.username?.[0] || 'U'}</Avatar>
          <span className="text-sm text-gray-600">{userInfo?.username} ({roleLabel[userInfo?.role] || userInfo?.role})</span>
          <Button type="link" icon={<LogoutOutlined />} onClick={logout}>退出</Button>
        </div>
      </Header>
      <Layout>
        <Sider width={260} className="bg-white">
          <Menu mode="inline" selectedKeys={[selectedKey]} items={menuItems} onClick={({ key }) => setSelectedKey(key)} className="h-full border-r" />
        </Sider>
        <Content className="p-6 bg-gray-50">{renderContent()}</Content>
      </Layout>

      {/* 基地用户首次登录弹出申报风险识别框 */}
      <RiskIdentificationModal
        open={riskModalOpen}
        onClose={() => setRiskModalOpen(false)}
        onComplete={() => { setRiskModalOpen(false); setRiskChecked(true); }}
      />
    </Layout>
  );
};

export default AppLayout;
