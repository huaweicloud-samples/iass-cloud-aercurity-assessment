"""测试证据对比功能（独立版本）"""
import os
import re
from difflib import SequenceMatcher
from config import UPLOAD_DIR

def ocr_extract_text(image_path: str) -> str:
    """使用OCR提取图片中的文本"""
    try:
        # 尝试导入PaddleOCR
        from paddleocr import PaddleOCR
        # 初始化PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        # 执行OCR
        result = ocr.ocr(image_path, cls=True)
        # 提取文本
        text_lines = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) > 1:
                    text_lines.append(line[1][0])
        return '\n'.join(text_lines)
    except ImportError:
        # 如果PaddleOCR不可用，返回空字符串
        print("PaddleOCR未安装，跳过OCR提取")
        return ""
    except Exception as e:
        print(f"OCR提取失败: {e}")
        return ""

def extract_base_name_ip(text: str) -> tuple:
    """从文本中提取基地名称和IP地址"""
    # 提取IP地址
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ips = re.findall(ip_pattern, text)
    
    # 提取基地名称（简化版，实际应根据业务规则）
    base_names = []
    # 常见基地名称关键词
    base_keywords = ['基地', '中心', '节点', '机房', '数据中心']
    for keyword in base_keywords:
        if keyword in text:
            # 提取包含关键词的短语
            matches = re.findall(rf'[^。，！？\n]*{keyword}[^。，！？\n]*', text)
            base_names.extend(matches)
    
    return base_names, ips

def calculate_similarity(str1: str, str2: str) -> float:
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, str1, str2).ratio()

def compare_evidence_files(sample_file: str, upload_file: str, base_info: dict = None) -> dict:
    """
    对比样例举证和局点上传举证材料
    
    Args:
        sample_file: 样例文件路径
        upload_file: 上传文件路径
        base_info: 基地信息（包含基地名称、IP等）
    
    Returns:
        对比结果字典
    """
    result = {
        "file_name_similarity": 0.0,
        "content_similarity": 0.0,
        "final_score": 0.0,
        "is_satisfied": False,
        "details": {}
    }
    
    # 维度1：文件命名对比（权重0.2）
    sample_name = os.path.basename(sample_file)
    upload_name = os.path.basename(upload_file)
    
    # 标准化文件名
    sample_std = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9-]', '', sample_name)
    upload_std = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9-]', '', upload_name)
    
    # 计算相似度
    name_similarity = calculate_similarity(sample_std, upload_std)
    
    # 综合文件名相似度
    result["file_name_similarity"] = name_similarity
    result["details"]["file_name"] = {
        "sample_name_std": sample_std,
        "upload_name_std": upload_std,
        "name_similarity": name_similarity
    }
    
    # 维度2：RAG内容识别对比（权重0.8）
    sample_text = ocr_extract_text(sample_file)
    upload_text = ocr_extract_text(upload_file)
    
    result["details"]["content"] = {
        "sample_text": sample_text[:200] + "..." if len(sample_text) > 200 else sample_text,
        "upload_text": upload_text[:200] + "..." if len(upload_text) > 200 else upload_text,
    }
    
    # 分支A：涉及基地名称/IP信息
    sample_bases, sample_ips = extract_base_name_ip(sample_text)
    upload_bases, upload_ips = extract_base_name_ip(upload_text)
    
    has_base_info = len(sample_bases) > 0 or len(sample_ips) > 0
    
    if has_base_info:
        # 与申报据点信息对比
        content_match = True
        
        if base_info:
            # 检查基地名称是否匹配
            declared_base = base_info.get("base_name", "")
            if declared_base:
                base_match = any(declared_base in base or base in declared_base for base in upload_bases)
                if not base_match:
                    content_match = False
            
            # 检查IP地址是否匹配
            declared_ips = base_info.get("ips", [])
            if declared_ips:
                ip_match = any(ip in upload_ips for ip in declared_ips)
                if not ip_match:
                    content_match = False
        
        result["details"]["content"]["branch"] = "A: 涉及基地名称/IP信息"
        result["details"]["content"]["base_info_check"] = {
            "match": content_match,
            "sample_bases": sample_bases,
            "upload_bases": upload_bases,
            "sample_ips": sample_ips,
            "upload_ips": upload_ips,
            "declared_base": base_info.get("base_name", "") if base_info else "",
            "declared_ips": base_info.get("ips", []) if base_info else []
        }
        
        result["content_similarity"] = 1.0 if content_match else 0.0
    else:
        # 分支B：不涉及基地信息，使用文本相似度
        text_sim = calculate_similarity(sample_text, upload_text)
        
        # 关键词覆盖度
        sample_keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', sample_text))
        upload_keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', upload_text))
        
        if len(sample_keywords) > 0:
            keyword_coverage = len(sample_keywords & upload_keywords) / len(sample_keywords)
        else:
            keyword_coverage = 0.0
        
        result["details"]["content"]["branch"] = "B: 不涉及基地信息"
        result["details"]["content"]["text_similarity"] = text_sim
        result["details"]["content"]["keyword_coverage"] = keyword_coverage
        
        # 综合内容相似度（文本相似度70% + 关键词覆盖30%）
        result["content_similarity"] = text_sim * 0.7 + keyword_coverage * 0.3
    
    # 综合得分（文件名20% + 内容80%）
    result["final_score"] = result["file_name_similarity"] * 0.2 + result["content_similarity"] * 0.8
    
    # 判断是否满足（得分>=0.6）
    result["is_satisfied"] = result["final_score"] >= 0.6
    
    return result

# 测试文件路径
sample_file = os.path.join(UPLOAD_DIR, "evidence", "samples", "0815010001不连接访问平台截图.png")
upload_file = os.path.join(UPLOAD_DIR, "evidence", "materials", "4e35cf2f-e0b3-4cd8-8f65-601fc33513ba_5ac1f7894aac48c7899faaa95f526d9a.png")

print("=" * 50)
print("测试OCR功能")
print("=" * 50)

# 测试样例文件OCR
print(f"\n样例文件: {sample_file}")
print(f"文件存在: {os.path.exists(sample_file)}")
sample_text = ocr_extract_text(sample_file)
print(f"提取文本长度: {len(sample_text)}")
print(f"提取文本内容: {sample_text[:300]}...")

# 测试上传文件OCR
print(f"\n上传文件: {upload_file}")
print(f"文件存在: {os.path.exists(upload_file)}")
upload_text = ocr_extract_text(upload_file)
print(f"提取文本长度: {len(upload_text)}")
print(f"提取文本内容: {upload_text[:300]}...")

print("\n" + "=" * 50)
print("测试证据对比功能")
print("=" * 50)

# 测试对比功能
result = compare_evidence_files(sample_file, upload_file, {"base_id": "test_base_123"})
print(f"\n对比结果:")
print(f"  文件名相似度: {result['file_name_similarity']:.2f}")
print(f"  内容相似度: {result['content_similarity']:.2f}")
print(f"  最终得分: {result['final_score']:.2f}")
print(f"  是否满足: {result['is_satisfied']}")
print(f"  内容分支: {result['details']['content'].get('branch', 'N/A')}")
