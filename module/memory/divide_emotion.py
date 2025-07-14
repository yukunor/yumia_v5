import os
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from utils import logger  # ロガーのインポート

# === 環境変数の読み込み ===
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["emotion_db"]
emotion_collection = db["emotion_data"]

# === 日本語感情名 → 英語ファイル名の対応辞書 ===
EMOTION_MAP = {
    "喜び": "Joy", "期待": "Anticipation", "怒り": "Anger", "嫌悪": "Disgust", "悲しみ": "Sadness",
    "驚き": "Surprise", "恐れ": "Fear", "信頼": "Trust", "楽観": "Optimism", "誇り": "Pride",
    "病的状態": "Morbidness", "積極性": "Aggressiveness", "冷笑": "Cynicism", "悲観": "Pessimism",
    "軽蔑": "Contempt", "羨望": "Envy", "憤慨": "Outrage", "自責": "Remorse", "不信": "Unbelief",
    "恥": "Shame", "失望": "Disappointment", "絶望": "Despair", "感傷": "Sentimentality",
    "畏敬": "Awe", "好奇心": "Curiosity", "歓喜": "Delight", "服従": "Submission",
    "罪悪感": "Guilt", "不安": "Anxiety", "愛": "Love", "希望": "Hope", "優位": "Dominance"
}

# === 感情の重みによる保存カテゴリの分類 ===
def get_memory_category(weight):
    if weight >= 95:
        return "long"
    elif weight >= 80:
        return "intermediate"
    else:
        return "short"

# === 感情データをMongoDBに保存する関数 ===
def divide_and_store(emotion_data: dict) -> str:
    try:
        weight = emotion_data.get("重み", 0)
        category = get_memory_category(weight)
        main_emotion = emotion_data.get("主感情", "")

        # ログ出力
        logger.debug(f"[DEBUG] カテゴリ: {category}")
        logger.debug(f"[DEBUG] 主感情: {main_emotion}")
        logger.debug(f"[DEBUG] 英語ファイル名: {EMOTION_MAP.get(main_emotion)}")

        # MongoDBに保存するための整形
        emotion_data["category"] = category
        emotion_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emotion_data["データ種別"] = "emotion"

        result = emotion_collection.insert_one({"data": emotion_data})
        logger.info(f"[MongoDB] 感情データ保存完了: {result.inserted_id}")
        return f"mongo_id:{result.inserted_id}"
    except Exception as e:
        logger.error(f"[ERROR] 感情データ保存失敗: {e}")
        return ""

