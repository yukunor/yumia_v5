#module/emotion/main_emotion.py
import os
import json
import re
from datetime import datetime

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client
from module.emotion.index_emotion import save_index_data


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

#応答テキストの中から感情構造JSONを抽出し、辞書形式で返す。
def save_response_to_memory(response_text: str) -> dict | None:
    try:
        logger.debug("💾 save_response_to_memory 開始")

        # まず完全なJSONかどうかを試す
        try:
            parsed = json.loads(response_text)
            logger.info(f"[INFO] JSONパース成功（直接）: {parsed}")
            return parsed
        except json.JSONDecodeError:
            logger.warning("⚠ JSONパース失敗。混在形式の可能性あり → 正規表現で抽出を試行")

        # 🔍 正規表現で { ... } ブロックを複数抽出し、末尾から順に試す
        matches = re.findall(r'({.*})', response_text, re.DOTALL)
        if matches:
            for match in reversed(matches):
                try:
                    parsed = json.loads(match)
                    logger.info(f"[INFO] JSONパース成功（正規抽出）: {parsed}")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.warning(f"[WARN] 抽出JSONパース失敗: {e}")
        else:
            logger.warning("[WARN] 正規表現によるJSON候補抽出に失敗")

    except Exception as e:
        logger.error(f"❌ 構造データ抽出中に例外発生: {e}")

    logger.info("📭 JSON抽出に失敗。Noneを返します。")
    return None

#抽出済みの感情構造データ（JSON）を MongoDB Atlas の emotion_db.emotion_data に保存する。
def write_structured_emotion_data(data: dict):
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
        
        # 🔄 インデックスにも同時保存(emotion_index.py)
        if "date" in data:
            save_index_data(
                data=data,
                emotion_en=main_emotion_en,
                category=category
            )
        else:
            logger.warning("⚠ dateが存在しないためインデックス保存スキップ")

    except Exception as e:
        logger.error(f"❌ 感情構造データ保存失敗: {e}")
        
