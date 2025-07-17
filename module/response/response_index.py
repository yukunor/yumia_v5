import json
import os
import re
from utils import logger, get_mongo_client
from bson import ObjectId

def load_index():
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")
        db = client["emotion_db"]
        collection = db["emotion_index"]
        data = list(collection.find({}))
        logger.info(f"[LOAD] emotion_index 読み込み完了: {len(data)} 件")
        return data
    except Exception as e:
        logger.error(f"[ERROR] MongoDBからのemotion_index取得失敗: {e}")
        return []

def load_and_categorize_index():
    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}
    for item in all_index:
        category = item.get("category", "unknown")
        if category in categorized:
            categorized[category].append(item)
    for cat, items in categorized.items():
        logger.info(f"[INFO] {cat}カテゴリ: {len(items)} 件")
    return categorized

def compute_composition_difference(comp1, comp2):
    keys = set(k for k in comp1.keys() | comp2.keys())
    return sum(abs(comp1.get(k, 0) - comp2.get(k, 0)) for k in keys)

def filter_by_keywords(index_data, input_keywords):
    filtered = [item for item in index_data if set(item.get("キーワード", [])) & set(input_keywords)]
    logger.info(f"[FILTER] キーワード一致: {len(filtered)} 件")
    return filtered

def calculate_composition_score(base_comp: dict, target_comp: dict) -> float:
    score = 0.0
    for key in base_comp:
        if key in target_comp:
            diff = abs(base_comp[key] - target_comp[key])
            score += max(0, 100 - diff)
    return score

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
    logger.info(f"[MATCH] 構成比マッチ候補数: {len(valid_candidates)}")

    if not valid_candidates:
        logger.warning("[WARN] 構成比マッチ候補なし")
        return None

    best = max(valid_candidates, key=lambda c: calculate_composition_score(current_composition, c["構成比"]))
    logger.info("[SELECT] 最も構成比が近い候補を選出")
    return best

def extract_best_reference(current_emotion, index_data, category):
    logger.info(f"[START] カテゴリ {category} の参照候補を抽出")
    input_keywords = current_emotion.get("keywords", [])
    matched = filter_by_keywords(index_data, input_keywords)

    if not matched:
        logger.info(f"[SKIP] {category}カテゴリ: キーワード一致なし")
        return None

    best_match = find_best_match_by_composition(current_emotion.get("構成比", {}), matched)

    if best_match:
        save_path = best_match.get("保存先", f"mongo/{category}/{best_match.get('emotion', 'Unknown')}")
        result = {
            "emotion": best_match,
            "source": f"{category}-match",
            "match_info": f"キーワード一致（{', '.join(input_keywords)}）",
            "保存先": save_path,
            "date": best_match.get("date")
        }

        def convert_objectid(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        logger.debug("[RESULT] extract_best_reference の返却データ:\n" + json.dumps(result, default=convert_objectid, ensure_ascii=False, indent=2))
        return result

    logger.info(f"[NOTE] {category}カテゴリ: 一致はあるが構成比が合致しない")
    return None
