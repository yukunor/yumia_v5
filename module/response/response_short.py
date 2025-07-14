import json
from utils import logger  # 共通ロガーをインポート

def load_emotion_by_date(path: str, target_date: str) -> dict | None:
    print(f"[DEBUG] load_emotion_by_date 呼び出し: path={path}, date={target_date}")  # ← 追加
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, list):
                for entry in data:
                    if entry.get("date") == target_date:
                        print(f"[DEBUG] マッチしたデータ（list形式）: {entry}")  # ← 追加
                        return entry

            elif isinstance(data, dict) and "履歴" in data:
                for entry in data["履歴"]:
                    if entry.get("date") == target_date:
                        print(f"[DEBUG] マッチしたデータ（履歴形式）: {entry}")  # ← 追加
                        return entry

    except Exception as e:
        logger.warning(f"[WARN] データ取得失敗: {path} ({e})")
    return None

def compute_composition_difference(comp1, comp2):
    keys = set(k for k in comp1.keys() | comp2.keys())
    diff_sum = sum(abs(comp1.get(k, 0) - comp2.get(k, 0)) for k in keys)
    print(f"[DEBUG] 構成比差分スコア: {diff_sum}")  # ← 追加
    return diff_sum

def match_short_keywords(now_emotion: dict, index_data: list) -> list:
    logger.info(f"[構成比一致度優先] shortカテゴリ: {len(index_data)}件をスコアリング中...")
    results = []

    current_composition = now_emotion.get("構成比", {})
    input_keywords = set(now_emotion.get("keywords", []))
    print(f"[DEBUG] 入力キーワード: {input_keywords}")  # ← 追加

    for item in index_data:
        path = item.get("保存先")
        date = item.get("date")
        target_emotion = load_emotion_by_date(path, date)
        if not target_emotion:
            print(f"[DEBUG] 感情データ読み込み失敗: {path}, date={date}")  # ← 追加
            continue

        target_composition = target_emotion.get("構成比", {})
        diff_score = compute_composition_difference(current_composition, target_composition)

        target_keywords = set(target_emotion.get("keywords", []))
        matched_keywords = list(input_keywords & target_keywords)

        print(f"[DEBUG] 比較対象キーワード: {target_keywords} → 一致: {matched_keywords}")  # ← 追加

        if matched_keywords:
            results.append({
                "emotion": target_emotion,
                "matched_keywords": matched_keywords,
                "match_score": diff_score,
                "match_category": "short",
                "保存先": path,
                "date": date
            })

    results.sort(key=lambda x: x["match_score"])
    print(f"[DEBUG] マッチ候補数（short）: {len(results)} 件")  # ← 追加
    return results[:3]

