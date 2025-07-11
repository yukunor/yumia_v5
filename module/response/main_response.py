from llm_client import generate_emotion_from_prompt_simple as estimate_emotion, generate_emotion_from_prompt_with_context, extract_emotion_summary
from response.response_index import load_and_categorize_index, extract_best_reference, find_best_match_by_composition
from utils import logger
from main_memory import handle_emotion, save_emotion_sample  # 追加
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
    best_match = None

    try:
        print("✎ステップ①: 感情推定 開始")
        raw_response, initial_emotion = estimate_emotion(user_input)
        summary_str = ", ".join([f"{k}:{v}%" for k, v in initial_emotion.get("構成比", {}).items()])
        print(f"💫推定応答内容（raw）: {raw_response}")
        print(f"💞構成比（主感情: {initial_emotion.get('主感情', '未定義')}）: (構成比: {summary_str})")

        # ✅ GPT推定結果をデータセットに記録
        save_emotion_sample(user_input, raw_response, initial_emotion.get("構成比", {}))

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
                emotion_data = refer.get("emotion", {})
                path = emotion_data.get("保存先")
                date = emotion_data.get("date")
                full_emotion = load_emotion_by_date(path, date) if path and date else None
                if full_emotion:
                    keywords = emotion_data.get("キーワード", [])
                    match_info = refer.get("match_info", "")
                    reference_emotions.append({
                        "emotion": full_emotion,
                        "source": refer.get("source"),
                        "match_info": match_info
                    })
        print(f"📌 キーワード一致による参照感情件数: {len(reference_emotions)}件")

        best_match = find_best_match_by_composition(initial_emotion["構成比"], [r["emotion"] for r in reference_emotions])

        if best_match is None:
            print("✎ステップ④: 一致なし → 仮応答を使用")
            final_response = raw_response
            response_emotion = initial_emotion
        else:
            print("✎ステップ④: 応答生成と感情再推定 開始")
            final_response, response_emotion = generate_emotion_from_prompt_with_context(user_input, [best_match])

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

        if best_match:
            print("📌 参照感情データ:")
            for idx, emo_entry in enumerate(reference_emotions, start=1):
                emo = emo_entry["emotion"]
                ratio = emo.get("構成比", {})
                summary_str = ", ".join([f"{k}:{v}%" for k, v in ratio.items()])
                match_info = emo_entry.get("match_info", "")
                source = emo_entry.get("source", "不明")
                print(f"  [{idx}] {summary_str} | 状況: {emo.get('状況', '')} | キーワード: {', '.join(emo.get('keywords', []))}（{match_info}｜{source}）")
        else:
            print("📌 参照感情データ: 参照なし")

        # ✅ 感情保存用に渡す（emotion_index 用）
        response_emotion["emotion_vector"] = response_emotion.get("構成比", {})
        handle_emotion(response_emotion, user_input=user_input, response_text=final_response)

        return final_response, response_emotion
    except Exception as e:
        logger.error(f"[ERROR] 最終応答ログ出力中にエラー発生: {e}")
        raise

