import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from module.utils.utils import logger

_mongo_client = None

def get_mongo_client():
    global _mongo_client

    if _mongo_client is not None:
        try:
            _mongo_client.admin.command("ping")
            logger.info("[✅] 既存のMongoClientは正常に接続されています")
            return _mongo_client
        except ConnectionFailure:
            logger.warning("[⚠️] 既存のMongoClientが失敗しました。再接続を試みます")
            logger.warning("[WARNING] 既存のMongoClientが失敗 → 再接続")

    try:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            raise ValueError("環境変数 'MONGODB_URI' が設定されていません")

        _mongo_client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        _mongo_client.admin.command("ping")
        logger.info("[✅] MongoDBへの新規接続に成功しました")
        logger.info("[INFO] MongoDB Atlas接続成功")
        return _mongo_client
    except Exception as e:
        logger.warning(f"[❌] MongoDB接続に失敗しました: {e}")
        logger.warning(f"[ERROR] MongoDB接続失敗: {e}")
        return None

