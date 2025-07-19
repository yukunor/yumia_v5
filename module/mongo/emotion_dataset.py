
# module/mongo/emotion_dataset.py

from pymongo import MongoClient
from datetime import datetime
import os

# MongoDB接続設定
MONGO_URI = os.getenv("MONGODB_URI")  # .env などから読み込む
DB_NAME = "emotion_db"
COLLECTION_NAME = "dialogue_history"

def get_recent_dialogue_history(n: int = 3) -> list[dict]:
    """
    MongoDBから直近n件の対話履歴を取得（昇順に並べて返す）
    """
    try:
        client = MongoClient(MONGO_URI)
        collection = client[DB_NAME][COLLECTION_NAME]

        # timestampの降順で取得し、昇順に並べ直す
        cursor = collection.find({}, {"_id": 0, "role": 1, "message": 1})\
                           .sort("timestamp", -1)\
                           .limit(n)

        result = list(cursor)[::-1]  # 最新順→昇順に反転

        return result

    except Exception as e:
        print(f"[ERROR] MongoDBからの履歴取得に失敗: {e}")
        return []
