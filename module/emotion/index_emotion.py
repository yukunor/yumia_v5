# module/index/index_emotion.py

import json
import os
from datetime import datetime
from collections import defaultdict, Counter

from module.utils.utils import mongo_logger as logger
from module.mongo.mongo_client import get_mongo_client

# 英語 → 日本語の正規順マッピング（構成比整形の基準）
EMOTION_TRANSLATION_REVERSE = {
    "Joy": "喜び", "Anticipation": "期待", "Anger": "怒り", "Disgust": "嫌悪",
    "Sadness": "悲しみ", "Surprise": "驚き", "Fear": "恐れ", "Trust": "信頼",
    "Optimism": "楽観", "Pride": "誇り", "Morbidness": "病的状態", "Aggressiveness": "積極性",
    "Cynicism": "冷笑", "Pessimism": "悲観", "Contempt": "軽蔑", "Envy": "羨望",
    "Outrage": "憤慨", "Remorse": "自責", "Unbelief": "不信", "Shame": "恥",
    "Disappointment": "失望", "Despair": "絶望", "Sentimentality": "感傷", "Awe": "畏敬",
    "Curiosity": "好奇心", "Delight": "歓喜", "Submission": "服従", "Guilt": "罪悪感",
    "Anxiety": "不安", "Love": "愛", "Hope": "希望", "Dominance": "優位"
}

def save_index_data(data: dict, emotion_en: str, category: str):
    """
    感情構造データを MongoDB Atlas の emotion_db.emotion_index に保存する。
    主感情・emotion はどちらも英語。
    構成比は EMOTION_TRANSLATION_REVERSE の順に従って並べる。
    """
    try:
        client = get_mongo_client()
        if client is None:
            logger.error("❌ MongoDBクライアント取得に失敗")
            return

        db = client["emotion_db"]
        collection = db["emotion_index"]

        # 🔧 構成比32感情ベクトル（正規順）
        full_composition = {}
        original_comp = data.get("構成比", {})
        for en_emotion, ja_emotion in EMOTION_TRANSLATION_REVERSE.items():
            full_composition[ja_emotion] = original_comp.get(ja_emotion, 0)

        # 🔒 date完全同期
        if "date" not in data:
            logger.error("❌ 'date' が data に存在しないため index に保存不可")
            return

        index_document = {
            "date": data["date"],
            "主感情": emotion_en,  # ✅ 修正：英語
            "構成比": full_composition,
            "キーワード": data.get("keywords", []),
            "emotion": emotion_en,  # ✅ 英語
            "category": category
        }

        result = collection.insert_one(index_document)
        logger.info(f"✅ インデックス保存成功: _id={result.inserted_id} / date={data['date']}")

    except Exception as e:
        logger.error(f"❌ インデックス保存中にエラー: {e}")
