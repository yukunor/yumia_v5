import os
from typing import Tuple
import pytesseract
from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}

def perform_ocr(file_path: str) -> Tuple[str, str]:
    """
    OCRを実行し、("内容", "text"/"image") を返す。
    - 入力は画像（元画像またはimage_conversion済）
    - 出力は：
        - 10文字以上 → ("テキスト", "text")
        - 10文字未満 → (ファイルパス, "image")
    """
    ext = os.path.splitext(file_path)[-1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return "", "none"

    try:
        with Image.open(file_path) as img:
            content = pytesseract.image_to_string(img, lang="jpn+eng").strip()

        if len(content) >= 10:
            return content, "text"
        else:
            return file_path, "image"

    except Exception as e:
        print(f"[ERROR] OCR処理失敗: {e}")
        return "", "none"
