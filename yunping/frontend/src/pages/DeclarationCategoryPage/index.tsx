import { useState, useEffect } from 'react';
import { Card, Button, Upload, Tag, Space, message } from 'antd';
import { UploadOutlined, SaveOutlined, DownloadOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd';
import {
  uploadDeclarationTemplate, getCategoryTemplates,
  saveDeclarationEdit, getDeclarationEdit, downloadDeclarationDocument,
  type DeclarationTemplate, type ContentItem
} from '../../api';
import { renderEditableDocumentContent } from '../../components/EditableDocumentRenderer';
import { useAppStore } from '../../store';

interface CategoryPageProps { category: string; }

const categoryNames: Record<string, string> = {
  '01': '01 申报书', '02': '02 系统安全计划', '03': '03 业务连续性和供应链报告',
  '04': '04 可迁移性报告', '05': '05 标准符合性证明', '06': '06 统一规范落实情况',
};

const DeclarationCategoryPage = ({ category }: CategoryPageProps) => {
  const [templates, setTemplates] = useState<DeclarationTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  // 每个模板的编辑内容（key为templateId）
  const [templateEditContents, setTemplateEditContents] = useState<Record<number, ContentItem[]>>({});
  const [saving, setSaving] = useState(false);

  // 存储每个模板的编辑状态
  const [templateEditStatus, setTemplateEditStatus] = useState<Record<number, {isEdited: boolean, version: number}>>({});

  const { userInfo, currentBaseId, currentBaseName } = useAppStore();
  const isAdmin = userInfo?.role === 'sys_admin' || userInfo?.role === 'eval_admin';

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const res = (await getCategoryTemplates(category)) as any;
      const templatesData = res.templates || [];
      setTemplates(templatesData);
      
      // 如果有当前基地，获取每个模板的编辑状态和内容
      if (currentBaseId) {
        const statusMap: Record<number, {isEdited: boolean, version: number}> = {};
        const contentsMap: Record<number, ContentItem[]> = {};
        for (const template of templatesData) {
          try {
            const editRes = (await getDeclarationEdit(category, template.template.id, currentBaseId)) as any;
            statusMap[template.template.id] = {
              isEdited: editRes.is_edited || false,
              version: editRes.version || 0
            };
            // 如果已编辑，保存编辑内容；否则使用模板原始内容
            if (editRes.is_edited && editRes.contents) {
              contentsMap[template.template.id] = editRes.contents;
            } else {
              contentsMap[template.template.id] = template.parsed_content || [];
            }
          } catch {
            statusMap[template.template.id] = { isEdited: false, version: 0 };
            contentsMap[template.template.id] = template.parsed_content || [];
          }
        }
        setTemplateEditStatus(statusMap);
        setTemplateEditContents(contentsMap);
      }
    } catch (e: any) { message.error(e.message || '获取模板失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchTemplates(); }, [category, currentBaseId]);

  const handleUpload = async () => {
    if (!fileList.length) { message.warning('请先选择要上传的模板文件'); return; }
    try {
      const formData = new FormData();
      formData.append('file', fileList[0] as any);
      formData.append('name', fileList[0].name);
      await uploadDeclarationTemplate(category, formData);
      message.success('模板上传成功');
      setFileList([]);
      fetchTemplates();
    } catch (e: any) { message.error(e.message || '模板上传失败'); }
  };

  // 保存编辑
  const handleSave = async (templateId: number) => {
    if (!currentBaseId) { message.warning('请先在顶部选择基地'); return; }
    
    const contents = templateEditContents[templateId];
    if (!contents) { message.warning('暂无内容可保存'); return; }
    
    setSaving(true);
    try {
      await saveDeclarationEdit(category, {
        template_id: templateId, base_id: currentBaseId, base_name: currentBaseName, contents,
      });
      message.success('保存成功');
      
      // 保存成功后，重新获取编辑内容以确保显示最新数据
      try {
        const res = (await getDeclarationEdit(category, templateId, currentBaseId)) as any;
        setTemplateEditContents(prev => ({
          ...prev,
          [templateId]: res.contents || contents
        }));
        setTemplateEditStatus(prev => ({
          ...prev,
          [templateId]: {
            isEdited: res.is_edited || true,
            version: res.version || (prev[templateId]?.version || 0) + 1
          }
        }));
      } catch (error) {
        console.error('重新获取编辑内容失败:', error);
      }
      
      // 同时刷新模板列表
      fetchTemplates();
    } catch (e: any) { message.error(e.message || '保存失败'); }
    finally { setSaving(false); }
  };

  // 下载文档
  const handleDownload = async (templateId: number) => {
    if (!currentBaseId) {
      message.warning('请先在顶部选择基地');
      return;
    }
    
    try {
      const url = await downloadDeclarationDocument(category, templateId, currentBaseId);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${currentBaseName}_${category}_v${templateEditStatus[templateId]?.version || 0}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      message.error('下载失败，请确保已保存编辑内容');
    }
  };

  // 处理内容变化
  const handleContentChange = (templateId: number, index: number, newContent: { content_type: string; content_data: string }) => {
    setTemplateEditContents(prev => {
      const contents = [...(prev[templateId] || [])];
      contents[index] = newContent;
      return { ...prev, [templateId]: contents };
    });
  };

  // 渲染每个模板卡片
  const renderTemplateCard = (template: DeclarationTemplate) => {
    const tid = template.template.id;
    const templateStatus = templateEditStatus[tid] || { isEdited: false, version: 0 };
    const contents = templateEditContents[tid] || template.parsed_content || [];

    return (
      <Card key={tid} className="mb-4" title={
        <Space>
          <span>{template.template.name}</span>
          {templateStatus.isEdited && <Tag color="blue">已编辑 v{templateStatus.version}</Tag>}
        </Space>
      } extra={
        currentBaseId ? (
          <Space>
            <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={() => handleSave(tid)}>保存</Button>
            <Button icon={<DownloadOutlined />} onClick={() => handleDownload(tid)}>下载</Button>
          </Space>
        ) : null
      }>
        {currentBaseId ? (
          <div className="border border-blue-200 rounded p-4 bg-blue-50/30">
            <div className="text-xs text-gray-400 mb-2">可编辑 · 基地: {currentBaseName}</div>
            {contents.length > 0 
              ? renderEditableDocumentContent(contents, (index, newContent) => handleContentChange(tid, index, newContent))
              : <div className="text-gray-400 text-center py-8">暂无内容可编辑</div>
            }
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">请先在顶部选择基地</div>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-4">
      <Card title={categoryNames[category] || `目录 ${category}`} extra={
        <Space>
          <Upload 
            beforeUpload={(file) => { 
              setFileList([file]); 
              handleUpload();
              return false; 
            }} 
            onRemove={() => setFileList([])} 
            fileList={fileList} 
            maxCount={1} 
            accept=".docx,.xlsx,.xls"
            showUploadList={false}
          >
            <Button icon={<UploadOutlined />} disabled={!isAdmin}>模板上传</Button>
          </Upload>
        </Space>
      }>
        {loading ? (
          <div className="text-center py-8 text-gray-400">加载中...</div>
        ) : templates.length > 0 ? (
          <div>{templates.map(renderTemplateCard)}</div>
        ) : (
          <div className="text-center py-8 text-gray-400">{isAdmin ? '暂无模板，请点击"模板上传"按钮上传' : '管理员尚未上传模板'}</div>
        )}
      </Card>
    </div>
  );
};

export default DeclarationCategoryPage;
