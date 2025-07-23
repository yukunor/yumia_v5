#module/emorion/emotion_stats.py
import os
import json
from datetime import datetime

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client  # ロガーとMongo関数のインポート
from module.llm.llm_client import generate_emotion_from_prompt_with_context

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

#GPTで感情構造を生成し、EMOTION_MAPに基づいた32感情の構成比ベクトルを返す。
def get_composition_vector(user_input: str, emotion_structure: dict, best_match: dict | None) -> dict:
    _, emotion_data = generate_emotion_from_prompt_with_context(user_input, emotion_structure, best_match)
    raw_composition = emotion_data.get("構成比", {})
    full_vector = {emotion: raw_composition.get(emotion, 0) for emotion in EMOTION_MAP.keys()}
    return full_vector


# 現在感情：読み込み
def load_current_emotion():
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            collection = db["current_emotion"]
            latest = collection.find_one(sort=[("timestamp", -1)])
            return latest["emotion_vector"] if latest else {}
    except Exception as e:
        logger.error(f"[ERROR] 現在感情の読み込みに失敗: {e}")
        return {}



# 感情ベクトル合成処理（あなたの既存関数）
def merge_emotion_vectors(
    current: dict,
    new: dict,
    weight_new: float = 0.3,
    decay_factor: float = 0.9,
    normalize: bool = True
) -> dict:
    combined = {}
    all_keys = set(current.keys()) | set(new.keys())
    for key in all_keys:
        old_val = current.get(key, 0)
        new_val = new.get(key, 0)
        if key in new:
            merged = (1 - weight_new) * old_val + weight_new * new_val
        else:
            merged = old_val * decay_factor
        combined[key] = merged

    if normalize:
        total = sum(combined.values())
        if total > 0:
            combined = {k: round((v / total) * 100, 2) for k, v in combined.items()}

    return combined

# 現在感情：保存
def save_current_emotion(emotion_vector):
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            collection = db["current_emotion"]
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "emotion_vector": emotion_vector
            }
            collection.insert_one(entry)
            logger.info("[INFO] 現在感情をMongoDBに保存しました")
    except Exception as e:
        logger.error(f"[ERROR] 現在感情の保存に失敗: {e}")



# 32感情ベクトル → 6感情要約
def summarize_feeling(feeling_vector: dict) -> dict:
    summary = {
        "喜び": sum(feeling_vector.get(e, 0) for e in ["歓喜", "希望", "信頼", "楽観", "愛"]) / 5,
        "怒り": sum(feeling_vector.get(e, 0) for e in ["憤慨", "軽蔑", "怒り"]) / 3,
        "悲しみ": sum(feeling_vector.get(e, 0) for e in ["絶望", "自責", "恥", "感傷"]) / 4,
        "楽しさ": sum(feeling_vector.get(e, 0) for e in ["好奇心", "期待", "喜び"]) / 3,
        "自信": sum(feeling_vector.get(e, 0) for e in ["優位", "誇り"]) / 2,
        "困惑": sum(feeling_vector.get(e, 0) for e in ["恐れ", "不信", "不安"]) / 3,
    }

    summary = {k: round((v / 100) * 10) for k, v in summary.items()}

    print("【6感情サマリー】")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return summary
