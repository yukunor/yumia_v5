from llm_client import generate_emotion_from_prompt_simple as estimate_emotion, generate_emotion_from_prompt_with_context, extract_emotion_summary
from response.response_index import load_and_categorize_index, extract_best_reference, find_best_match_by_composition
from utils import logger, get_mongo_client, load_current_emotion, save_current_emotion, merge_emotion_vectors
from module.memory.main_memory import handle_emotion, save_emotion_sample, append_emotion_history, pad_emotion_vector
from module.memory.emotion_stats import synthesize_current_emotion
import json
import os
from bson import ObjectId
from utils import summarize_feeling

client = get_mongo_client()
if client is None:
    raise ConnectionError("[ERROR] MongoDBクライアントの取得に失敗しました")
db = client["emotion_db"]

def get_mongo_collection(category, emotion_label):
    try:
        collection_name = f"{category}_{emotion_label}"
        return db[collection_name]
    except Exception as e:
        logger.error(f"[ERROR] MongoDBコレクション取得失敗: {e}")
        return None

def load_emotion_by_date(path, target_date):
    print(f"[DEBUG] load_emotion_by_date() 呼び出し: path={path}, date={target_date}")

    if path.startswith("mongo/"):
        print("[DEBUG] MongoDB読み込みルートへ")
        try:
            parts = path.split("/")
            if len(parts) == 3:
                _, category, emotion_label = parts
                print(f"[DEBUG] MongoDBクエリ: category={category}, label={emotion_label}, date={target_date}")

                try:
                    db.client.admin.command("ping")
                    print("[DEBUG] MongoDB ping成功: 接続は有効")
                except Exception as e:
                    print(f"[DEBUG] MongoDB ping失敗: {e}")
                    return None

                collection = db["emotion_data"]
                doc = collection.find_one({"category": category, "emotion": emotion_label})
                print(f"[DEBUG] emotion_data コレクション検索: {doc is not None}")

                if doc and "data" in doc and "履歴" in doc["data"]:
                    for entry in doc["data"]["履歴"]:
                        print(f"[DEBUG] 照合中: entry.date={entry.get('date')} vs target_date={target_date}")
                        if str(entry.get("date")) == str(target_date):
                            print(f"[DEBUG] MongoDB履歴内一致: {entry}")
                            return entry

                print("[DEBUG] 該当データが見つかりませんでした")
        except Exception as e:
            logger.error(f"[ERROR] MongoDBデータ取得失敗: {e}")
            print(f"[DEBUG] 例外発生: {e}")
        return None

    try:
        if not os.path.exists(path):
            logger.warning(f"[WARNING] 指定されたパスが存在しません: {path}")
            return None

        print(f"[DEBUG] ローカルファイル読み込み: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[DEBUG] ローカルデータ型: {type(data)}")

        if isinstance(data, list):
            for item in reversed(data):
                if str(item.get("date")) == str(target_date):
                    print(f"[DEBUG] ローカルファイルからの読み込み成功: {item}")
                    return item

        elif isinstance(data, dict) and "履歴" in data:
            for item in reversed(data["履歴"]):
                print(f"[DEBUG] ローカルファイル照合中: item.date={repr(item.get('date'))} vs target_date={repr(target_date)}")
                if str(item.get("date")) == str(target_date):
                    print(f"[DEBUG] ローカルファイル履歴からの読み込み成功: {item}")
                    return item

    except Exception as e:
        logger.error(f"[ERROR] 感情データの読み込み失敗: {e}")
    return None

def load_emotion_by_date(path, target_date):
    if path.startswith("mongo/"):
        try:
            parts = path.split("/")
            if len(parts) == 3:
                _, category, emotion_label = parts

                try:
                    db.client.admin.command("ping")
                except Exception as e:
                    return None

                collection = db["emotion_data"]
                doc = collection.find_one({"category": category, "emotion": emotion_label})

                if doc and "data" in doc and "履歴" in doc["data"]:
                    for entry in doc["data"]["履歴"]:
                        if str(entry.get("date")) == str(target_date):
                            return entry
            return None
        except Exception as e:
            logger.error(f"[ERROR] MongoDBデータ取得失敗: {e}")
            return None

    try:
        if not os.path.exists(path):
            logger.warning(f"[WARNING] 指定されたパスが存在しません: {path}")
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in reversed(data):
                if str(item.get("date")) == str(target_date):
                    return item

        elif isinstance(data, dict) and "履歴" in data:
            for item in reversed(data["履歴"]):
                if str(item.get("date")) == str(target_date):
                    return item

    except Exception as e:
        logger.error(f"[ERROR] 感情データの読み込み失敗: {e}")
    return None

def run_response_pipeline(user_input: str) -> tuple[str, dict]:
    initial_emotion = {}
    reference_emotions = []
    best_match = None

    current_feeling = load_current_emotion()

    try:
        raw_response, initial_emotion = estimate_emotion(user_input, current_emotion=current_feeling)
        save_emotion_sample(user_input, raw_response, initial_emotion.get("構成比", {}))
    except Exception as e:
        logger.error(f"[ERROR] 感情推定中にエラー発生: {e}")
        raise

    try:
        categorized = load_and_categorize_index()
    except Exception as e:
        logger.error(f"[ERROR] インデックス読み込み中にエラー発生: {e}")
        raise

    try:
        for category in ["short", "intermediate", "long"]:
            refer = extract_best_reference(initial_emotion, categorized.get(category, []), category)
            if refer:
                emotion_data = refer.get("emotion", {})
                path = refer.get("保存先")
                date = refer.get("date")
                full_emotion = load_emotion_by_date(path, date) if path and date else None
                if full_emotion:
                    reference_emotions.append({
                        "emotion": full_emotion,
                        "source": refer.get("source"),
                        "match_info": refer.get("match_info", "")
                    })
        best_match = find_best_match_by_composition(initial_emotion["構成比"], [r["emotion"] for r in reference_emotions])

        if best_match is None:
            final_response = raw_response
            response_emotion = initial_emotion
        else:
            context = [best_match]
            context.append({
                "emotion": {
                    "現在の気分": current_feeling
                },
                "source": "現在の気分合成データ",
                "match_info": "現在の気分のプロンプト挿入用"
            })
            final_response, response_emotion = generate_emotion_from_prompt_with_context(user_input, context)

    except Exception as e:
        logger.error(f"[ERROR] GPT応答生成中にエラー発生: {e}")
        raise

    try:
        reference_data = best_match if isinstance(best_match, dict) else {"構成比": {}, "source": "不明", "date": "不明"}

        response_emotion["emotion_vector"] = response_emotion.get("構成比", {})
        handle_emotion(response_emotion, user_input=user_input, response_text=final_response)

        padded_ratio = pad_emotion_vector(response_emotion.get("構成比", {}))
        response_emotion["構成比"] = padded_ratio
        append_emotion_history(response_emotion)

        merged = merge_emotion_vectors(current_feeling, response_emotion.get("構成比", {}))
        save_current_emotion(merged)

        return final_response, response_emotion
    except Exception as e:
        logger.error(f"[ERROR] 最終応答ログ出力中にエラー発生: {e}")
        raise

