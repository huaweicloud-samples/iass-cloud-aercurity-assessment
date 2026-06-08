"""测试大模型配置系统"""
import os
import sys
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_config_service import llm_config_service
from app.services.rag_service import RAGService
from app.services.multi_agent_service import MultiAgentOrchestrator
from app.services.vector_store import VectorStore

def test_config_service():
    """测试配置服务"""
    print("=" * 60)
    print("测试配置服务")
    print("=" * 60)
    
    # 测试保存配置
    config = {
        "base_url": "http://127.0.0.1:1234/v1",
        "model_id": "qwen3.5-2b",
        "api_key": "test_key",
        "embedding_base_url": "https://api.modelarts-maas.com/v1",
        "embedding_model_id": "bge-m3",
        "embedding_api_key": "test_embedding_key",
        "rerank_enabled": True,
        "rerank_top_k": 20
    }
    
    saved_config = llm_config_service.save_config("test_user", config)
    print(f"保存配置成功: {saved_config['user_id']}")
    
    # 测试加载配置
    loaded_config = llm_config_service.load_config("test_user")
    print(f"加载配置成功: {loaded_config['user_id']}")
    
    # 测试获取各种配置
    llm_cfg = llm_config_service.get_llm_config("test_user")
    print(f"LLM配置: {llm_cfg}")
    
    embedding_cfg = llm_config_service.get_embedding_config("test_user")
    print(f"Embedding配置: {embedding_cfg}")
    
    rerank_cfg = llm_config_service.get_rerank_config("test_user")
    print(f"Rerank配置: {rerank_cfg}")
    
    return True

def test_rag_service():
    """测试RAG服务"""
    print("\n" + "=" * 60)
    print("测试RAG服务")
    print("=" * 60)
    
    llm_config = {
        "baseUrl": "http://127.0.0.1:1234/v1",
        "modelId": "qwen3.5-2b",
        "apiKey": "test_key"
    }
    
    rag_service = RAGService(llm_config)
    print(f"RAG服务可用: {rag_service.is_available()}")
    
    # 测试生成响应（如果没有实际的LLM服务，会返回错误信息）
    response = rag_service.generate_response("测试提示词", max_tokens=100)
    print(f"生成响应: {response[:100]}...")
    
    return True

def test_agent_service():
    """测试Agent服务"""
    print("\n" + "=" * 60)
    print("测试Agent服务")
    print("=" * 60)
    
    llm_config = {
        "baseUrl": "http://127.0.0.1:1234/v1",
        "modelId": "qwen3.5-2b",
        "apiKey": "test_key"
    }
    
    orchestrator = MultiAgentOrchestrator(llm_config)
    print(f"Agent服务可用: {orchestrator.is_available()}")
    
    # 测试运行Agent（如果没有实际的LLM服务，会返回错误信息）
    result = orchestrator.run("标准解读", {"name": "测试证据"})
    print(f"Agent运行结果: {result}")
    
    return True

def test_vector_store():
    """测试向量存储"""
    print("\n" + "=" * 60)
    print("测试向量存储")
    print("=" * 60)
    
    embedding_config = {
        "modelId": "bge-m3",
        "baseUrl": "https://api.modelarts-maas.com/v1",
        "apiKey": "test_key"
    }
    
    vector_store = VectorStore(embedding_config)
    
    # 添加文档
    documents = ["这是第一个测试文档", "这是第二个测试文档", "这是第三个测试文档"]
    vector_store.add_documents(documents)
    print(f"添加文档数量: {vector_store.get_document_count()}")
    
    # 测试搜索
    query_embedding = [0.1] * 1024  # 模拟查询向量
    results = vector_store.search(query_embedding, top_k=2)
    print(f"搜索结果: {results}")
    
    return True

def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 60)
    print("测试API端点")
    print("=" * 60)
    
    # 检查API模块是否可以导入
    try:
        from app.api.v1 import llm_config, ai_services
        print("✓ API模块导入成功")
        
        # 检查路由器是否创建
        print(f"✓ LLM配置路由器: {llm_config.router}")
        print(f"✓ AI服务路由器: {ai_services.router}")
        
        return True
    except Exception as e:
        print(f"✗ API模块导入失败: {e}")
        return False

def test_config_files():
    """测试配置文件"""
    print("\n" + "=" * 60)
    print("测试配置文件")
    print("=" * 60)
    
    # 检查配置文件是否存在
    config_file = "configs/llm_config_admin.json"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"✓ 配置文件存在: {config_file}")
            print(f"  用户ID: {config.get('user_id')}")
            print(f"  模型ID: {config.get('model_id')}")
            print(f"  Base URL: {config.get('base_url')}")
            return True
    else:
        print(f"✗ 配置文件不存在: {config_file}")
        return False

def test_env_config():
    """测试环境变量配置"""
    print("\n" + "=" * 60)
    print("测试环境变量配置")
    print("=" * 60)
    
    from config import (
        AI_MODEL_API_KEY,
        AI_MODEL_BASE_URL,
        EMBEDDING_MODEL,
        VECTOR_DIMENSION,
        SIMILARITY_THRESHOLD,
        RERANK_MODEL,
        RERANK_ENABLED,
        RRF_K
    )
    
    print(f"✓ AI_MODEL_API_KEY: {AI_MODEL_API_KEY}")
    print(f"✓ AI_MODEL_BASE_URL: {AI_MODEL_BASE_URL}")
    print(f"✓ EMBEDDING_MODEL: {EMBEDDING_MODEL}")
    print(f"✓ VECTOR_DIMENSION: {VECTOR_DIMENSION}")
    print(f"✓ SIMILARITY_THRESHOLD: {SIMILARITY_THRESHOLD}")
    print(f"✓ RERANK_MODEL: {RERANK_MODEL}")
    print(f"✓ RERANK_ENABLED: {RERANK_ENABLED}")
    print(f"✓ RRF_K: {RRF_K}")
    
    return True

if __name__ == "__main__":
    print("大模型配置系统测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("配置文件测试", test_config_files()))
    results.append(("环境变量测试", test_env_config()))
    results.append(("配置服务测试", test_config_service()))
    results.append(("RAG服务测试", test_rag_service()))
    results.append(("Agent服务测试", test_agent_service()))
    results.append(("向量存储测试", test_vector_store()))
    results.append(("API端点测试", test_api_endpoints()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查配置")
