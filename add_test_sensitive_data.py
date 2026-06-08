"""添加测试敏感信息数据"""
import sqlite3
import json

conn = sqlite3.connect('e:/云码道/yunpinggu/document_db.sqlite')
cursor = conn.cursor()

# 获取第一个文档内容
cursor.execute('SELECT id, content_data FROM document_contents WHERE document_id = 1 LIMIT 1')
row = cursor.fetchone()

if row:
    doc_id, content_data = row
    print(f"找到文档内容 ID: {doc_id}")
    
    try:
        # 解析JSON内容
        content = json.loads(content_data)
        
        # 添加敏感信息测试数据
        if isinstance(content, dict) and 'text' in content:
            original_text = content['text']
            # 添加敏感关键字
            new_text = original_text + " 本系统使用美光内存和MySQL5.7数据库，同时考虑镁光技术方案。"
            content['text'] = new_text
            
            # 更新数据库
            updated_content = json.dumps(content, ensure_ascii=False)
            cursor.execute('UPDATE document_contents SET content_data = ? WHERE id = ?', (updated_content, doc_id))
            conn.commit()
            
            print(f"已更新文档内容，添加敏感信息测试数据")
            print(f"原文本: {original_text}")
            print(f"新文本: {new_text}")
        else:
            print("文档内容格式不符合预期")
            
    except json.JSONDecodeError:
        print("文档内容不是有效的JSON格式")
else:
    print("未找到文档内容")

conn.close()