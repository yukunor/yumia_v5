# module/file_handler/file_router.py

import os
import shutil
from fastapi import UploadFile
from uuid import uuid4

from module.file_handler.ocr_processor import perform_ocr
from module.file_handler.image_processor import process_image

# テキスト系ファイル拡張子
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}

# 画像系ファイル拡張子
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}

# ドキュメント系拡張子（OCR対象）
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx"}

# 一時保存フォルダ
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

def save_temp_file(uploaded_file: UploadFile) -> str:
    """
    一時ファイルとして保存し、そのパスを返す。
    """
    ext = os.path.splitext(uploaded_file.filename)[-1].lower()
    unique_name = f"{uuid4().hex}{ext}"
    save_path = os.path.join(TEMP_DIR, unique_name)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(uploaded_file.file, f)

    return save_path


def handle_uploaded_file(uploaded_file: UploadFile) -> tuple[str, str]:
    """
    アップロードファイルを処理し、（抽出テキスト, ファイルタイプ）を返す。
    ファイルタイプは "text", "image", "none" のいずれか。
    """
    file_path = save_temp_file(uploaded_file)
    ext = os.path.splitext(file_path)[-1].lower()

    # テキストファイル系 → そのまま読み込む
    if ext in TEXT_EXTENSIONS:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content.strip(), "text"
        except Exception:
            return "", "none"

    # 画像 or ドキュメント → OCR実施
    elif ext in IMAGE_EXTENSIONS or ext in DOCUMENT_EXTENSIONS:
        try:
            text = perform_ocr(file_path)
            if len(text.strip()) >= 10:
                return text.strip(), "text"
            else:
                return file_path, "image"
        except Exception:
            return "", "none"

    else:
        # 未対応形式
        return "", "none"
