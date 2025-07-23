#module/utils/utils.py
import os
from datetime import datetime
from dotenv import load_dotenv
import certifi
import json
import openai
from pymongo import DESCENDING

print("📌 [STEP] utils.py 読み込み開始")
openai.api_key = os.getenv("OPENAI_API_KEY")
print(f"📌 [ENV] OPENAI_API_KEY 読み込み結果: {'あり' if openai.api_key else 'なし'}")

LOG_LEVEL_THRESHOLD = "DEBUG"
LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40
}

# ✅ log_to_mongo を最初に定義（これがないと MongoLogger の評価に使えない）
def log_to_mongo(level: str, message: str):
    print(f"[CALL] log_to_mongo: {level} - {message}")
    try:
        from module.mongo.mongo_client import get_mongo_client  # ← 遅延importで安全
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

# ✅ 先に MongoLogger を定義（log_to_mongo 使用可能に）
class MongoLogger:
    def log(self, level: str, message: str):
        print(f"[LOG WRAPPER] 呼び出しレベル: {level} / 閾値: {LOG_LEVEL_THRESHOLD}")
        if LEVEL_ORDER[level] >= LEVEL_ORDER[LOG_LEVEL_THRESHOLD]:
            log_to_mongo(level, message)

    def debug(self, message: str): self.log("DEBUG", message)
    def info(self, message: str): self.log("INFO", message)
    def warning(self, message: str): self.log("WARNING", message)
    def error(self, message: str): self.log("ERROR", message)

logger = MongoLogger()
print(f"📌 [CHECK] logger の型: {type(logger)}")

# MongoDBクライアント（← logger 初期化後にインポート）
from module.mongo.mongo_client import get_mongo_client

# MongoDBにログを保存
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

# 履歴を取得
def load_history(limit: int = 100) -> list[dict]:
    client = get_mongo_client()
    if client is None:
        raise ConnectionError("MongoDBクライアントの取得に失敗しました")

    db = client["emotion_db"]
    collection = db["dialogue_history"]
    cursor = collection.find().sort("timestamp", DESCENDING).limit(limit)

    history = []
    for doc in cursor:
        history.append({
            "timestamp": doc.get("timestamp"),
            "role": doc.get("role"),
            "message": doc.get("message")
        })
    return history

# プロンプト読み込み
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

# 会話履歴保存
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

# テスト用出力
if __name__ == "__main__":
    print("=== Logger Test Start ===", flush=True)
    logger.debug("🌟 デバッグ動作確認")
    logger.info("🔔 通常の情報ログ")
    print("=== Logger Test End ===", flush=True)
