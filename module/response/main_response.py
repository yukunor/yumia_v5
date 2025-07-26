#module/responce/main_responce.py
import json
import os
from bson import ObjectId

import module.response.response_index as response_index
import module.response.responce_long as long_history
import module.response.responce_intermediate as intermediate_history
import module.response.responce_short as short_history
from module.mongo.mongo_client import get_mongo_client
from module.llm.llm_client import generate_gpt_response_from_history
from module.response.response_short import find_short_history_by_emotion_and_date
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

import json

    #文字列がJSON形式ならdictに変換。そうでなければそのまま返す。
def try_parse_json(text: str) -> dict | str:
    try:
        parsed = json.loads(text)
        logger.info(f"[INFO] JSONパース成功: {parsed}")
        return parsed
    except json.JSONDecodeError:
        logger.info(f"[INFO] JSONパース失敗。元のテキストを返します: {text}")
        return text

    #履歴＋現在感情に基づいて GPT 応答を生成し、整形して返す。
def get_history_based_response() -> dict:
    logger.info("[START] get_history_based_response")

    response_text = generate_gpt_response_from_history()
    logger.info(f"[INFO] GPT応答テキスト: {response_text}")

    return {
        "type": "history",  # または fallback / gpt
        "response": response_text
    }

    #GPTからの履歴ベース応答がJSON形式なら、構成比とキーワードを抽出して返す。そうでなければ文字列のまま返す。
def find_response_by_emotion() -> dict:
    logger.info("[START] find_response_by_emotion")

    response_dict = get_history_based_response()
    response_text = response_dict.get("response", "")
    logger.info(f"[INFO] GPT応答の元テキスト: {response_text[:300]}")  # 長文カット（任意）

    parsed = try_parse_json(response_text)

    if isinstance(parsed, dict):
        logger.info(f"[INFO] JSONとして解析成功: 構成比とキーワードを抽出中")
        composition = parsed.get("構成比", {})
        keywords = parsed.get("keywords", [])
        logger.info(f"[INFO] 構成比: {composition}")
        logger.info(f"[INFO] キーワード: {keywords}")
        return {
            "type": "extracted",
            "構成比": composition,
            "keywords": keywords
        }
    else:
        logger.warning("[WARN] 応答はJSON形式ではありません。生文字列として返します")
        return {
            "type": "text",
            "raw_response": parsed
        }

    #構成比とキーワードからインデックス応答を取得する統合関数。
def get_best_match(emotion_structure: dict) -> dict | None:
    logger.info("[START] get_best_match")

    # 🔹 emotion_structure から構成比とキーワードを抽出
    composition = emotion_structure.get("構成比", {})
    keywords = emotion_structure.get("keywords", [])
    logger.info(f"[INFO] 構成比: {composition}")
    logger.info(f"[INFO] キーワード: {keywords}")

    # 🔹 MongoDBからインデックスを読み込み、カテゴリ分け
    categorized_index = response_index.load_and_categorize_index()
    logger.info("[INFO] カテゴリ別インデックスの読み込み完了")

    # 🔹 各カテゴリでフィルタリングと構成比マッチング
    for category in ["long", "intermediate", "short"]:
        items = categorized_index.get(category, [])
        logger.debug(f"[INFO] {category}カテゴリのアイテム数: {len(items)}")

        filtered = response_index.filter_by_keywords(items, keywords)
        logger.debug(f"[INFO] {category}カテゴリでキーワード一致: {len(filtered)} 件")

        if not filtered:
            continue

        best_match = response_index.find_best_match_by_composition(composition, filtered)
        if best_match:
            logger.debug(f"[SUCCESS] {category}カテゴリで構成比一致の応答を発見")
            return best_match

    logger.debug("[WARN] 全カテゴリで一致するインデックスが見つかりませんでした")
    return None

    #各カテゴリ（short → intermediate → long）から指定された感情名と日付に一致する履歴を取得して返す。
def collect_all_category_responses(emotion_name: str, date_str: str) -> dict:
    logger.info(f"[START] collect_all_category_responses - 感情: {emotion_name}, 日付: {date_str}")

    # short
    all_short_data = short_history.get_all_short_category_data()
    logger.debug(f"[INFO] shortカテゴリのデータ件数: {len(all_short_data)}")
    short_match = short_history.search_short_history(
        all_data=all_short_data,
        emotion_name=emotion_name,
        category_name="short",
        target_date=date_str
    )
    if short_match:
        logger.debug(f"[MATCH] shortカテゴリで一致データあり")
    else:
        logger.debug(f"[NO MATCH] shortカテゴリで一致データなし")

    # intermediate
    all_intermediate_data = intermediate_history.get_all_intermediate_category_data()
    logger.debug(f"[INFO] intermediateカテゴリのデータ件数: {len(all_intermediate_data)}")
    intermediate_match = intermediate_history.search_intermediate_history(
        all_data=all_intermediate_data,
        emotion_name=emotion_name,
        category_name="intermediate",
        target_date=date_str
    )
    if intermediate_match:
        logger.debug(f"[MATCH] intermediateカテゴリで一致データあり")
    else:
        logger.debug(f"[NO MATCH] intermediateカテゴリで一致データなし")

    # long
    all_long_data = long_history.get_all_long_category_data()
    logger.debug(f"[INFO] longカテゴリのデータ件数: {len(all_long_data)}")
    long_match = long_history.search_long_history(
        all_data=all_long_data,
        emotion_name=emotion_name,
        category_name="long",
        target_date=date_str
    )
    if long_match:
        logger.debug(f"[MATCH] longカテゴリで一致データあり")
    else:
        logger.debug(f"[NO MATCH] longカテゴリで一致データなし")

    logger.debug("[END] collect_all_category_responses 完了")

    return {
        "short": short_match,
        "intermediate": intermediate_match,
        "long": long_match
    }
