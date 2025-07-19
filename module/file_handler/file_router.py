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

# ドキュメント系拡張子（OCR対象：ファイルに埋め込まれた画像に対応するため）
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx"}

# 一時保存フォルダ
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

def save_temp_file(uploaded_file: UploadFile) -> str:
    """
    一時ファイルとして保存し、そのパスを返す。
    保存前に3つ以上ファイルが存在する場合、古い順に削除する。
    """
    # 🔁 古いファイルを削除
    existing_files = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR)]
    if len(existing_files) >= MAX_TEMP_FILES:
        # 最終更新日時でソートして古い順に並べる
        existing_files.sort(key=lambda f: os.path.getmtime(f))
        files_to_delete = existing_files[:len(existing_files) - MAX_TEMP_FILES + 1]
        for f in files_to_delete:
            try:
                os.remove(f)
            except Exception as e:
                print(f"[WARN] ファイル削除失敗: {f} - {e}")

    # 📦 新しいファイルを保存
    ext = os.path.splitext(uploaded_file.filename)[-1].lower()
    unique_name = f"{uuid4().hex}{ext}"
    save_path = os.path.join(TEMP_DIR, unique_name)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(uploaded_file.file, f)

    return save_path

def get_latest_temp_file() -> str | None:
    """
    一時保存ディレクトリ内で一番新しいファイルを返す。
    """
    files = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR)]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]


def handle_uploaded_file(uploaded_file: UploadFile | None) -> tuple[str, str]:
    """
    アップロードファイルを処理し、（抽出テキスト, ファイルタイプ）を返す。
    ファイルタイプは "text", "image", "none" のいずれか。

    - uploaded_file があればそれを保存・処理
    - なければ temp_files 内の最新ファイルを使って処理
    """
    # ファイルの保存と選択
    if uploaded_file:
        file_path = save_temp_file(uploaded_file)
    else:
        file_path = get_latest_temp_file()
        if not file_path:
            return "", "none"

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
        return "", "none"
