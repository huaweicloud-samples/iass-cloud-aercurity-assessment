"""大模型配置API"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.llm_config_service import llm_config_service

router = APIRouter(prefix="/api/v1/llm-config", tags=["大模型配置"])

class LLMConfigRequest(BaseModel):
    """LLM配置请求"""
    base_url: str
    model_id: str
    api_key: str
    embedding_base_url: Optional[str] = None
    embedding_model_id: Optional[str] = None
    embedding_api_key: Optional[str] = None
    rerank_base_url: Optional[str] = None
    rerank_model_id: Optional[str] = None
    rerank_api_key: Optional[str] = None
    rerank_enabled: Optional[bool] = False
    rerank_top_k: Optional[int] = 20
    multimodal_base_url: Optional[str] = None
    multimodal_model_id: Optional[str] = None
    multimodal_api_key: Optional[str] = None
    multimodal_enabled: Optional[bool] = False

@router.get("/{user_id}")
async def get_llm_config(user_id: str):
    """获取用户LLM配置"""
    config = llm_config_service.load_config(user_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"code": 200, "data": config}

@router.post("/{user_id}")
async def save_llm_config(user_id: str, config: LLMConfigRequest):
    """保存用户LLM配置"""
    config_dict = config.model_dump()
    saved_config = llm_config_service.save_config(user_id, config_dict)
    return {"code": 200, "message": "配置保存成功", "data": saved_config}

@router.get("/{user_id}/embedding")
async def get_embedding_config(user_id: str):
    """获取Embedding配置"""
    config = llm_config_service.get_embedding_config(user_id)
    return {"code": 200, "data": config}

@router.get("/{user_id}/llm")
async def get_llm_only_config(user_id: str):
    """获取LLM配置"""
    config = llm_config_service.get_llm_config(user_id)
    return {"code": 200, "data": config}

@router.get("/{user_id}/rerank")
async def get_rerank_config(user_id: str):
    """获取Rerank配置"""
    config = llm_config_service.get_rerank_config(user_id)
    return {"code": 200, "data": config}

@router.get("/{user_id}/multimodal")
async def get_multimodal_config(user_id: str):
    """获取多模态配置"""
    config = llm_config_service.get_multimodal_config(user_id)
    return {"code": 200, "data": config}

@router.get("/providers/list")
async def get_providers():
    """获取支持的LLM服务提供商列表"""
    providers = [
        {
            "id": "openai",
            "name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "embedding_models": ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]
        },
        {
            "id": "huawei",
            "name": "华为云 ModelArts",
            "base_url": "https://api.modelarts-maas.com/v1",
            "models": ["qwen3.5-2b", "qwen3.5-72b", "baichuan2-13b"],
            "embedding_models": ["bge-m3", "bge-large-zh"],
            "rerank_models": ["bge-reranker-v2-m3"]
        },
        {
            "id": "zhipu",
            "name": "智谱AI",
            "base_url": "https://open.bigmodel.cn/api/paas/v3",
            "models": ["glm-4", "glm-3-turbo"],
            "embedding_models": ["embedding-2", "embedding-3"]
        },
        {
            "id": "baidu",
            "name": "百度文心一言",
            "base_url": "https://aip.baidubce.com/rpc/2.0",
            "models": ["ernie-bot-4", "ernie-bot-turbo"],
            "embedding_models": ["embedding-v1"]
        },
        {
            "id": "aliyun",
            "name": "阿里通义千问",
            "base_url": "https://dashscope.aliyuncs.com",
            "models": ["qwen-max", "qwen-plus", "qwen-turbo"],
            "embedding_models": ["text-embedding-v2"]
        },
        {
            "id": "ollama",
            "name": "Ollama",
            "base_url": "http://localhost:11434/v1",
            "models": ["llama3", "mistral", "qwen3.5-2b"],
            "multimodal_models": ["llava", "bakllava"]
        }
    ]
    return {"code": 200, "data": providers}
