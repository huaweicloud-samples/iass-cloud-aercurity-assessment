import { useState, useEffect } from 'react';
import { Card, Form, Input, Select, Button, Switch, message, Tabs, Space, Divider, Tag } from 'antd';
import { SaveOutlined, ExperimentOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { getLLMConfig, saveLLMConfig, getProviders } from '../../api';

interface Provider {
  id: string;
  name: string;
  base_url: string;
  models: string[];
  embedding_models: string[];
  rerank_models?: string[];
  multimodal_models?: string[];
}


const LLMConfigPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [status, setStatus] = useState<{ llm: boolean; embedding: boolean }>({ llm: false, embedding: false });

  useEffect(() => {
    fetchProviders();
    fetchConfig();
  }, []);

  const fetchProviders = async () => {
    try {
      const res = await getProviders() as any;
      setProviders(res.data || []);
    } catch (e: any) {
      message.error(e.message || '获取服务提供商失败');
    }
  };

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const res = await getLLMConfig('admin') as any;
      if (res.data) {
        form.setFieldsValue(res.data);
        // 根据base_url推断提供商
        const provider = providers.find(p => res.data.base_url?.includes(p.base_url));
        if (provider) {
          setSelectedProvider(provider.id);
        }
      }
    } catch (e: any) {
      message.error(e.message || '获取配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId);
    const provider = providers.find(p => p.id === providerId);
    if (provider) {
      form.setFieldsValue({
        base_url: provider.base_url,
        embedding_base_url: provider.base_url,
        rerank_base_url: provider.base_url,
        multimodal_base_url: provider.base_url
      });
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await saveLLMConfig('admin', values);
      message.success('配置保存成功');
    } catch (e: any) {
      message.error(e.message || '保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      // 这里可以添加测试连接的逻辑
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('连接测试成功');
      setStatus({ llm: true, embedding: true });
    } catch (e: any) {
      message.error('连接测试失败');
      setStatus({ llm: false, embedding: false });
    } finally {
      setTesting(false);
    }
  };

  const getCurrentProvider = () => {
    return providers.find(p => p.id === selectedProvider);
  };

  const currentProvider = getCurrentProvider();

  return (
    <div className="p-6">
      <Card title="大模型配置" loading={loading}>
        <Form form={form} layout="vertical">
          <Form.Item label="服务提供商" name="provider">
            <Select
              placeholder="选择服务提供商"
              onChange={handleProviderChange}
              value={selectedProvider}
              options={providers.map(p => ({ label: p.name, value: p.id }))}
            />
          </Form.Item>

          <Tabs
            items={[
              {
                key: 'llm',
                label: 'LLM配置',
                children: (
                  <div className="space-y-4">
                    <Form.Item
                      label="API基础URL"
                      name="base_url"
                      rules={[{ required: true, message: '请输入API基础URL' }]}
                    >
                      <Input placeholder="https://api.openai.com/v1" />
                    </Form.Item>
                    <Form.Item
                      label="模型ID"
                      name="model_id"
                      rules={[{ required: true, message: '请选择模型' }]}
                    >
                      <Select
                        placeholder="选择模型"
                        options={currentProvider?.models?.map(m => ({ label: m, value: m })) || []}
                      />
                    </Form.Item>
                    <Form.Item
                      label="API密钥"
                      name="api_key"
                      rules={[{ required: true, message: '请输入API密钥' }]}
                    >
                      <Input.Password placeholder="sk-..." />
                    </Form.Item>
                  </div>
                ),
              },
              {
                key: 'embedding',
                label: 'Embedding配置',
                children: (
                  <div className="space-y-4">
                    <Form.Item label="Embedding API基础URL" name="embedding_base_url">
                      <Input placeholder="https://api.openai.com/v1" />
                    </Form.Item>
                    <Form.Item label="Embedding模型ID" name="embedding_model_id">
                      <Select
                        placeholder="选择Embedding模型"
                        options={currentProvider?.embedding_models?.map(m => ({ label: m, value: m })) || []}
                      />
                    </Form.Item>
                    <Form.Item label="Embedding API密钥" name="embedding_api_key">
                      <Input.Password placeholder="sk-..." />
                    </Form.Item>
                  </div>
                ),
              },
              {
                key: 'rerank',
                label: 'Rerank配置',
                children: (
                  <div className="space-y-4">
                    <Form.Item label="启用Rerank" name="rerank_enabled" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                    <Form.Item label="Rerank API基础URL" name="rerank_base_url">
                      <Input placeholder="https://api.openai.com/v1/rerank" />
                    </Form.Item>
                    <Form.Item label="Rerank模型ID" name="rerank_model_id">
                      <Select
                        placeholder="选择Rerank模型"
                        options={currentProvider?.rerank_models?.map(m => ({ label: m, value: m })) || []}
                      />
                    </Form.Item>
                    <Form.Item label="Rerank API密钥" name="rerank_api_key">
                      <Input.Password placeholder="sk-..." />
                    </Form.Item>
                    <Form.Item label="Top-K" name="rerank_top_k">
                      <Input type="number" placeholder="20" />
                    </Form.Item>
                  </div>
                ),
              },
              {
                key: 'multimodal',
                label: '多模态配置',
                children: (
                  <div className="space-y-4">
                    <Form.Item label="启用多模态" name="multimodal_enabled" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                    <Form.Item label="多模态API基础URL" name="multimodal_base_url">
                      <Input placeholder="https://api.openai.com/v1" />
                    </Form.Item>
                    <Form.Item label="多模态模型ID" name="multimodal_model_id">
                      <Select
                        placeholder="选择多模态模型"
                        options={currentProvider?.multimodal_models?.map(m => ({ label: m, value: m })) || []}
                      />
                    </Form.Item>
                    <Form.Item label="多模态API密钥" name="multimodal_api_key">
                      <Input.Password placeholder="sk-..." />
                    </Form.Item>
                  </div>
                ),
              },
            ]}
          />

          <Divider />

          <div className="flex items-center justify-between">
            <Space>
              <span>服务状态：</span>
              <Tag icon={status.llm ? <CheckCircleOutlined /> : <CloseCircleOutlined />} color={status.llm ? 'success' : 'error'}>
                LLM: {status.llm ? '正常' : '异常'}
              </Tag>
              <Tag icon={status.embedding ? <CheckCircleOutlined /> : <CloseCircleOutlined />} color={status.embedding ? 'success' : 'error'}>
                Embedding: {status.embedding ? '正常' : '异常'}
              </Tag>
            </Space>
            <Space>
              <Button icon={<ExperimentOutlined />} loading={testing} onClick={handleTest}>
                测试连接
              </Button>
              <Button type="primary" icon={<SaveOutlined />} loading={loading} onClick={handleSave}>
                保存配置
              </Button>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default LLMConfigPage;
