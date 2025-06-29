import json
import os
import re
from utils import logger  # 共通ロガーをインポート

def load_index():
    with open("index/emotion_index.jsonl", "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def is_similar_composition(current, target):
    # 0を除外して感情成分だけを取り出す
    current_keys = {k for k, v in current.items() if v > 0}
    target_keys = {k for k, v in target.items() if v > 0}

    # 感情成分（非ゼロの感情）が完全一致しているか
    return current_keys == target_keys

def search_similar_emotions(now_emotion: dict) -> dict:
    logger.info(f"[検索] 構成比類似の候補を抽出中...")

    current_composition = now_emotion["構成比"]
    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}

    for item in all_index:
        if not is_similar_composition(current_composition, item["構成比"]):
            continue

        # スラッシュ・バックスラッシュ両方に対応して分割
        normalized_path = os.path.normpath(item["保存先"])
        parts = re.split(r"[\\/]", normalized_path)
        category = parts[1] if len(parts) > 1 else "unknown"

        if category in categorized and len(categorized[category]) < 10:
            categorized[category].append(item)

    logger.info(f"[検索結果] long: {len(categorized['long'])}件, intermediate: {len(categorized['intermediate'])}件, short: {len(categorized['short'])}件")

    return categorized
