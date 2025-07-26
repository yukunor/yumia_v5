#module/oblivion/oblivion_purge.py
from datetime import datetime, timedelta

from module.mongo.mongo_client import get_mongo_client
from module.utils.utils import logger


#emotion_oblivion に保存されたデータのうち、"date" が6か月以上前のものを完全削除する。
def delete_expired_oblivion_entries():
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        collection = db["emotion_oblivion"]

        threshold = datetime.now() - timedelta(days=180)
        expired_ids = []

        # 全件走査して、dateがしきい値より古いものを抽出
        all_entries = list(collection.find({}))
        for doc in all_entries:
            date_str = doc.get("date")
            if not date_str:
                continue
            try:
                record_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                if record_date < threshold:
                    expired_ids.append(doc["_id"])
            except Exception as e:
                logger.warning(f"[WARN] 日付解析失敗: {date_str} | {e}")

        if expired_ids:
            result = collection.delete_many({"_id": {"$in": expired_ids}})
            logger.info(f"🗑️ 6か月以上経過した忘却データを {result.deleted_count} 件削除しました")
        else:
            logger.info("⏳ 削除対象となる6か月以上前の忘却データはありませんでした")

    except Exception as e:
        logger.error(f"[ERROR] emotion_oblivion の期限切れ削除に失敗: {e}")

#emotion_oblivion に保存された shortカテゴリのデータのうち、"date" が14日以上前のものを完全削除する。
def delete_expired_short_oblivion_entries():
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        collection = db["emotion_oblivion"]

        threshold = datetime.now() - timedelta(days=14)
        expired_ids = []

        # shortカテゴリ限定で処理
        short_entries = list(collection.find({"category": "short"}))

        for doc in short_entries:
            date_str = doc.get("date")
            if not date_str:
                continue
            try:
                record_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                if record_date < threshold:
                    expired_ids.append(doc["_id"])
            except Exception as e:
                logger.warning(f"[WARN] 日付解析失敗: {date_str} | {e}")

        if expired_ids:
            result = collection.delete_many({"_id": {"$in": expired_ids}})
            logger.info(f"🗑️ shortカテゴリの忘却データを {result.deleted_count} 件削除しました（14日以上経過）")
        else:
            logger.info("⏳ 削除対象となる14日以上前のshortデータはありませんでした")

    except Exception as e:
        logger.error(f"[ERROR] shortカテゴリの忘却データ削除に失敗: {e}")
