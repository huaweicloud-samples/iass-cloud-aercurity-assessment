import { Input } from 'antd';
import { renderFormattedTable } from '../DocumentRenderer';

const { TextArea } = Input;

/** 修复JSON中的NaN值 */
const fixNaN = (str: string) => {
  return str.replace(/:\s*NaN([,\]\}])/g, ': ""$1');
};

/** 渲染可编辑的格式化段落 */
const renderEditableFormattedParagraph = (
  data: any, 
  index: number, 
  onChange: (index: number, newData: any) => void
) => {
  const { text, heading_level, is_list, list_level, alignment } = data;
  
  const handleTextChange = (newText: string) => {
    const newData = { ...data, text: newText };
    onChange(index, newData);
  };

  if (heading_level > 0) {
    const sizes: Record<number, string> = { 1: 'text-2xl', 2: 'text-xl', 3: 'text-lg', 4: 'text-base', 5: 'text-sm' };
    const cls = `${sizes[heading_level] || 'text-base'} font-bold text-gray-900 mt-4 mb-2`;
    
    return (
      <div className={cls}>
        <Input
          value={text}
          onChange={(e) => handleTextChange(e.target.value)}
          size="small"
          className="w-full"
          style={{ fontSize: 'inherit', fontWeight: 'inherit' }}
        />
      </div>
    );
  }

  if (is_list) {
    const indent = (list_level || 0) * 24;
    return (
      <div className="flex items-start text-sm text-gray-700 leading-relaxed" style={{ paddingLeft: indent }}>
        <span className="mr-2 mt-0.5">•</span>
        <TextArea
          value={text}
          onChange={(e) => handleTextChange(e.target.value)}
          size="small"
          autoSize={{ minRows: 1, maxRows: 6 }}
          className="w-full"
        />
      </div>
    );
  }

  const alignCls = alignment === 'center' ? 'text-center' : alignment === 'right' ? 'text-right' : '';
  if (!text) return <div className="h-3" />;
  
  return (
    <div className={`text-sm text-gray-700 leading-relaxed ${alignCls}`}>
      <TextArea
        value={text}
        onChange={(e) => handleTextChange(e.target.value)}
        autoSize={{ minRows: 1, maxRows: 6 }}
        className="w-full"
      />
    </div>
  );
};

/** 渲染可编辑的表格 */
const renderEditableFormattedTable = (
  data: any,
  index: number,
  onChange: (index: number, newData: any) => void
) => {
  // 检测是否为Excel格式（有sheet_name或columns字段）
  if (data.sheet_name || data.columns) {
    // Excel表格 - 暂时不支持编辑，显示只读
    return renderFormattedTable(data);
  }
  
  const { data: tableData, style: tblStyle, merge_info: mergeInfo } = data;
  if (!tableData || tableData.length === 0) return null;
  const hasHeader = tblStyle && (tblStyle.includes('TableGrid') || tblStyle.includes('LightShading'));

  const handleCellChange = (rowIndex: number, colIndex: number, newValue: string) => {
    const newTableData = [...tableData];
    newTableData[rowIndex] = [...newTableData[rowIndex]];
    newTableData[rowIndex][colIndex] = newValue;
    
    const newData = { ...data, data: newTableData };
    onChange(index, newData);
  };

  // 处理合并单元格：需要跳过被合并的单元格
  const renderCell = (ri: number, ci: number, cell: string) => {
    const cellMerge = mergeInfo?.[ri]?.[ci] || {};
    
    // 如果是垂直合并的延续单元格，不渲染
    if (cellMerge.vMerge === 'continue') {
      return null;
    }
    
    // 计算colspan和rowspan
    const colSpan = cellMerge.gridSpan || 1;
    let rowSpan = 1;
    
    // 计算rowspan：检查下方有多少个continue的单元格
    if (cellMerge.vMerge === 'restart') {
      for (let r = ri + 1; r < tableData.length; r++) {
        if (mergeInfo?.[r]?.[ci]?.vMerge === 'continue') {
          rowSpan++;
        } else {
          break;
        }
      }
    }
    
    const isHeader = ri === 0 && hasHeader;
    const CellTag = isHeader ? 'th' : 'td';
    
    return (
      <CellTag
        key={ci}
        colSpan={colSpan > 1 ? colSpan : undefined}
        rowSpan={rowSpan > 1 ? rowSpan : undefined}
        className={`border border-gray-300 px-3 py-2 ${isHeader ? 'font-semibold text-gray-800 text-left' : 'text-gray-700'}`}
      >
        <Input
          value={cell}
          onChange={(e) => handleCellChange(ri, ci, e.target.value)}
          size="small"
          className="w-full"
          style={{ minWidth: '100px' }}
        />
      </CellTag>
    );
  };

  return (
    <div className="overflow-x-auto my-3">
      <table className="w-full text-sm border-collapse border border-gray-300">
        <tbody>
          {tableData.map((row: string[], ri: number) => (
            <tr key={ri} className={ri === 0 && hasHeader ? 'bg-gray-100' : (ri % 2 === 0 ? 'bg-white' : 'bg-gray-50')}>
              {row.map((cell: string, ci: number) => renderCell(ri, ci, cell))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

/** 渲染可编辑的文档内容（保留格式） */
export const renderEditableDocumentContent = (
  contents: { content_type: string; content_data: string }[],
  onContentChange: (index: number, newContent: { content_type: string; content_data: string }) => void
) => {
  if (!contents || !contents.length) return <div className="text-gray-400 text-center py-8">暂无内容</div>;
  
  return (
    <div className="py-4 px-2 space-y-1">
      {contents.map((content, idx) => {
        try {
          // 检查content_data是否已经是对象
          let data = content.content_data;
          if (typeof data === 'string') {
            // 修复NaN值
            const fixedStr = fixNaN(data);
            data = JSON.parse(fixedStr);
          }
          
          const handleDataChange = (newData: any) => {
            onContentChange(idx, {
              content_type: content.content_type,
              content_data: JSON.stringify(newData)
            });
          };
          
          if (content.content_type === 'paragraph') {
            return (
              <div key={idx}>
                {renderEditableFormattedParagraph(data, idx, handleDataChange)}
              </div>
            );
          } else {
            return (
              <div key={idx}>
                {renderEditableFormattedTable(data, idx, handleDataChange)}
              </div>
            );
          }
        } catch (error) {
          console.error('解析内容失败:', error);
          return (
            <div key={idx} className="p-2 border border-red-200 bg-red-50 rounded">
              <p className="text-red-600 text-sm">内容解析失败</p>
              <TextArea
                value={content.content_data}
                onChange={(e) => onContentChange(idx, {
                  content_type: content.content_type,
                  content_data: e.target.value
                })}
                autoSize={{ minRows: 1, maxRows: 6 }}
                className="text-sm mt-2"
              />
            </div>
          );
        }
      })}
    </div>
  );
};