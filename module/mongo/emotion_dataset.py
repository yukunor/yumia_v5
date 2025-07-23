# module/mongo/emotion_dataset.py

from pymongo import MongoClient
from datetime import datetime
import os
from module.utils.utils import logger

# MongoDB接続設定（RenderのEnvironment Variablesから取得）
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = "emotion_db"
COLLECTION_NAME = "dialogue_history"

def get_recent_dialogue_history(n: int = 3) -> list[dict]:
    """
    MongoDBから直近n件の対話履歴を取得（昇順に並べて返す）

    返却形式:
    [
        {"role": "user", "message": "こんにちは"},
        {"role": "assistant", "message": "こんにちは、ご主人。"},
        ...
    ]
    """
    try:
        client = MongoClient(MONGO_URI)
        collection = client[DB_NAME][COLLECTION_NAME]

        # timestamp降順で取得し、昇順に並べ直す
        cursor = collection.find(
            {},
            {"_id": 0, "role": 1, "message": 1}
        ).sort("timestamp", -1).limit(n)

        result = list(cursor)[::-1]  # 昇順に並べ替え

        return result

    except Exception as e:
        print(f"[ERROR] MongoDBからの履歴取得に失敗: {e}")
        return []

