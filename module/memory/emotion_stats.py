def get_top_long_emotions():
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        collection = db["emotion_index"]

        long_docs = collection.find({"category": "long"})
        counter = Counter()

        for i, doc in enumerate(long_docs, start=1):
            category = doc.get("category", "undefined")
            emotion_en = doc.get("emotion", "Unknown").strip()
            history_list = doc.get("履歴", [])

            print(f"[DEBUG] doc {i} を処理中: category = {category} | emotion = {emotion_en}")
            print(f"[DEBUG] doc {i} の履歴数: {len(history_list)}")

            key = f"{category}/{emotion_en}"
            counter[key] += len(history_list)

        print("\n📊 [カテゴリ/感情: 件数] 出力:")
        for key, count in counter.items():
            print(f"  - {key}: {count}件")

        return counter

    except Exception as e:
        logger.error(f"[ERROR] MongoDBからlongカテゴリ感情の取得に失敗: {e}")
        return {}


