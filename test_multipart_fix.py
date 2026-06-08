"""测试修复后的multipart API调用"""
import requests
import json
from io import BytesIO

# 测试智能审核API（使用正确的multipart格式）
def test_compare_evidence_fixed():
    url = "http://localhost:8000/api/v1/evidence/compare/4e35cf2f-e0b3-4cd8-8f65-601fc33513ba"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEyMyIsImV4cCI6MTczNTU3MjY3N30.5FqZJ-6hV6YRHxEJD8k1h3I8eO6M1B_L0aQ3wXkL8aY"
    }
    
    # 正确的multipart/form-data格式
    files = {
        'base_info': (None, json.dumps({"base_id": "test_base_123"}), 'application/json')
    }
    
    try:
        response = requests.post(url, headers=headers, files=files)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        if hasattr(e, 'response'):
            print(f"响应内容: {e.response.text}")
        return None

# 测试错误的multipart格式（手动设置Content-Type）
def test_compare_evidence_wrong():
    url = "http://localhost:8000/api/v1/evidence/compare/4e35cf2f-e0b3-4cd8-8f65-601fc33513ba"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEyMyIsImV4cCI6MTczNTU3MjY3N30.5FqZJ-6hV6YRHxEJD8k1h3I8eO6M1B_L0aQ3wXkL8aY",
        "Content-Type": "multipart/form-data"  # 错误：缺少boundary
    }
    
    # 错误的multipart格式
    data = {
        'base_info': json.dumps({"base_id": "test_base_123"})
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        return response
    except Exception as e:
        print(f"错误: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("测试正确的multipart格式（修复后）")
    print("=" * 60)
    test_compare_evidence_fixed()
    
    print("\n" + "=" * 60)
    print("测试错误的multipart格式（修复前）")
    print("=" * 60)
    test_compare_evidence_wrong()
