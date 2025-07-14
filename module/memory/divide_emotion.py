import os
import json
from pymongo import MongoClient
import certifi
from utils import logger  # ロガーのインポート

# 日本語感情名 → 英語ファイル名の対応辞書
EMOTION_MAP = {
    "喜び": "Joy", "期待": "Anticipation", "怒り": "Anger", "嫌悪": "Disgust", "悲しみ": "Sadness",
    "驚き": "Surprise", "恐れ": "Fear", "信頼": "Trust", "楽観": "Optimism", "誇り": "Pride",
    "病的状態": "Morbidness", "積極性": "Aggressiveness", "冷笑": "Cynicism", "悲観": "Pessimism",
    "軽蔑": "Contempt", "羨望": "Envy", "憤慨": "Outrage", "自責": "Remorse", "不信": "Unbelief",
    "恥": "Shame", "失望": "Disappointment", "絶望": "Despair", "感傷": "Sentimentality", "畏敬": "Awe",
    "好奇心": "Curiosity", "歓喜": "Delight", "服従": "Submission", "罪悪感": "Guilt", "不安": "Anxiety",
    "愛": "Love", "希望": "Hope", "優位": "Dominance"
}

# 感情の重みによる保存カテゴリ分類
def get_memory_category(weight):
    if weight >= 95:
        return "long"
    elif weight >= 80:
        return "intermediate"
    else:
        return "short"

# 感情データをMongoDBに保存
def divide_and_store(emotion_data: dict) -> str:
    print("📥 [STEP] divide_and_store 開始")
    try:
        weight = emotion_data.get("重み", 0)
        category = get_memory_category(weight)
        main_emotion = emotion_data.get("主感情", "")
        english_emotion = EMOTION_MAP.get(main_emotion)

        print(f"🔍 重み: {weight}, カテゴリ: {category}")
        print(f"🔠 主感情: {main_emotion} → 英語: {english_emotion}")

        if not english_emotion:
            raise ValueError(f"主感情 '{main_emotion}' に対応する英語名が見つかりません")

        uri = "mongodb+srv://noriyukikondo99:Aa1192296%21@cluster0.oe0tni1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(uri, tlsCAFile=certifi.where())
        db = client["emotion_db"]
        collection = db["emotion_data"]

        print("📡 MongoDBへ接続完了 → データ検索開始...")
        existing = collection.find_one({"emotion": english_emotion, "category": category})

        if existing:
            print("📄 既存データに追記")
            collection.update_one(
                {"_id": existing["_id"]},
                {"$push": {"data.履歴": emotion_data}}
            )
            logger.info(f"[UPDATE] MongoDBに既存データ追記: {english_emotion} ({category})")
        else:
            print("🆕 新規データとして登録")
            doc = {
                "emotion": english_emotion,
                "category": category,
                "data": {
                    "履歴": [emotion_data]
                }
            }
            collection.insert_one(doc)
            logger.info(f"[INSERT] MongoDBに新規データ追加: {english_emotion} ({category})")

        print(f"✅ [SUCCESS] 感情データの保存完了: mongo/{category}/{english_emotion}")
        return f"mongo/{category}/{english_emotion}"

    except Exception as e:
        logger.error(f"[ERROR] divide_and_store失敗: {e}")
        print(f"❌ [ERROR] divide_and_store失敗: {e}")
        raise

