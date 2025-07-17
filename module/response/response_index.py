import json
import os
import re
from utils import logger, get_mongo_client  # 共通ロガーとMongoDBクライアントをインポート
from bson import ObjectId

# MongoDB から index データを取得
def load_index():
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")
        db = client["emotion_db"]
        collection = db["emotion_index"]
        data = list(collection.find({}))
        return data
    except Exception as e:
        logger.error(f"MongoDBからの取得に失敗: {e}")
        return []

# インデックスをカテゴリに分類
def load_and_categorize_index():
    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}

    for item in all_index:
        category = item.get("category", "unknown")
        if category in categorized:
            categorized[category].append(item)

    return categorized

# 感情構成比の差異スコア（低いほど似ている）
def compute_composition_difference(comp1, comp2):
    keys = set(k for k in comp1.keys() | comp2.keys())
    return sum(abs(comp1.get(k, 0) - comp2.get(k, 0)) for k in keys)

# キーワード一致でフィルタ
def filter_by_keywords(index_data, input_keywords):
    filtered = [item for item in index_data if set(item.get("キーワード", [])) & set(input_keywords)]
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
    def is_valid_candidate(candidate_comp, base_comp):
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

    if not valid_candidates:
        return None

    best = max(valid_candidates, key=lambda c: calculate_composition_score(current_composition, c["構成比"]))
    return best

# 最適な参照データを抽出
def extract_best_reference(current_emotion, index_data, category):
    print("============================")
    print(f"\U0001F4D8 [カテゴリ: {category}] 参照候補の抽出開始")

    input_keywords = current_emotion.get("keywords", [])
    matched = filter_by_keywords(index_data, input_keywords)
    print(f"\U0001F50D キーワードフィルタ適用: {input_keywords}")
    print(f"\U0001F3AF 一致件数: {len(matched)}")

    if not matched:
        print(f"🟨 {category}カテゴリ: キーワード一致なし → スキップ")
        print("============================")
        return None

    best_match = find_best_match_by_composition(current_emotion.get("構成比", {}), matched)
    print(f"\U0001F50E 構成比マッチング対象数: {len(matched)}")
    print(f"✅ 有効な候補数: {len([m for m in matched if m == best_match]) if best_match else 0}")

    if best_match:
        print(f"✅ {category}カテゴリ: ベストマッチが見つかりました")
        print("============================")

        save_path = best_match.get("保存先")
        if not save_path:
            save_path = f"mongo/{category}/{best_match.get('emotion', 'Unknown')}"

        result = {
            "emotion": best_match,
            "source": f"{category}-match",
            "match_info": f"キーワード一致（{', '.join(input_keywords)}）",
            "保存先": save_path,
            "date": best_match.get("date")
        }

        return result

    print(f"🟥 {category}カテゴリ: 一致はあるが構成比が合致しない")
    print("============================")
    return None
