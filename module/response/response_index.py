#module/response/response_index.py
import json
import os
import re
from bson import ObjectId

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client
from module.llm.llm_client import generate_gpt_response_from_history
from module.params import emotion_map

# 構成比とキーワードを受け取る検索インターフェース
# Search interface that receives composition and keywords
def search_index_response(composition: dict, keywords: list[str]) -> dict:
    composition = emotion_structure.get("構成比", {})
    # Extract composition ratio
    keywords = emotion_structure.get("keywords", [])
    # Extract keywords

# 英語の感情名を日本語に変換
# Convert emotion name from English to Japanese
def translate_emotion(emotion): 
    return emotion_map.get(emotion, emotion)

# 受け取った構成比（部分的）を emotion_map 順に整形（不足は0で埋める）
# Normalize partial composition vector in the order of emotion_map (fill missing with 0)
def normalize_composition_vector(partial_composition: dict) -> dict: 
    return {jp_emotion: partial_composition.get(jp_emotion, 0) for jp_emotion in emotion_map.values()}

# MongoDBからemotion_indexを取得
# Load emotion_index from MongoDB
def load_index():
    logger.debug("📥 [STEP] MongoDBからemotion_indexを取得します...")
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")
        # Failed to obtain MongoDB client
        db = client["emotion_db"]
        collection = db["emotion_index"]
        data = list(collection.find({}))
        logger.info(f"✅ [SUCCESS] emotion_index データ件数: {len(data)}")
        # Number of emotion_index records
        return data
    except Exception as e:
        logger.warning(f"❌ [ERROR] MongoDBからの取得に失敗: {e}")
        # Failed to retrieve from MongoDB
        return []

# 取得したemotion_indexをカテゴリごとに分類
# Categorize loaded emotion_index data by category
def load_and_categorize_index():
    logger.info("📂 [STEP] インデックスをカテゴリごとに分類します...")
    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}

    for item in all_index:
        category = item.get("category", "unknown")
        if category in categorized:
            categorized[category].append(item)

    for cat, items in categorized.items():
        logger.debug(f"📊 {cat}カテゴリ: {len(items)} 件")
        # Number of records per category

    return categorized

# キーワードフィルタリング処理
# Perform keyword filtering on categorized emotion_index
def filter_by_keywords(index_data, input_keywords):
    logger.info(f"🔍 キーワードフィルタ適用: {input_keywords}")
    filtered = [item for item in index_data if set(item.get("キーワード", [])) & set(input_keywords)]
    logger.info(f"🎯 一致件数: {len(filtered)}")
    return filtered

# 英語の感情名を日本語に変換（重複あり）
# Convert English emotion name to Japanese (duplicate)
def translate_emotion(emotion: str) -> str:
    return emotion_map.get(emotion, emotion)

# 構成比の一致スコアに基づき最も近い候補を選出
# Find best match based on similarity of emotion composition
def find_best_match_by_composition(current_composition, candidates):
    logger.info(f"🔎 構成比マッチング対象数: {len(candidates)}")
    logger.debug(f"[DEBUG] current_composition type: {type(current_composition)}")
    logger.debug(f"[DEBUG] current_composition value: {current_composition}")

    # 🔸 スコア計算関数
    # Score calculation function
    def calculate_composition_score(base: dict, target: dict) -> float:
        shared_keys = set(base.keys()) & set(target.keys())
        score = 0.0
        for key in shared_keys:
            diff = abs(base.get(key, 0) - target.get(key, 0))
            score += (100 - diff)
        return score / len(shared_keys) if shared_keys else 0.0

    # 🔸 候補の適格性判定
    # Validity check for candidate
    def is_valid_candidate(candidate_comp, base_comp):
        logger.debug(f"[DEBUG] candidate_comp type: {type(candidate_comp)} / base_comp type: {type(base_comp)}")
        logger.debug(f"[DEBUG] candidate_comp: {candidate_comp}")
        logger.debug(f"[DEBUG] base_comp: {base_comp}")

        try:
            base_filtered = {k: v for k, v in base_comp.items() if v > 5}
            cand_filtered = {k: v for k, v in candidate_comp.items() if v > 5}
        except AttributeError as e:
            logger.warning(f"[ERROR] .items() 呼び出し失敗: {e}")
            return False

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

    logger.info(f"✅ 有効な候補数: {len(valid_candidates)}")
    if not valid_candidates:
        logger.warning("❌ 構成比マッチ候補なし")
        return None

    # 🔸 最もスコアが高い候補を選出
    # Select candidate with highest similarity score
    best = max(valid_candidates, key=lambda c: calculate_composition_score(current_composition, c["構成比"]))

    # 🔸 結果の翻訳表示
    # Translate and log best match
    jp_emotion = translate_emotion(best.get("emotion", "Unknown"))
    logger.info(f"🏅 最も構成比が近い候補を選出: {jp_emotion}")

    return best

