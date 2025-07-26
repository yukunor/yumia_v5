import sys
import os
import re
import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel


# モジュールパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), "module"))
from module.llm.llm_client import generate_emotion_from_prompt_with_context
from module.utils.utils import load_history, append_history
from module.utils.utils import logger
from module.emotion.main_emotion import save_response_to_memory
from module.emotion.emotion_stats import summarize_feeling
from module.llm.llm_client import run_emotion_update_pipeline
from module.emotion.emotion_stats import load_current_emotion
from module.response.main_responce import find_response_by_emotion, get_best_match, collect_all_category_responses

import inspect
print(f"📌 loggerの型（main.py）: {type(logger)}")
print(f"📌 logger 定義ファイル: {inspect.getfile(logger.__class__)}")

app = FastAPI()

class UserMessage(BaseModel):
    message: str

def sanitize_output_for_display(text: str) -> str:
    text = re.sub(r"
json\s*\{.*?\}\s*
", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\s*\"date\"\s*:\s*\".*?\".*?\"keywords\"\s*:\s*\[.*?\]\s*\}", "", text, flags=re.DOTALL)
    return text.strip()

@app.get("/")
def get_ui():
    return FileResponse("static/index.html")

@app.get("/history")
#過去履歴をチャット欄に呼び出し
def get_history():
    try:
        return {"history": load_history()}
    except Exception as e:
        logger.exception("履歴取得中に例外が発生しました")
        raise HTTPException(status_code=500, detail="履歴の取得中にエラーが発生しました。")

@app.post("/chat")
async def chat(message: str = Form(...), file: UploadFile = File(None), background_tasks: BackgroundTasks = None):
    #①エンドポイントに到達
    logger.info(f"📌 loggerの型: {type(logger)}")
    logger.debug("✅ /chat エンドポイントに到達")
    logger.info("✅ debug() 実行済み", flush=True)

    try:
        user_input = message
        logger.debug(f"📥 ユーザー入力取得完了: {user_input}")

        # 🔸 添付ファイルの内容を抽出し user_input に追加
        if file:
            logger.debug(f"📎 添付ファイル名: {file.filename}")
            extracted_text = await handle_uploaded_file(file)
            if extracted_text:
                user_input += f"\n\n[添付ファイルの内容]:\n{extracted_text}"

         # 🔸 履歴に保存
        append_history("user", user_input)
        logger.debug("📝 ユーザー履歴追加完了")

        # 🔸 ②現在感情をロード
        # 🔸  MongoDBからインデックス取得
        index_data = load_index()
        # 🔸  現在感情ベクトルの読み込み
        current_emotion = load_current_emotion()
        logger.debug(f"🎯 [INFO] 現在感情ベクトル: {current_emotion}")

        #llm呼び出し（1回目)
        response_text = generate_gpt_response_from_history()
        print(f"📨 GPT応答:\n{response_text}")

        # 🔸 ③ 応答がJSON形式か判定し、構成比とキーワード抽出
        emotion_data = find_response_by_emotion()

        if emotion_data["type"] == "extracted":
            logger.info("[STEP] GPT応答から構成比とキーワードを取得済")

            # 🔸 ④ インデックスからベストマッチ検索
            best_match = get_best_match(emotion_data)

            if best_match:
                logger.info("[STEP] インデックスにマッチした応答を取得")
                append_history("assistant", best_match.get("応答", ""))
                return {"response": best_match.get("応答", "")}

            else:
                # 🔸 ⑤ マッチがなければ履歴を検索
                from datetime import datetime
                dominant_emotion = next(iter(emotion_data["構成比"]), None)

                if dominant_emotion:
                    today = datetime.now().strftime("%Y-%m-%d")
                    matched = collect_all_category_responses(
                        emotion_name=dominant_emotion,
                        date_str=today
                    )

                    # 優先順位で応答候補を返す（short > intermediate > long）
                    for cat in ["short", "intermediate", "long"]:
                        if matched.get(cat):
                            reply = matched[cat].get("応答", "")
                            logger.info(f"[STEP] 履歴から {cat} カテゴリの応答を返却")
                            append_history("assistant", reply)
                            return {"response": reply}

                logger.warning("[WARN] 履歴にも一致する応答が見つかりませんでした")
                fallback_message = "ごめんなさい、うまく思い出せませんでした。"
                append_history("assistant", fallback_message)
                return {"response": fallback_message}

        else:
            # JSONでない（text出力）の場合、文字列として扱う
            logger.info("[STEP] GPT応答が構造化されていないため、生の応答を返却")
            append_history("assistant", response_text)
            return {"response": response_text}

        #🔸llm呼び出し(2回目)
        final_response, final_emotion = generate_emotion_from_prompt_with_context(
            user_input=user_input,
            emotion_structure=emotion_data.get("構成比", {}),
            best_match=get_best_match(emotion_data)
        )

        append_history("assistant", final_response)
        return {"response": final_response}
        

        # 🔸 感情構成比の抽出と保存・サマリー処理
        composition = emotion_data.get("構成比", {})
        update_message, summary = run_emotion_update_pipeline(composition)

        # 🔸 ログ出力（6感情サマリー）
        if summary:
            logger.info("🧠 感情サマリー:")
            for k, v in summary.items():
                logger.info(f"  {k}: {v}")

        return {"response": response_text, "summary": summary}

    except Exception as e:
        logger.error(f"❌ エラー発生: {e}")
        return PlainTextResponse("エラーが発生しました。", status_code=500)
