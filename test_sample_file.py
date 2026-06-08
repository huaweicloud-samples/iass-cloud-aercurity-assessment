"""测试样例文件查找功能"""
import os
from config import UPLOAD_DIR

def find_sample_file(sample_name: str) -> str:
    """查找样例文件"""
    sample_dir = os.path.join(UPLOAD_DIR, "evidence", "samples")
    print(f"样例文件目录: {sample_dir}")
    print(f"要查找的文件名: {sample_name}")
    
    if os.path.exists(sample_dir):
        print(f"目录存在，包含文件: {os.listdir(sample_dir)}")
        for file in os.listdir(sample_dir):
            print(f"检查文件: {file}")
            print(f"  - '{sample_name}' in '{file}': {sample_name in file}")
            print(f"  - '{file}' in '{sample_name}': {file in sample_name}")
            if sample_name in file or file in sample_name:
                file_path = os.path.join(sample_dir, file)
                print(f"找到匹配文件: {file_path}")
                return file_path
    else:
        print("目录不存在")
    
    return None

# 测试查找"0815010001不连接访问平台截图"
sample_name = "0815010001不连接访问平台截图"
result = find_sample_file(sample_name)
if result:
    print(f"✓ 成功找到样例文件: {result}")
else:
    print(f"✗ 未找到样例文件: {sample_name}")
