"""
LLM统一集成层 - 兼容OpenAI/Azure/本地私有化模型
"""
import logging
from typing import Optional, List
from openai import OpenAI

from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class LLMService:
    """大模型统一服务接口"""

    def __init__(self, base_url: str = None, api_key: str = None, model: str = None):
        self.base_url = base_url or LLM_BASE_URL
        self.api_key = api_key or LLM_API_KEY
        self.model = model or LLM_MODEL
        self._client = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        return self._client

    def chat_completion(
        self,
        messages: List[dict],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """文本对话补全"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def get_embedding(self, text: str, model: str = None) -> List[float]:
        """获取文本向量嵌入"""
        try:
            embed_model = model or LLM_EMBEDDING_MODEL
            response = self.client.embeddings.create(
                model=embed_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding调用失败: {e}")
            raise

    def vision_completion(
        self,
        text_prompt: str,
        image_url: str = None,
        image_base64: str = None,
        temperature: float = 0.1,
    ) -> str:
        """多模态视觉理解"""
        content = [{"type": "text", "text": text_prompt}]
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_base64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
            })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                temperature=temperature,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"视觉理解调用失败: {e}")
            raise


# ============ Prompt模板体系 ============

class PromptTemplates:
    """标准化Prompt模板"""

    EVIDENCE_GENERATION = """你是一位云计算服务安全评估专家。请根据以下标准条目要求，生成规范的运行情况描述和证据清单。

标准条目：{requirement}
条目ID：{item_id}
标杆参考：{benchmark_content}

请输出：
1. 规范的运行情况描述
2. 所需证据材料清单
3. 关键检查要点
"""

    DIFF_COMPARISON = """你是一位安全评估审核专家。请对比以下申报材料与标杆材料，找出差异和不足。

标准条目：{requirement}
申报材料：{submission_content}
标杆材料：{benchmark_content}

请输出：
1. 差异明细（缺失项、不一致项、不规范项）
2. 合规得分（0-100）
3. 整改建议
"""

    INTERACTIVE_GUIDE = """你是一位安全评估申报引导助手。用户正在填报以下标准条目的材料，请引导用户补全信息。

标准条目：{requirement}
当前填报内容：{current_content}
缺失要点：{missing_points}

请输出：
1. 需要补充的问题列表
2. 填报草稿建议
3. 证据材料清单
"""

    SELF_HEALING_DIAGNOSIS = """你是一位安全评估诊断专家。以下条目审核未通过，请分析根因并给出精准整改方案。

标准条目：{requirement}
审核失败原因：{failure_reason}
差异详情：{diagnosis_detail}

请区分问题类型（配置问题/材料问题/截图问题），并输出：
1. 根因分析
2. 精准整改步骤
3. 需要重新采集的截图要求（如有）
"""

    STANDARD_INTERPRETATION = """你是一位GB/T 31168-2023标准解读专家。请解读以下标准条目的合规要求。

条目ID：{item_id}
标准要求：{requirement}
标杆参考：{benchmark_content}

请输出：
1. 核心合规要素拆解
2. 关键检查点
3. 常见不合规情形
4. 证据材料要求
"""
