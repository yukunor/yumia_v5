import os
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from utils import logger  # ロガーのインポート

# 環境変数読み込み
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["emotion_db"]
collection = db["emotion_data"]
history_collection = db["emotion_history"]
dataset_collection = db["emotion_dataset"]

# 全32感情リスト
ALL_EMOTIONS = [
    "喜び", "期待", "怒り", "嫌悪", "悲しみ", "驚き", "恐れ", "信頼", "楽観", "誇り",
    "病的状態", "積極性", "冷笑", "悲観", "軽蔑", "羨望", "憤慨", "自責", "不信", "恥",
    "失望", "絶望", "感傷", "畏敬", "好奇心", "歓喜", "服従", "罪悪感", "不安", "愛", "希望", "優位"
]

# ベクトル補完関数
def pad_emotion_vector(vector):
    return {emotion: vector.get(emotion, 0) for emotion in ALL_EMOTIONS}

# 感情データ処理関数（MongoDBに保存）
def handle_emotion(emotion_data, user_input=None, response_text=None):
    try:
        padded_vector = pad_emotion_vector(emotion_data.get("構成比", {}))
        document = {
            "category": emotion_data.get("強度", "intermediate"),
            "emotion": emotion_data.get("主感情", ""),
            "data": {
                "構成比": padded_vector,
                "状況": emotion_data.get("状況", ""),
                "心理反応": emotion_data.get("心理反応", ""),
                "関係性変化": emotion_data.get("関係性変化", ""),
                "関連": emotion_data.get("関連", []),
                "keywords": emotion_data.get("keywords", []),
                "履歴": emotion_data.get("履歴", []),
                "データ種別": emotion_data.get("データ種別", "emotion"),
                "重み": emotion_data.get("重み", 50),
                "主感情": emotion_data.get("主感情", "")
            },
            "timestamp": datetime.utcnow()
        }
        collection.insert_one(document)
        logger.info("[INFO] 感情データをMongoDBに保存しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情データ保存に失敗しました: {e}")
        raise

# 感情データ記録関数（別コレクションに保存）
def save_emotion_sample(input_text, response_text, emotion_vector):
    padded_vector = pad_emotion_vector(emotion_vector)
    record = {
        "input": input_text,
        "response": response_text,
        "emotion_vector": padded_vector,
        "timestamp": datetime.utcnow()
    }
    try:
        dataset_collection.insert_one(record)
        logger.info("[INFO] emotion_dataset に感情サンプルを記録しました。")
        print("[✅] emotion_dataset に感情サンプルを記録しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情データの記録に失敗しました: {e}")
        print(f"[❌] 感情データの記録に失敗しました: {e}")

# 感情履歴保存関数（MongoDB履歴コレクションへ）
def append_emotion_history(emotion_data):
    try:
        padded_vector = pad_emotion_vector(emotion_data.get("構成比", {}))
        record = {
            "timestamp": datetime.utcnow(),
            "主感情": emotion_data.get("主感情", ""),
            "構成比": padded_vector
        }
        history_collection.insert_one(record)
        logger.info("[INFO] emotion_history に履歴を追加しました。")
        print("[✅] emotion_history に履歴を追加しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情履歴の保存に失敗しました: {e}")
        print(f"[❌] 感情履歴の保存に失敗しました: {e}")

