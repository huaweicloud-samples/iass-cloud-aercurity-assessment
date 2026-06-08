import { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, message, Popconfirm, Modal, Form, Input } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getBases, createBase, updateBase, deleteBase, type BaseInfo } from '../../api';

const BaseManagePage = () => {
  const [bases, setBases] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingBase, setEditingBase] = useState<BaseInfo | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = (await getBases()) as any;
      setBases(res.bases || []);
    } catch (e: any) { message.error(e.message || '获取基地列表失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAdd = () => {
    setEditingBase(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: BaseInfo) => {
    setEditingBase(record);
    form.setFieldsValue({ name: record.name, code: record.code });
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try { await deleteBase(id); message.success('删除成功'); fetchData(); }
    catch (e: any) { message.error(e.message || '删除失败'); }
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editingBase) {
        await updateBase(editingBase.id, values);
        message.success('更新成功');
      } else {
        await createBase(values);
        message.success('创建成功');
      }
      setModalOpen(false);
      fetchData();
    } catch (e: any) { message.error(e.message || '操作失败'); }
  };

  const columns = [
    { title: '基地名称', dataIndex: 'name', key: 'name' },
    { title: '基地编码', dataIndex: 'code', key: 'code' },
    { title: '申报状态', dataIndex: 'declaration_status', key: 'status', width: 120,
      render: (s: string) => {
        const map: Record<string, { color: string; label: string }> = {
          pending: { color: 'default', label: '待申报' },
          submitted: { color: 'processing', label: '已提交' },
          approved: { color: 'success', label: '已通过' },
          rejected: { color: 'error', label: '已驳回' },
        };
        const info = map[s] || { color: 'default', label: s };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
    { title: '关联用户', key: 'users', width: 200,
      render: (_: any, r: any) => r.admin_user_names?.length ? <span className="text-sm text-gray-600">{r.admin_user_names.join(', ')}</span> : <span className="text-gray-400">-</span>,
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180,
      render: (t: string) => new Date(t).toLocaleString('zh-CN'),
    },
    { title: '操作', key: 'action', width: 150,
      render: (_: any, record: BaseInfo) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该基地？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card title="基地管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增基地</Button>}>
      <Table columns={columns} dataSource={bases} rowKey="id" loading={loading} pagination={false} />
      <Modal title={editingBase ? '编辑基地' : '新增基地'} open={modalOpen} onCancel={() => setModalOpen(false)} onOk={handleSubmit}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="基地名称" rules={[{ required: true, message: '请输入基地名称' }]}>
            <Input placeholder="请输入基地名称" />
          </Form.Item>
          <Form.Item name="code" label="基地编码" rules={[{ required: true, message: '请输入基地编码' }]}>
            <Input placeholder="请输入基地编码" disabled={!!editingBase} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default BaseManagePage;
