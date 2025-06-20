import os
import json
import jsonlines
import ast
from datetime import datetime
from utils import logger  # ロガーをインポート

# 階層情報を保存するJSONLファイルのパス
file_index_path = r"C:\Users\近藤憲之\Desktop\ロードマップ\yumia_v5\yumia_v5\file_index.jsonl"

# ファイル情報を保持するためのクラス
class FileInfo:
    def __init__(self, path, file_type, size, created_at, updated_at, functions=None, classes=None):
        self.path = path
        self.file_type = file_type
        self.size = size
        self.created_at = created_at
        self.updated_at = updated_at
        self.functions = functions if functions else []
        self.classes = classes if classes else []

    def to_dict(self):
        return {
            "path": self.path,
            "file_type": self.file_type,
            "size": self.size,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "functions": self.functions,
            "classes": self.classes
        }

# ファイル階層を探索して、情報をJSONLに保存
def explore_directory(directory):
    existing_files = set()
    file_data = load_existing_file_data()

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path in existing_files:
                continue

            file_info = get_file_info(file_path)
            if file_info:
                write_file_index(file_info)
                existing_files.add(file_path)
                file_data.append(file_info.to_dict())

    remove_deleted_files(file_data, existing_files)

# ファイルの情報を取得する
def get_file_info(file_path):
    try:
        file_type = file_path.split('.')[-1] if '.' in file_path else 'Unknown'
        size = os.path.getsize(file_path)
        created_at = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        updated_at = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        functions, classes = [], []
        if file_type == 'py':
            functions, classes = extract_functions_classes(file_path)

        return FileInfo(file_path, file_type, size, created_at, updated_at, functions, classes)

    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        return None

# Pythonファイルから関数とクラスを抽出する
def extract_functions_classes(file_path):
    functions = []
    classes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
    except Exception as e:
        logger.error(f"Error extracting functions and classes from {file_path}: {e}")

    return functions, classes

# JSONLにファイル情報を書き込む
def write_file_index(file_info):
    try:
        with jsonlines.open(file_index_path, mode='a') as writer:
            writer.write(file_info.to_dict())
        logger.info(f"File info written: {file_info.path}")
    except Exception as e:
        logger.error(f"Error writing file info to index: {e}")

# 既存のファイルデータを読み込む
def load_existing_file_data():
    try:
        if os.path.exists(file_index_path):
            with jsonlines.open(file_index_path, mode='r') as reader:
                return [obj for obj in reader]
        return []
    except Exception as e:
        logger.error(f"Error reading existing file data: {e}")
        return []

# 削除されたファイルをJSONLから削除する
def remove_deleted_files(file_data, existing_files):
    try:
        remaining_files = set(file['path'] for file in file_data)
        deleted_files = remaining_files - existing_files
        if deleted_files:
            new_data = [file for file in file_data if file['path'] not in deleted_files]
            with jsonlines.open(file_index_path, mode='w') as writer:
                writer.write_all(new_data)
            logger.info(f"Deleted files removed from index: {deleted_files}")
    except Exception as e:
        logger.error(f"Error removing deleted files from index: {e}")

# 実行してファイル階層を探索するディレクトリのパス
directory_to_explore = r"C:\Users\近藤憲之\Desktop\ロードマップ\yumia_v5\yumia_v5"

# ファイル階層を探索し、情報を保存
explore_directory(directory_to_explore)
