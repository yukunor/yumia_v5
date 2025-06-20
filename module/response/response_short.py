import json
from utils import logger  # 共通ロガーをインポート

def load_emotion_from_path(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def keyword_match_score(target_keywords, now_keywords):
    return sum(1 for word in target_keywords if word in now_keywords)

def match_short_keywords(now_emotion: dict, index_data: list) -> list:
    logger.info(f"[キーワード検索] shortカテゴリ: インデックス{len(index_data)}件中から一致をスコアリング中...")

    now_keywords = now_emotion.get("keywords", []) + now_emotion.get("関連", [])

    scored_data = []
    for item in index_data:
        path = item.get("保存先")
        data = load_emotion_from_path(path)
        if not data:
            continue

        target_keywords = data.get("keywords", []) + data.get("関連", [])
        score = keyword_match_score(target_keywords, now_keywords)

        scored_data.append((score, data))

    scored_data.sort(key=lambda x: x[0], reverse=True)
    if scored_data:
        logger.info(f"[一致結果] 最大一致スコア: {scored_data[0][0]}")
    else:
        logger.info("[一致結果] 一致スコアが0のため該当なし")

    return [data for score, data in scored_data[:3]]
