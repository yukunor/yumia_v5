import os
import json
from datetime import datetime
from .divide_emotion import divide_and_store  # ✅ divide_and_store は index 保存しない設計に統一
from .index_emotion import update_emotion_index
from utils import logger, get_mongo_client

ALL_EMOTIONS = [
    "喜び", "期待", "怒り", "嫌悪", "悲しみ", "驚き", "恐れ", "信頼", "楽観", "誇り",
    "病的状態", "積極性", "冷笑", "悲観", "軽蔑", "羨望", "憤慨", "自責", "不信", "恥",
    "失望", "絶望", "感傷", "畏敬", "好奇心", "歓喜", "服従", "罪悪感", "不安", "愛", "希望", "優位"
]

# MongoDB 接続
try:
    client = get_mongo_client()
    if client is None:
        raise ConnectionError("[ERROR] MongoDBクライアントの取得に失敗しました")
    db = client["emotion_db"]
    collection_history = db["emotion_history"]
    collection_samples = db["emotion_samples"]
except Exception as e:
    logger.error(f"[ERROR] MongoDB接続失敗: {e}")
    raise

def pad_emotion_vector(vector):
    return {emotion: vector.get(emotion, 0) for emotion in ALL_EMOTIONS}

def handle_emotion(emotion_data, user_input=None, response_text=None):
    try:
        memory_path = divide_and_store(emotion_data)  # ✅ データ保存のみ行う
        update_emotion_index(emotion_data, memory_path)  # ✅ index 保存はここでのみ実行
        logger.info("[INFO] 感情データ処理が完了しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情データ処理中にエラー発生: {e}")
        raise

def save_emotion_sample(input_text, response_text, emotion_vector):
    try:
        padded_vector = pad_emotion_vector(emotion_vector)
        record = {
            "input": input_text,
            "response": response_text,
            "emotion_vector": padded_vector,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        collection_samples.insert_one(record)
        logger.info("[INFO] MongoDBに感情サンプルを記録しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情サンプルの記録に失敗しました: {e}")

def append_emotion_history(emotion_data):
    try:
        padded_vector = pad_emotion_vector(emotion_data.get("構成比", {}))
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "主感情": emotion_data.get("主感情", ""),
            "構成比": padded_vector
        }
        collection_history.insert_one(record)
        logger.info("[INFO] MongoDBに感情履歴を記録しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情履歴の保存に失敗しました: {e}")
