import json
from utils import logger  # 共通ロガーをインポート
from module.mongo.mongo_client import get_mongo_client
from bson import ObjectId

def get_all_long_category_data():
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")

        db = client["emotion_db"]
        collection = db["emotion_data"]

        # 🔍 category: "long" のみを抽出
        long_data = list(collection.find({"category": "long"}))
        logger.info(f"✅ longカテゴリのデータ件数: {len(long_data)}")
        return long_data

    except Exception as e:
        logger.error(f"[ERROR] longカテゴリデータの取得失敗: {e}")
        return []

def extract_long_summary(best_match: dict) -> dict:
    """
    best_match から long カテゴリに該当する場合に必要な情報を抽出する。
    """
    if not best_match or best_match.get("category") != "long":
        return {}

    return {
        "date": best_match.get("date"),
        "emotion": best_match.get("emotion"),
        "category": best_match.get("category")
    }







def load_emotion_by_date(path: str, target_date: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, list):
                for entry in data:
                    if entry.get("date") == target_date:
                        return entry

            elif isinstance(data, dict) and "履歴" in data:
                for entry in data["履歴"]:
                    if entry.get("date") == target_date:
                        return entry

    except Exception as e:
        logger.warning(f"[WARN] データ取得失敗: {path} ({e})")
    return None

def compute_composition_difference(comp1, comp2):
    keys = set(k for k in comp1.keys() | comp2.keys())
    diff_sum = sum(abs(comp1.get(k, 0) - comp2.get(k, 0)) for k in keys)
    return diff_sum

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

        if matched_keywords:
            results.append({
                "emotion": target_emotion,
                "matched_keywords": matched_keywords,
                "match_score": diff_score,
                "match_category": "long",
                "保存先": path,
                "date": date
            })

    results.sort(key=lambda x: x["match_score"])
    return results[:3]

