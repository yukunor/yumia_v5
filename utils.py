import os
from datetime import datetime
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import certifi
import json
import openai

# Renderの環境変数からOpenAIのAPIキーを取得
openai.api_key = os.getenv("OPENAI_API_KEY")

# ロガー
logger = logging.getLogger("yumia_logger")
if not logger.hasHandlers():
    handler = logging.FileHandler("app.log", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

# 🔌 MongoDB Atlas接続管理関数
_mongo_client = None

def get_mongo_client():
    global _mongo_client
    if _mongo_client is not None:
        try:
            _mongo_client.admin.command("ping")
            return _mongo_client
        except ConnectionFailure:
            print("[DEBUG] 既存のMongoClientが失敗 → 再接続")

    try:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            raise ValueError("環境変数 'MONGODB_URI' が設定されていません")

        _mongo_client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        _mongo_client.admin.command("ping")
        print("[DEBUG] MongoDB Atlas接続成功")
        return _mongo_client
    except Exception as e:
        print(f"[ERROR] MongoDB接続失敗: {e}")
        logger.error(f"[ERROR] MongoDB接続失敗: {e}")
        return None

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

# 会話履歴：読み込み
def load_history(limit=100):
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            collection = db["dialogue_history"]
            entries = list(collection.find().sort("timestamp", -1).limit(limit))
            return list(reversed(entries))
    except Exception as e:
        logger.error(f"[ERROR] 履歴の読み込みに失敗: {e}")
        return []

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

