# module/response/response_long.py

# MongoDBのemotion_dataから、categoryが"long"の全データを取得する。
# Retrieve all data from MongoDB emotion_data where category is "long".
def get_all_long_category_data():
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")
        # Failed to obtain MongoDB client

        db = client["emotion_db"]
        collection = db["emotion_data"]

        long_data = list(collection.find({"category": "long"}))
        logger.info(f"✅ longカテゴリのデータ件数: {len(long_data)}")
        # Number of records in long category
        return long_data

    except Exception as e:
        logger.error(f"[ERROR] longカテゴリデータの取得失敗: {e}")
        # Failed to retrieve long category data
        return []

# 取得済みlongデータ群から、emotion・category・dateが一致する履歴1件を探して返す。
# From the fetched long data, find and return one record where emotion, category, and date all match.
def search_long_history(all_data, emotion_name, category_name, target_date):
    try:
        for item in all_data:
            if item.get("emotion") == emotion_name and item.get("category") == category_name:
                history_list = item.get("data", {}).get("履歴", [])
                for record in history_list:
                    if record.get("date") == target_date:
                        logger.info("✅ 感情履歴の一致データを発見（long）")
                        # Found a matching emotion history (long)
                        return record

        logger.info("🔍 emotion/categoryは一致したが、dateの一致は見つかりませんでした（long）")
        # Emotion/category matched, but no matching date was found (long)
        return None

    except Exception as e:
        logger.error(f"[ERROR] 感情履歴検索中にエラー発生: {e}")
        # Error occurred while searching emotion history
        return None

