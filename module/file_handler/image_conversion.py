# module/file_handler/image_conversion.py

import os
from typing import List
from uuid import uuid4
from pdf2image import convert_from_path
from PIL import Image
from docx import Document

TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

def convert_pdf_to_images(file_path: str) -> List[str]:
    """
    PDFを画像に変換し、画像ファイルパスのリストを返す。
    """
    try:
        pages = convert_from_path(file_path)
        image_paths = []
        for i, page in enumerate(pages):
            img_path = os.path.join(TEMP_IMAGE_DIR, f"{uuid4().hex}_page{i+1}.png")
            page.save(img_path, "PNG")
            image_paths.append(img_path)
        return image_paths
    except Exception as e:
        print(f"[ERROR] PDF変換失敗: {e}")
        return []

def convert_docx_to_images(file_path: str) -> List[str]:
    """
    DOCX を画像に変換（暫定: テキスト抽出→画像化）。
    ※ 本格実装時は html2image 等と組み合わせる必要あり。
    """
    try:
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        if not text:
            return []
        # テキストを一時画像として保存
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        # ※ Pillow に直接描画処理を行う必要あり（未実装）
        img_path = os.path.join(TEMP_IMAGE_DIR, f"{uuid4().hex}_docx.png")
        img.save(img_path)
        return [img_path]
    except Exception as e:
        print(f"[ERROR] DOCX変換失敗: {e}")
        return []

def convert_to_images(file_path: str) -> List[str]:
    """
    拡張子に応じて画像変換関数を呼び出す。
    """
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return convert_pdf_to_images(file_path)
    elif ext == ".docx":
        return convert_docx_to_images(file_path)
    else:
        return []
