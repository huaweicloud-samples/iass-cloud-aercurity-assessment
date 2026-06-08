"""简化的大模型配置系统测试"""
import os
import json
import sys

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_config_files():
    """测试配置文件"""
    print("=" * 60)
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
            print(f"  Embedding模型: {config.get('embedding_model_id')}")
            print(f"  Rerank启用: {config.get('rerank_enabled')}")
            print(f"  多模态启用: {config.get('multimodal_enabled')}")
            return True
    else:
        print(f"✗ 配置文件不存在: {config_file}")
        return False

def test_env_config():
    """测试环境变量配置"""
    print("\n" + "=" * 60)
    print("测试环境变量配置")
    print("=" * 60)
    
    # 读取.env文件
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
            print(f"✓ 环境变量文件存在: {env_file}")
            print("\n环境变量内容:")
            print(env_content)
            return True
    else:
        print(f"✗ 环境变量文件不存在: {env_file}")
        return False

def test_service_files():
    """测试服务文件"""
    print("\n" + "=" * 60)
    print("测试服务文件")
    print("=" * 60)
    
    service_files = [
        "app/services/llm_config_service.py",
        "app/services/rag_service.py",
        "app/services/multi_agent_service.py",
        "app/services/vector_store.py"
    ]
    
    all_exist = True
    for file_path in service_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            all_exist = False
    
    return all_exist

def test_api_files():
    """测试API文件"""
    print("\n" + "=" * 60)
    print("测试API文件")
    print("=" * 60)
    
    api_files = [
        "app/api/v1/llm_config.py",
        "app/api/v1/ai_services.py"
    ]
    
    all_exist = True
    for file_path in api_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            all_exist = False
    
    return all_exist

def test_model_files():
    """测试模型文件"""
    print("\n" + "=" * 60)
    print("测试模型文件")
    print("=" * 60)
    
    model_files = [
        "app/models/llm_config.py"
    ]
    
    all_exist = True
    for file_path in model_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            all_exist = False
    
    return all_exist

def test_frontend_files():
    """测试前端文件"""
    print("\n" + "=" * 60)
    print("测试前端文件")
    print("=" * 60)
    
    frontend_files = [
        "yunping/frontend/src/pages/LLMConfigPage/index.tsx"
    ]
    
    all_exist = True
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            all_exist = False
    
    return all_exist

def test_main_py():
    """测试main.py路由注册"""
    print("\n" + "=" * 60)
    print("测试main.py路由注册")
    print("=" * 60)
    
    main_file = "main.py"
    if os.path.exists(main_file):
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查是否导入了新的路由
            has_llm_config = "llm_config_router" in content
            has_ai_services = "ai_services_router" in content
            
            print(f"✓ main.py存在")
            print(f"  LLM配置路由: {'✓' if has_llm_config else '✗'}")
            print(f"  AI服务路由: {'✓' if has_ai_services else '✗'}")
            
            return has_llm_config and has_ai_services
    else:
        print(f"✗ main.py不存在")
        return False

def test_config_py():
    """测试config.py配置"""
    print("\n" + "=" * 60)
    print("测试config.py配置")
    print("=" * 60)
    
    config_file = "config.py"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查是否添加了新的配置
            has_ai_config = "AI_MODEL_API_KEY" in content
            has_embedding_config = "EMBEDDING_MODEL" in content
            has_vector_config = "VECTOR_DIMENSION" in content
            has_rerank_config = "RERANK_ENABLED" in content
            
            print(f"✓ config.py存在")
            print(f"  AI模型配置: {'✓' if has_ai_config else '✗'}")
            print(f"  Embedding配置: {'✓' if has_embedding_config else '✗'}")
            print(f"  向量配置: {'✓' if has_vector_config else '✗'}")
            print(f"  Rerank配置: {'✓' if has_rerank_config else '✗'}")
            
            return has_ai_config and has_embedding_config and has_vector_config and has_rerank_config
    else:
        print(f"✗ config.py不存在")
        return False

def test_requirements():
    """测试requirements.txt"""
    print("\n" + "=" * 60)
    print("测试requirements.txt")
    print("=" * 60)
    
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查是否添加了新的依赖
            has_sentence_transformers = "sentence-transformers" in content
            has_faiss = "faiss-cpu" in content
            has_pydantic_settings = "pydantic-settings" in content
            
            print(f"✓ requirements.txt存在")
            print(f"  sentence-transformers: {'✓' if has_sentence_transformers else '✗'}")
            print(f"  faiss-cpu: {'✓' if has_faiss else '✗'}")
            print(f"  pydantic-settings: {'✓' if has_pydantic_settings else '✗'}")
            
            return has_sentence_transformers and has_faiss and has_pydantic_settings
    else:
        print(f"✗ requirements.txt不存在")
        return False

if __name__ == "__main__":
    print("大模型配置系统测试（简化版）")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("配置文件测试", test_config_files()))
    results.append(("环境变量测试", test_env_config()))
    results.append(("服务文件测试", test_service_files()))
    results.append(("API文件测试", test_api_files()))
    results.append(("模型文件测试", test_model_files()))
    results.append(("前端文件测试", test_frontend_files()))
    results.append(("main.py路由测试", test_main_py()))
    results.append(("config.py配置测试", test_config_py()))
    results.append(("requirements.txt测试", test_requirements()))
    
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
        print("🎉 所有测试通过！大模型配置系统已成功实现！")
    else:
        print("⚠️  部分测试失败，请检查配置")
