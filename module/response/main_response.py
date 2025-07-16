from llm_client import generate_emotion_from_prompt_simple as estimate_emotion, generate_emotion_from_prompt_with_context, extract_emotion_summary
from response.response_index import load_and_categorize_index, extract_best_reference, find_best_match_by_composition
from utils import logger, get_mongo_client
from module.memory.main_memory import handle_emotion, save_emotion_sample, append_emotion_history, pad_emotion_vector
from module.memory.emotion_stats import synthesize_current_emotion
import json
import os
from bson import ObjectId

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

                collection = get_mongo_collection(category, emotion_label)
                print(f"[DEBUG] collection の有無: {collection}")
                if collection is not None:
                    record = collection.find_one({"date": target_date})
                    if record:
                        print(f"[DEBUG] MongoDB取得結果（単独）: {record}")
                        return record

                    print("[DEBUG] collection.find({}) 実行")
                    docs = list(collection.find({}))
                    print(f"[DEBUG] 取得ドキュメント数: {len(docs)}")
                    for doc in docs:
                        print(f"[DEBUG] ドキュメント構造確認: {doc}")
                        history_list = []
                        if "履歴" in doc:
                            history_list = doc["履歴"]
                        elif "data" in doc and "履歴" in doc["data"]:
                            history_list = doc["data"]["履歴"]

                        for entry in history_list:
                            print(f"[DEBUG] 照合中: entry.date={entry.get('date')} vs target_date={target_date}")
                            if str(entry.get("date")) == str(target_date):
                                print(f"[DEBUG] MongoDB履歴内一致: {entry}")
                                return entry

                    print("[DEBUG] 最終確認: 全レコードを直接照合")
                    for doc in docs:
                        if str(doc.get("date")) == str(target_date):
                            print(f"[DEBUG] MongoDB最終一致成功: {doc}")
                            return doc

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

def run_response_pipeline(user_input: str) -> tuple[str, dict]:
    initial_emotion = {}
    reference_emotions = []
    best_match = None

    print("[DEBUG] 現在の気分を合成中...")
    current_feeling_data = synthesize_current_emotion()
    current_feeling = current_feeling_data.get("現在の気分", {})
    long_base_emotion = current_feeling_data.get("主感情", "未定義")
    print(f"[DEBUG] 合成された現在の気分: {current_feeling}")
    print(f"[DEBUG] 合成された主感情: {long_base_emotion}")

    try:
        print("✎ステップ①: 感情推定 開始")
        raw_response, initial_emotion = estimate_emotion(user_input)
        summary_str = ", ".join([f"{k}:{v}%" for k, v in initial_emotion.get("構成比", {}).items()])
        print(f"💫推定応答内容（raw）: {raw_response}")
        print(f"💞構成比（主感情: {initial_emotion.get('主感情', '未定義')}）: (構成比: {summary_str})")
        save_emotion_sample(user_input, raw_response, initial_emotion.get("構成比", {}))
    except Exception as e:
        logger.error(f"[ERROR] 感情推定中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ②: インデックス全件読み込み 開始")
        categorized = load_and_categorize_index()
        print(f"インデックス件数: short={len(categorized.get('short', []))}件, intermediate={len(categorized.get('intermediate', []))}件, long={len(categorized.get('long', []))}件")
    except Exception as e:
        logger.error(f"[ERROR] インデックス読み込み中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ③: キーワード一致＆構成比類似 抽出 開始")
        for category in ["short", "intermediate", "long"]:
            refer = extract_best_reference(initial_emotion, categorized.get(category, []), category)
            print(f"[DEBUG] refer ({category}): {refer}")
            if refer:
                emotion_data = refer.get("emotion", {})
                path = refer.get("保存先")
                date = refer.get("date")
                print(f"[DEBUG] path: {path}, date: {date}")
                full_emotion = load_emotion_by_date(path, date) if path and date else None
                print(f"[DEBUG] load_emotion_by_date 結果: {full_emotion}")
                if full_emotion:
                    reference_emotions.append({
                        "emotion": full_emotion,
                        "source": refer.get("source"),
                        "match_info": refer.get("match_info", "")
                    })
        print(f"📌 キーワード一致による参照感情件数: {len(reference_emotions)}件")

        best_match = find_best_match_by_composition(initial_emotion["構成比"], [r["emotion"] for r in reference_emotions])
        print(f"[DEBUG] 最終的なベストマッチ: {best_match}")

        if best_match is None:
            print("✎ステップ④: 一致なし → 仮応答を使用")
            final_response = raw_response
            response_emotion = initial_emotion
        else:
            print("✎ステップ④: 応答生成と感情再推定 開始")
            context = [best_match]
            context.append({
                "emotion": {
                    "人格基盤（long_base_emotion）": long_base_emotion,
                    "現在の気分": current_feeling
                },
                "source": "現在の気分合成データ",
                "match_info": "人格基盤と現在の気分のプロンプト挿入用"
            })
            final_response, response_emotion = generate_emotion_from_prompt_with_context(user_input, context)

    except Exception as e:
        logger.error(f"[ERROR] GPT応答生成中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ⑤: 応答のサニタイズ 完了")
        print(f"💬 最終応答内容（再掲）:\n💭{final_response.strip()}")
        main_emotion = response_emotion.get('主感情', '未定義')
        final_summary = ", ".join([f"{k}:{v}%" for k, v in response_emotion.get("構成比", {}).items()])
        print(f"💞構成比（主感情: {main_emotion}）: {final_summary}")

        if best_match:
            print("📌 参照感情データ:")
            for idx, emo_entry in enumerate(reference_emotions, start=1):
                emo = emo_entry["emotion"]
                ratio = emo.get("構成比", {})
                summary_str = ", ".join([f"{k}:{v}%" for k, v in ratio.items()])
                print(f"  [{idx}] {summary_str} | 状況: {emo.get('状況', '')} | キーワード: {', '.join(emo.get('keywords', []))}（{emo_entry.get('match_info', '')}｜{emo_entry.get('source', '不明')}）")
        else:
            print("📌 参照感情データ: 参照なし")

        response_emotion["emotion_vector"] = response_emotion.get("構成比", {})
        handle_emotion(response_emotion, user_input=user_input, response_text=final_response)

        padded_ratio = pad_emotion_vector(response_emotion.get("構成比", {}))
        response_emotion["構成比"] = padded_ratio
        append_emotion_history(response_emotion)

        return final_response, response_emotion
    except Exception as e:
        logger.error(f"[ERROR] 最終応答ログ出力中にエラー発生: {e}")
        raise
