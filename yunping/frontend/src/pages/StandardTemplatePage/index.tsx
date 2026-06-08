import { useState, useEffect } from 'react';
import { Card, Button, Upload, Space, message, Empty, Input } from 'antd';
import { UploadOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd';
import {
  uploadStandardTemplate, getStandardTemplates,
  saveStandardEdit, getStandardEdit,
  type StandardTemplate, type ContentItem
} from '../../api';
import { renderDocumentContent } from '../../components/DocumentRenderer';
import { useAppStore } from '../../store';

const StandardTemplatePage = () => {
  const [templates, setTemplates] = useState<StandardTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editContents, setEditContents] = useState<ContentItem[]>([]);
  const [editBaseId, setEditBaseId] = useState('');
  const [editBaseName, setEditBaseName] = useState('');
  const [saving, setSaving] = useState(false);

  const { userInfo, currentBaseId, currentBaseName } = useAppStore();
  const isAdmin = userInfo?.role === 'sys_admin' || userInfo?.role === 'eval_admin';

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const res = (await getStandardTemplates()) as any;
      setTemplates(res.templates || []);
    } catch (e: any) { message.error(e.message || '获取模板失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchTemplates(); }, []);

  const handleUpload = async () => {
    if (!fileList.length) { message.warning('请先选择要上传的模板文件'); return; }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', fileList[0] as any);
      formData.append('name', fileList[0].name);
      await uploadStandardTemplate(formData);
      message.success('模板上传成功');
      setFileList([]);
      fetchTemplates();
    } catch (e: any) { message.error(e.message || '模板上传失败'); }
    finally { setUploading(false); }
  };

  const handleEdit = async (template: StandardTemplate) => {
    if (!currentBaseId) { message.warning('请先在顶部选择基地'); return; }
    setEditBaseId(currentBaseId);
    setEditBaseName(currentBaseName);
    try {
      const res = (await getStandardEdit(template.template.id, currentBaseId)) as any;
      setEditContents(res.contents || []);
    } catch {
      setEditContents(template.parsed_content || []);
    }
    setEditingId(template.template.id);
  };

  const handleSave = async (templateId: number) => {
    setSaving(true);
    try {
      await saveStandardEdit({ template_id: templateId, base_id: editBaseId, base_name: editBaseName, contents: editContents });
      message.success('保存成功');
      setEditingId(null);
      fetchTemplates();
    } catch (e: any) { message.error(e.message || '保存失败'); }
    finally { setSaving(false); }
  };

  const updateParagraph = (idx: number, text: string) => {
    const c = [...editContents];
    try {
      const d = JSON.parse(c[idx].content_data);
      d.text = text;
      c[idx] = { content_type: 'paragraph', content_data: JSON.stringify(d) };
    } catch {
      c[idx] = { content_type: 'paragraph', content_data: JSON.stringify({ text, style: 'Normal', heading_level: 0, is_list: false, list_level: 0, alignment: null, runs: [] }) };
    }
    setEditContents(c);
  };

  // 更新Word表格单元格
  const updateTableCell = (ci: number, ri: number, colI: number, val: string) => {
    const c = [...editContents];
    try {
      const d = JSON.parse(c[ci].content_data);
      d.data[ri][colI] = val;
      c[ci] = { content_type: 'table', content_data: JSON.stringify(d) };
      setEditContents(c);
    } catch {}
  };

  // 更新Excel表格单元格（数据格式为 Record[]）
  const updateExcelCell = (contentIdx: number, rowIdx: number, colName: string, val: string) => {
    const c = [...editContents];
    try {
      const d = JSON.parse(c[contentIdx].content_data);
      if (d.data && d.data[rowIdx]) {
        d.data[rowIdx][colName] = val;
        c[contentIdx] = { content_type: 'table', content_data: JSON.stringify(d) };
        setEditContents(c);
      }
    } catch {}
  };

  // 渲染可编辑表格单元格（支持合并单元格）
  const renderEditableCell = (idx: number, ri: number, ci: number, cell: string, mergeInfo: any[]) => {
    const cellMerge = mergeInfo?.[ri]?.[ci] || {};
    
    // 如果是垂直合并的延续单元格，不渲染
    if (cellMerge.vMerge === 'continue') {
      return null;
    }
    
    // 计算colspan和rowspan
    const colSpan = cellMerge.gridSpan || 1;
    let rowSpan = 1;
    
    // 计算rowspan
    if (cellMerge.vMerge === 'restart') {
      const tableData = JSON.parse(editContents[idx].content_data).data;
      for (let r = ri + 1; r < tableData.length; r++) {
        if (mergeInfo?.[r]?.[ci]?.vMerge === 'continue') {
          rowSpan++;
        } else {
          break;
        }
      }
    }
    
    return (
      <td
        key={ci}
        colSpan={colSpan > 1 ? colSpan : undefined}
        rowSpan={rowSpan > 1 ? rowSpan : undefined}
        className="border border-gray-300 p-1"
      >
        <Input
          size="small"
          value={cell}
          variant="borderless"
          onChange={(e) => updateTableCell(idx, ri, ci, e.target.value)}
        />
      </td>
    );
  };

  // 渲染可编辑Excel表格
  const renderEditableExcelTable = (idx: number, data: any) => {
    const { columns, data: rows } = data;
    
    // 如果没有columns但有data，从data中提取columns
    let displayColumns = columns;
    if ((!displayColumns || displayColumns.length === 0) && rows && rows.length > 0) {
      displayColumns = Object.keys(rows[0]);
    }

    const formatValue = (val: any) => {
      if (val === null || val === undefined) return '';
      if (typeof val === 'number' && isNaN(val)) return '';
      if (val === 'NaN') return '';
      return String(val);
    };

    // 如果没有列，返回空
    if (!displayColumns || displayColumns.length === 0) {
      return null;
    }

    return (
      <div className="my-3">
        <div className="overflow-x-auto overflow-y-auto border border-gray-300 rounded" style={{ maxHeight: '600px' }}>
          <table className="w-full text-xs border-collapse" style={{ minWidth: 'max-content' }}>
            <thead className="sticky top-0 z-10">
              <tr className="bg-blue-50">
                {displayColumns.map((col: string, ci: number) => (
                  <th key={ci} className="border border-gray-300 px-3 py-2 font-semibold text-gray-800 text-left whitespace-nowrap" style={{ minWidth: '80px' }}>
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows && rows.length > 0 ? (
                rows.map((row: Record<string, any>, ri: number) => (
                  <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    {displayColumns.map((col: string, ci: number) => (
                      <td key={ci} className="border border-gray-300 p-1" style={{ maxWidth: '250px' }}>
                        <Input
                          size="small"
                          value={formatValue(row[col])}
                          variant="borderless"
                          className="w-full"
                          onChange={(e) => updateExcelCell(idx, ri, col, e.target.value)}
                        />
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={displayColumns.length} className="border border-gray-300 px-3 py-4 text-center text-gray-400">
                    暂无数据，可添加新行
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderEditableContent = () => {
    if (!editContents.length) return <Empty description="暂无内容可编辑" />;
    
    // 修复JSON中的NaN值
    const fixNaN = (str: string) => {
      return str.replace(/:\s*NaN([,\]\}])/g, ': ""$1');
    };
    
    return (
      <div className="space-y-1 py-2">
        {editContents.map((content, idx) => {
          try {
            let data = content.content_data;
            if (typeof data === 'string') {
              const fixedStr = fixNaN(data);
              data = JSON.parse(fixedStr);
            }
            
            const contentData = data as any;
            
            if (content.content_type === 'paragraph') {
              const isHeading = contentData.heading_level > 0;
              return (
                <div key={idx}>
                  {isHeading ? (
                    <div className="mb-2"><Input value={contentData.text} onChange={(e) => updateParagraph(idx, e.target.value)} className={contentData.heading_level === 1 ? 'text-xl font-bold' : contentData.heading_level === 2 ? 'text-lg font-bold' : 'font-bold'} /></div>
                  ) : (
                    <Input.TextArea autoSize={{ minRows: 1, maxRows: 6 }} value={contentData.text} onChange={(e) => updateParagraph(idx, e.target.value)} className="text-sm" />
                  )}
                </div>
              );
            } else {
              // 检测是否为Excel格式
              if (contentData.sheet_name || contentData.columns) {
                return <div key={idx}>{renderEditableExcelTable(idx, contentData)}</div>;
              }
              // Word表格格式
              const mergeInfo = contentData.merge_info || [];
              return (
                <div key={idx} className="overflow-x-auto my-2">
                  <table className="w-full text-xs border-collapse border border-gray-300">
                    <tbody>
                      {contentData.data?.map((row: string[], ri: number) => (
                        <tr key={ri}>{row?.map((cell: string, ci: number) => renderEditableCell(idx, ri, ci, cell, mergeInfo))}</tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            }
          } catch (e: any) {
            console.error('编辑内容解析失败:', e, content);
            return (
              <div key={idx} className="p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                内容解析失败: {e.message || '未知错误'}
              </div>
            );
          }
        })}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <Card title="标准项刷新" extra={
        <Space>
          {templates.length > 0 && !editingId && (
            <Button type="primary" icon={<EditOutlined />} onClick={() => handleEdit(templates[0])}>编辑</Button>
          )}
          {editingId && (
            <>
              <Button onClick={() => setEditingId(null)}>取消</Button>
              <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={() => handleSave(editingId)}>保存</Button>
            </>
          )}
          <Upload beforeUpload={(file) => { setFileList([file]); return false; }} onRemove={() => setFileList([])} fileList={fileList} maxCount={1} accept=".docx,.xlsx,.xls">
            <Button icon={<UploadOutlined />} disabled={!isAdmin}>模板上传</Button>
          </Upload>
          <Button type="primary" icon={<SaveOutlined />} loading={uploading} onClick={() => {
            if (fileList.length > 0) { handleUpload(); }
            else { message.warning('请先选择文件'); }
          }}>保存</Button>
        </Space>
      }>
        {loading ? (
          <div className="text-center py-8 text-gray-400">加载中...</div>
        ) : editingId ? (
          <div className="border border-blue-200 rounded p-4 bg-blue-50/30">
            <div className="text-xs text-gray-400 mb-2">编辑模式 · 基地: {editBaseName}</div>
            {renderEditableContent()}
          </div>
        ) : templates.length > 0 ? (
          renderDocumentContent(templates[0].parsed_content || [])
        ) : (
          <div className="text-center py-8 text-gray-400">{isAdmin ? '暂无模板，请点击"模板上传"按钮上传' : '管理员尚未上传模板'}</div>
        )}
      </Card>
    </div>
  );
};

export default StandardTemplatePage;
