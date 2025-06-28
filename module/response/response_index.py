import json
import os
import re
from utils import logger  # 共通ロガーをインポート

def load_index():
    with open("index/emotion_index.jsonl", "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def is_similar_composition(current, target):
    # 感情構成比のキーが完全一致しているか
    if set(current.keys()) != set(target.keys()):
        return False
    # 各構成比の乖離が15%以内か
    for key in current:
        if abs(current[key] - target[key]) > 15:
            return False
    return True

def search_similar_emotions(now_emotion: dict) -> dict:
    main_emotion = now_emotion["主感情"]
    logger.info(f"[検索] 主感情一致かつ構成比類似の候補を抽出中... 現在の主感情: {main_emotion}")
    current_composition = now_emotion["構成比"]

    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}

    for item in all_index:
        if item["主感情"] != main_emotion:
            continue
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
