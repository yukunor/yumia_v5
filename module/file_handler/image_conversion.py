# module/file_handler/image_conversion.py

import os
from typing import List
from uuid import uuid4
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
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
    DOCXを簡易的に画像化（テキスト抽出→画像生成）。
    ※ 本格実装では html2image 等が望ましい。
    """
    try:
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        if not text:
            return []

        # テキストを白背景の画像に描画
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        draw.text((20, 20), text, fill=(0, 0, 0), font=font)

        img_path = os.path.join(TEMP_IMAGE_DIR, f"{uuid4().hex}_docx.png")
        img.save(img_path)
        return [img_path]

    except Exception as e:
        print(f"[ERROR] DOCX変換失敗: {e}")
        return []


def convert_to_images(file_path: str) -> List[str]:
    """
    指定ファイルを拡張子に応じて画像変換し、画像パスのリストを返す。
    """
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return convert_pdf_to_images(file_path)
    elif ext == ".docx":
        return convert_docx_to_images(file_path)
    else:
        return []
