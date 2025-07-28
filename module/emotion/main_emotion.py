# module/emotion/main_emotion.py

import os
import json
import re
from datetime import datetime

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client
from module.emotion.index_emotion import save_index_data
from module.params import emotion_map

# 応答テキストの中から感情構造JSONを抽出し、辞書形式で返す。
# Extract emotion structure JSON from response text and return as a dictionary.
def save_response_to_memory(response_text: str) -> dict | None:
    try:
        logger.debug("💾 save_response_to_memory 開始")  # save_response_to_memory start

        # まず完全なJSONかどうかを試す
        # First, try if it's a complete JSON
        try:
            parsed = json.loads(response_text)
            logger.info(f"[INFO] JSONパース成功（直接）: {parsed}")  # JSON parse succeeded (direct)
            return parsed
        except json.JSONDecodeError:
            logger.warning("⚠ JSONパース失敗。混在形式の可能性あり → 正規表現で抽出を試行")  # JSON parse failed, possibly mixed format → try extraction by regex

        # 🔍 正規表現で { ... } ブロックを複数抽出し、末尾から順に試す
        # Extract multiple { ... } blocks by regex and try from the end
        matches = re.findall(r'({.*})', response_text, re.DOTALL)
        if matches:
            for match in reversed(matches):
                try:
                    parsed = json.loads(match)
                    logger.info(f"[INFO] JSONパース成功（正規抽出）: {parsed}")  # JSON parse succeeded (regex extraction)
                    return parsed
                except json.JSONDecodeError as e:
                    logger.warning(f"[WARN] 抽出JSONパース失敗: {e}")  # Extracted JSON parse failed
        else:
            logger.warning("[WARN] 正規表現によるJSON候補抽出に失敗")  # Failed to extract JSON candidate by regex

    except Exception as e:
        logger.error(f"❌ 構造データ抽出中に例外発生: {e}")  # Exception occurred during structure data extraction

    logger.info("📭 JSON抽出に失敗。Noneを返します。")  # JSON extraction failed, returning None
    return None

# 抽出済みの感情構造データ（JSON）を MongoDB Atlas の emotion_db.emotion_data に保存する。
# Save the extracted emotion structure data (JSON) to MongoDB Atlas emotion_db.emotion_data.
def write_structured_emotion_data(data: dict):
    try:
        client = get_mongo_client()
        if client is None:
            logger.error("❌ MongoDBクライアント取得に失敗")  # Failed to obtain MongoDB client
            return

        db = client["emotion_db"]
        collection = db["emotion_data"]

        # 主感情を英語に変換
        # Convert main emotion to English
        main_emotion_ja = data.get("主感情", "")
        main_emotion_en = emotion_map_reverse.get(main_emotion_ja)
        if not main_emotion_en:
            logger.warning(f"⚠ 主感情が未定義または翻訳不可: {main_emotion_ja}")  # Main emotion undefined or not translatable
            return

        # 重みに応じてカテゴリを決定
        # Determine category based on weight
        weight = int(data.get("重み", 0))
        if weight >= 95:
            category = "long"
        elif weight >= 80:
            category = "intermediate"
        else:
            category = "short"

        # 保存形式整形
        # Format for saving
        document = {
            "emotion": main_emotion_en,
            "category": category,
            "data": data.copy(),
            "履歴": [data.copy()]  # History
        }

        # MongoDBへ保存（新規挿入）
        # Save to MongoDB (insert)
        result = collection.insert_one(document)
        logger.info(f"✅ MongoDB保存成功: _id={result.inserted_id}, 感情={main_emotion_en}, カテゴリ={category}")  # MongoDB save successful
        
        # 🔄 インデックスにも同時保存
        # Also save to index simultaneously
        if "date" in data:
            save_index_data(
                data=data,
                emotion_en=main_emotion_en,
                category=category
            )
        else:
            logger.warning("⚠ dateが存在しないためインデックス保存スキップ")  # Skipped index saving because date is missing

    except Exception as e:
        logger.error(f"❌ 感情構造データ保存失敗: {e}")  # Failed to save emotion structure data
