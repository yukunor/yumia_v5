from llm_client import generate_emotion_from_prompt as estimate_emotion, generate_gpt_response, extract_emotion_summary
from response.response_index import search_similar_emotions
from response.response_long import match_long_keywords
from response.response_intermediate import match_intermediate_keywords
from response.response_short import match_short_keywords
from utils import logger
import time
import copy
import os
import json

def load_emotion_by_date(path, target_date):
    try:
        print(f"[DEBUG] 感情データ読み込み開始: path={path}, date={target_date}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in reversed(data):
                if item.get("date") == target_date:
                    print(f"[DEBUG] 感情データ一致: date={item.get('date')}")
                    return item

        elif isinstance(data, dict) and "履歴" in data:
            for item in reversed(data["履歴"]):
                if item.get("date") == target_date:
                    print(f"[DEBUG] 感情データ一致: date={item.get('date')}")
                    return item

        print(f"[WARNING] 感情データ一致なし: 指定date={target_date}")
    except Exception as e:
        print(f"[ERROR] ファイル読み込み失敗: {e}")
        logger.error(f"[ERROR] 感情データの読み込み失敗: {e}")
    return None

def run_response_pipeline(user_input: str) -> tuple[str, dict]:
    initial_emotion = {}
    main_emotion = "未定義"
    used_llm_only = False

    try:
        logger.info("[TIMER] ▼ ステップ① 感情推定 開始")
        print("🙄 ステップ①: 感情推定 開始")
        t1 = time.time()
        _, initial_emotion = estimate_emotion(user_input)
        print("🙄 感情推定結果:", initial_emotion)
        logger.info(f"[TIMER] ▲ ステップ① 感情推定 完了: {time.time() - t1:.2f}秒")

        if not isinstance(initial_emotion, dict):
            logger.error(f"[ERROR] 感情推定結果が辞書形式ではありません: {type(initial_emotion)} - {initial_emotion}")
            initial_emotion = {}

        main_emotion = initial_emotion.get("主感情", "未定義")
        logger.debug(f"[DEBUG] 推定された主感情: {main_emotion}")
        logger.info("[INFO] 感情推定完了")

    except Exception as e:
        logger.error(f"[ERROR] 感情推定中にエラー発生: {e}")
        raise

    try:
        logger.info("[TIMER] ▼ ステップ② 類似感情検索 開始")
        print("🔍 ステップ②: 類似感情検索 開始")
        t2 = time.time()
        top30_emotions = search_similar_emotions(initial_emotion)
        logger.info(f"[TIMER] ▲ ステップ② 類似感情検索 完了: {time.time() - t2:.2f}秒")

        count_long = len(top30_emotions.get("long", []))
        count_intermediate = len(top30_emotions.get("intermediate", []))
        count_short = len(top30_emotions.get("short", []))
        total_matches = count_long + count_intermediate + count_short

        print(f"📊 構成比一致: {total_matches}件 / 不一致: {1533 - total_matches}件")
        print(f"📦 カテゴリ別: short={count_short}件, intermediate={count_intermediate}件, long={count_long}件")
        logger.info(f"[検索結果] long: {count_long}件, intermediate: {count_intermediate}件, short: {count_short}件")

        reference_emotions = []

        if total_matches == 0:
            print("📬 構成比一致データなし → ステップ③をスキップ")
        else:
            logger.info("[TIMER] ▼ ステップ③ キーワードマッチ 開始")
            print("🧹 ステップ③: キーワードマッチング 開始")
            t3 = time.time()
            long_matches = match_long_keywords(initial_emotion, top30_emotions.get("long", []))
            intermediate_matches = match_intermediate_keywords(initial_emotion, top30_emotions.get("intermediate", []))
            short_matches = match_short_keywords(initial_emotion, top30_emotions.get("short", []))
            logger.info(f"[TIMER] ▲ ステップ③ キーワードマッチ 完了: {time.time() - t3:.2f}秒")

            print(f"🔖 マッチ件数: long={len(long_matches)}件, intermediate={len(intermediate_matches)}件, short={len(short_matches)}件")
            print("✅ キーワードマッチ成立 → 一致カテゴリはマッチデータを参照し、不一致カテゴリはスコア上位3件を使用")

            matched_categories = {
                "long": long_matches,
                "intermediate": intermediate_matches,
                "short": short_matches
            }

            for category, matches in matched_categories.items():
                if matches:
                    for e in matches:
                        path = e.get("保存先")
                        date = e.get("date")
                        if path and date:
                            full_emotion = load_emotion_by_date(path, date)
                            if full_emotion:
                                reference_emotions.append({
                                    "emotion": full_emotion,
                                    "source": f"{category}-match"
                                })
                else:
                    for item in top30_emotions.get(category, [])[:3]:
                        path = item.get("保存先")
                        date = item.get("date")
                        if path and date:
                            full_emotion = load_emotion_by_date(path, date)
                            if full_emotion:
                                reference_emotions.append({
                                    "emotion": full_emotion,
                                    "source": f"{category}-score"
                                })

            print(f"📚 合計参照データ件数: {len(reference_emotions)}件")

    except Exception as e:
        logger.error(f"[ERROR] 類似感情検索中にエラー発生: {e}")
        raise

    try:
        logger.info("[TIMER] ▼ ステップ④ GPT応答生成＋感情再推定 開始")
        print("💬 ステップ④: GPT応答生成＋感情再推定 開始")
        t4 = time.time()
        response, response_emotion = generate_gpt_response_and_emotion(user_input, [r["emotion"] for r in reference_emotions])
        print("📨 応答内容:", response)
        summary = extract_emotion_summary(response_emotion, main_emotion)
        print("📊 応答構成比 summary 確認:", summary)
        print(f"📚 参照感情数: {len(reference_emotions)}件")
        logger.info(f"[TIMER] ▲ ステップ④ GPT応答生成＋感情再推定 完了: {time.time() - t4:.2f}秒")

        if reference_emotions:
            print("📌 GPT応答で以下の感情データを参照しました:")
            for idx, emo_entry in enumerate(reference_emotions, start=1):
                emo = emo_entry["emotion"]
                source = emo_entry.get("source", "不明")
                main = emo.get("主感情", "不明")
                ratio = emo.get("構成比", {})
                date = emo.get("date", "不明")
                situation = emo.get("状況", "")
                keywords = emo.get("keywords", [])
                summary_parts = [f"{k}:{v}%" for k, v in ratio.items()]
                summary_str = ", ".join(summary_parts)
                keywords_str = ", ".join(keywords)
                print(f"  [{idx}] 出典: {source} | 主感情: {main} | 構成比: {summary_str} | 日付: {date} | 状況: {situation} | キーワード: {keywords_str}")

        return response, response_emotion

    except Exception as e:
        logger.error(f"[ERROR] GPT応答生成または感情再推定中にエラー発生: {e}")
        return "", initial_emotion
