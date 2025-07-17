import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from utils import logger, get_mongo_client

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

def get_memory_category(weight):
    if weight >= 95:
        return "long"
    elif weight >= 80:
        return "intermediate"
    else:
        return "short"

def normalize_emotion_vector(構成比: dict) -> dict:
    return {emotion:構成比.get(emotion, 0) for emotion in EMOTION_KEYS}

def update_emotion_index(emotion_data, memory_path):
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")

        db = client["emotion_db"]
        collection = db["emotion_index"]

        index_entry = {
            "date": emotion_data.get("date", datetime.now().strftime("%Y%m%d%H%M%S")),
            "主感情": emotion_data.get("主感情", "Unknown"),
            "構成比": normalize_emotion_vector(emotion_data.get("構成比", {})),
            "キーワード": emotion_data.get("keywords", []),
            "emotion": EMOTION_MAP.get(emotion_data.get("主感情"), "Unknown"),
            "category": get_memory_category(emotion_data.get("重み", 0)),
            "保存先": memory_path
        }

        collection.insert_one(index_entry)
        logger.info(f"[MongoDB] emotion_index に登録: {index_entry['date']}")
    except Exception as e:
        logger.error(f"[ERROR] MongoDB登録失敗: {e}")

def extract_personality_tendency() -> dict:
    emotion_counter = Counter()
    try:
        client = get_mongo_client()
        db = client["emotion_db"]
        collection_names = db.list_collection_names()
        long_collections = [name for name in collection_names if name.startswith("long_")]

        for col_name in long_collections:
            collection = db[col_name]
            docs = list(collection.find({}))

            for doc in docs:
                history_list = []
                if "履歴" in doc:
                    history_list = doc["履歴"]
                elif "data" in doc and "履歴" in doc["data"]:
                    history_list = doc["data"]["履歴"]

                for entry in history_list:
                    main_emotion = entry.get("主感情")
                    if main_emotion:
                        emotion_counter[main_emotion] += 1

        return dict(emotion_counter.most_common(4))

    except Exception as e:
        logger.error(f"[ERROR] 人格傾向データ抽出失敗: {e}")
        return {}

