"""RAG服务"""
from openai import OpenAI
import httpx
from typing import Dict, Optional

class RAGService:
    """RAG检索增强生成服务"""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """
        初始化RAG服务
        
        Args:
            llm_config: LLM配置字典，包含baseUrl, modelId, apiKey
        """
        self.llm_config = llm_config or {}
        
        if llm_config and llm_config.get("baseUrl"):
            http_client = httpx.Client(verify=False)
            self.client = OpenAI(
                base_url=llm_config.get("baseUrl"),
                api_key=llm_config.get("apiKey", "sk-xxx"),
                http_client=http_client
            )
        else:
            self.client = None
    
    def generate_response(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        生成响应
        
        Args:
            prompt: 输入提示词
            max_tokens: 最大生成token数
            temperature: 温度参数，控制随机性
            
        Returns:
            生成的响应文本
        """
        if not self.client:
            return "LLM客户端未初始化，请检查配置"
        
        try:
            response = self.client.chat.completions.create(
                model=self.llm_config.get("modelId", "gpt-4"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成响应失败: {str(e)}"
    
    def chat_with_context(self, query: str, context: str, max_tokens: int = 1000) -> str:
        """
        基于上下文的对话
        
        Args:
            query: 用户查询
            context: 检索到的上下文信息
            max_tokens: 最大生成token数
            
        Returns:
            生成的响应文本
        """
        prompt = f"""请基于以下上下文信息回答用户的问题。如果上下文中没有相关信息，请如实说明。

上下文信息：
{context}

用户问题：
{query}

请给出准确的回答："""
        
        return self.generate_response(prompt, max_tokens)
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.client is not None
