import json
import os
import re
from pymongo import MongoClient
import certifi
from utils import logger  # 共通ロガーをインポート
from bson import ObjectId

# MongoDB から index データを取得
def load_index():
    print("\U0001F4E5 [STEP] MongoDBからemotion_indexを取得します...")
    try:
        uri = "mongodb+srv://noriyukikondo99:Aa1192296%21@cluster0.oe0tni1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(uri, tlsCAFile=certifi.where())
        db = client["emotion_db"]
        collection = db["emotion_index"]
        data = list(collection.find({}))
        print(f"✅ [SUCCESS] emotion_index データ件数: {len(data)}")
        return data
    except Exception as e:
        print(f"❌ [ERROR] MongoDBからの取得に失敗: {e}")
        return []

# インデックスをカテゴリに分類
def load_and_categorize_index():
    print("\U0001F4C2 [STEP] インデックスをカテゴリごとに分類します...")
    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}

    for item in all_index:
        category = item.get("category", "unknown")
        if category in categorized:
            categorized[category].append(item)

    for cat, items in categorized.items():
        print(f"\U0001F4CA {cat}カテゴリ: {len(items)} 件")

    return categorized

# 感情構成比の差異スコア（低いほど似ている）
def compute_composition_difference(comp1, comp2):
    keys = set(k for k in comp1.keys() | comp2.keys())
    return sum(abs(comp1.get(k, 0) - comp2.get(k, 0)) for k in keys)

# キーワード一致でフィルタ
def filter_by_keywords(index_data, input_keywords):
    print(f"\U0001F50D キーワードフィルタ適用: {input_keywords}")
    filtered = [item for item in index_data if set(item.get("キーワード", [])) & set(input_keywords)]
    print(f"\U0001F3AF 一致件数: {len(filtered)}")
    return filtered

# 類似スコアを計算
def calculate_composition_score(base_comp: dict, target_comp: dict) -> float:
    score = 0.0
    for key in base_comp:
        if key in target_comp:
            diff = abs(base_comp[key] - target_comp[key])
            score += max(0, 100 - diff)
    return score

# 構成比で最も近いデータを選出
def find_best_match_by_composition(current_composition, candidates):
    print(f"\U0001F50E 構成比マッチング対象数: {len(candidates)}")

    def is_valid_candidate(candidate_comp, base_comp):
        # ノイズ除去（5以下は無視）
        base_filtered = {k: v for k, v in base_comp.items() if v > 5}
        cand_filtered = {k: v for k, v in candidate_comp.items() if v > 5}

        base_keys = list(base_filtered.keys())
        shared_keys = set(base_filtered.keys()) & set(cand_filtered.keys())
        required_match = max(len(base_keys) - 1, 1)
        matched = 0

        for key in shared_keys:
            diff = abs(base_filtered.get(key, 0) - cand_filtered.get(key, 0))
            if diff <= 30:
                matched += 1

        return matched >= required_match

    valid_candidates = [
        c for c in candidates if is_valid_candidate(c["構成比"], current_composition)
    ]

    print(f"✅ 有効な候補数: {len(valid_candidates)}")
    if not valid_candidates:
        print("❌ 構成比マッチ候補なし")
        return None

    best = max(valid_candidates, key=lambda c: calculate_composition_score(current_composition, c["構成比"]))
    print("\U0001F3C5 最も構成比が近い候補を選出")
    return best

# 最適な参照データを抽出
def extract_best_reference(current_emotion, index_data, category):
    print(f"\n============================")
    print(f"\U0001F4D8 [カテゴリ: {category}] 参照候補の抽出開始")

    input_keywords = current_emotion.get("keywords", [])
    matched = filter_by_keywords(index_data, input_keywords)

    if not matched:
        print(f"\U0001F7E8 {category}カテゴリ: キーワード一致なし → スキップ")
        return None

    best_match = find_best_match_by_composition(current_emotion.get("構成比", {}), matched)

    if best_match:
        print(f"✅ {category}カテゴリ: ベストマッチが見つかりました")
        result = {
            "emotion": best_match,
            "source": f"{category}-match",
            "match_info": f"キーワード一致（{', '.join(input_keywords)}）",
            "保存先": best_match.get("保存先"),
            "date": best_match.get("date")
        }

        # ObjectIdを文字列に変換してから表示
        def convert_objectid(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        print(f"[DEBUG] extract_best_reference() の返却データ: {json.dumps(result, default=convert_objectid, ensure_ascii=False, indent=2)}")
        return result

    print(f"\U0001F7E5 {category}カテゴリ: 一致はあるが構成比が合致しない")
    return None
