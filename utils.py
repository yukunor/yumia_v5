import jsonlines
import os
from datetime import datetime
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import certifi

# 環境変数読み込み（.envファイルから）
load_dotenv()

# 会話履歴関連
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

# プロンプト読み込み関連
def load_emotion_prompt():
    """感情推定用プロンプトは毎回読み込む"""
    with open("emotion_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def load_dialogue_prompt():
    """応答生成用プロンプトは毎回読み込む"""
    with open("dialogue_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

_cached_system_prompt = None

def load_system_prompt_cached():
    """システムプロンプトは一度だけ読み込む（キャッシュ）"""
    global _cached_system_prompt
    if _cached_system_prompt is None:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            _cached_system_prompt = f.read().strip()
    return _cached_system_prompt

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
            raise ValueError("環境変数 'MONGO_URI' が設定されていません")

        _mongo_client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        _mongo_client.admin.command("ping")
        print("[DEBUG] MongoDB Atlas接続成功")
        return _mongo_client
    except Exception as e:
        print(f"[ERROR] MongoDB接続失敗: {e}")
        logger.error(f"[ERROR] MongoDB接続失敗: {e}")
        return None
