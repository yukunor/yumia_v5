#module/responce/main_responce.py
from llm_client import generate_emotion_from_prompt_simple as estimate_emotion, generate_emotion_from_prompt_with_context, extract_emotion_summary
from response.response_index import load_and_categorize_index, extract_best_reference, find_best_match_by_composition
from utils import logger, get_mongo_client, load_current_emotion, save_current_emotion, merge_emotion_vectors
from module.memory.main_memory import handle_emotion, save_emotion_sample, append_emotion_history, pad_emotion_vector
from module.memory.emotion_stats import synthesize_current_emotion
import json
import os
from bson import ObjectId
from utils import summarize_feeling


from module.response.response_long import find_history_by_emotion_and_date as find_long
from module.response.response_short import find_history_by_emotion_and_date as find_short
from module.response.response_intermediate import find_history_by_emotion_and_date as find_intermediate
from module.mongo.mongo_client import get_mongo_client  # 新たな統一モジュールを使用

client = get_mongo_client()
if client is None:
    raise ConnectionError("[ERROR] MongoDBクライアントの取得に失敗しました")
db = client["emotion_db"]

def get_mongo_collection(category, emotion_label):
    try:
        client = get_mongo_client()
        if client is None:
            raise ConnectionError("MongoDBクライアントの取得に失敗しました")

        db = client["emotion_db"]
        collection_name = f"{category}_{emotion_label}"
        return db[collection_name]
    except Exception as e:
        logger.error(f"[ERROR] MongoDBコレクション取得失敗: {e}")
        return None

def find_response_by_emotion(emotion_structure: dict) -> dict:　#LLMの初期応答で取得したキーワードと感情構成比、各responceで処理
    composition = emotion_structure.get("構成比", {})
    keywords = emotion_structure.get("keywords", [])

def collect_all_category_responses(emotion_name: str, date_str: str) -> dict:
    """
    各カテゴリ（short → intermediate → long）から指定された感情名と日付に一致する履歴を取得する。
    """
    short_data = find_short(emotion_name, "short", date_str)
    intermediate_data = find_intermediate(emotion_name, "intermediate", date_str)
    long_data = find_long(emotion_name, "long", date_str)

    return {
        "short": short_data,
        "intermediate": intermediate_data,
        "long": long_data
    }
