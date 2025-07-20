import json
from utils import logger  # 共通ロガーをインポート
from module.mongo.mongo_client import get_mongo_client
from bson import ObjectId

def get_all_long_category_data():
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")

        db = client["emotion_db"]
        collection = db["emotion_data"]

        # 🔍 category: "long" のみを抽出
        long_data = list(collection.find({"category": "long"}))
        logger.info(f"✅ longカテゴリのデータ件数: {len(long_data)}")
        return long_data

    except Exception as e:
        logger.error(f"[ERROR] longカテゴリデータの取得失敗: {e}")
        return []

def extract_long_summary(best_match: dict) -> dict:
    """
    best_match から long カテゴリに該当する場合に必要な情報を抽出する。
    """
    if not best_match or best_match.get("category") != "long":
        return {}

    return {
        "date": best_match.get("date"),
        "emotion": best_match.get("emotion"),
        "category": best_match.get("category")
    }


def find_history_by_emotion_and_date(emotion_name, category_name, target_date):
    client = get_mongo_client()
    db = client["emotion_db"]
    collection = db["emotion_data"]

    try:
        # ステップ①: emotion と category で候補を絞る
        base_doc = collection.find_one({
            "emotion": emotion_name,
            "category": category_name
        })

        if not base_doc:
            logger.warning("❌ 指定されたemotionとcategoryの組み合わせが見つかりません")
            return None

        # ステップ②: data.履歴 から date 一致を検索
        history_list = base_doc.get("data", {}).get("履歴", [])
        for record in history_list:
            if record.get("date") == target_date:
                logger.info("✅ 感情履歴の一致データを発見")
                return record

        logger.info("🔍 emotionとcategoryは一致したが、dateの一致は見つかりませんでした")
        return None

    except Exception as e:
        logger.error(f"[ERROR] 感情履歴検索中にエラー発生: {e}")
        return None
