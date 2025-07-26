# module/oblivion/oblivion_short.py
from datetime import datetime, timedelta

from module.emotion.emotion_stats import load_current_emotion
from module.mongo.mongo_client import get_mongo_client
from module.utils.utils import logger


def get_expired_short_term_emotions():
    """
    MongoDBから"short"カテゴリの感情データを全件取得し、
    各履歴内の日付が7日以上前のものがあるドキュメントのみ抽出する。
    """
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        collection = db["emotion_data"]

        short_docs = list(collection.find({"category": "short"}))
        expired_docs = []
        threshold = datetime.now() - timedelta(days=7)

        for doc in short_docs:
            history_list = doc.get("data", {}).get("履歴", [])
            for entry in history_list:
                date_str = entry.get("date")
                try:
                    entry_time = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                    if entry_time < threshold:
                        expired_docs.append(doc)
                        break
                except Exception as e:
                    logger.warning(f"[WARN] 無効な日付形式（{date_str}）: {e}")

        logger.info(f"✅ 期限切れshort感情: {len(expired_docs)} 件")
        return expired_docs

    except Exception as e:
        logger.error(f"[ERROR] 短期記憶の期限確認に失敗: {e}")
        return []


def save_oblivion_short_entries():
    """
    "short"カテゴリの感情データから、1週間以上前の履歴を抽出し、
    必要な情報のみを emotion_oblivion コレクションに保存する。
    """
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        source_collection = db["emotion_data"]
        target_collection = db["emotion_oblivion"]

        threshold = datetime.now() - timedelta(days=7)
        short_docs = list(source_collection.find({"category": "short"}))
        oblivion_entries = []

        for doc in short_docs:
            history_list = doc.get("data", {}).get("履歴", [])
            for entry in history_list:
                date_str = entry.get("date")
                if not date_str:
                    continue
                try:
                    entry_time = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                    if entry_time < threshold:
                        record = {
                            "source_id": str(doc["_id"]),
                            "emotion": doc.get("emotion"),
                            "date": date_str,
                            "構成比": entry.get("構成比", {}),
                            "状況": entry.get("状況", ""),
                            "keywords": entry.get("keywords", []),
                        }
                        oblivion_entries.append(record)
                except Exception as e:
                    logger.warning(f"[WARN] 履歴の日付形式が不正: {date_str} | {e}")

        if oblivion_entries:
            result = target_collection.insert_many(oblivion_entries)
            logger.info(f"✅ 忘却記録を {len(result.inserted_ids)} 件保存しました")
        else:
            logger.info("⛔ 忘却対象データはありませんでした")

    except Exception as e:
        logger.error(f"[ERROR] 忘却記憶の保存に失敗: {e}")
