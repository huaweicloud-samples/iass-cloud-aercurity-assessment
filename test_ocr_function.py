"""测试OCR功能"""
import os
from config import UPLOAD_DIR

def ocr_extract_text(image_path: str) -> str:
    """使用OCR提取图片中的文本"""
    try:
        # 尝试导入PaddleOCR
        from paddleocr import PaddleOCR
        # 初始化PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        # 执行OCR
        result = ocr.ocr(image_path, cls=True)
        # 提取文本
        text_lines = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) > 1:
                    text_lines.append(line[1][0])
        return '\n'.join(text_lines)
    except ImportError:
        # 如果PaddleOCR不可用，返回空字符串
        print("PaddleOCR未安装，跳过OCR提取")
        return ""
    except Exception as e:
        print(f"OCR提取失败: {e}")
        return ""

# 测试OCR功能
sample_file = os.path.join(UPLOAD_DIR, "evidence", "samples", "0815010001不连接访问平台截图.png")
print(f"测试文件: {sample_file}")
print(f"文件存在: {os.path.exists(sample_file)}")

text = ocr_extract_text(sample_file)
print(f"提取的文本长度: {len(text)}")
print(f"提取的文本内容: {text[:200]}...")
