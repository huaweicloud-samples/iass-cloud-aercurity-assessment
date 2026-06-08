"""测试证据对比功能"""
import os
from config import UPLOAD_DIR
from app.api.v1.evidence import compare_evidence_files, ocr_extract_text

# 测试文件路径
sample_file = os.path.join(UPLOAD_DIR, "evidence", "samples", "0815010001不连接访问平台截图.png")
upload_file = os.path.join(UPLOAD_DIR, "evidence", "materials", "4e35cf2f-e0b3-4cd8-8f65-601fc33513ba_5ac1f7894aac48c7899faaa95f526d9a.png")

print("=" * 50)
print("测试OCR功能")
print("=" * 50)

# 测试样例文件OCR
print(f"\n样例文件: {sample_file}")
print(f"文件存在: {os.path.exists(sample_file)}")
sample_text = ocr_extract_text(sample_file)
print(f"提取文本长度: {len(sample_text)}")
print(f"提取文本内容: {sample_text[:200]}...")

# 测试上传文件OCR
print(f"\n上传文件: {upload_file}")
print(f"文件存在: {os.path.exists(upload_file)}")
upload_text = ocr_extract_text(upload_file)
print(f"提取文本长度: {len(upload_text)}")
print(f"提取文本内容: {upload_text[:200]}...")

print("\n" + "=" * 50)
print("测试证据对比功能")
print("=" * 50)

# 测试对比功能
result = compare_evidence_files(sample_file, upload_file, {"base_id": "test_base_123"})
print(f"\n对比结果:")
print(f"  文件名相似度: {result['file_name_similarity']:.2f}")
print(f"  内容相似度: {result['content_similarity']:.2f}")
print(f"  最终得分: {result['final_score']:.2f}")
print(f"  是否满足: {result['is_satisfied']}")
print(f"  详细信息: {result['details']}")
