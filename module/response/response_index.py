import json
import os
import re
from utils import logger  # 共通ロガーをインポート

def load_index():
    with open("index/emotion_index.jsonl", "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def is_similar_composition(current, target, max_diff=70):
    current_items = {k: v for k, v in current.items() if v > 0}
    target_items = {k: v for k, v in target.items() if v > 0}

    print("[DEBUG] 比較中: current_keys =", current_items)
    print("[DEBUG] 比較中: target_keys  =", target_items)

    if set(current_items.keys()) != set(target_items.keys()):
        print("[DEBUG] ❌ キー不一致")
        return False

    for key in current_items:
        cur_val = current_items[key]
        tgt_val = target_items.get(key, 0)

        print(f"[DEBUG] 🔍 {key}: 差 = {abs(cur_val - tgt_val)} <= {max_diff} ?")

        if abs(cur_val - tgt_val) > max_diff:
            print(f"[DEBUG] ❌ {key} が範囲外")
            return False

    print(f"[DEBUG] ✅ 構成比一致（±{max_diff}ポイント以内）")
    return True


def search_similar_emotions(now_emotion: dict) -> dict:
    logger.info(f"[検索] 構成比類似の候補を抽出中...")

    current_composition = now_emotion["構成比"]
    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}

    match_count = 0
    mismatch_count = 0

    for item in all_index:
        if not is_similar_composition(current_composition, item["構成比"]):
            mismatch_count += 1
            continue

        match_count += 1

        normalized_path = os.path.normpath(item["保存先"])
        parts = re.split(r"[\\/]", normalized_path)
        category = parts[-2] if len(parts) >= 2 else "unknown"
        print("[DEBUG] category:", category)

        if category in categorized and len(categorized[category]) < 10:
            categorized[category].append(item)

    print(f"📊 構成比一致: {match_count}件 / 不一致: {mismatch_count}件")
    print(f"📦 カテゴリ別: short={len(categorized['short'])}件, intermediate={len(categorized['intermediate'])}件, long={len(categorized['long'])}件")
    logger.info(f"[検索結果] long: {len(categorized['long'])}件, intermediate: {len(categorized['intermediate'])}件, short: {len(categorized['short'])}件")
    logger.info(f"[DEBUG] ✅ 一致: {match_count}件 / ❌ 不一致: {mismatch_count}件")

    return categorized
