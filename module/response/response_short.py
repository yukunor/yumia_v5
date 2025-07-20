import json
from utils import logger
from module.mongo.mongo_client import get_mongo_client
from bson import ObjectId

def get_all_short_category_data():
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")

        db = client["emotion_db"]
        collection = db["emotion_data"]

        # 🔍 category: "short" のみを抽出
        short_data = list(collection.find({"category": "short"}))
        logger.info(f"✅ shortカテゴリのデータ件数: {len(short_data)}")
        return short_data

    except Exception as e:
        logger.error(f"[ERROR] shortカテゴリデータの取得失敗: {e}")
        return []

def extract_short_summary(best_match: dict) -> dict:
    if not best_match or best_match.get("category") != "short":
        return {}

    return {
        "date": best_match.get("date"),
        "emotion": best_match.get("emotion"),
        "category": best_match.get("category")
    }

def find_short_history_by_emotion_and_date(emotion_name, category_name, target_date):
    client = get_mongo_client()
    db = client["emotion_db"]
    collection = db["emotion_data"]

    try:
        base_doc = collection.find_one({
            "emotion": emotion_name,
            "category": category_name
        })

        if not base_doc:
            logger.warning("❌ 指定されたemotionとcategoryの組み合わせが見つかりません")
            return None

        history_list = base_doc.get("data", {}).get("履歴", [])
        for record in history_list:
            if record.get("date") == target_date:
                logger.info("✅ 感情履歴の一致データを発見（short）")
                return record

        logger.info("🔍 emotionとcategoryは一致したが、dateの一致は見つかりませんでした（short）")
        return None

    except Exception as e:
        logger.error(f"[ERROR] shortカテゴリ履歴検索中にエラー発生: {e}")
        return None
