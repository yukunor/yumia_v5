# module/file_handler/image_conversion.py

import os
from typing import List
from uuid import uuid4
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
from docx import Document

from module.file_router import route_file_for_processing
from module.utils.utils import logger

TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

# PDFを画像に変換し、画像ファイルパスのリストを返す。
# Convert PDF to images and return list of image file paths.
def convert_pdf_to_images(file_path: str) -> List[str]:
    
    try:
        pages = convert_from_path(file_path)
        image_paths = []
        for i, page in enumerate(pages):
            img_path = os.path.join(TEMP_IMAGE_DIR, f"{uuid4().hex}_page{i+1}.png")
            page.save(img_path, "PNG")
            image_paths.append(img_path)
        return image_paths
    except Exception as e:
        logger.warning(f"[ERROR] PDF変換失敗: {e}")  # PDF conversion failed
        return []

# DOCXを単純に画像化する（テキスト抽出や描画処理を行わず、レイアウト簡易化）。
# Simply convert DOCX to image (without text extraction or drawing, simplified layout).
def convert_docx_to_images(file_path: str) -> List[str]:
    try:
        # 仮に「このファイルを受け取った」という証明用のダミー画像を作成
        # Create dummy image as proof of file receipt (placeholder)
        # 本格実装では html2image や Word → PDF → Image 等に置き換え
        # In full implementation, replace with html2image or Word→PDF→Image etc.
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        draw.text((30, 250), "DOCX file image placeholder", fill=(0, 0, 0), font=font)

        img_path = os.path.join(TEMP_IMAGE_DIR, f"{uuid4().hex}_docx.png")
        img.save(img_path)
        return [img_path]

    except Exception as e:
        logger.warning(f"[ERROR] DOCX画像化失敗: {e}")  # DOCX image conversion failed
        return []

# 指定ファイルを拡張子に応じて画像変換し、画像パスのリストを返す。
# Convert specified file to images depending on extension, return list of image paths.
def convert_to_images(file_path: str) -> List[str]:
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return convert_pdf_to_images(file_path)
    elif ext == ".docx":
        return convert_docx_to_images(file_path)
    else:
        return []

