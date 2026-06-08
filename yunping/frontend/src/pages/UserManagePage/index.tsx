import { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, message, Popconfirm, Modal, Form, Input, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getUsers, createUser, updateUser, deleteUser, getBases, type UserDetail } from '../../api';

const roleOptions = [
  { label: '系统管理员', value: 'sys_admin' },
  { label: '评估管理员', value: 'eval_admin' },
  { label: '基地申报人员', value: 'base_user' },
  { label: '审核专家', value: 'auditor' },
];

const roleLabel: Record<string, string> = {
  sys_admin: '系统管理员', eval_admin: '评估管理员', base_user: '基地申报人员', auditor: '审核专家',
};

const UserManagePage = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [bases, setBases] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserDetail | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const userRes = await getUsers();
      setUsers((userRes as any).users || []);
    } catch (e: any) { message.error(e.message || '获取用户列表失败'); }
    try {
      const baseRes = await getBases();
      setBases((baseRes as any).bases || []);
    } catch (e: any) { message.error(e.message || '获取基地列表失败'); }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleAdd = () => {
    setEditingUser(null);
    form.resetFields();
    form.setFieldsValue({ role: 'base_user', assigned_bases: [] });
    setModalOpen(true);
  };

  const handleEdit = (record: any) => {
    setEditingUser(record);
    const baseIds = record.base_details?.map((b: any) => b.id) || JSON.parse(record.assigned_bases || '[]');
    form.setFieldsValue({ role: record.role, assigned_bases: baseIds, is_active: record.is_active });
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try { await deleteUser(id); message.success('删除成功'); fetchData(); }
    catch (e: any) { message.error(e.message || '删除失败'); }
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    // 管理员角色不需要关联基地，确保 assigned_bases 有值
    const assignedBases = values.assigned_bases || [];
    try {
      if (editingUser) {
        await updateUser(editingUser.id, { role: values.role, assigned_bases: assignedBases, is_active: values.is_active });
        message.success('更新成功');
      } else {
        await createUser({ username: values.username, password: values.password, role: values.role, assigned_bases: assignedBases });
        message.success('创建成功');
      }
      setModalOpen(false);
      fetchData();
    } catch (e: any) { message.error(e.message || '操作失败'); }
  };

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '角色', dataIndex: 'role', key: 'role', width: 120,
      render: (r: string) => <Tag color={r === 'sys_admin' ? 'red' : r === 'eval_admin' ? 'orange' : r === 'auditor' ? 'blue' : 'green'}>{roleLabel[r] || r}</Tag>,
    },
    { title: '关联基地', key: 'bases', width: 250,
      render: (_: any, r: any) => {
        if (r.role !== 'base_user') return <Tag color="blue">所有基地</Tag>;
        const details = r.base_details || [];
        if (!details.length) return <span className="text-gray-400">未关联</span>;
        return <Space size={4} wrap>{details.map((b: any) => <Tag key={b.id}>{b.name}</Tag>)}</Space>;
      },
    },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (active: boolean) => <Tag color={active ? 'green' : 'red'}>{active ? '启用' : '禁用'}</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180,
      render: (t: string) => new Date(t).toLocaleString('zh-CN'),
    },
    { title: '操作', key: 'action', width: 150,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该用户？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card title="用户管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增用户</Button>}>
      <Table columns={columns} dataSource={users} rowKey="id" loading={loading} pagination={false} />
      <Modal title={editingUser ? '编辑用户' : '新增用户'} open={modalOpen} onCancel={() => setModalOpen(false)} onOk={handleSubmit} width={600}>
        <Form form={form} layout="vertical">
          {!editingUser && (
            <>
              <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3, message: '至少3个字符' }]}>
                <Input placeholder="请输入用户名" />
              </Form.Item>
              <Form.Item name="password" label="密码" rules={[{ required: true, min: 6, message: '至少6个字符' }]}>
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
            </>
          )}
          <Form.Item name="role" label="角色" rules={[{ required: true, message: '请选择角色' }]}>
            <Select options={roleOptions} placeholder="请选择角色" onChange={(value) => {
              // 切换为管理员角色时清空关联基地并更新校验
              if (value !== 'base_user') {
                form.setFieldValue('assigned_bases', []);
              }
              form.validateFields(['assigned_bases']).catch(() => {});
            }} />
          </Form.Item>
          <Form.Item name="assigned_bases" label="关联基地" rules={[{ required: form.getFieldValue('role') === 'base_user', message: '基地申报人员请至少选择一个基地' }]}>
            <Select mode="multiple" placeholder={form.getFieldValue('role') === 'base_user' ? '请选择关联基地' : '管理员角色无需关联基地，可选填'} options={bases.map((b: any) => ({ label: `${b.name} (${b.code})`, value: b.id }))} />
          </Form.Item>
          {editingUser && (
            <Form.Item name="is_active" label="状态" valuePropName="checked">
              <Select options={[{ label: '启用', value: true }, { label: '禁用', value: false }]} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </Card>
  );
};

export default UserManagePage;
