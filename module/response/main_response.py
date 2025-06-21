from llm_client import generate_emotion_from_prompt as estimate_emotion
from response.response_index import search_similar_emotions
from response.response_long import match_long_keywords
from response.response_intermediate import match_intermediate_keywords
from response.response_short import match_short_keywords
from llm_client import generate_gpt_response
from utils import logger  # ロガーのインポート
import time

def run_response_pipeline(user_input: str) -> tuple[str, dict]:
    now_emotion = {}
    main_emotion = "未定義"

    try:
        logger.info("[TIMER] ▼ ステップ① 感情推定 開始")
        print("🧐 ステップ①: 感情推定 開始")
        t1 = time.time()
        response_text, emotion_data = estimate_emotion(user_input)
        print("🧐 感情推定結果:", emotion_data)
        logger.info(f"[TIMER] ▲ ステップ① 感情推定 完了: {time.time() - t1:.2f}秒")

        if not isinstance(emotion_data, dict):
            logger.error(f"[ERROR] estimate_emotionの戻り値が辞書形式ではありません: {type(emotion_data)} - {emotion_data}")
            emotion_data = {}

        now_emotion = emotion_data
        main_emotion = now_emotion.get("主感情", "未定義")
        logger.debug(f"[DEBUG] 推定された主感情: {main_emotion}")
        logger.info("[INFO] 感情推定完了")

    except Exception as e:
        logger.error(f"[ERROR] 感情推定中にエラー発生: {e}")
        raise

    try:
        logger.info("[TIMER] ▼ ステップ② 類似感情検索 開始")
        print("🔍 ステップ②: 類似感情検索 開始")
        t2 = time.time()
        logger.info(f"[検索] 主感情一致かつ構成比類似の候補を抽出中... 現在の主感情: {main_emotion}")
        top30_emotions = search_similar_emotions(now_emotion)
        logger.info(f"[TIMER] ▲ ステップ② 類似感情検索 完了: {time.time() - t2:.2f}秒")

        logger.info(f"[検索結果] long: {len(top30_emotions.get('long', []))}件, intermediate: {len(top30_emotions.get('intermediate', []))}件, short: {len(top30_emotions.get('short', []))}件")

        logger.info("[TIMER] ▼ ステップ③ キーワードマッチ 開始")
        print("🤩 ステップ③: キーワードマッチング 開始")
        t3 = time.time()
        long_matches = match_long_keywords(now_emotion, top30_emotions.get("long", []))
        intermediate_matches = match_intermediate_keywords(now_emotion, top30_emotions.get("intermediate", []))
        short_matches = match_short_keywords(now_emotion, top30_emotions.get("short", []))
        logger.info(f"[TIMER] ▲ ステップ③ キーワードマッチ 完了: {time.time() - t3:.2f}秒")

        reference_emotions = long_matches + intermediate_matches + short_matches

        if not reference_emotions:
            logger.info(f"[参照なし] 主感情「{main_emotion}」に類似した感情データは見つかりませんでした。")
        else:
            logger.info(f"[参照あり] 主感情「{main_emotion}」に対し、{len(reference_emotions)} 件の類似感情データを参照します。")

    except Exception as e:
        logger.error(f"[ERROR] 類似感情検索中にエラー発生: {e}")
        raise

    try:
        logger.info("[TIMER] ▼ ステップ④ GPT応答生成 開始")
        print("💬 ステップ④: GPT応答生成 開始")
        t4 = time.time()
        response = generate_gpt_response(user_input, reference_emotions)
        print("📨 生成された返信:", response)
        logger.info(f"[TIMER] ▲ ステップ④ GPT応答生成 完了: {time.time() - t4:.2f}秒")
        logger.info("[INFO] GPT応答生成完了")

    except Exception as e:
        logger.error(f"[ERROR] GPT応答生成中にエラー発生: {e}")
        raise

    print("📎 保存対象の感情データ:", now_emotion)
    return response, now_emotion
