import os
from typing import Tuple
import pytesseract
from PIL import Image

from module.file_router import route_file_for_processing
from module.utils.utils import logger

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}

# OCRを実行し、("内容", "text"/"image") を返す。
# Execute OCR and return ("content", "text"/"image").
def perform_ocr(file_path: str) -> Tuple[str, str]:
    ext = os.path.splitext(file_path)[-1].lower()

    # テキストファイル処理（無条件でtext扱い）
    # Text file processing (unconditionally treat as text)
    if ext in TEXT_EXTENSIONS:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            return content, "text"
        except Exception as e:
            print(f"[ERROR] テキスト読込失敗: {e}")  # Text read failed
            return "", "none"

    # 画像ファイル処理（OCR＋文字数判定）
    # Image file processing (OCR + character count check)
    if ext in IMAGE_EXTENSIONS:
        try:
            with Image.open(file_path) as img:
                content = pytesseract.image_to_string(img, lang="jpn+eng").strip()
            if len(content) >= 10:
                return content, "text"
            else:
                return file_path, "image"
        except Exception as e:
            print(f"[ERROR] OCR処理失敗: {e}")  # OCR processing failed
            return "", "none"

    # どちらでもないファイル
    # Files that are neither text nor image
    return "", "none"
