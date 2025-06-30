from llm_client import generate_emotion_from_prompt as estimate_emotion, generate_emotion_from_prompt, extract_emotion_summary
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
    try:
        print("✎ステップ①: 感情推定 開始")
        raw_response, initial_emotion = estimate_emotion(user_input)
        print(f"💭推定応答内容（raw）: {raw_response}")
        print(f"💞推定構成比（主感情: {initial_emotion.get('主感情', '未定義')}) : {extract_emotion_summary(initial_emotion)}")

        print("✎ステップ②: 類似感情検索 開始")
        top30_emotions = search_similar_emotions(initial_emotion)
        counts = {k: len(v) for k, v in top30_emotions.items()}
        total_matches = sum(counts.values())
        print(f"構成比一致: {total_matches}件 / 不一致: {1533 - total_matches}件")
        print(f"カテゴリ別: short={counts.get('short', 0)}件, intermediate={counts.get('intermediate', 0)}件, long={counts.get('long', 0)}件")

        print("✎ステップ③: キーワードマッチング 開始")
        matched_categories = {
            "long": match_long_keywords(initial_emotion, top30_emotions.get("long", [])),
            "intermediate": match_intermediate_keywords(initial_emotion, top30_emotions.get("intermediate", [])),
            "short": match_short_keywords(initial_emotion, top30_emotions.get("short", []))
        }
        print(f"マッチ件数: long={len(matched_categories['long'])}件, intermediate={len(matched_categories['intermediate'])}件, short={len(matched_categories['short'])}件")
        print("参照データ: 3件（スコア上位）")

        reference_emotions = []
        for category, matches in matched_categories.items():
            selected = matches if matches else top30_emotions.get(category, [])[:3]
            for item in selected:
                path = item.get("保存先")
                date = item.get("date")
                if path and date:
                    full_emotion = load_emotion_by_date(path, date)
                    if full_emotion:
                        reference_emotions.append({
                            "emotion": full_emotion,
                            "source": f"{category}-match" if matches else f"{category}-score"
                        })

        print("✎ステップ④: 応答生成と感情再推定 開始")
        response, response_emotion = generate_emotion_from_prompt(user_input)
        print(f"💭最終応答文: {response}")
        print(f"💞応答構成比（主感情: {response_emotion.get('主感情', '未定義')}) : {extract_emotion_summary(response_emotion)}")

        print("📌 参照感情データ:")
        for idx, emo_entry in enumerate(reference_emotions, start=1):
            emo = emo_entry["emotion"]
            ratio = emo.get("構成比", {})
            situation = emo.get("状況", "")
            keywords = emo.get("keywords", [])
            summary_str = ", ".join(f"{k}:{v}%" for k, v in ratio.items())
            print(f"  [{idx}] {summary_str} | 状況: {situation} | キーワード: {', '.join(keywords)}")

        print("✎ステップ⑤: 応答のサニタイズ 完了")
        return response, response_emotion

    except Exception as e:
        logger.error(f"[ERROR] run_response_pipeline中にエラー発生: {e}")
        raise

