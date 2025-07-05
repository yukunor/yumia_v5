from llm_client import generate_emotion_from_prompt as estimate_emotion, generate_emotion_from_prompt, extract_emotion_summary
from response.response_index import load_and_categorize_index, extract_best_reference
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
        print("✎ステップ②: インデックス全件読み込み 開始")
        categorized = load_and_categorize_index()
        count_long = len(categorized.get("long", []))
        count_intermediate = len(categorized.get("intermediate", []))
        count_short = len(categorized.get("short", []))
        print(f"インデックス件数: short={count_short}件, intermediate={count_intermediate}件, long={count_long}件")
    except Exception as e:
        logger.error(f"[ERROR] インデックス読み込み中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ③: キーワード一致＆構成比類似 抽出 開始")
        for category in ["short", "intermediate", "long"]:
            refer = extract_best_reference(initial_emotion, categorized.get(category, []), category)
            if refer:
                path = refer.get("保存先")
                date = refer.get("date")
                full_emotion = load_emotion_by_date(path, date) if path and date else None
                if full_emotion:
                    keywords = refer.get("keywords", [])
                    match_info = f"キーワード「{keywords[0]}」" if keywords else "キーワード一致"
                    reference_emotions.append({
                        "emotion": full_emotion,
                        "source": f"{category}-match",
                        "match_info": match_info
                    })
        print(f"📌 キーワード一致による参照感情件数: {len(reference_emotions)}件")
    except Exception as e:
        logger.error(f"[ERROR] キーワード一致処理中にエラー発生: {e}")
        raise

    try:
        if not reference_emotions:
            print("✎ステップ④: 一致なし → 仮応答を使用")
            final_response = raw_response
            response_emotion = initial_emotion
        else:
            print("✎ステップ④: 応答生成と感情再推定 開始")
            final_response, response_emotion = generate_emotion_from_prompt(user_input)
    except Exception as e:
        logger.error(f"[ERROR] GPT応答生成中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ⑤: 応答のサニタイズ 完了")
        print("💬 最終応答内容（再掲）:")
        print(f"💭{final_response.strip()}")
        main_emotion = response_emotion.get('主感情', '未定義')
        final_summary = ", ".join([f"{k}:{v}%" for k, v in response_emotion.get("構成比", {}).items()])
        print(f"💞構成比（主感情: {main_emotion}）: {final_summary}")

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
