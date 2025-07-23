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


# ログレベルのしきい値（必要に応じて "DEBUG" などに変更可能）
LOG_LEVEL_THRESHOLD = "DEBUG" # "DEBUG", "INFO", "WARNING", "ERROR"


# ログレベルの優先度
LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40
}

# MongoDBへログを保存
def log_to_mongo(level: str, message: str):
    print(f"[CALL] log_to_mongo: {level} - {message}")
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

# ログラッパー（ログレベルしきい値で出力制御）
class MongoLogger:
    def log(self, level: str, message: str):
        print(f"[LOG WRAPPER] 呼び出しレベル: {level} / 閾値: {LOG_LEVEL_THRESHOLD}")
        if LEVEL_ORDER[level] >= LEVEL_ORDER[LOG_LEVEL_THRESHOLD]:
            log_to_mongo(level, message)

    def debug(self, message: str): self.log("DEBUG", message)
    def info(self, message: str): self.log("INFO", message)
    def warning(self, message: str): self.log("WARNING", message)
    def error(self, message: str): self.log("ERROR", message)
# 任意の場所で import して使用
mongo_logger = MongoLogger()








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


if __name__ == "__main__":
    print("=== Logger Test Start ===", flush=True)
    logger.debug("🌟 デバッグ動作確認")
    logger.info("🔔 通常の情報ログ")
    print("=== Logger Test End ===", flush=True)
