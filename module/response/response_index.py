#module/response/response_index.py
import json
import os
import re
from bson import ObjectId

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client
from module.llm.llm_client import generate_gpt_response_from_history


# 英語→日本語変換辞書
emotion_map = {
    "Joy": "喜び", "Anticipation": "期待", "Anger": "怒り", "Disgust": "嫌悪",
    "Sadness": "悲しみ", "Surprise": "驚き", "Fear": "恐れ", "Trust": "信頼",
    "Optimism": "楽観", "Pride": "誇り", "病的状態": "病的状態", "Aggressiveness": "積極性",
    "Cynicism": "冷笑", "Pessimism": "悲観", "Contempt": "軽蔑", "Envy": "羨望",
    "Outrage": "憤慨", "Guilt": "自責", "Unbelief": "不信", "Shame": "恥",
    "Disappointment": "失望", "Despair": "絶望", "Sentimentality": "感傷", "Awe": "畏敬",
    "Curiosity": "好奇心", "Delight": "歓喜", "服従": "服従", "Remorse": "罪悪感",
    "Anxiety": "不安", "Love": "愛", "Hope": "希望", "Dominance": "優位"
}

def search_index_response(composition: dict, keywords: list[str]) -> dict: #検索用の構成比とキーワードの受取
    composition = emotion_structure.get("構成比", {})
    keywords = emotion_structure.get("keywords", [])

def translate_emotion(emotion): #英語の感情名を日本語に変換
    return emotion_map.get(emotion, emotion)

def normalize_composition_vector(partial_composition: dict) -> dict: 
    """
    受け取った構成比（部分的）を emotion_map 順に整形（不足は0で埋める）
    """
    return {jp_emotion: partial_composition.get(jp_emotion, 0) for jp_emotion in emotion_map.values()}

def load_index():
    print("📥 [STEP] MongoDBからemotion_indexを取得します...")
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")
        db = client["emotion_db"]
        collection = db["emotion_index"]
        data = list(collection.find({}))
        print(f"✅ [SUCCESS] emotion_index データ件数: {len(data)}")
        return data
    except Exception as e:
        print(f"❌ [ERROR] MongoDBからの取得に失敗: {e}")
        return []

def load_and_categorize_index(): #取得したemotion_db.emotion_indexをcategoryごとに分類分け
    print("📂 [STEP] インデックスをカテゴリごとに分類します...")
    all_index = load_index()
    categorized = {"long": [], "intermediate": [], "short": []}

    for item in all_index:
        category = item.get("category", "unknown")
        if category in categorized:
            categorized[category].append(item)

    for cat, items in categorized.items():
        print(f"📊 {cat}カテゴリ: {len(items)} 件")

    return categorized

def filter_by_keywords(index_data, input_keywords): #カテゴライズした辞書形式のemotion_indexからキーワード検索を実施
    print(f"🔍 キーワードフィルタ適用: {input_keywords}")
    filtered = [item for item in index_data if set(item.get("キーワード", [])) & set(input_keywords)]
    print(f"🎯 一致件数: {len(filtered)}")
    return filtered

def find_best_match_by_composition(current_composition, candidates):
    print(f"🔎 構成比マッチング対象数: {len(candidates)}")
    print(f"[DEBUG] current_composition type: {type(current_composition)}")
    print(f"[DEBUG] current_composition value: {current_composition}")

    # 🔸 スコア計算関数を内包定義
    def calculate_composition_score(base: dict, target: dict) -> float:
        shared_keys = set(base.keys()) & set(target.keys())
        score = 0.0
        for key in shared_keys:
            diff = abs(base.get(key, 0) - target.get(key, 0))
            score += (100 - diff)
        return score / len(shared_keys) if shared_keys else 0.0

    # 🔸 候補の適格性判定
    def is_valid_candidate(candidate_comp, base_comp):
        print(f"[DEBUG] candidate_comp type: {type(candidate_comp)} / base_comp type: {type(base_comp)}")
        print(f"[DEBUG] candidate_comp: {candidate_comp}")
        print(f"[DEBUG] base_comp: {base_comp}")

        try:
            base_filtered = {k: v for k, v in base_comp.items() if v > 5}
            cand_filtered = {k: v for k, v in candidate_comp.items() if v > 5}
        except AttributeError as e:
            print(f"[ERROR] .items() 呼び出し失敗: {e}")
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

    print(f"✅ 有効な候補数: {len(valid_candidates)}")
    if not valid_candidates:
        print("❌ 構成比マッチ候補なし")
        return None

    # 🔸 スコア最大の候補を選出
    best = max(valid_candidates, key=lambda c: calculate_composition_score(current_composition, c["構成比"]))

    # 🔸 翻訳（翻訳辞書が別にあればそちらに委譲しても可）
    jp_emotion = translate_emotion(best.get("emotion", "Unknown"))
    print(f"🏅 最も構成比が近い候補を選出: {jp_emotion}")

    return best
