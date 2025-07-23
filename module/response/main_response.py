#module/responce/main_responce.py
import json
import os
from bson import ObjectId

from module.mongo.mongo_client import get_mongo_client
from module.llm.llm_client import generate_gpt_response_from_history
from module.response.response_short import find_short_history_by_emotion_and_date 
from module.response.response_intermediate import find_intermediate_history_by_emotion_and_date
from module.response.response_long import find_long_history_by_emotion_and_date
from module.utils.utils import logger

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

def find_response_by_emotion(emotion_structure: dict) -> dict: #LLMの初期応答で取得したキーワードと感情構成比、各responceで処理
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
