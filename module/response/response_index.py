import json
import os
import re
from utils import logger  # 共通ロガーをインポート

def load_index():
    with open("index/emotion_index.jsonl", "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def load_and_categorize_index():
    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}

    for item in all_index:
        path = os.path.normpath(item.get("保存先", ""))
        parts = re.split(r"[\\/]", path)
        category = parts[-2] if len(parts) >= 2 else "unknown"

        if category in categorized:
            categorized[category].append(item)

    return categorized

def compute_composition_difference(comp1, comp2):
    keys = set(k for k in comp1.keys() | comp2.keys())
    return sum(abs(comp1.get(k, 0) - comp2.get(k, 0)) for k in keys)

def filter_by_keywords(index_data, input_keywords):
    return [item for item in index_data if set(item.get("キーワード", [])) & set(input_keywords)]

def find_best_match_by_composition(current_composition, candidates):
    scored = []
    for item in candidates:
        diff = compute_composition_difference(current_composition, item.get("構成比", {}))
        scored.append((diff, item))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0])
    return scored[0][1]

def extract_best_reference(current_emotion, index_data, category):
    input_keywords = current_emotion.get("keywords", [])
    print(f"[DEBUG] [{category}] 入力キーワード: {input_keywords}")
    
    matched = filter_by_keywords(index_data, input_keywords)
    print(f"[DEBUG] [{category}] キーワード一致件数: {len(matched)}")

    if not matched:
        print(f"🟨 {category}カテゴリ: キーワード一致なし → スキップ")
        return None

    best_match = find_best_match_by_composition(current_emotion.get("構成比", {}), matched)
    print(f"[DEBUG] [{category}] 最も近い構成比のデータ: {best_match}")

    if best_match:
        print(f"✅ {category}カテゴリ: キーワード一致あり → 最も近い構成比の1件を採用")
        return {
            "emotion": best_match,
            "source": f"{category}-match",
            "match_info": f"キーワード一致（{', '.join(input_keywords)}）"
        }

    print(f"🟥 {category}カテゴリ: キーワード一致ありだが構成比マッチなし")
    return None
