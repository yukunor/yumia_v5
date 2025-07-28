# module/index/index_emotion.py

import json
import os
from datetime import datetime
from collections import defaultdict, Counter

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client
from module.params import emotion_map  # ✅ 共通辞書の読み込み

# ✅ 正規順の日本語感情リスト（英語順に並べ替え）
emotion_order = [emotion_map[en] for en in sorted(emotion_map.keys()) if en in emotion_map]

def save_index_data(data: dict, emotion_en: str, category: str):
    """
    感情構造データを MongoDB Atlas の emotion_db.emotion_index に保存する。
    主感情・emotion はどちらも英語。
    構成比は emotion_map に基づく日本語感情で統一し、英語順で並べる。
    """
    try:
        client = get_mongo_client()
        if client is None:
            logger.error("❌ MongoDBクライアント取得に失敗")
            return

        db = client["emotion_db"]
        collection = db["emotion_index"]

        # 🔧 構成比32感情ベクトル（emotion_mapの英語順 → 日本語で格納）
        full_composition = {}
        original_comp = data.get("構成比", {})
        for ja_emotion in emotion_order:
            full_composition[ja_emotion] = original_comp.get(ja_emotion, 0)

        # 🔒 date完全同期
        if "date" not in data:
            logger.error("❌ 'date' が data に存在しないため index に保存不可")
            return

        index_document = {
            "date": data["date"],
            "主感情": emotion_en,
            "構成比": full_composition,
            "キーワード": data.get("keywords", []),
            "emotion": emotion_en,
            "category": category
        }

        result = collection.insert_one(index_document)
        logger.info(f"✅ インデックス保存成功: _id={result.inserted_id} / date={data['date']}")

    except Exception as e:
        logger.error(f"❌ インデックス保存中にエラー: {e}")
