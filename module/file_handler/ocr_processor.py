# module/file_handler/ocr_processor.py

import os
from typing import Optional
from PIL import Image
import pytesseract

from pdf2image import convert_from_path
from docx import Document

# OCR処理の共通関数
def perform_ocr(file_path: str) -> str:
    ext = os.path.splitext(file_path)[-1].lower()

    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}:
        return ocr_image(file_path)

    elif ext == ".pdf":
        return ocr_pdf(file_path)

    elif ext == ".docx":
        return ocr_docx(file_path)

    else:
        return ""

# 画像からOCR
def ocr_image(file_path: str) -> str:
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang='jpn+eng')
        return text
    except Exception as e:
        print(f"[ERROR] 画像OCR失敗: {e}")
        return ""

# PDFを画像化して全ページOCR
def ocr_pdf(file_path: str) -> str:
    try:
        pages = convert_from_path(file_path)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page, lang='jpn+eng') + "\n"
        return text
    except Exception as e:
        print(f"[ERROR] PDF OCR失敗: {e}")
        return ""

# Word（.docx）からテキスト抽出
def ocr_docx(file_path: str) -> str:
    try:
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"[ERROR] DOCX OCR失敗: {e}")
        return ""
