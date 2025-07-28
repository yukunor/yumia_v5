import os
import shutil
from uuid import uuid4
from fastapi import UploadFile

from module.utils.utils import logger

# 最大一時保存ファイル数
# Maximum number of temporary saved files
MAX_TEMP_FILES = 3

# テキスト系ファイル拡張子（完全にテキストと判断できるもの）
# Text file extensions (definitely text)
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}

# 非テキスト系ファイル拡張子（画像変換が必要な可能性のあるもの）
# Non-text file extensions (may require image conversion)
NON_TEXT_EXTENSIONS = {".pdf", ".docx", ".pptx"}

# 一時保存フォルダ
# Temporary storage folder
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)


# 保存前に3つ以上ファイルが存在する場合、古い順に削除する。
# Before saving, if there are more than 3 files, delete oldest first.
def save_temp_file(uploaded_file: UploadFile) -> str:
    existing_files = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR)]
    if len(existing_files) >= MAX_TEMP_FILES:
        existing_files.sort(key=lambda f: os.path.getmtime(f))
        files_to_delete = existing_files[:len(existing_files) - MAX_TEMP_FILES + 1]
        for f in files_to_delete:
            try:
                os.remove(f)
            except Exception as e:
                print(f"[WARN] ファイル削除失敗: {f} - {e}")  # File deletion failed

    ext = os.path.splitext(uploaded_file.filename)[-1].lower()
    unique_name = f"{uuid4().hex}{ext}"
    save_path = os.path.join(TEMP_DIR, unique_name)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(uploaded_file.file, f)

    return save_path

# 一時保存ディレクトリ内で一番新しいファイルを返す。
# Return the newest file in the temporary storage directory.
def get_latest_temp_file() -> str | None:
    files = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR)]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]

# ファイルの種類を判定し、処理対象ファイルのパスを返す。
# Determine file type and return path of file to process.
def route_file_for_processing(uploaded_file: UploadFile | None) -> str:
    if uploaded_file:
        file_path = save_temp_file(uploaded_file)
    else:
        file_path = get_latest_temp_file()
        if not file_path:
            return ""

    ext = os.path.splitext(file_path)[-1].lower()

    # テキストファイル → そのまま返す
    # Text file → return as is
    if ext in TEXT_EXTENSIONS:
        return file_path

    # 非テキスト（PDF, DOCXなど） → 画像変換して返す（1枚目）
    # Non-text (PDF, DOCX etc.) → convert to image and return (first page)
    elif ext in NON_TEXT_EXTENSIONS:
        try:
            image_paths = convert_to_images(file_path)
            if image_paths:
                return image_paths[0]  # Use first image only
            else:
                return ""
        except Exception as e:
            logger.warning(f"[ERROR] 画像変換失敗: {e}")  # Image conversion failed
            return ""

    # その他（png, jpg など画像ファイル） → そのまま返す
    # Others (png, jpg etc. image files) → return as is
    else:
        return file_path
