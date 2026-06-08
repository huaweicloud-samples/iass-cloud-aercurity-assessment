"""证据清单管理API"""
import os
import uuid
import json
import re
from datetime import datetime
from typing import Optional, List
from difflib import SequenceMatcher

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import pandas as pd

from app.database import get_db
from app.core.auth import get_current_user, RoleChecker
from app.models.audit import User
from config import UPLOAD_DIR, MAX_FILE_SIZE

allow_eval_admin = RoleChecker("eval_admin")

router = APIRouter(prefix="/api/v1/evidence", tags=["证据对比"])


class EvidenceItem(BaseModel):
    id: str
    序号: int
    章节名称: str
    举证名称: str
    样例举证: Optional[str] = None
    局点上传举证材料: Optional[str] = None
    审核结果: Optional[str] = "待审核"
    样例举证文件: Optional[str] = None
    局点上传文件: Optional[str] = None
    举证诊断结果: Optional[str] = None


class EvidenceListResponse(BaseModel):
    total: int
    items: List[EvidenceItem]


# 证据清单文件路径
EVIDENCE_LIST_PATH = os.path.join(UPLOAD_DIR, "evidence_list.json")


@router.post("/upload-list", summary="管理员上传证据清单")
async def upload_evidence_list(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    """管理员上传Excel格式的证据清单"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".xlsx", ".xls"):
        raise HTTPException(status_code=400, detail="仅支持Excel文件格式(.xlsx, .xls)")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制({MAX_FILE_SIZE // 1024 // 1024}MB)")
    
    # 保存文件
    evidence_dir = os.path.join(UPLOAD_DIR, "evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    
    unique_filename = f"evidence_list_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(evidence_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 解析Excel文件
    try:
        df = pd.read_excel(file_path)
        
        # 打印原始列名用于调试
        print(f"Excel原始列名: {list(df.columns)}")
        
        # 将NaN替换为空字符串
        df = df.fillna('')
        
        # 转换为列表，保留所有列
        items = []
        for idx, row in df.iterrows():
            item = {
                "id": str(uuid.uuid4()),
                "局点上传举证材料": None,
                "审核结果": "待审核",
                "样例举证文件": None,
                "局点上传文件": None,
                "举证诊断结果": None,
            }
            
            # 添加所有Excel列的数据
            for col in df.columns:
                col_str = str(col).strip()
                val = row[col]
                if pd.notna(val) and val != '':
                    item[col_str] = val
                else:
                    item[col_str] = ''
            
            # 确保有序号
            if '序号' not in item or not item['序号']:
                item['序号'] = idx + 1
            
            items.append(item)
        
        print(f"解析到 {len(items)} 条证据项")
        print(f"列名: {list(df.columns)}")
        
        # 保存为JSON
        with open(EVIDENCE_LIST_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "file_path": file_path,
                "items": items,
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        return {
            "code": 200,
            "message": "证据清单上传成功",
            "total": len(items),
            "items": items
        }
        
    except Exception as e:
        import traceback
        print(f"解析Excel文件失败: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"解析Excel文件失败: {str(e)}")


@router.get("/list", summary="获取证据清单列表")
async def get_evidence_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取证据清单列表"""
    if not os.path.exists(EVIDENCE_LIST_PATH):
        return {
            "total": 0,
            "items": [],
            "file_path": None
        }
    
    try:
        with open(EVIDENCE_LIST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {
            "total": len(data.get("items", [])),
            "items": data.get("items", []),
            "file_path": data.get("file_path"),
            "updated_at": data.get("updated_at")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取证据清单失败: {str(e)}")


@router.post("/upload-material/{item_id}", summary="上传举证材料")
async def upload_evidence_material(
    item_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """用户上传举证材料"""
    if not os.path.exists(EVIDENCE_LIST_PATH):
        raise HTTPException(status_code=404, detail="证据清单不存在，请等待管理员上传")
    
    # 读取现有数据
    with open(EVIDENCE_LIST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 查找对应项
    items = data.get("items", [])
    item_index = None
    for i, item in enumerate(items):
        if item["id"] == item_id:
            item_index = i
            break
    
    if item_index is None:
        raise HTTPException(status_code=404, detail="未找到对应的证据项")
    
    # 保存文件
    evidence_dir = os.path.join(UPLOAD_DIR, "evidence", "materials")
    os.makedirs(evidence_dir, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{item_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(evidence_dir, unique_filename)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 更新数据
    items[item_index]["局点上传举证材料"] = file.filename
    items[item_index]["局点上传文件"] = file_path
    items[item_index]["审核结果"] = "待审核"
    
    # 保存
    data["items"] = items
    data["updated_at"] = datetime.now().isoformat()
    with open(EVIDENCE_LIST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {
        "code": 200,
        "message": "举证材料上传成功",
        "item": items[item_index]
    }


@router.get("/material/{item_id}", summary="获取举证材料文件")
async def get_material_file(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取局点上传的举证材料文件"""
    from fastapi.responses import FileResponse
    
    if not os.path.exists(EVIDENCE_LIST_PATH):
        raise HTTPException(status_code=404, detail="证据清单不存在")
    
    with open(EVIDENCE_LIST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 查找对应项
    items = data.get("items", [])
    item = None
    for i in items:
        if i["id"] == item_id:
            item = i
            break
    
    if not item:
        raise HTTPException(status_code=404, detail="未找到对应的证据项")
    
    # 获取文件路径
    file_path = item.get("局点上传文件")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="举证材料文件不存在")
    
    filename = item.get("局点上传举证材料", "material")
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.post("/audit/{item_id}", summary="审核举证材料")
async def audit_evidence(
    item_id: str,
    result: str = Form(..., description="审核结果：满足/不满足"),
    diagnosis: str = Form(None, description="举证诊断结果"),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    """管理员审核举证材料"""
    if not os.path.exists(EVIDENCE_LIST_PATH):
        raise HTTPException(status_code=404, detail="证据清单不存在")
    
    with open(EVIDENCE_LIST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    items = data.get("items", [])
    item_index = None
    for i, item in enumerate(items):
        if item["id"] == item_id:
            item_index = i
            break
    
    if item_index is None:
        raise HTTPException(status_code=404, detail="未找到对应的证据项")
    
    items[item_index]["审核结果"] = result
    if diagnosis:
        items[item_index]["举证诊断结果"] = diagnosis
    
    data["items"] = items
    data["updated_at"] = datetime.now().isoformat()
    with open(EVIDENCE_LIST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {
        "code": 200,
        "message": "审核完成",
        "item": items[item_index]
    }


@router.get("/sample-info/{sample_name}", summary="获取样例文件信息")
async def get_sample_file_info(
    sample_name: str,
    current_user: User = Depends(get_current_user)
):
    """获取样例举证文件信息（文件名、类型等）"""
    import mimetypes
    
    # 样例文件目录
    sample_dir = os.path.join(UPLOAD_DIR, "evidence", "samples")
    
    # 尝试查找样例文件
    if os.path.exists(sample_dir):
        for file in os.listdir(sample_dir):
            # 匹配文件名（支持部分匹配）
            if sample_name in file or file in sample_name:
                file_path = os.path.join(sample_dir, file)
                ext = file.split('.').pop().lower() if '.' in file else ''
                
                # 判断文件类型
                file_type = 'other'
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']:
                    file_type = 'image'
                elif ext == 'pdf':
                    file_type = 'pdf'
                elif ext in ['doc', 'docx']:
                    file_type = 'word'
                
                return {
                    "found": True,
                    "filename": file,
                    "type": file_type,
                    "url": f"/api/v1/evidence/sample/{file}"
                }
    
    return {
        "found": False,
        "filename": sample_name,
        "type": "other",
        "url": f"/api/v1/evidence/sample/{sample_name}"
    }


@router.get("/sample/{sample_name}", summary="获取样例文件")
async def get_sample_file(
    sample_name: str,
    current_user: User = Depends(get_current_user)
):
    """获取样例举证文件"""
    from fastapi.responses import FileResponse
    
    # 样例文件目录
    sample_dir = os.path.join(UPLOAD_DIR, "evidence", "samples")
    
    # 尝试查找样例文件
    if os.path.exists(sample_dir):
        for file in os.listdir(sample_dir):
            # 匹配文件名（支持部分匹配）
            if sample_name in file or file in sample_name:
                file_path = os.path.join(sample_dir, file)
                return FileResponse(
                    file_path,
                    filename=file,
                    media_type="application/octet-stream"
                )
    
    # 如果没找到精确匹配，尝试直接使用sample_name作为文件名
    sample_path = os.path.join(sample_dir, sample_name)
    if os.path.exists(sample_path):
        return FileResponse(
            sample_path,
            filename=sample_name,
            media_type="application/octet-stream"
        )
    
    raise HTTPException(status_code=404, detail=f"样例文件不存在: {sample_name}")


# ============ 证据对比审核辅助函数 ============

def extract_evidence_number(filename: str) -> str:
    """从文件名中提取举证编号，如"01-身份认证.png" -> "01" """
    # 匹配开头的数字编号
    match = re.match(r'^(\d+)', filename)
    return match.group(1) if match else ""


def standardize_filename(filename: str) -> str:
    """标准化文件名：去除扩展名、时间戳等"""
    # 去除扩展名
    name = os.path.splitext(filename)[0]
    # 去除时间戳（如 _20240101_123456）
    name = re.sub(r'_\d{8}_\d{6}', '', name)
    # 去除特殊字符，只保留中文、字母、数字、连字符
    name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9-]', '', name)
    return name


def calculate_similarity(str1: str, str2: str) -> float:
    """计算两个字符串的相似度（0-1）"""
    return SequenceMatcher(None, str1, str2).ratio()


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
    # 提取基地名称（通常包含"基地"、"中心"、"节点"等关键词）
    base_patterns = [
        r'([^，。\s]+(?:基地|中心|节点|站点))',
        r'([^，。\s]+(?:基地|中心|节点|站点))',
    ]
    base_names = []
    for pattern in base_patterns:
        matches = re.findall(pattern, text)
        base_names.extend(matches)
    
    # 提取IP地址
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ips = re.findall(ip_pattern, text)
    
    return list(set(base_names)), list(set(ips))


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
        "details": {}
    }
    
    # 维度1：文件命名对比（权重0.2）
    sample_name = os.path.basename(sample_file)
    upload_name = os.path.basename(upload_file)
    
    # 提取举证编号
    sample_num = extract_evidence_number(sample_name)
    upload_num = extract_evidence_number(upload_name)
    
    # 标准化文件名
    sample_std = standardize_filename(sample_name)
    upload_std = standardize_filename(upload_name)
    
    # 计算相似度
    num_similarity = 1.0 if sample_num == upload_num else 0.0
    name_similarity = calculate_similarity(sample_std, upload_std)
    
    # 综合文件名相似度（编号占70%，名称占30%）
    result["file_name_similarity"] = num_similarity * 0.7 + name_similarity * 0.3
    result["details"]["file_name"] = {
        "sample_number": sample_num,
        "upload_number": upload_num,
        "sample_name_std": sample_std,
        "upload_name_std": upload_std,
        "number_match": num_similarity == 1.0,
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
        
        result["content_similarity"] = 1.0 if content_match else 0.0
        result["details"]["content"]["branch"] = "A: 涉及基地名称/IP信息"
        result["details"]["content"]["base_info_check"] = {
            "sample_bases": sample_bases,
            "upload_bases": upload_bases,
            "sample_ips": sample_ips,
            "upload_ips": upload_ips,
            "declared_base": base_info.get("base_name", "") if base_info else "",
            "declared_ips": base_info.get("ips", []) if base_info else [],
            "match": content_match
        }
    else:
        # 分支B：不涉及基地名称/IP
        # 核对举证与样例一致性
        text_similarity = calculate_similarity(sample_text, upload_text)
        
        # 关键要素覆盖检查
        sample_keywords = re.findall(r'[\u4e00-\u9fa5]{2,}', sample_text)
        upload_keywords = re.findall(r'[\u4e00-\u9fa5]{2,}', upload_text)
        
        keyword_coverage = 0.0
        if sample_keywords:
            matched = sum(1 for kw in sample_keywords if kw in upload_keywords)
            keyword_coverage = matched / len(sample_keywords)
        
        # 综合内容相似度（文本相似度60% + 关键词覆盖40%）
        result["content_similarity"] = text_similarity * 0.6 + keyword_coverage * 0.4
        result["details"]["content"]["branch"] = "B: 不涉及基地名称/IP"
        result["details"]["content"]["text_similarity"] = text_similarity
        result["details"]["content"]["keyword_coverage"] = keyword_coverage
        result["details"]["content"]["sample_keywords"] = sample_keywords[:10]
        result["details"]["content"]["upload_keywords"] = upload_keywords[:10]
    
    # 计算最终得分
    result["final_score"] = result["file_name_similarity"] * 0.2 + result["content_similarity"] * 0.8
    
    # 判断是否满足审核
    result["is_satisfied"] = result["final_score"] >= 0.8
    
    return result


@router.post("/compare/{item_id}", summary="证据对比审核")
async def compare_evidence(
    item_id: str,
    base_info: Optional[str] = Form(None, description="基地信息JSON字符串"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """对样例举证和局点上传举证材料进行对比审核"""
    if not os.path.exists(EVIDENCE_LIST_PATH):
        raise HTTPException(status_code=404, detail="证据清单不存在")
    
    with open(EVIDENCE_LIST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 查找对应项
    items = data.get("items", [])
    item_index = None
    item = None
    for i, item_data in enumerate(items):
        if item_data["id"] == item_id:
            item_index = i
            item = item_data
            break
    
    if not item:
        raise HTTPException(status_code=404, detail="未找到对应的证据项")
    
    # 检查是否已上传材料
    if not item.get("局点上传文件"):
        raise HTTPException(status_code=400, detail="请先上传举证材料")
    
    # 查找样例文件
    sample_name = item.get("样例举证") or item.get("举证名称")
    if not sample_name:
        raise HTTPException(status_code=400, detail="未找到样例举证")
    
    sample_dir = os.path.join(UPLOAD_DIR, "evidence", "samples")
    sample_file = None
    
    if os.path.exists(sample_dir):
        for file in os.listdir(sample_dir):
            if sample_name in file or file in sample_name:
                sample_file = os.path.join(sample_dir, file)
                break
    
    if not sample_file or not os.path.exists(sample_file):
        raise HTTPException(status_code=404, detail=f"样例文件不存在: {sample_name}")
    
    upload_file = item["局点上传文件"]
    
    # 解析基地信息
    base_data = {}
    if base_info:
        try:
            base_data = json.loads(base_info)
        except:
            pass
    
    # 执行对比
    compare_result = compare_evidence_files(sample_file, upload_file, base_data)
    
    # 生成诊断结果
    diagnosis_parts = []
    
    # 文件名对比结果
    file_name_score = compare_result["file_name_similarity"]
    if file_name_score >= 0.8:
        diagnosis_parts.append(f"✓ 文件命名匹配（相似度{file_name_score:.2f}）")
    else:
        diagnosis_parts.append(f"✗ 文件命名不匹配（相似度{file_name_score:.2f}）")
    
    # 内容对比结果
    content_score = compare_result["content_similarity"]
    content_details = compare_result["details"]["content"]
    
    if content_details.get("branch") == "A: 涉及基地名称/IP信息":
        base_check = content_details.get("base_info_check", {})
        if base_check.get("match"):
            diagnosis_parts.append("✓ 基地名称/IP信息与申报信息一致")
        else:
            diagnosis_parts.append("✗ 基地名称/IP信息与申报信息不一致")
    else:
        text_sim = content_details.get("text_similarity", 0)
        kw_cov = content_details.get("keyword_coverage", 0)
        diagnosis_parts.append(f"文本相似度: {text_sim:.2f}, 关键词覆盖: {kw_cov:.2f}")
    
    diagnosis = "\n".join(diagnosis_parts)
    
    # 更新审核结果
    result_str = "满足" if compare_result["is_satisfied"] else "不满足"
    items[item_index]["审核结果"] = result_str
    items[item_index]["举证诊断结果"] = diagnosis
    
    data["items"] = items
    data["updated_at"] = datetime.now().isoformat()
    with open(EVIDENCE_LIST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {
        "code": 200,
        "message": "对比审核完成",
        "result": compare_result,
        "audit_result": result_str,
        "diagnosis": diagnosis
    }
