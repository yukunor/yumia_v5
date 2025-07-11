from llm_client import generate_emotion_from_prompt_simple as estimate_emotion, generate_emotion_from_prompt_with_context, extract_emotion_summary
from response.response_index import load_and_categorize_index, extract_best_reference, find_best_match_by_composition
from utils import logger
from main_memory import handle_emotion  # 追加
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
        print("\u270e\u30b9\u30c6\u30c3\u30d7\uff11: \u611f\u60c5\u63a8\u5b9a \u958b\u59cb")
        raw_response, initial_emotion = estimate_emotion(user_input)
        summary_str = ", ".join([f"{k}:{v}%" for k, v in initial_emotion.get("\u69cb\u6210\u6bd4", {}).items()])
        print(f"\ud83d\udcab\u63a8\u5b9a\u5fdc\u7b54\u5185\u5bb9（raw）: {raw_response}")
        print(f"\ud83d\udc96\u69cb\u6210\u6bd4（\u4e3b\u611f\u60c5: {initial_emotion.get('主感情', '未定義')}\uff09: (\u69cb\u6210\u6bd4: {summary_str})")
    except Exception as e:
        logger.error(f"[ERROR] 感情推定中にエラー発生: {e}")
        raise

    try:
        print("\u270e\u30b9\u30c6\u30c3\u30d7\uff12: \u30a4\u30f3\u30c7\u30c3\u30af\u30b9\u5168\u4ef6\u8aad\u307f\u8fbc\u307f \u958b\u59cb")
        categorized = load_and_categorize_index()
        count_long = len(categorized.get("long", []))
        count_intermediate = len(categorized.get("intermediate", []))
        count_short = len(categorized.get("short", []))
        print(f"\u30a4\u30f3\u30c7\u30c3\u30af\u30b9\u4ef6\u6570: short={count_short}\u4ef6, intermediate={count_intermediate}\u4ef6, long={count_long}\u4ef6")
    except Exception as e:
        logger.error(f"[ERROR] インデックス読み込み中にエラー発生: {e}")
        raise

    try:
        print("\u270e\u30b9\u30c6\u30c3\u30d7\uff13: \u30ad\u30fc\u30ef\u30fc\u30c9\u4e00\u81f4\uff06\u69cb\u6210\u6bd4\u985e\u4f3c \u62bd\u51fa \u958b\u59cb")
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
        print(f"\ud83d\udccc \u30ad\u30fc\u30ef\u30fc\u30c9\u4e00\u81f4\u306b\u3088\u308b\u53c2\u7167\u611f\u60c5\u4ef6\u6570: {len(reference_emotions)}\u4ef6")

        best_match = find_best_match_by_composition(initial_emotion["構成比"], [r["emotion"] for r in reference_emotions])

        if best_match is None:
            print("\u270e\u30b9\u30c6\u30c3\u30d7\uff14: \u4e00\u81f4\u306a\u3057 \u2192 \u4eee\u5fdc\u7b54\u3092\u4f7f\u7528")
            final_response = raw_response
            response_emotion = initial_emotion
        else:
            print("\u270e\u30b9\u30c6\u30c3\u30d7\uff14: \u5fdc\u7b54\u751f\u6210\u3068\u611f\u60c5\u518d\u63a8\u5b9a \u958b\u59cb")
            final_response, response_emotion = generate_emotion_from_prompt_with_context(user_input, [best_match])

    except Exception as e:
        logger.error(f"[ERROR] GPT応答生成中にエラー発生: {e}")
        raise

    try:
        print("\u270e\u30b9\u30c6\u30c3\u30d7\uff15: \u5fdc\u7b54\u306e\u30b5\u30cb\u30bf\u30a4\u30ba \u5b8c\u4e86")
        print("\ud83d\udcac \u6700\u7d42\u5fdc\u7b54\u5185\u5bb9\uff08\u518d\u63a1\uff09:")
        print(f"\ud83d\udcad{final_response.strip()}")
        main_emotion = response_emotion.get('主感情', '未定義')
        final_summary = ", ".join([f"{k}:{v}%" for k, v in response_emotion.get("構成比", {}).items()])
        print(f"\ud83d\udc96\u69cb\u6210\u6bd4（\u4e3b\u611f\u60c5: {main_emotion}\uff09: {final_summary}")

        if best_match:
            print("\ud83d\udccc \u53c2\u7167\u611f\u60c5\u30c7\u30fc\u30bf:")
            for idx, emo_entry in enumerate(reference_emotions, start=1):
                emo = emo_entry["emotion"]
                ratio = emo.get("構成比", {})
                summary_str = ", ".join([f"{k}:{v}%" for k, v in ratio.items()])
                match_info = emo_entry.get("match_info", "")
                source = emo_entry.get("source", "不明")
                print(f"  [{idx}] {summary_str} | 状況: {emo.get('状況', '')} | キーワード: {', '.join(emo.get('keywords', []))}（{match_info}｜{source}）")
        else:
            print("\ud83d\udccc \u53c2\u7167\u611f\u60c5\u30c7\u30fc\u30bf: \u53c2\u7167\u306a\u3057")

        # ✅ 感情保存用に渡す（dataset_emotion用）
        response_emotion["emotion_vector"] = response_emotion.get("構成比", {})  # 明示的に追加
        handle_emotion(response_emotion, user_input=user_input, response_text=final_response)

        return final_response, response_emotion
    except Exception as e:
        logger.error(f"[ERROR] 最終応答ログ出力中にエラー発生: {e}")
        raise

