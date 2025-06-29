import json
from utils import logger  # 共通ロガーをインポート

def load_emotion_by_date(path: str, target_date: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "履歴" in data:
                for entry in data["履歴"]:
                    if entry.get("date") == target_date:
                        return entry
    except Exception as e:
        logger.warning(f"[WARN] データ取得失敗: {path} ({e})")
    return None

def compute_composition_difference(comp1, comp2):
    keys = set(k for k in comp1.keys() | comp2.keys())
    return sum(abs(comp1.get(k, 0) - comp2.get(k, 0)) for k in keys)

def match_long_keywords(now_emotion: dict, index_data: list) -> list:
    logger.info(f"[構成比一致度優先] longカテゴリ: {len(index_data)}件をスコアリング中...")
    results = []

    current_composition = now_emotion.get("構成比", {})
    input_keywords = set(now_emotion.get("keywords", []))

    for item in index_data:
        path = item.get("保存先")
        date = item.get("date")
        target_emotion = load_emotion_by_date(path, date)
        if not target_emotion:
            continue

        target_composition = target_emotion.get("構成比", {})
        diff_score = compute_composition_difference(current_composition, target_composition)

        target_keywords = set(target_emotion.get("keywords", []))
        matched_keywords = list(input_keywords & target_keywords)

        results.append({
            "emotion": target_emotion,
            "matched_keywords": matched_keywords,
            "match_score": diff_score,
            "match_category": "long"
        })

    # 差分スコアが小さい順にソート
    results.sort(key=lambda x: x["match_score"])
    return results[:3]

