"""测试敏感信息扫描功能"""
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

# 测试用例
test_cases = [
    ("这是一个包含美光技术的文档", {"美光": ["美光"]}),
    ("我们使用MySQL5.7数据库", {"mysql5.7": ["MySQL5.7"]}),
    ("系统采用镁光内存和Micron SSD", {"美光": ["Micron"], "镁光": ["镁光"]}),
    ("数据库版本是mysql 5.7，服务器使用美光内存", {"美光": ["美光"], "mysql5.7": ["mysql 5.7"]}),
    ("没有敏感信息的文档", {}),
    ("测试MYSQL5.7和mysql-5.7", {"mysql5.7": ["MYSQL5.7", "mysql-5.7"]}),
]

print("测试敏感信息扫描功能:")
print("=" * 50)

for i, (text, expected) in enumerate(test_cases, 1):
    result = scan_text_for_sensitive_keywords(text)
    print(f"测试用例 {i}:")
    print(f"  文本: {text}")
    print(f"  预期: {expected}")
    print(f"  实际: {result}")
    print(f"  结果: {'✓ 通过' if result == expected else '✗ 失败'}")
    print()

# 测试统计功能
print("测试关键字统计:")
test_text = "美光内存和镁光内存都是优质产品，MySQL5.7数据库稳定可靠，mysql 5.7版本也很流行。"
result = scan_text_for_sensitive_keywords(test_text)
print(f"测试文本: {test_text}")
print(f"扫描结果: {result}")

# 统计每个关键字的出现次数
for category, keywords in result.items():
    keyword_counts = {}
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        count = len(pattern.findall(test_text))
        keyword_counts[kw] = count
    print(f"{category}: {keyword_counts}, 总数: {sum(keyword_counts.values())}")