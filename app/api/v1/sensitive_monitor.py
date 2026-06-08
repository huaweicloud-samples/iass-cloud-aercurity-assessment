"""敏感信息监测API"""
import re
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from app.database import get_db
from app.models.audit import Base_, Material
from app.models.document import BaseDocument, DocumentContent

# Pydantic模型定义
class SensitiveItem(BaseModel):
    """敏感信息项"""
    document_name: str
    category: str
    sensitive_type: str
    keywords: List[str]
    keyword_counts: Dict[str, int]
    total_count: int
    content_preview: str

class SensitiveScanRequest(BaseModel):
    """敏感信息扫描请求"""
    base_id: str

class SensitiveScanResult(BaseModel):
    """敏感信息扫描结果"""
    base_id: str
    base_name: str
    total_sensitive_count: int
    category_counts: Dict[str, int]
    sensitive_items: List[SensitiveItem]
    scan_time: str

router = APIRouter(prefix="/api/v1/sensitive", tags=["敏感信息监测"])

# 敏感信息关键字配置
SENSITIVE_KEYWORDS = {
    "美光": ["美光", "micron", "Micron"],
    "镁光": ["镁光", "magnesium light", "Mg光"],
    "mysql5.7": ["mysql5.7", "mysql 5.7", "mysql-5.7", "mysql version 5.7"]
}

# 扫描范围配置
SCAN_CATEGORIES = {
    "01": "01申报书",
    "02": "02系统安全计划", 
    "03": "03业务连续性和供应链报告",
    "04": "04可迁移性报告",
    "05": "05标准符合性证明",
    "06": "06统一规范落实情况",
    "standard": "标准项刷新"
}

def scan_text_for_sensitive_keywords(text: str) -> Dict[str, List[str]]:
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

def scan_document_content(content: str, document_name: str, category: str) -> List[SensitiveItem]:
    """扫描单个文档内容"""
    sensitive_items = []
    
    # 扫描敏感关键字
    keyword_results = scan_text_for_sensitive_keywords(content)
    
    # 调试信息
    if keyword_results:
        print(f"DEBUG: 在文档 '{document_name}' 中发现敏感信息: {keyword_results}")
    
    for keyword_category, found_keywords in keyword_results.items():
        # 统计每个关键字出现的次数
        keyword_counts = {}
        for kw in found_keywords:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            count = len(pattern.findall(content))
            keyword_counts[kw] = count
        
        # 创建敏感信息项
        sensitive_item = SensitiveItem(
            document_name=document_name,
            category=category,
            sensitive_type=keyword_category,
            keywords=list(keyword_counts.keys()),
            keyword_counts=keyword_counts,
            total_count=sum(keyword_counts.values()),
            content_preview=content[:200] + "..." if len(content) > 200 else content
        )
        sensitive_items.append(sensitive_item)
    
    return sensitive_items

@router.post("/scan", response_model=SensitiveScanResult, summary="执行敏感信息扫描")
async def scan_sensitive_info(
    request: SensitiveScanRequest,
    db: Session = Depends(get_db)
):
    """扫描指定基地的敏感信息"""
    try:
        # 验证基地是否存在
        base = db.query(Base_).filter(Base_.id == request.base_id).first()
        if not base:
            raise HTTPException(status_code=404, detail="基地不存在")
        
        print(f"DEBUG: 开始扫描基地 {base.name} (ID: {base.id}, Code: {base.code})")
        
        all_sensitive_items = []
        total_sensitive_count = 0
        category_counts = {cat: 0 for cat in SENSITIVE_KEYWORDS.keys()}
        
        # 1. 扫描申报书刷新01-06对应文档
        # 首先获取基地的code
        base_code = base.code
        
        # 获取该基地的所有文档
        documents = db.query(BaseDocument).filter(
            BaseDocument.base_code == base_code
        ).all()
        
        print(f"DEBUG: 找到 {len(documents)} 个文档")
        
        for category_code, category_name in SCAN_CATEGORIES.items():
            if category_code == "standard":
                continue  # 标准项刷新单独处理
            
            # 过滤出包含分类代码的文档（如01、02等）
            category_documents = []
            for doc in documents:
                # 检查文件路径是否包含分类代码
                if f"\\{category_code}\\" in doc.file_path or f"/{category_code}/" in doc.file_path:
                    category_documents.append(doc)
            
            print(f"DEBUG: 分类 {category_name} ({category_code}) 找到 {len(category_documents)} 个文档")
            
            for doc in category_documents:
                # 获取文档内容
                contents = db.query(DocumentContent).filter(
                    DocumentContent.document_id == doc.id
                ).all()
                
                for content in contents:
                    if content.content_data:  # 注意：字段名是content_data不是content_text
                        # 解析JSON格式的内容数据
                        import json
                        try:
                            content_data = json.loads(content.content_data)
                            # 提取文本内容
                            text_content = ""
                            if isinstance(content_data, dict):
                                # 如果是字典，提取所有文本字段
                                for value in content_data.values():
                                    if isinstance(value, str):
                                        text_content += value + " "
                            elif isinstance(content_data, list):
                                # 如果是列表，连接所有字符串元素
                                for item in content_data:
                                    if isinstance(item, str):
                                        text_content += item + " "
                            else:
                                text_content = str(content_data)
                            
                            if text_content:
                                sensitive_items = scan_document_content(
                                    text_content,
                                    f"{category_name} - {doc.base_name}",
                                    category_name
                                )
                                all_sensitive_items.extend(sensitive_items)
                                
                                # 更新统计
                                for item in sensitive_items:
                                    total_sensitive_count += item.total_count
                                    if item.sensitive_type in category_counts:
                                        category_counts[item.sensitive_type] += item.total_count
                        except json.JSONDecodeError:
                            # 如果不是JSON，直接作为文本处理
                            text_content = content.content_data
                            sensitive_items = scan_document_content(
                                text_content,
                                f"{category_name} - {doc.base_name}",
                                category_name
                            )
                            all_sensitive_items.extend(sensitive_items)
                            
                            # 更新统计
                            for item in sensitive_items:
                                total_sensitive_count += item.total_count
                                if item.sensitive_type in category_counts:
                                    category_counts[item.sensitive_type] += item.total_count
        
        # 2. 扫描标准项刷新中对应内容
        # 查找包含"standard"的文档
        standard_documents = []
        for doc in documents:
            if "standard" in doc.file_path.lower():
                standard_documents.append(doc)
        
        print(f"DEBUG: 标准项刷新找到 {len(standard_documents)} 个文档")
        
        for doc in standard_documents:
            contents = db.query(DocumentContent).filter(
                DocumentContent.document_id == doc.id
            ).all()
            
            for content in contents:
                if content.content_data:
                    # 解析JSON格式的内容数据
                    import json
                    try:
                        content_data = json.loads(content.content_data)
                        # 提取文本内容
                        text_content = ""
                        if isinstance(content_data, dict):
                            for value in content_data.values():
                                if isinstance(value, str):
                                    text_content += value + " "
                        elif isinstance(content_data, list):
                            for item in content_data:
                                if isinstance(item, str):
                                    text_content += item + " "
                        else:
                            text_content = str(content_data)
                        
                        if text_content:
                            sensitive_items = scan_document_content(
                                text_content,
                                f"标准项刷新 - {doc.base_name}",
                                "标准项刷新"
                            )
                            all_sensitive_items.extend(sensitive_items)
                            
                            # 更新统计
                            for item in sensitive_items:
                                total_sensitive_count += item.total_count
                                if item.sensitive_type in category_counts:
                                    category_counts[item.sensitive_type] += item.total_count
                    except json.JSONDecodeError:
                        text_content = content.content_data
                        sensitive_items = scan_document_content(
                            text_content,
                            f"标准项刷新 - {doc.base_name}",
                            "标准项刷新"
                        )
                        all_sensitive_items.extend(sensitive_items)
                        
                        # 更新统计
                        for item in sensitive_items:
                            total_sensitive_count += item.total_count
                            if item.sensitive_type in category_counts:
                                category_counts[item.sensitive_type] += item.total_count
        
        # 3. 扫描申报材料
        materials = db.query(Material).filter(
            Material.base_id == request.base_id
        ).all()
        
        for material in materials:
            if material.content_text:
                # 确定材料类型
                material_type = "申报材料"
                if material.material_type == "description":
                    material_type = "描述材料"
                elif material.material_type == "evidence":
                    material_type = "证据材料"
                
                sensitive_items = scan_document_content(
                    material.content_text,
                    f"{material_type} - {material.file_path or '未命名'}",
                    material_type
                )
                all_sensitive_items.extend(sensitive_items)
                
                # 更新统计
                for item in sensitive_items:
                    total_sensitive_count += item.total_count
                    if item.sensitive_type in category_counts:
                        category_counts[item.sensitive_type] += item.total_count
        
        # 按敏感信息数量排序
        all_sensitive_items.sort(key=lambda x: x.total_count, reverse=True)
        
        return SensitiveScanResult(
            base_id=request.base_id,
            base_name=base.name,
            total_sensitive_count=total_sensitive_count,
            category_counts=category_counts,
            sensitive_items=all_sensitive_items,
            scan_time=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描失败: {str(e)}")

@router.get("/results/{base_id}", response_model=SensitiveScanResult, summary="获取扫描结果")
async def get_scan_results(
    base_id: str,
    db: Session = Depends(get_db)
):
    """获取指定基地的扫描结果"""
    # 这里可以添加缓存或数据库存储的扫描结果查询逻辑
    # 目前先返回空结果，实际实现时可以存储扫描结果到数据库
    base = db.query(Base_).filter(Base_.id == base_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="基地不存在")
    
    return SensitiveScanResult(
        base_id=base_id,
        base_name=base.name,
        total_sensitive_count=0,
        category_counts={cat: 0 for cat in SENSITIVE_KEYWORDS.keys()},
        sensitive_items=[],
        scan_time=datetime.now().isoformat()
    )