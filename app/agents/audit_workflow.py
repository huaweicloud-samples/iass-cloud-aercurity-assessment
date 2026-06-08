"""
LangGraph Agent工作流 - 多智能体协同审核
状态机: 初始 → 任务分拣 → 标准解读 → 证据审查 → 判定结果
                                              ↓ (不通过)
                                         自愈诊断 → 生成建议 → 结束
"""
import logging
from typing import Dict, Any, TypedDict, List, Optional
from datetime import datetime

from app.services.llm_service import LLMService, PromptTemplates
from app.services.rag_service import RAGService
from app.services.llm_config_service import llm_config_service
from app.services.vector_store import VectorStore

# 创建全局RAG服务实例
_llm_config = llm_config_service.get_llm_config("admin")
_embedding_config = llm_config_service.get_embedding_config("admin")
rag_service = RAGService(_llm_config) if _llm_config else None
vector_store = VectorStore(_embedding_config) if _embedding_config else None

logger = logging.getLogger(__name__)


# ============ 工作流状态定义 ============

class AuditState(TypedDict, total=False):
    """审核工作流状态"""
    item_id: str
    item_requirement: str
    base_id: str
    # 任务分拣结果
    task_type: str
    process_path: str
    # 标准解读结果
    standard_interpretation: str
    key_check_points: List[str]
    benchmark_content: str
    # 证据审查结果
    audit_result: str  # pass/fail
    score: int
    differences: List[Dict[str, Any]]
    # 自愈诊断结果
    diagnosis: str
    suggestion: str
    # 交互引导
    guide_questions: List[str]
    # 元信息
    current_step: str
    error: Optional[str]


# ============ Agent节点实现 ============

class DispatcherAgent:
    """任务分拣Agent - 分析条目复杂度，分配审核路径"""

    def __init__(self, llm: LLMService):
        self.llm = llm

    def run(self, state: AuditState) -> AuditState:
        logger.info(f"[任务分拣] 条目: {state.get('item_id')}")
        requirement = state.get("item_requirement", "")

        # 简单规则分拣 + LLM辅助
        if any(kw in requirement for kw in ["截图", "配置", "界面"]):
            task_type = "visual_audit"
            process_path = "vision_first"
        elif any(kw in requirement for kw in ["文档", "报告", "记录"]):
            task_type = "document_audit"
            process_path = "text_first"
        else:
            task_type = "standard_audit"
            process_path = "standard"

        state["task_type"] = task_type
        state["process_path"] = process_path
        state["current_step"] = "dispatched"
        return state


class InterpreterAgent:
    """标准解读Agent - 检索标杆样本，拆解合规检查要素"""

    def __init__(self, llm: LLMService):
        self.llm = llm

    def run(self, state: AuditState) -> AuditState:
        logger.info(f"[标准解读] 条目: {state.get('item_id')}")
        item_id = state.get("item_id", "")
        requirement = state.get("item_requirement", "")

        # RAG检索标杆材料
        benchmark_content = ""
        try:
            query_embedding = self.llm.get_embedding(requirement)
            if vector_store:
                results = vector_store.search(query_embedding, top_k=3)
                if results:
                    benchmark_content = "\n".join(
                        r[0] for r in results  # results是Tuple[str, float]，r[0]是文档内容
                    )
        except Exception as e:
            logger.warning(f"标杆检索失败: {e}")

        # LLM标准解读
        try:
            prompt = PromptTemplates.STANDARD_INTERPRETATION.format(
                item_id=item_id,
                requirement=requirement,
                benchmark_content=benchmark_content or "无标杆参考"
            )
            interpretation = self.llm.chat_completion([
                {"role": "system", "content": "你是GB/T 31168-2023标准解读专家"},
                {"role": "user", "content": prompt}
            ])
        except Exception as e:
            interpretation = f"标准解读失败: {e}"

        state["standard_interpretation"] = interpretation
        state["benchmark_content"] = benchmark_content
        state["current_step"] = "interpreted"
        return state


class EvidenceAgent:
    """证据审查Agent - 文本、视觉、关联性三位一体核验"""

    def __init__(self, llm: LLMService):
        self.llm = llm

    def run(self, state: AuditState, submission_content: str = "") -> AuditState:
        logger.info(f"[证据审查] 条目: {state.get('item_id')}")
        requirement = state.get("item_requirement", "")
        benchmark = state.get("benchmark_content", "")

        # LLM差异对比审核
        try:
            prompt = PromptTemplates.DIFF_COMPARISON.format(
                requirement=requirement,
                submission_content=submission_content or "（未提供申报材料）",
                benchmark_content=benchmark or "（无标杆参考）"
            )
            result = self.llm.chat_completion([
                {"role": "system", "content": "你是安全评估审核专家，请严格按GB/T 31168-2023标准审核"},
                {"role": "user", "content": prompt}
            ])

            # 解析审核结果
            audit_result = "fail"
            score = 0
            if "合规得分" in result:
                try:
                    import re
                    score_match = re.search(r"合规得分[：:]\s*(\d+)", result)
                    if score_match:
                        score = int(score_match.group(1))
                        audit_result = "pass" if score >= 80 else "fail"
                except:
                    pass

            state["audit_result"] = audit_result
            state["score"] = score
            state["differences"] = [{"detail": result}]
        except Exception as e:
            state["audit_result"] = "fail"
            state["score"] = 0
            state["differences"] = [{"detail": f"审核失败: {e}"}]

        state["current_step"] = "audited"
        return state


class GuideAgent:
    """交互引导Agent - 辅助用户补全材料"""

    def __init__(self, llm: LLMService):
        self.llm = llm

    def run(self, state: AuditState, user_input: str = "") -> AuditState:
        logger.info(f"[交互引导] 条目: {state.get('item_id')}")
        requirement = state.get("item_requirement", "")
        interpretation = state.get("standard_interpretation", "")

        try:
            prompt = PromptTemplates.INTERACTIVE_GUIDE.format(
                requirement=requirement,
                current_content=user_input or "（尚未填报）",
                missing_points=interpretation or "（待分析）"
            )
            guide_result = self.llm.chat_completion([
                {"role": "system", "content": "你是安全评估申报引导助手"},
                {"role": "user", "content": prompt}
            ])
            state["guide_questions"] = [guide_result]
        except Exception as e:
            state["guide_questions"] = [f"引导生成失败: {e}"]

        state["current_step"] = "guided"
        return state


class DiagnosisAgent:
    """自愈诊断Agent - 定位审核失败根因，输出整改方案"""

    def __init__(self, llm: LLMService):
        self.llm = llm

    def run(self, state: AuditState) -> AuditState:
        logger.info(f"[自愈诊断] 条目: {state.get('item_id')}")
        requirement = state.get("item_requirement", "")
        differences = state.get("differences", [])

        try:
            prompt = PromptTemplates.SELF_HEALING_DIAGNOSIS.format(
                requirement=requirement,
                failure_reason=state.get("audit_result", "unknown"),
                diagnosis_detail=str(differences)
            )
            diagnosis_result = self.llm.chat_completion([
                {"role": "system", "content": "你是安全评估诊断专家"},
                {"role": "user", "content": prompt}
            ])
            state["diagnosis"] = diagnosis_result
            state["suggestion"] = diagnosis_result
        except Exception as e:
            state["diagnosis"] = f"诊断失败: {e}"
            state["suggestion"] = ""

        state["current_step"] = "diagnosed"
        return state


# ============ 工作流编排 ============

class AuditWorkflow:
    """审核工作流编排器"""

    def __init__(self, llm: LLMService = None):
        self.llm = llm or LLMService()
        self.dispatcher = DispatcherAgent(self.llm)
        self.interpreter = InterpreterAgent(self.llm)
        self.evidence = EvidenceAgent(self.llm)
        self.guide = GuideAgent(self.llm)
        self.diagnosis = DiagnosisAgent(self.llm)

    def run_full_audit(
        self,
        item_id: str,
        item_requirement: str,
        base_id: str,
        submission_content: str = ""
    ) -> AuditState:
        """执行完整审核流程"""
        state: AuditState = {
            "item_id": item_id,
            "item_requirement": item_requirement,
            "base_id": base_id,
            "current_step": "init"
        }

        try:
            # 1. 任务分拣
            state = self.dispatcher.run(state)
            logger.info(f"任务分拣完成: type={state['task_type']}")

            # 2. 标准解读
            state = self.interpreter.run(state)
            logger.info("标准解读完成")

            # 3. 证据审查
            state = self.evidence.run(state, submission_content)
            logger.info(f"证据审查完成: result={state['audit_result']}, score={state.get('score', 0)}")

            # 4. 审核不通过则自愈诊断
            if state["audit_result"] == "fail":
                state = self.diagnosis.run(state)
                logger.info("自愈诊断完成")

        except Exception as e:
            logger.error(f"审核工作流异常: {e}")
            state["error"] = str(e)
            state["audit_result"] = "fail"

        return state

    def run_guide(
        self,
        item_id: str,
        item_requirement: str,
        base_id: str,
        user_input: str = ""
    ) -> AuditState:
        """执行交互引导流程"""
        state: AuditState = {
            "item_id": item_id,
            "item_requirement": item_requirement,
            "base_id": base_id,
            "current_step": "init"
        }

        try:
            state = self.interpreter.run(state)
            state = self.guide.run(state, user_input)
        except Exception as e:
            state["error"] = str(e)

        return state
