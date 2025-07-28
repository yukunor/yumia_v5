# module/response/response_intermediate.py

# MongoDBのemotion_dataから、categoryが"intermediate"の全データを取得する。
# Retrieve all data from MongoDB emotion_data where category is "intermediate".
def get_all_intermediate_category_data():
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")
        # Failed to obtain MongoDB client

        db = client["emotion_db"]
        collection = db["emotion_data"]

        data = list(collection.find({"category": "intermediate"}))
        logger.info(f"✅ intermediateカテゴリのデータ件数: {len(data)}")
        # Number of records in intermediate category
        return data

    except Exception as e:
        logger.error(f"[ERROR] intermediateカテゴリデータの取得失敗: {e}")
        # Failed to retrieve intermediate category data
        return []

# 取得済みintermediateデータ群から、emotion・category・dateが一致する履歴1件を探して返す。
# From the fetched intermediate data, find and return one record where emotion, category, and date all match.
def search_intermediate_history(all_data, emotion_name, category_name, target_date):
    for item in all_data:
        if item.get("emotion") == emotion_name and item.get("category") == category_name:
            history_list = item.get("data", {}).get("履歴", [])
            for record in history_list:
                if record.get("date") == target_date:
                    logger.info("✅ 感情履歴の一致データを発見（intermediate）")
                    # Found a matching emotion history (intermediate)
                    return record

    logger.info("🔍 emotion/categoryは一致したが、dateの一致は見つかりませんでした（intermediate）")
    # Emotion/category matched, but no matching date was found (intermediate)
    return None

