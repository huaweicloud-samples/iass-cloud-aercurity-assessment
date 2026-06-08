"""
OCR图文识别服务
支持PaddleOCR和Tesseract双引擎
"""
import os
import hashlib
import logging
import json
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OCRService:
    """OCR图文识别服务"""

    def __init__(self):
        self._cache = {}  # 简单内存缓存，生产环境用Redis
        self._paddle_ocr = None

    @property
    def paddle_ocr(self):
        """懒加载PaddleOCR引擎"""
        if self._paddle_ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                    show_log=False
                )
            except ImportError:
                logger.warning("PaddleOCR未安装，OCR功能不可用")
                return None
        return self._paddle_ocr

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _check_cache(self, file_hash: str) -> Optional[str]:
        """检查缓存"""
        cached = self._cache.get(file_hash)
        if cached:
            cache_time = cached.get("time")
            if datetime.now() - cache_time < timedelta(days=30):
                return cached.get("result")
        return None

    def _save_cache(self, file_hash: str, result: str):
        """保存缓存"""
        self._cache[file_hash] = {
            "result": result,
            "time": datetime.now()
        }

    def preprocess_image(self, image_path: str) -> str:
        """图像预处理：去噪、灰度、二值化、锐化"""
        try:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"无法读取图像: {image_path}")

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            processed_path = image_path.replace(".", "_processed.", 1)
            cv2.imwrite(processed_path, binary)
            return processed_path
        except ImportError:
            logger.warning("OpenCV未安装，跳过图像预处理")
            return image_path

    def recognize_image(self, file_path: str, use_preprocess: bool = True) -> str:
        """识别图片中的文字"""
        file_hash = self._get_file_hash(file_path)

        # 检查缓存
        cached = self._check_cache(file_hash)
        if cached:
            logger.info(f"OCR缓存命中: {file_hash}")
            return cached

        # 图像预处理
        process_path = file_path
        if use_preprocess:
            try:
                process_path = self.preprocess_image(file_path)
            except Exception as e:
                logger.warning(f"图像预处理失败: {e}")

        # OCR识别
        result_text = ""
        ocr_engine = self.paddle_ocr
        if ocr_engine:
            try:
                result = ocr_engine.ocr(process_path, cls=True)
                if result and result[0]:
                    texts = [line[1][0] for line in result[0]]
                    result_text = "\n".join(texts)
            except Exception as e:
                logger.error(f"PaddleOCR识别失败: {e}")

        # 清理临时文件
        if use_preprocess and process_path != file_path:
            try:
                os.remove(process_path)
            except:
                pass

        # 保存缓存
        self._save_cache(file_hash, result_text)
        return result_text

    def recognize_pdf(self, file_path: str) -> str:
        """识别PDF中的文字"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            all_text = []
            for page in doc:
                text = page.get_text()
                if text.strip():
                    all_text.append(text)
                else:
                    # 文字提取为空，尝试OCR
                    pix = page.get_pixmap()
                    img_path = f"{file_path}_page_{page.number}.png"
                    pix.save(img_path)
                    ocr_text = self.recognize_image(img_path)
                    all_text.append(ocr_text)
                    try:
                        os.remove(img_path)
                    except:
                        pass
            doc.close()
            return "\n".join(all_text)
        except ImportError:
            logger.warning("PyMuPDF未安装，PDF识别不可用")
            return ""

    def recognize(self, file_path: str) -> str:
        """统一识别入口，自动判断文件类型"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self.recognize_pdf(file_path)
        elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
            return self.recognize_image(file_path)
        elif ext in (".docx", ".doc"):
            # Word文档直接提取文本
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:
            logger.warning(f"不支持的文件格式: {ext}")
            return ""


# 全局OCR服务实例
ocr_service = OCRService()
