# module/emotion/emotion_stats.py
import os
import json
from datetime import datetime

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client
from module.params import emotion_map, emotion_map_reverse

# 🔸 構成比を32感情に正規化（日本語キー順）
# 🔸 Normalize composition ratio into 32 emotions (Japanese key order)
def normalize_composition_vector(raw_composition: dict) -> dict:
    return {emotion: raw_composition.get(emotion, 0) for emotion in emotion_map_reverse.keys()}

# 現在感情：読み込み
# Load current emotion
def load_current_emotion():
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            collection = db["current_emotion"]
            latest = collection.find_one(sort=[("timestamp", -1)])
            return latest["emotion_vector"] if latest else {}
    except Exception as e:
        logger.error(f"[ERROR] 現在感情の読み込みに失敗: {e}")  # Failed to load current emotion
        return {}

# 感情ベクトル合成処理
# Emotion vector merging process
def merge_emotion_vectors(
    current: dict,
    new: dict,
    weight_new: float = 0.3,
    decay_factor: float = 0.9,
    normalize: bool = True
) -> dict:
    """
    既存の感情ベクトル `current` と、新しい感情ベクトル `new` を重み付きで合成する。
    数値型以外の値が含まれていた場合は無視される。

    Parameters:
        current (dict): 現在の感情ベクトル
        new (dict): 新しい感情ベクトル
        weight_new (float): 新ベクトルに対する重み（0.0〜1.0）
        decay_factor (float): 非更新値の減衰率（0.0〜1.0）
        normalize (bool): 合計100になるよう正規化するか

    Returns:
        dict: 合成後の感情ベクトル
    """
    combined = {}
    all_keys = set(current.keys()) | set(new.keys())

    for key in all_keys:
        old_val = current.get(key, 0)
        new_val = new.get(key, 0)

        # 型安全：数値以外を除外
        try:
            old_val = float(old_val)
            new_val = float(new_val)
        except (ValueError, TypeError):
            logger.warning(f"[WARN] 非数値型の感情値が検出されました: key={key}, old_val={old_val}, new_val={new_val} → スキップ")
            continue

        if key in new:
            merged = (1 - weight_new) * old_val + weight_new * new_val
        else:
            merged = old_val * decay_factor

        combined[key] = merged

    # 正規化（合計100に丸める）
    if normalize:
        total = sum(combined.values())
        if total > 0:
            combined = {k: round((v / total) * 100, 2) for k, v in combined.items()}

    return combined


# 現在感情：保存
# Save current emotion
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
            logger.info("[INFO] 現在感情をMongoDBに保存しました")  # Current emotion saved to MongoDB
    except Exception as e:
        logger.error(f"[ERROR] 現在感情の保存に失敗: {e}")  # Failed to save current emotion

# 32感情ベクトル → 6感情要約
# 32-emotion vector → 6-emotion summary
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

    logger.info("【6感情サマリー】")  # 6-emotion summary
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return summary
