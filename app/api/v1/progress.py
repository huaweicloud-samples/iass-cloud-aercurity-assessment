"""进度看板API - 统计基地刷新进度"""
import os
import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import Base_, Item, Material
from app.models.document import Template, BaseDocument
from config import UPLOAD_DIR

router = APIRouter(prefix="/api/v1/progress", tags=["进度看板"])

# 证据清单文件路径
EVIDENCE_LIST_PATH = os.path.join(UPLOAD_DIR, "evidence", "evidence_list.json")


@router.get("/overview", summary="获取基地刷新进度概览")
async def get_progress_overview(
    base_id: Optional[str] = Query(None, description="基地ID，不传则返回所有基地进度"),
    db: Session = Depends(get_db)
):
    """
    获取基地刷新进度概览

    返回数据：
    - 01-06文档刷新进度：每个文档类型（01-06）的已编辑模板数/总模板数
    - 标准项刷新进度：已刷新条目数/总条目数（526条）
    - 举证材料进度：已上传并合格的材料数/总材料数
    """

    # 1. 获取基地列表
    if base_id:
        bases = db.query(Base_).filter(Base_.id == base_id).all()
    else:
        bases = db.query(Base_).all()

    # 2. 获取申报书模板总数（01-06每个文档类型）
    declaration_categories = ["01", "02", "03", "04", "05", "06"]
    declaration_templates = {}
    for cat in declaration_categories:
        count = db.query(Template).filter(
            Template.document_type == f"申报书-{cat}",
            Template.status == "active"
        ).count()
        declaration_templates[cat] = count

    # 3. 获取标准项模板总数
    standard_template_count = db.query(Template).filter(
        Template.document_type == "标准项",
        Template.status == "active"
    ).count()

    # 4. 获取标准项总数（固定526条）
    total_items = db.query(Item).count()

    # 5. 读取证据清单获取举证材料总数
    total_evidence = 0
    evidence_data = None
    if os.path.exists(EVIDENCE_LIST_PATH):
        try:
            with open(EVIDENCE_LIST_PATH, "r", encoding="utf-8") as f:
                evidence_data = json.load(f)
                total_evidence = len(evidence_data.get("items", []))
        except Exception as e:
            print(f"读取证据清单失败: {e}")

    # 6. 统计每个基地的进度
    base_progress = []
    for base in bases:
        # 6.1 统计01-06文档刷新进度
        declaration_progress = []
        for cat in declaration_categories:
            # 获取该文档类型的所有模板ID
            template_ids = db.query(Template.id).filter(
                Template.document_type == f"申报书-{cat}",
                Template.status == "active"
            ).all()
            template_ids = [t[0] for t in template_ids]

            # 统计该基地已编辑的模板数
            if template_ids:
                edited_count = db.query(BaseDocument).filter(
                    BaseDocument.template_id.in_(template_ids),
                    BaseDocument.base_code == base.id
                ).distinct(BaseDocument.template_id).count()
            else:
                edited_count = 0

            declaration_progress.append({
                "category": cat,
                "total": declaration_templates[cat],
                "edited": edited_count,
                "progress": round(edited_count / declaration_templates[cat] * 100, 2) if declaration_templates[cat] > 0 else 0
            })

        # 6.2 统计标准项刷新进度
        # 标准项刷新进度 = 该基地已上传材料的条目数 / 总条目数
        standard_edited = db.query(Material.item_id).filter(
            Material.base_id == base.id
        ).distinct().count()

        standard_progress = {
            "total": total_items,
            "edited": standard_edited,
            "progress": round(standard_edited / total_items * 100, 2) if total_items > 0 else 0
        }

        # 6.3 统计举证材料进度
        # 举证材料进度 = 该基地已上传且审核通过的材料数 / 总材料数
        evidence_passed = 0
        if evidence_data and total_evidence > 0:
            evidence_items = evidence_data.get("items", [])
            # 统计审核结果为"满足"的材料数量
            evidence_passed = sum(1 for item in evidence_items if item.get("审核结果") == "满足")

        evidence_progress = {
            "total": total_evidence,
            "passed": evidence_passed,
            "progress": round(evidence_passed / total_evidence * 100, 2) if total_evidence > 0 else 0
        }

        base_progress.append({
            "base_id": base.id,
            "base_name": base.name,
            "base_code": base.code,
            "declaration_progress": declaration_progress,
            "standard_progress": standard_progress,
            "evidence_progress": evidence_progress
        })

    return {
        "bases": base_progress,
        "summary": {
            "declaration_templates": declaration_templates,
            "standard_template_count": standard_template_count,
            "total_items": total_items,
            "total_evidence": total_evidence
        }
    }
