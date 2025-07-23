#module/utils/utils.py
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
import certifi
import json
import openai
from pymongo import DESCENDING
from module.mongo.mongo_client import get_mongo_client


# Renderの環境変数からOpenAIのAPIキーを取得
openai.api_key = os.getenv("OPENAI_API_KEY")

# MongoDBへ直接ログを記録する関数
def log_to_mongo(level: str, message: str):
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            collection = db["app_log"]
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": level,
                "message": message
            }
            collection.insert_one(log_entry)
    except Exception as e:
        print(f"[ERROR] MongoDBログ記録失敗: {e}")

# Pythonのloggerでinfo/debug/errorを呼び出し可能にするラッパー
class MongoLogger:
    def info(self, message): log_to_mongo("INFO", message)
    def debug(self, message): log_to_mongo("DEBUG", message)
    def warning(self, message): log_to_mongo("WARNING", message)
    def error(self, message): log_to_mongo("ERROR", message)

# 任意のモジュールで使用可能
logger = MongoLogger()


#　履歴を取得しWeb UI上に100件を上限として表示
def load_history(limit: int = 100) -> list[dict]:
    """
    MongoDBのdialogue_historyから、timestampが新しい順に最大limit件の履歴を取得する。
    """
    client = get_mongo_client()
    if client is None:
        raise ConnectionError("MongoDBクライアントの取得に失敗しました")

    db = client["emotion_db"]
    collection = db["dialogue_history"]

    # timestampで降順ソート → 新しい順にlimit件取得
    cursor = collection.find().sort("timestamp", DESCENDING).limit(limit)

    history = []
    for doc in cursor:
        history.append({
            "timestamp": doc.get("timestamp"),
            "role": doc.get("role"),
            "message": doc.get("message")
        })

# プロンプト読み込み関連
def load_emotion_prompt():
    with open("emotion_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def load_dialogue_prompt():
    with open("dialogue_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

_cached_system_prompt = None

def load_system_prompt_cached():
    global _cached_system_prompt
    if _cached_system_prompt is None:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            _cached_system_prompt = f.read().strip()
    return _cached_system_prompt
    

# 会話履歴：保存
def append_history(role, message):
    try:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "message": message
        }
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            collection = db["dialogue_history"]
            collection.insert_one(entry)
            logger.info(f"[INFO] 履歴をMongoDBに保存: {entry}")
    except Exception as e:
        logger.error(f"[ERROR] 履歴保存に失敗: {e}")
