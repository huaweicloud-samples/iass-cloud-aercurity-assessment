"""向量存储服务"""
from typing import Dict, List, Tuple, Optional
import numpy as np

class VectorStore:
    """向量存储服务（简化版，使用numpy实现）"""
    
    def __init__(self, embedding_config: Optional[Dict] = None):
        """
        初始化向量存储
        
        Args:
            embedding_config: Embedding配置字典
        """
        self.embedding_config = embedding_config or {}
        self.documents = []  # 存储文档文本
        self.embeddings = []  # 存储文档向量
        self.dimension = 1024  # 默认向量维度
    
    def add_documents(self, texts: List[str], embeddings: List[List[float]] = None):
        """
        添加文档到向量库
        
        Args:
            texts: 文档文本列表
            embeddings: 可选的预计算向量列表
        """
        if embeddings:
            self.embeddings.extend(embeddings)
        else:
            # 如果没有提供向量，生成随机向量（实际应用中应该调用embedding模型）
            for text in texts:
                embedding = np.random.rand(self.dimension).tolist()
                self.embeddings.append(embedding)
        
        self.documents.extend(texts)
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        向量检索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回top-k结果
            
        Returns:
            文档和相似度分数的列表
        """
        if not self.embeddings:
            return []
        
        # 计算余弦相似度
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(self.embeddings)
        
        # 余弦相似度
        similarities = np.dot(doc_vecs, query_vec) / (
            np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query_vec)
        )
        
        # 获取top-k索引
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append((self.documents[idx], float(similarities[idx])))
        
        return results
    
    def get_document_count(self) -> int:
        """获取文档数量"""
        return len(self.documents)
    
    def clear(self):
        """清空向量库"""
        self.documents = []
        self.embeddings = []
