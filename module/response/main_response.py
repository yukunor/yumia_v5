import sys
import os
import json

# Add module path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from llm_client import generate_emotion_from_prompt_simple as estimate_emotion,
    generate_emotion_from_prompt_with_context, extract_emotion_summary
from module.response.response_index import load_and_categorize_index, extract_best_reference
from utils import logger

def load_emotion_by_date(path, target_date):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            if item.get("date") == target_date:
                return item
    except Exception as e:
        logger.warning(f"[WARN] 感情データ読込失敗: {path}, error={e}")
    return None

def run_response_pipeline(user_input: str) -> tuple[str, dict]:
    """Main pipeline for emotion-based response generation"""
    initial_emotion = {}
    reference_emotions = []

    try:
        print("✎ステップ①: 感情推定 開始")
        raw_response, initial_emotion = estimate_emotion(user_input)

        # Extract keywords from user input for matching
        keywords = extract_keywords_from_input(user_input)
        initial_emotion["keywords"] = keywords

        summary_str = ", ".join([f"{k}:{v}%" for k, v in initial_emotion.get("構成比", {}).items()])
        print(f"💭推定応答内容（raw）: {raw_response}")
        print(f"💞構成比（主感情: {initial_emotion.get('主感情', '未定義')}）: （構成比: {summary_str}）")
        print(f"🔍抽出キーワード: {keywords}")
        logger.info(f"[PIPELINE] 感情推定完了: 主感情={initial_emotion.get('主感情')}, キーワード={keywords}")
    except Exception as e:
        logger.error(f"[ERROR] 感情推定中にエラー発生: {e}")
        raise

    try:
        print("✎ステップ②: 感情インデックス分類 開始")
        categorized = load_and_categorize_index()
        logger.info("[PIPELINE] 感情インデックス分類完了")

        print("✎ステップ③: キーワード一致検索 開始")
        for category in ["long", "intermediate", "short"]:
            refer = extract_best_reference(initial_emotion, categorized.get(category, []), category)
            if refer:
                match_info = refer.get("match_info", "")
                full_emotion = load_emotion_by_date(refer["emotion"]["保存先"], refer["emotion"]["date"])
                if full_emotion:
                    reference_emotions.append({
                        "emotion": full_emotion,
                        "source": refer.get("source"),
                        "match_info": match_info,
                        "category": category
                    })
                    logger.info(f"[PIPELINE] 参照感情追加: {category}カテゴリ, 主感情={full_emotion.get('主感情')}, マッチ情報={match_info}")
        print(f"📌 キーワード一致による参照感情件数: {len(reference_emotions)}件")
        logger.info(f"[PIPELINE] 参照感情検索完了: {len(reference_emotions)}件の感情データを取得")
    except Exception as e:
        logger.error(f"[ERROR] キーワード一致処理中にエラー発生: {e}")
        raise

    try:
        if not reference_emotions:
            print("✎ステップ④: 一致なし → 仮応答を使用")
            final_response = raw_response
            response_emotion = initial_emotion
            logger.info("[PIPELINE] 参照感情なし: 初期応答を使用")
        else:
            print("✎ステップ④: 応答生成と感情再推定 開始")
            final_response, response_emotion = generate_emotion_from_prompt_with_context(
                user_input,
                [r["emotion"] for r in reference_emotions]
            )
            logger.info(f"[PIPELINE] 文脈応答生成完了: 主感情={response_emotion.get('主感情')}")
    except Exception as e:
        logger.error(f"[ERROR] GPT応答生成中にエラー発生: {e}")
        # Graceful fallback to initial response
        print("⚠️ 応答生成失敗 → 初期応答にフォールバック")
        final_response = raw_response
        response_emotion = initial_emotion
        logger.warning("[PIPELINE] 応答生成失敗: 初期応答を使用")

    try:
        print("✎ステップ⑤: 応答のサニタイズ 完了")
    except Exception as e:
        logger.warning(f"[WARN] 応答後処理に失敗: {e}")

    return final_response, response_emotion
