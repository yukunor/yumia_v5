import json
from utils import logger  # 共通ロガーをインポート

def load_emotion_from_path(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def compute_composition_difference(comp1, comp2):
    keys = set(k for k in comp1.keys() | comp2.keys())
    return sum(abs(comp1.get(k, 0) - comp2.get(k, 0)) for k in keys)

def match_intermediate_keywords(now_emotion: dict, index_data: list) -> list:
    logger.info(f"[構成比一致度優先] intermediateカテゴリ: {len(index_data)}件をスコアリング中...")
    results = []

    current_composition = now_emotion.get("構成比", {})

    for item in index_data:
        path = item.get("保存先")
        data = load_emotion_from_path(path)
        if not data:
            continue

        target_composition = data.get("構成比", {})
        diff_score = compute_composition_difference(current_composition, target_composition)
        results.append((diff_score, data))

    # 差分スコアが小さい順にソート
    results.sort(key=lambda x: x[0])
    return [data for _, data in results[:3]]

