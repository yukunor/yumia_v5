# file_handling.py
import os
import json
import shutil
import logging

logger = logging.getLogger(__name__)

# 通常ファイル操作
def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"{file_path} が削除されました。")
        return f"{file_path} が削除されました。"
    else:
        raise FileNotFoundError(f"{file_path} は存在しません。")

def create_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    logger.info(f"{file_path} が作成されました。")
    return f"{file_path} が作成されました。"

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    logger.info(f"{file_path} に書き込みました。")

# Pythonファイル操作
def create_python_file(file_path, code_to_write):
    if os.path.exists(file_path):
        raise FileExistsError(f"{file_path} はすでに存在します。")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(code_to_write)
    logger.info(f"{file_path} が作成されました。")
    return f"{file_path} が作成されました。"

def read_python_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def append_to_python_file(file_path, code_to_add):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write("\n" + code_to_add)
    logger.info(f"コードが {file_path} に追加されました。")

def rewrite_python_file(file_path, new_code):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_code)
    logger.info(f"{file_path} が書き換えられました。")

# バックアップ・復元
def create_backup(file_path):
    backup_path = f"{file_path}.bak"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} が見つかりません。")
    shutil.copy(file_path, backup_path)
    logger.info(f"バックアップが {backup_path} に作成されました。")
    return f"{backup_path} が作成されました。"

def rollback(file_path):
    backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"{backup_path} が見つかりません。")
    shutil.copy(backup_path, file_path)
    logger.info(f"{file_path} がバックアップから復元されました。")
    return f"{file_path} がバックアップから復元されました。"
