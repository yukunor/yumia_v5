#module/emotion/basic_personality.py
import os
import json
from collections import Counter

from module.mongo.mongo_client import get_mongo_client
from module.utils.utils import logger



# 英語→日本語の感情マッピング辞書
emotion_map = {
    "Anger": "怒り", "Anticipation": "期待", "Anxiety": "不安", "Awe": "畏敬",
    "Contempt": "軽蔑", "Curiosity": "好奇心", "Cynicism": "冷笑", "Delight": "歓喜",
    "Despair": "絶望", "Disappointment": "失望", "Disgust": "嫌悪", "Dominance": "優位",
    "Envy": "羨望", "Fear": "恐れ", "Guilt": "自責", "Hope": "希望", "Joy": "喜び",
    "Love": "愛", "Optimism": "楽観", "Outrage": "憤慨", "Pessimism": "悲観",
    "Pride": "誇り", "Remorse": "後悔", "Sadness": "悲しみ", "Sentimentality": "感傷",
    "Shame": "恥", "Surprise": "驚き", "Trust": "信頼", "Unbelief": "不信",
    "Aggressiveness": "積極性"
}

def get_top_long_emotions():
    
    #MongoDBからlongカテゴリのemotionをカウントし、
    #出現頻度の高い感情トップ4（日本語）を返す。
    
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        collection = db["emotion_data"]

        logger.info("📡 MongoDBクライアント接続完了 → longカテゴリを走査")
        long_docs = collection.find({"category": "long"})

        counter = Counter()
        for i, doc in enumerate(long_docs, start=1):
            emotion_en = str(doc.get("emotion", "")).strip()
            if not emotion_en:
                logger.warning(f"[WARN] doc {i} にemotionフィールドが存在しない")
                continue
            counter[emotion_en] += 1
            logger.debug(f"[DEBUG] doc {i}: emotion = {emotion_en}")

        total = sum(counter.values())
        logger.debug(f"[DEBUG] 主感情カウント合計: {total} 件")

        top4_en = counter.most_common(4)
        top4_jp = [(emotion_map.get(en, en), count) for en, count in top4_en]

        logger.info(f"🧭 現在人格傾向（日本語）: {dict(top4_jp)}")
        return top4_jp

    except Exception as e:
        logger.error(f"[ERROR] MongoDBからlongカテゴリ感情の取得に失敗: {e}")
        return []
