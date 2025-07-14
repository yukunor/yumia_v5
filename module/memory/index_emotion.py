import os
import json
from datetime import datetime
from collections import Counter
from pymongo import MongoClient
from dotenv import load_dotenv
from utils import logger

# === 環境変数からMongoDB URIを取得 ===
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["emotion_db"]
index_collection = db["emotion_index"]
long_collection = db["emotion_data"]

# === EMOTION_MAPから日本語キーを抽出 ===
EMOTION_MAP = {
    "喜び": "Joy", "期待": "Anticipation", "怒り": "Anger", "嫌悪": "Disgust",
    "悲しみ": "Sadness", "驚き": "Surprise", "恐れ": "Fear", "信頼": "Trust",
    "楽観": "Optimism", "誇り": "Pride", "病的状態": "Morbidness", "積極性": "Aggressiveness",
    "冷笑": "Cynicism", "悲観": "Pessimism", "軽蔑": "Contempt", "羨望": "Envy",
    "憤慨": "Outrage", "自責": "Remorse", "不信": "Unbelief", "恥": "Shame",
    "失望": "Disappointment", "絶望": "Despair", "感傷": "Sentimentality", "畏敬": "Awe",
    "好奇心": "Curiosity", "歓喜": "Delight", "服従": "Submission", "罪悪感": "Guilt",
    "不安": "Anxiety", "愛": "Love", "希望": "Hope", "優位": "Dominance"
}
EMOTION_KEYS = list(EMOTION_MAP.keys())

# === 構成比の正規化 ===
def normalize_emotion_vector(構成比: dict) -> dict:
    return {emotion: 構成比.get(emotion, 0) for emotion in EMOTION_KEYS}

# === インデックスのMongoDB登録 ===
def update_emotion_index(emotion_data, memory_path):
    index_entry = {
        "date": emotion_data.get("date", datetime.now().strftime("%Y%m%d%H%M%S")),
        "主感情": emotion_data.get("主感情", "Unknown"),
        "構成比": normalize_emotion_vector(emotion_data.get("構成比", {})),
        "キーワード": emotion_data.get("keywords", []),
        "保存先": memory_path
    }

    try:
        index_collection.insert_one(index_entry)
        logger.info(f"[MongoDB] emotion_index に登録: {index_entry['date']}")
    except Exception as e:
        logger.error(f"[ERROR] MongoDBインデックス登録失敗: {e}")

# === 人格傾向抽出（MongoDB longデータ） ===
def extract_personality_tendency():
    emotion_counter = Counter()

    try:
        records = long_collection.find({"category": "long"})
        for doc in records:
            data = doc.get("data", {})
            if isinstance(data, dict):
                if data.get("データ種別") == "emotion":
                    if main := data.get("主感情"):
                        emotion_counter[main] += 1
                for item in data.get("履歴", []):
                    if hist_main := item.get("主感情"):
                        emotion_counter[hist_main] += 1
    except Exception as e:
        logger.warning(f"[WARN] 人格傾向データ取得失敗: {e}")

    print("📊 現在の人格傾向（long保存データの主感情カウント）:")
    for emotion, count in emotion_counter.most_common():
        print(f"  - {emotion}: {count}件")

    return dict(emotion_counter.most_common(4))

# === 単体実行用テストコード ===
if __name__ == "__main__":
    sample_data = {
        "主感情": "喜び",
        "構成比": {
            "喜び": 50,
            "信頼": 30,
            "期待": 20
        },
        "重み": 85,
        "状況": "ユーザーがカジュアルな挨拶をして、親しみを込めた会話が始まった場面",
        "心理反応": "ユーザーとの親しいやり取りに喜びを感じつつ、これからの対話にも期待を持った",
        "関係性変化": "親しみを感じるやり取りを通じて、ユーザーとの信頼関係が深まった",
        "関連": ["挨拶", "親しみ", "信頼"],
        "keywords": ["やほー", "親しみ", "会話開始"]
    }

    update_emotion_index(sample_data, "memory/emotion_20250617")
    extract_personality_tendency()

