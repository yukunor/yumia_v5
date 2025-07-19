import os
from datetime import datetime
import logging
from dotenv import load_dotenv
import certifi
import json
import openai

# Renderの環境変数からOpenAIのAPIキーを取得
openai.api_key = os.getenv("OPENAI_API_KEY")

# ロガー
logger = logging.getLogger("yumia_logger")
if not logger.hasHandlers():
    handler = logging.FileHandler("app.log", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


# 会話履歴：保存
def append_history(role, message):
    try:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "message": message
        }
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            collection = db["dialogue_history"]
            collection.insert_one(entry)
            logger.info(f"[INFO] 履歴をMongoDBに保存: {entry}")
    except Exception as e:
        logger.error(f"[ERROR] 履歴保存に失敗: {e}")

# 会話履歴：読み込み
def load_history(limit=100):
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            collection = db["dialogue_history"]
            entries = list(collection.find().sort("timestamp", -1).limit(limit))
            for entry in entries:
                if "_id" in entry:
                    entry["_id"] = str(entry["_id"])
            return list(reversed(entries))
    except Exception as e:
        logger.error(f"[ERROR] 履歴の読み込みに失敗: {e}")
        return []

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

# 感情ベクトルの合成（加重平均 + 減衰 + 正規化）
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

# プロンプト読み込み関連
def load_emotion_prompt():
    with open("emotion_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def load_dialogue_prompt():
    with open("dialogue_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

_cached_system_prompt = None

def load_system_prompt_cached():
    global _cached_system_prompt
    if _cached_system_prompt is None:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            _cached_system_prompt = f.read().strip()
    return _cached_system_prompt

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

    # ✅ 10点満点で換算し、四捨五入で整数化
    summary = {k: round((v / 100) * 10) for k, v in summary.items()}

    print("【6感情サマリー】")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return summary