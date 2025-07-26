from bson import ObjectId

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client

def remove_index_entries_by_date():
    """
    emotion_oblivion に保存された short / intermediate カテゴリの date に一致する履歴を、
    emotion_index コレクションから削除する（_id単位ではなく履歴要素単位）。
    """
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        index_collection = db["emotion_index"]
        oblivion_collection = db["emotion_oblivion"]

        # short / intermediate 限定
        target_entries = list(oblivion_collection.find({
            "category": {"$in": ["short", "intermediate"]}
        }))

        if not target_entries:
            logger.info("⛔ 忘却記録が存在しないため、emotion_index の履歴削除はスキップされました")
            return

        total_modified = 0

        for entry in target_entries:
            target_date = entry.get("date")
            if not target_date:
                continue

            # 該当する emotion_index ドキュメント（履歴内のdate一致）
            matching_docs = list(index_collection.find({"履歴.date": target_date}))

            for doc in matching_docs:
                original_history = doc.get("履歴", [])
                new_history = [h for h in original_history if h.get("date") != target_date]

                result = index_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"履歴": new_history}}
                )

                if result.modified_count:
                    total_modified += 1
                    logger.info(f"🧹 emotion_index: _id={doc['_id']} から履歴 date={target_date} を削除")

        logger.info(f"✅ emotion_index の履歴削除完了（更新件数: {total_modified}）")

    except Exception as e:
        logger.error(f"[ERROR] emotion_index の履歴削除処理に失敗: {e}")



def remove_history_entries_by_date():
    """
    emotion_oblivion に保存された short / intermediate カテゴリの各 date に基づき、
    emotion_data 内の履歴配列から該当する履歴オブジェクトを削除する。
    """
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        oblivion_collection = db["emotion_oblivion"]
        data_collection = db["emotion_data"]

        # short / intermediate のみ対象
        target_entries = list(oblivion_collection.find({
            "category": {"$in": ["short", "intermediate"]}
        }))

        if not target_entries:
            logger.info("⛔ 忘却記録が存在しないため、履歴削除はスキップされました")
            return

        modified_total = 0

        for entry in target_entries:
            date = entry.get("date")
            if not date:
                continue

            # emotion_data の中で data.履歴[].date == この date を持つドキュメントを探す
            target_doc = data_collection.find_one({"data.履歴.date": date})

            if not target_doc:
                logger.warning(f"[WARN] date={date} に一致する履歴を持つ感情データが見つかりませんでした")
                continue

            history_list = target_doc.get("data", {}).get("履歴", [])
            new_history = [h for h in history_list if h.get("date") != date]

            result = data_collection.update_one(
                {"_id": target_doc["_id"]},
                {"$set": {"data.履歴": new_history}}
            )

            if result.modified_count:
                modified_total += 1
                logger.info(f"🧹 履歴削除: _id={target_doc['_id']} | date={date}")

        logger.info(f"✅ emotion_data の履歴削除完了（更新件数: {modified_total}）")

    except Exception as e:
        logger.error(f"[ERROR] emotion_data の履歴削除に失敗: {e}")
