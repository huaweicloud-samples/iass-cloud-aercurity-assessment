import React from 'react';
import { Empty } from 'antd';

/** 按Word格式渲染段落 - 支持标题层级、加粗、斜体、下划线、列表、对齐 */
export const renderFormattedParagraph = (data: any) => {
  const { text, heading_level, is_list, list_level, alignment, runs } = data;

  if (heading_level > 0) {
    const level = Math.min(heading_level + 1, 5);
    const sizes: Record<number, string> = { 1: 'text-2xl', 2: 'text-xl', 3: 'text-lg', 4: 'text-base', 5: 'text-sm' };
    const cls = `${sizes[heading_level] || 'text-base'} font-bold text-gray-900 mt-4 mb-2`;
    if (level === 2) return <h2 className={cls}>{text}</h2>;
    if (level === 3) return <h3 className={cls}>{text}</h3>;
    if (level === 4) return <h4 className={cls}>{text}</h4>;
    if (level === 5) return <h5 className={cls}>{text}</h5>;
    return <h2 className={cls}>{text}</h2>;
  }

  if (is_list) {
    const indent = (list_level || 0) * 24;
    return (
      <div className="flex items-start text-sm text-gray-700 leading-relaxed" style={{ paddingLeft: indent }}>
        <span className="mr-2 mt-0.5">•</span>
        <span>{renderRuns(runs, text)}</span>
      </div>
    );
  }

  const alignCls = alignment === 'center' ? 'text-center' : alignment === 'right' ? 'text-right' : '';
  if (!text) return <div className="h-3" />;
  return <p className={`text-sm text-gray-700 leading-relaxed ${alignCls}`}>{renderRuns(runs, text)}</p>;
};

const renderRuns = (runs: any[] | undefined, fallbackText: string) => {
  if (!runs || runs.length === 0) return fallbackText;
  return runs.map((run: any, i: number) => {
    if (!run.text) return null;
    let cls = '';
    if (run.bold) cls += ' font-bold';
    if (run.italic) cls += ' italic';
    if (run.underline) cls += ' underline';
    const style: React.CSSProperties = {};
    if (run.font_size) style.fontSize = `${run.font_size}pt`;
    if (run.font_name) style.fontFamily = run.font_name;
    return <span key={i} className={cls} style={style}>{run.text}</span>;
  });
};

/** 渲染Excel表格 - 数据格式为 { sheet_name, columns, data: Record[] } */
export const renderExcelTable = (data: any) => {
  const { columns, data: rows } = data;
  
  // 如果没有columns但有data，从data中提取columns
  let displayColumns = columns;
  if ((!displayColumns || displayColumns.length === 0) && rows && rows.length > 0) {
    displayColumns = Object.keys(rows[0]);
  }
  
  // 处理各种特殊值
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
        <table className="w-full text-sm border-collapse" style={{ minWidth: 'max-content' }}>
          <thead className="sticky top-0 z-10">
            <tr className="bg-blue-50">
              {displayColumns.map((col: string, ci: number) => (
                <th key={ci} className="border border-gray-300 px-4 py-3 font-semibold text-gray-800 text-left whitespace-nowrap" style={{ minWidth: '100px' }}>
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
                    <td key={ci} className="border border-gray-300 px-4 py-3 text-gray-700 whitespace-pre-wrap break-words" style={{ maxWidth: '300px', wordBreak: 'break-word' }}>
                      {formatValue(row[col])}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={displayColumns.length} className="border border-gray-300 px-4 py-6 text-center text-gray-400">
                  暂无数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

/** 按Word格式渲染表格 - 支持合并单元格 */
export const renderFormattedTable = (data: any) => {
  // 检测是否为Excel格式（有sheet_name或columns字段）
  if (data.sheet_name || data.columns) {
    return renderExcelTable(data);
  }
  
  const { data: tableData, style: tblStyle, merge_info: mergeInfo } = data;
  if (!tableData || tableData.length === 0) return null;
  const hasHeader = tblStyle && (tblStyle.includes('TableGrid') || tblStyle.includes('LightShading'));

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
        {cell}
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

/** 按Word模板格式渲染完整文档内容 */
export const renderDocumentContent = (contents: { content_type: string; content_data: string }[]) => {
  if (!contents || !contents.length) return <Empty description="暂无内容" />;
  
  // 修复JSON中的NaN值
  const fixNaN = (str: string) => {
    // 替换 : NaN, 或 : NaN} 或 : NaN] 为空字符串
    return str.replace(/:\s*NaN([,\]\}])/g, ': ""$1');
  };
  
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
          
          if (content.content_type === 'paragraph') {
            return <div key={idx}>{renderFormattedParagraph(data)}</div>;
          } else {
            return <div key={idx}>{renderFormattedTable(data)}</div>;
          }
        } catch (e: any) {
          console.error('渲染内容失败:', e, content);
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
