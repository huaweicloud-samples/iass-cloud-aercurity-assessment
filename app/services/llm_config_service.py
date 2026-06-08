"""大模型配置服务"""
import os
import json
from typing import Dict, Optional
from datetime import datetime
from config import CONFIG_DIR

class LLMConfigService:
    """大模型配置管理服务"""
    
    def __init__(self):
        self.config_dir = CONFIG_DIR
        os.makedirs(self.config_dir, exist_ok=True)
    
    def get_config_file_path(self, user_id: str) -> str:
        """获取用户配置文件路径"""
        return os.path.join(self.config_dir, f"llm_config_{user_id}.json")
    
    def load_config(self, user_id: str) -> Optional[Dict]:
        """加载用户配置"""
        config_file = self.get_config_file_path(user_id)
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_config(self, user_id: str, config: Dict) -> Dict:
        """保存用户配置"""
        config_file = self.get_config_file_path(user_id)
        config['user_id'] = user_id
        config['updated_at'] = datetime.now().isoformat()
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return config
    
    def get_embedding_config(self, user_id: str = "admin") -> Dict[str, str]:
        """获取Embedding配置"""
        config = self.load_config(user_id)
        if config:
            return {
                "baseUrl": config.get("embedding_base_url"),
                "modelId": config.get("embedding_model_id"),
                "apiKey": config.get("embedding_api_key")
            }
        return {}
    
    def get_llm_config(self, user_id: str = "admin") -> Dict[str, str]:
        """获取LLM配置"""
        config = self.load_config(user_id)
        if config:
            return {
                "baseUrl": config.get("base_url"),
                "modelId": config.get("model_id"),
                "apiKey": config.get("api_key")
            }
        return {}
    
    def get_rerank_config(self, user_id: str = "admin") -> Dict[str, str]:
        """获取Rerank配置"""
        config = self.load_config(user_id)
        if config:
            return {
                "baseUrl": config.get("rerank_base_url"),
                "modelId": config.get("rerank_model_id"),
                "apiKey": config.get("rerank_api_key"),
                "enabled": config.get("rerank_enabled", False),
                "topK": config.get("rerank_top_k", 20)
            }
        return {}
    
    def get_multimodal_config(self, user_id: str = "admin") -> Dict[str, str]:
        """获取多模态配置"""
        config = self.load_config(user_id)
        if config:
            return {
                "baseUrl": config.get("multimodal_base_url"),
                "modelId": config.get("multimodal_model_id"),
                "apiKey": config.get("multimodal_api_key"),
                "enabled": config.get("multimodal_enabled", False)
            }
        return {}

# 全局配置服务实例
llm_config_service = LLMConfigService()
