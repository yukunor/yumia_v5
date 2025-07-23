import sys
import os
import re
import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


# モジュールパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), "module"))
from module.llm.llm_client import generate_emotion_from_prompt_with_context
from module.utils.utils import load_history, logger, append_history
from module.emotion.main_memory import save_response_to_memory



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
    background_tasks: BackgroundTasks = None  # ← 追加
):
    logger.debug("✅ /chat エンドポイントに到達")
    try:
        user_input = message
        logger.debug(f"📥 ユーザー入力取得完了: {user_input}")

        if file:
            logger.debug(f"📎 添付ファイル名: {file.filename}")
            extracted_text = await handle_uploaded_file(file)
            if extracted_text:
                user_input += f"\n\n[添付ファイルの内容]:\n{extracted_text}"

        append_history("user", user_input)
        logger.debug("📝 ユーザー履歴追加完了")

        # 応答生成
        response = await run_response_pipeline(user_input)
        logger.debug("🧾 応答生成完了")

        # 応答後にバックグラウンドで保存
        background_tasks.add_task(save_response_to_memory, response)

        return PlainTextResponse(response)

    except Exception as e:
        logger.error(f"❌ エラー発生: {e}")
        return PlainTextResponse("エラーが発生しました。", status_code=500)
