"""测试证据对比API"""
import requests
import json

# 测试样例文件信息API
def test_sample_file_info():
    url = "http://localhost:8000/api/v1/evidence/sample-info/0815010001不连接访问平台截图"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEyMyIsImV4cCI6MTczNTU3MjY3N30.5FqZJ-6hV6YRHxEJD8k1h3I8eO6M1B_L0aQ3wXkL8aY"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        return None

# 测试智能审核API
def test_compare_evidence():
    url = "http://localhost:8000/api/v1/evidence/compare/4e35cf2f-e0b3-4cd8-8f65-601fc33513ba"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEyMyIsImV4cCI6MTczNTU3MjY3N30.5FqZJ-6hV6YRHxEJD8k1h3I8eO6M1B_L0aQ3wXkL8aY"
    }
    
    # 准备FormData
    files = {
        'base_info': (None, json.dumps({"base_id": "test_base_123"}))
    }
    
    try:
        response = requests.post(url, headers=headers, files=files)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("测试样例文件信息API")
    print("=" * 50)
    test_sample_file_info()
    
    print("\n" + "=" * 50)
    print("测试智能审核API")
    print("=" * 50)
    test_compare_evidence()
