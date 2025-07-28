#module/response/response_short.py
import json
from bson import ObjectId

from module.mongo.mongo_client import get_mongo_client
from module.response.response_index import find_best_match_by_composition
from module.utils.utils import logger

# MongoDBのemotion_dataから、categoryが"short"の全データを取得する。
# Retrieve all data from MongoDB emotion_data where category is "short".
def get_all_short_category_data():
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")
        # Failed to obtain MongoDB client

        db = client["emotion_db"]
        collection = db["emotion_data"]

        short_data = list(collection.find({"category": "short"}))
        logger.info(f"✅ shortカテゴリのデータ件数: {len(short_data)}")
        # Number of records in short category
        return short_data

    except Exception as e:
        logger.error(f"[ERROR] shortカテゴリデータの取得失敗: {e}")
        # Failed to retrieve short category data
        return []

# 取得済みshortデータ群から、emotion・category・dateが一致する履歴1件を探して返す。
# From the fetched short data, find and return one record where emotion, category, and date all match.
def search_short_history(all_data, emotion_name, category_name, target_date):
    for item in all_data:
        if item.get("emotion") == emotion_name and item.get("category") == category_name:
            history_list = item.get("data", {}).get("履歴", [])
            for record in history_list:
                if record.get("date") == target_date:
                    logger.info("✅ 感情履歴の一致データを発見（short）")
                    # Found a matching emotion history (short)
                    return record

    logger.info("🔍 emotion/categoryは一致したが、dateの一致は見つかりませんでした（short）")
    # Emotion/category matched, but no matching date was found (short)
    return None

