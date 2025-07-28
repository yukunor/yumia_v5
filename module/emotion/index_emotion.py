# module/index/index_emotion.py

import json
import os
from datetime import datetime
from collections import defaultdict, Counter

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client
from module.params import emotion_map 

# ✅ 正規順の日本語感情リスト（英語順に並べ替え）
# ✅ Ordered list of Japanese emotions sorted by English order
emotion_order = [emotion_map[en] for en in sorted(emotion_map.keys()) if en in emotion_map]

# 感情構造データを MongoDB Atlas の emotion_db.emotion_index に保存する。
# Save emotion structure data to MongoDB Atlas emotion_db.emotion_index.
def save_index_data(data: dict, emotion_en: str, category: str):
    try:
        client = get_mongo_client()
        if client is None:
            logger.error("❌ MongoDBクライアント取得に失敗")  # Failed to obtain MongoDB client
            return

        db = client["emotion_db"]
        collection = db["emotion_index"]

        # 🔧 構成比32感情ベクトル（emotion_mapの英語順 → 日本語で格納）
        # 🔧 Full 32 emotion composition vector (stored in Japanese order based on English order in emotion_map)
        full_composition = {}
        original_comp = data.get("構成比", {})
        for ja_emotion in emotion_order:
            full_composition[ja_emotion] = original_comp.get(ja_emotion, 0)

        # 🔒 date完全同期
        # 🔒 Ensure 'date' is fully synchronized
        if "date" not in data:
            logger.error("❌ 'date' が data に存在しないため index に保存不可")  # Cannot save index because 'date' is missing in data
            return

        index_document = {
            "date": data["date"],
            "主感情": emotion_en,  # Main emotion
            "構成比": full_composition,  # Composition ratio
            "キーワード": data.get("keywords", []),  # Keywords
            "emotion": emotion_en,
            "category": category
        }

        result = collection.insert_one(index_document)
        logger.info(f"✅ インデックス保存成功: _id={result.inserted_id} / date={data['date']}")  # Index saved successfully

    except Exception as e:
        logger.error(f"❌ インデックス保存中にエラー: {e}")  # Error occurred while saving index
