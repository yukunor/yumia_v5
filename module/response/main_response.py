from llm_client import generate_emotion_from_prompt as estimate_emotion, generate_emotion_from_prompt, extract_emotion_summary
from response.response_index import search_similar_emotions
from response.response_long import match_long_keywords
from response.response_intermediate import match_intermediate_keywords
from response.response_short import match_short_keywords
from utils import logger
import json

def load_emotion_by_date(path, target_date):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in reversed(data):
                if item.get("date") == target_date:
                    return item

        elif isinstance(data, dict) and "履歴" in data:
            for item in reversed(data["履歴"]):
                if item.get("date") == target_date:
                    return item
    except Exception as e:
        logger.error(f"[ERROR] 感情データの読み込み失敗: {e}")
    return None

def run_response_pipeline(user_input: str) -> tuple[str, dict]:
    initial_emotion = {}
    reference_emotions = []

    try:
        print("✎ステップ①: 感情推定 開始")
        raw_response, initial_emotion = estimate_emotion(user_input)
        summary_str = ", ".join([f"{k}:{v}%" for k, v in initial_emotion.get("構成比", {}).items()])
        print(f"💭推定応答内容（raw）: {raw_response}")
        print(f"💞構成比（主感情: {initial_emotion.get('主感情', '未定義')}）: （構成比: {summary_str}）")
    except Exception as e:
        logger.error(f"[ERROR] 感情推定中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ②: 類似感情検索 開始")
        top30_emotions = search_similar_emotions(initial_emotion)
        count_long = len(top30_emotions.get("long", []))
        count_intermediate = len(top30_emotions.get("intermediate", []))
        count_short = len(top30_emotions.get("short", []))
        total_matches = count_long + count_intermediate + count_short
        print(f"構成比一致: {total_matches}件 / 不一致: {1533 - total_matches}件")
        print(f"カテゴリ別: short={count_short}件, intermediate={count_intermediate}件, long={count_long}件")
    except Exception as e:
        logger.error(f"[ERROR] 類似感情検索中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ③: キーワードマッチング 開始")
        long_matches = match_long_keywords(initial_emotion, top30_emotions.get("long", []))
        intermediate_matches = match_intermediate_keywords(initial_emotion, top30_emotions.get("intermediate", []))
        short_matches = match_short_keywords(initial_emotion, top30_emotions.get("short", []))
        print(f"マッチ件数: long={len(long_matches)}件, intermediate={len(intermediate_matches)}件, short={len(short_matches)}件")

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
                    full_emotion = load_emotion_by_date(path, date) if path and date else None
                    if full_emotion:
                        keywords = e.get("keywords", [])
                        match_info = f"キーワード「{keywords[0]}」" if keywords else "キーワード一致"
                        reference_emotions.append({
                            "emotion": full_emotion,
                            "source": f"{category}-match",
                            "match_info": match_info
                        })
            else:
                for item in top30_emotions.get(category, [])[:3]:
                    path = item.get("保存先")
                    date = item.get("date")
                    full_emotion = load_emotion_by_date(path, date) if path and date else None
                    if full_emotion:
                        main_emotion = initial_emotion.get("主感情", "主感情未定義")
                        reference_emotions.append({
                            "emotion": full_emotion,
                            "source": f"{category}-score",
                            "match_info": f"主感情「{main_emotion}」に類似"
                        })

        total_reference = len(reference_emotions)
        match_count = sum(1 for e in reference_emotions if e["source"].endswith("-match"))
        score_count = total_reference - match_count
        print(f"参照データ: {total_reference}件（キーワード一致: {match_count}件 → 類似構成比から補完: {score_count}件）")
    except Exception as e:
        logger.error(f"[ERROR] キーワードマッチ中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ④: 応答生成と感情再推定 開始")
        print("※感情再推定処理ログ出力対象、出力はステップ⑤にて")
        final_response, response_emotion = generate_emotion_from_prompt(user_input)
    except Exception as e:
        logger.error(f"[ERROR] GPT応答生成中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ⑤: 応答のサニタイズ 完了")
        print("💬 最終応答内容（再掲）:")
        print(f"💭{final_response.strip()}")
        final_summary = ", ".join([f"{k}:{v}%" for k, v in response_emotion.get("構成比", {}).items()])
        print(f"💞構成比（主感情: {response_emotion.get('主感情', '未定義')}）: {final_summary}")

        print("📌 参照感情データ:")
        for idx, emo_entry in enumerate(reference_emotions, start=1):
            emo = emo_entry["emotion"]
            ratio = emo.get("構成比", {})
            summary_str = ", ".join([f"{k}:{v}%" for k, v in ratio.items()])
            match_info = emo_entry.get("match_info", "")
            print(f"  [{idx}] {summary_str} | 状況: {emo.get('状況', '')} | キーワード: {', '.join(emo.get('keywords', []))}（{match_info}）")

        return final_response, response_emotion
    except Exception as e:
        logger.error(f"[ERROR] 最終応答ログ出力中にエラー発生: {e}")
        raise

