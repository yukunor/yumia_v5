import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

_mongo_client = None

def get_mongo_client():
    global _mongo_client

    if _mongo_client is not None:
        try:
            _mongo_client.admin.command("ping")
            print("[✅] 既存のMongoClientは正常に接続されています")
            return _mongo_client
        except ConnectionFailure:
            print("[⚠️] 既存のMongoClientが失敗しました。再接続を試みます")
            print("[WARNING] 既存のMongoClientが失敗 → 再接続")

    try:
        mongo_uri = os.getenv("MONGODB_URI")
        print(f"[🔍] 環境変数 MONGODB_URI: {mongo_uri}")
        if not mongo_uri:
            raise ValueError("環境変数 'MONGODB_URI' が設定されていません")

        _mongo_client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        _mongo_client.admin.command("ping")
        print("[✅] MongoDBへの新規接続に成功しました")
        print("[INFO] MongoDB Atlas接続成功")
        return _mongo_client
    except Exception as e:
        print(f"[❌] MongoDB接続に失敗しました: {e}")
        print(f"[ERROR] MongoDB接続失敗: {e}")
        return None

