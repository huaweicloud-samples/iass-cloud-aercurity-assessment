import { useState, useEffect } from 'react';
import { Modal, Steps, Form, Input, InputNumber, Radio, Button, Space, Alert, Typography, message } from 'antd';
import { saveRiskIdentification, checkRiskIdentification, getBaseRiskRecord, type RiskIdentificationData } from '../../api';
import { useAppStore } from '../../store';

const { Text } = Typography;

interface RiskModalProps {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}

const RiskIdentificationModal = ({ open, onClose, onComplete }: RiskModalProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const { currentBaseId, currentBaseName } = useAppStore();

  // 5个板块的表单
  const [form1] = Form.useForm(); // 局点信息
  const [form2] = Form.useForm(); // 服务器规模
  const [form3] = Form.useForm(); // 测评通过情况
  const [form4] = Form.useForm(); // 运营运维模式
  const [form5] = Form.useForm(); // 物理机房

  const forms = [form1, form2, form3, form4, form5];

  const stepTitles = ['局点信息', '服务器规模及安可计划', '测评通过情况', '运营运维模式', '物理机房'];

  // 加载已有数据
  useEffect(() => {
    if (open && currentBaseId) {
      // 先检查是否存在记录
      checkRiskIdentification(currentBaseId).then((res: any) => {
        if (res.exists && res.current_step) {
          setCurrentStep(Math.min(res.current_step - 1, 4));
        }
        // 如果存在记录，加载已有数据到表单
        if (res.exists && res.id) {
          getBaseRiskRecord(currentBaseId).then((recordRes: any) => {
            const record = recordRes.record;
            if (record) {
              // 填充各表单数据
              form1.setFieldsValue({
                site_name: record.site_name,
                site_ip: record.site_ip,
                region_name: record.region_name,
              });
              form2.setFieldsValue({
                xinchuang_servers: record.xinchuang_servers,
                x86_servers: record.x86_servers,
              });
              form3.setFieldsValue({
                dengbao_passed: record.dengbao_passed,
                mipin_passed: record.mipin_passed,
              });
              form4.setFieldsValue({
                asset_huawei: record.asset_huawei,
                contract_direct: record.contract_direct,
              });
              form5.setFieldsValue({
                exclusive_room: record.exclusive_room,
                l1_huawei_supplier: record.l1_huawei_supplier,
                access_compliant: record.access_compliant,
              });
            }
          }).catch(() => {});
        }
      }).catch(() => {});
    }
  }, [open, currentBaseId]);

  const handleNext = async () => {
    try {
      await forms[currentStep].validateFields();
      if (currentStep < 4) {
        // 保存当前步骤
        await saveCurrentStep();
        setCurrentStep(currentStep + 1);
      }
    } catch { /* validation failed */ }
  };

  const handlePrev = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  const saveCurrentStep = async () => {
    // 收集所有已填写表单的数据
    const v1 = form1.getFieldsValue();
    const v2 = form2.getFieldsValue();
    const v3 = form3.getFieldsValue();
    const v4 = form4.getFieldsValue();
    const v5 = form5.getFieldsValue();
    
    const data: RiskIdentificationData = {
      base_id: currentBaseId!,
      current_step: currentStep + 2, // 下一步
      is_completed: false,
      // 包含所有已填写的数据
      site_name: v1.site_name,
      site_ip: v1.site_ip,
      region_name: v1.region_name,
      xinchuang_servers: v2.xinchuang_servers,
      x86_servers: v2.x86_servers,
      dengbao_passed: v3.dengbao_passed,
      mipin_passed: v3.mipin_passed,
      asset_huawei: v4.asset_huawei,
      contract_direct: v4.contract_direct,
      exclusive_room: v5.exclusive_room,
      l1_huawei_supplier: v5.l1_huawei_supplier,
      access_compliant: v5.access_compliant,
    };
    await saveRiskIdentification(data);
  };

  const handleComplete = async () => {
    try {
      await form5.validateFields();
      setSaving(true);
      const values5 = form5.getFieldsValue();
      // 收集所有表单数据
      const v1 = form1.getFieldsValue();
      const v2 = form2.getFieldsValue();
      const v3 = form3.getFieldsValue();
      const v4 = form4.getFieldsValue();

      const data: RiskIdentificationData = {
        base_id: currentBaseId!,
        site_name: v1.site_name,
        site_ip: v1.site_ip,
        region_name: v1.region_name,
        xinchuang_servers: v2.xinchuang_servers,
        x86_servers: v2.x86_servers,
        dengbao_passed: v3.dengbao_passed,
        mipin_passed: v3.mipin_passed,
        asset_huawei: v4.asset_huawei,
        contract_direct: v4.contract_direct,
        exclusive_room: values5.exclusive_room,
        l1_huawei_supplier: values5.l1_huawei_supplier,
        access_compliant: values5.access_compliant,
        is_completed: true,
        current_step: 5,
      };
      await saveRiskIdentification(data);
      message.success('申报风险识别信息已保存');
      onComplete();
      onClose();
    } catch (e: any) {
      message.error(e.message || '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Form form={form1} layout="vertical" className="mt-4">
            <Form.Item name="site_name" label="局点名称" rules={[{ required: true, message: '请输入局点名称' }]}>
              <Input placeholder="请输入局点名称" />
            </Form.Item>
            <Form.Item name="site_ip" label="IP地址" rules={[{ required: true, message: '请输入IP地址' }]}>
              <Input placeholder="请输入IP地址，如 192.168.1.1" />
            </Form.Item>
            <Form.Item name="region_name" label="Region名称" rules={[{ required: true, message: '请输入Region名称' }]}>
              <Input placeholder="请输入Region名称" />
            </Form.Item>
          </Form>
        );
      case 1:
        return (
          <Form form={form2} layout="vertical" className="mt-4">
            <Form.Item name="xinchuang_servers" label="信创服务器数量（台）" rules={[{ required: true, message: '请输入信创服务器数量' }]}>
              <InputNumber min={0} placeholder="请输入信创服务器数量" className="w-full" />
            </Form.Item>
            <Form.Item name="x86_servers" label="X86服务器数量（台）" rules={[{ required: true, message: '请输入X86服务器数量' }]}>
              <InputNumber min={0} placeholder="请输入X86服务器数量" className="w-full" />
            </Form.Item>
            <div className="bg-red-50 border border-red-200 rounded p-3 mt-2">
              <Text type="danger" className="text-sm font-medium">评估要求：</Text>
              <Text type="danger" className="text-sm block mt-1">物理服务器不低于100台，信创服务器占比不低于60%</Text>
            </div>
          </Form>
        );
      case 2:
        return (
          <Form form={form3} layout="vertical" className="mt-4">
            <Form.Item name="dengbao_passed" label="等保测评（渗透测试）是否通过并在有效期" rules={[{ required: true, message: '请选择' }]}>
              <Radio.Group>
                <Radio value="yes">是</Radio>
                <Radio value="no">否</Radio>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="mipin_passed" label="密评通过情况" rules={[{ required: true, message: '请选择' }]}>
              <Radio.Group>
                <Radio value="yes">是</Radio>
                <Radio value="no">否</Radio>
              </Radio.Group>
            </Form.Item>
          </Form>
        );
      case 3:
        return (
          <Form form={form4} layout="vertical" className="mt-4">
            <Form.Item name="asset_huawei" label="资产归属华为？" rules={[{ required: true, message: '请选择' }]}>
              <Radio.Group>
                <Radio value="yes">是</Radio>
                <Radio value="no">否</Radio>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="contract_direct" label="合同是否与政府客户直签？" rules={[{ required: true, message: '请选择' }]}>
              <Radio.Group>
                <Radio value="yes">是</Radio>
                <Radio value="no">否</Radio>
              </Radio.Group>
            </Form.Item>
          </Form>
        );
      case 4:
        return (
          <Form form={form5} layout="vertical" className="mt-4">
            <Form.Item name="exclusive_room" label="是否独享机房？" rules={[{ required: true, message: '请选择' }]}>
              <Radio.Group>
                <Radio value="yes">是</Radio>
                <Radio value="no">否</Radio>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="l1_huawei_supplier" label="L1是否是华为供应商" rules={[{ required: true, message: '请选择' }]}>
              <Radio.Group>
                <Radio value="yes">是</Radio>
                <Radio value="no">否</Radio>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="access_compliant" label="人员进出机房是否符合华为数据中心要求？" rules={[{ required: true, message: '请选择' }]}>
              <Radio.Group>
                <Radio value="yes">是</Radio>
                <Radio value="no">否</Radio>
              </Radio.Group>
            </Form.Item>
          </Form>
        );
      default:
        return null;
    }
  };

  return (
    <Modal
      title="申报信息及风险识别"
      open={open}
      onCancel={onClose}
      width={700}
      mask={{ closable: false }}
      footer={
        <div className="flex justify-between">
          <Button onClick={onClose}>稍后填写</Button>
          <Space>
            {currentStep > 0 && <Button onClick={handlePrev}>上一步</Button>}
            {currentStep < 4 ? (
              <Button type="primary" onClick={handleNext}>下一步</Button>
            ) : (
              <Button type="primary" loading={saving} onClick={handleComplete}>完成提交</Button>
            )}
          </Space>
        </div>
      }
    >
      <div className="mb-2 text-gray-500 text-sm">基地: {currentBaseName}</div>
      <Steps current={currentStep} size="small" items={stepTitles.map(t => ({ title: t }))} />
      {renderStepContent()}
      {currentStep === 0 && (
        <Alert type="info" message="请依次填写各板块信息，完成后将进行风险识别评估" className="mt-4" showIcon />
      )}
    </Modal>
  );
};

export default RiskIdentificationModal;
