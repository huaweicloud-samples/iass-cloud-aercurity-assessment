"""测试扫描函数"""
import re

# 敏感信息关键字配置
SENSITIVE_KEYWORDS = {
    "美光": ["美光", "micron", "Micron"],
    "镁光": ["镁光", "magnesium light", "Mg光"],
    "mysql5.7": ["mysql5.7", "mysql 5.7", "mysql-5.7", "mysql version 5.7"]
}

def scan_text_for_sensitive_keywords(text: str):
    """扫描文本中的敏感关键字"""
    results = {}
    
    for category, keywords in SENSITIVE_KEYWORDS.items():
        found_keywords = []
        for keyword in keywords:
            # 使用正则表达式进行不区分大小写的匹配
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                found_keywords.extend(matches)
        
        if found_keywords:
            # 去重并保留原始大小写
            unique_keywords = []
            seen = set()
            for kw in found_keywords:
                if kw.lower() not in seen:
                    seen.add(kw.lower())
                    unique_keywords.append(kw)
            results[category] = unique_keywords
    
    return results

# 测试文本
test_text = "版本：20211024V1.2 本系统使用美光内存和MySQL5.7数据库，同时考虑镁光技术方案。"
print(f"测试文本: {test_text}")
print(f"扫描结果: {scan_text_for_sensitive_keywords(test_text)}")

# 测试JSON解析
import json
json_content = '{"text": "版本：20211024V1.2 本系统使用美光内存和MySQL5.7数据库，同时考虑镁光技术方案。", "style": "Normal", "heading": 1}'
print(f"\nJSON内容: {json_content}")

try:
    content_data = json.loads(json_content)
    print(f"解析后的JSON: {content_data}")
    
    # 提取文本内容
    text_content = ""
    if isinstance(content_data, dict):
        for value in content_data.values():
            if isinstance(value, str):
                text_content += value + " "
    print(f"提取的文本: {text_content}")
    print(f"文本扫描结果: {scan_text_for_sensitive_keywords(text_content)}")
except json.JSONDecodeError as e:
    print(f"JSON解析错误: {e}")