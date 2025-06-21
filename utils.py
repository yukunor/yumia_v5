import jsonlines
import os
from datetime import datetime
import logging

history_file = "dialogue_history.jsonl"

def append_history(role, message):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "role": role,
        "message": message
    }
    with jsonlines.open(history_file, mode='a') as writer:
        writer.write(entry)

def load_history():
    if not os.path.exists(history_file):
        return []
    with jsonlines.open(history_file, "r") as reader:
        return list(reader)

def load_user_prompt():
    """ユーザープロンプトは毎回読み込む"""
    with open("user_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

_cached_system_prompt = None

def load_system_prompt_cached():
    """システムプロンプトは一度だけ読み込む（キャッシュ）"""
    global _cached_system_prompt
    if _cached_system_prompt is None:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            _cached_system_prompt = f.read().strip()
    return _cached_system_prompt

logger = logging.getLogger("yumia_logger")
if not logger.hasHandlers():
    handler = logging.FileHandler("app.log", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
