import os
import json
import re
from datetime import datetime

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client

# 主感情の日本語 → 英語マッピング
EMOTION_TRANSLATION = {
    "喜び": "Joy", "期待": "Anticipation", "怒り": "Anger", "嫌悪": "Disgust",
    "悲しみ": "Sadness", "驚き": "Surprise", "恐れ": "Fear", "信頼": "Trust",
    "楽観": "Optimism", "誇り": "Pride", "病的状態": "Morbidness", "積極性": "Aggressiveness",
    "冷笑": "Cynicism", "悲観": "Pessimism", "軽蔑": "Contempt", "羨望": "Envy",
    "憤慨": "Outrage", "自責": "Remorse", "不信": "Unbelief", "恥": "Shame",
    "失望": "Disappointment", "絶望": "Despair", "感傷": "Sentimentality", "畏敬": "Awe",
    "好奇心": "Curiosity", "歓喜": "Delight", "服従": "Submission", "罪悪感": "Guilt",
    "不安": "Anxiety", "愛": "Love", "希望": "Hope", "優位": "Dominance"
}

def save_response_to_memory(response_text: str) -> dict | None:
    """
    応答テキストの中から感情構造JSONを抽出し、辞書形式で返す。
    保存はこの関数では行わない。
    """
    try:
        logger.debug("💾 save_response_to_memory 開始")

        # 🔍 JSON部分の抽出（{}の最初のブロックを想定）
        match = re.search(r"\{[\s\S]*?\}", response_text)
        if not match:
            logger.warning("⚠ 応答にJSONデータが含まれていません")
            return None

        json_part = match.group()
        try:
            parsed_data = json.loads(json_part)
        except json.JSONDecodeError as e:
            logger.warning(f"⚠ JSONパース失敗: {e}")
            return None

        logger.debug(f"📦 構造化データ抽出成功: {parsed_data}")
        return parsed_data

    except Exception as e:
        logger.error(f"❌ 構造データ抽出中に例外発生: {e}")
        return None

def write_structured_emotion_data(data: dict):
    """
    抽出済みの感情構造データ（JSON）を MongoDB Atlas の emotion_db.emotion_data に保存する。
    """
    try:
        client = get_mongo_client()
        if client is None:
            logger.error("❌ MongoDBクライアント取得に失敗")
            return

        db = client["emotion_db"]
        collection = db["emotion_data"]

        # 主感情を英語に変換
        main_emotion_ja = data.get("主感情", "")
        main_emotion_en = EMOTION_TRANSLATION.get(main_emotion_ja)
        if not main_emotion_en:
            logger.warning(f"⚠ 主感情が未定義または翻訳不可: {main_emotion_ja}")
            return

        # 重みに応じてカテゴリを決定
        weight = int(data.get("重み", 0))
        if weight >= 95:
            category = "long"
        elif weight >= 80:
            category = "intermediate"
        else:
            category = "short"

        # 保存形式整形
        document = {
            "emotion": main_emotion_en,
            "category": category,
            "data": data.copy(),
            "履歴": [data.copy()]
        }

        # MongoDBへ保存（新規挿入）
        result = collection.insert_one(document)
        logger.info(f"✅ MongoDB保存成功: _id={result.inserted_id}, 感情={main_emotion_en}, カテゴリ={category}")

    except Exception as e:
        logger.error(f"❌ 感情構造データ保存失敗: {e}")
