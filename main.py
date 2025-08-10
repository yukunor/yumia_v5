import sys
import os
import re
import requests
from fastapi import FastAPI, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

# モジュールパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), "module"))

# LLMは最終出力のときにだけ呼ぶ
from module.llm.llm_client import generate_emotion_from_prompt_with_context

from module.utils.utils import load_history, append_history, logger
from module.emotion.main_emotion import save_response_to_memory, write_structured_emotion_data
from module.emotion.emotion_stats import (
    load_current_emotion,
    merge_emotion_vectors,
    save_current_emotion,
    summarize_feeling,
)
# 検索はローカル抽出結果（構成比＋キーワード）をキーにする
from module.response.response_index import search_index_response, load_and_categorize_index, load_index
# ローカル抽出（NRCLex＋MeCab）
from module.emotion.local_emotion import generate_fallback_emotion_data

from module.response.main_response import collect_all_category_responses
from module.oblivion.oblivion_module import run_oblivion_cleanup_all
from module.voice.voice_processing import synthesize_voice

app = FastAPI()

class UserMessage(BaseModel):
    message: str

# 応答テキストから末尾のJSONブロックを除去（UI表示用）
def sanitize_output_for_display(text: str) -> str:
    pattern = r'({.*})'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return text.replace(matches[-1], '').strip()
    return text.strip()

@app.get("/")
def get_ui():
    return FileResponse("static/index.html")

@app.get("/history")
def get_history():
    try:
        return {"history": load_history()}
    except Exception:
        logger.exception("履歴取得中に例外が発生しました")
        raise HTTPException(status_code=500, detail="履歴の取得中にエラーが発生しました。")

@app.post("/chat")
async def chat(
    message: str = Form(...),
    background_tasks: BackgroundTasks | None = None
):
    logger.debug("✅ /chat エンドポイントに到達")
    logger.info("✅ debug() 実行済み")

    try:
        user_input = message
        logger.debug(f"📥 ユーザー入力取得完了: {user_input}")

        # 履歴追加（user）
        append_history("user", user_input)
        logger.debug("📝 ユーザー履歴追加完了")

        # 現在感情ロード（ログ用）
        current_emotion = load_current_emotion()
        logger.debug(f"🎯 [INFO] 現在感情ベクトル: {current_emotion}")

        # ローカル抽出：構成比＋キーワード
        status, emotion_data = generate_fallback_emotion_data(user_input)
        if status != "ok":
            logger.warning("⚠ ローカル感情抽出に失敗。空の構成比で続行")
            emotion_data = {"構成比": {}, "keywords": []}

        # 感情インデックス検索（MongoDB Atlas）
        response_text = ""
        best_match = search_index_response(
            emotion_structure={
                "構成比": emotion_data.get("構成比", {}),
                "keywords": emotion_data.get("keywords", [])
            }
        )

        if best_match:
            logger.info("[STEP] インデックスにマッチした応答を取得")
            response_text = best_match.get("応答", "")
            if response_text:
                append_history("assistant", response_text)
        else:
            # フォールバック：主要感情＋当日でカテゴリ別に探す
            from datetime import datetime as _dt
            dominant_emotion = next(iter(emotion_data.get("構成比", {})), None)
            if dominant_emotion:
                today = _dt.now().strftime("%Y-%m-%d")
                matched = collect_all_category_responses(
                    emotion_name=dominant_emotion,
                    date_str=today
                )
                for cat in ["short", "intermediate", "long"]:
                    if matched.get(cat):
                        response_text = matched[cat].get("応答", "")
                        logger.info(f"[STEP] 履歴から {cat} カテゴリの応答を返却")
                        if response_text:
                            append_history("assistant", response_text)
                        break

            if not response_text:
                logger.warning("[WARN] 履歴にも一致する応答が見つかりませんでした")
                response_text = "ごめんなさい、うまく思い出せませんでした。"
                append_history("assistant", response_text)

        # 最終応答：感情構成比と参照を踏まえて生成（ここで初めてLLMを呼ぶ）
        final_response, final_emotion = generate_emotion_from_prompt_with_context(
            user_input=user_input,
            emotion_structure=emotion_data.get("構成比", {}),  # ←検索用の軽量構成比をそのまま渡す
            best_match=best_match
        )
        append_history("assistant", final_response)

        # 音声合成（VoiceVox）
        voice_settings = final_emotion.get("voicevox_settings")
        if voice_settings:
            audio_binary = synthesize_voice(final_response, voice_settings)
            with open("output.wav", "wb") as f:
                f.write(audio_binary)

        # 構造データ抽出・保存（最終応答に対して）
        parsed_emotion_data = save_response_to_memory(final_response)
        if parsed_emotion_data:
            write_structured_emotion_data(parsed_emotion_data)
            emotion_to_merge = parsed_emotion_data.get("構成比", final_emotion)
        else:
            logger.warning("⚠ 構造データ抽出失敗 → 直接生成した感情構成比を使用")
            emotion_to_merge = final_emotion

        # 現在感情の更新
        latest_emotion = load_current_emotion()
        merged_emotion = merge_emotion_vectors(
            current=latest_emotion,
            new=emotion_to_merge,
            weight_new=0.3,
            decay_factor=0.9,
            normalize=True
        )
        save_current_emotion(merged_emotion)
        summary = summarize_feeling(merged_emotion)

        # 背景で忘却処理
        if background_tasks:
            background_tasks.add_task(process_and_cleanup_emotion_data, final_response)

        visible_response = sanitize_output_for_display(final_response)

        return {
            "response": visible_response,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"❌ エラー発生: {e}")
        return PlainTextResponse("エラーが発生しました。", status_code=500)

def store_emotion_structured_data(response_text: str):
    logger.info("🧩 store_emotion_structured_data() が呼び出されました")
    parsed_emotion_data = save_response_to_memory(response_text)
    if parsed_emotion_data:
        write_structured_emotion_data(parsed_emotion_data)
    else:
        logger.warning("⚠ 背景タスク：構造データの抽出に失敗したため、保存をスキップ")

def process_and_cleanup_emotion_data(response_text: str):
    logger.info("🔄 感情データの保存と忘却処理を開始します")
    store_emotion_structured_data(response_text)
    logger.info("🧹 感情データ保存後、忘却処理を実行します")
    run_oblivion_cleanup_all()
    logger.info("✅ 感情データ保存＋忘却処理 完了")

# 起動時のチェック処理
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 システム起動チェック開始")
    try:
        resp = requests.get("http://localhost:50021/speakers")
        resp.raise_for_status()
        logger.info("🔈 VoiceVoxエンジンに接続成功")
    except Exception as e:
        logger.warning(f"⚠️ VoiceVoxエンジンに接続できませんでした: {e}")
    logger.info("✅ 起動前チェック完了")
