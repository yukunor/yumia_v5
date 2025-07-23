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

import inspect
print(f"📌 loggerの型（main.py）: {type(logger)}")
print(f"📌 logger 定義ファイル: {inspect.getfile(logger.__class__)}")

app = FastAPI()

class UserMessage(BaseModel):
    message: str

def sanitize_output_for_display(text: str) -> str:
    text = re.sub(r"```json\s*\{.*?\}\s*```", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\s*\"date\"\s*:\s*\".*?\".*?\"keywords\"\s*:\s*\[.*?\]\s*\}", "", text, flags=re.DOTALL)
    return text.strip()

@app.get("/")
def get_ui():
    return FileResponse("static/index.html")

@app.get("/history")
def get_history():
    try:
        return {"history": load_history()}
    except Exception as e:
        logger.exception("履歴取得中に例外が発生しました")
        raise HTTPException(status_code=500, detail="履歴の取得中にエラーが発生しました。")

@app.post("/chat")
async def chat(
    message: str = Form(...),
    file: UploadFile = File(None),
    background_tasks: BackgroundTasks = None
):
    print(f"📌 loggerの型: {type(logger)}")
    logger.debug("✅ /chat エンドポイントに到達")
    print("✅ debug() 実行済み", flush=True)

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

        # 🔸 感情推定と応答生成
        response_text, emotion_data = generate_emotion_from_prompt_with_context(user_input)
        logger.debug("🧾 応答生成完了")

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
