import sys
import os
import re
import traceback

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.responses import FileResponse, JSONResponse

# モジュールパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), "module"))

from utils import append_history, load_history, logger
from module.response.main_response import run_response_pipeline
import module.memory.main_memory as memory
from llm_client import extract_emotion_summary
from module.memory.index_emotion import extract_personality_tendency
from module.file_handler.file_router import handle_uploaded_file

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
    file: UploadFile = File(None)
):
    logger.debug("✅ /chat エンドポイントに到達")
    try:
        user_input = message
        logger.debug(f"📥 ユーザー入力取得完了: {user_input}")

        if file:
            logger.debug(f"📎 添付ファイル名: {file.filename}")
            extracted_text = await handle_uploaded_file(file)  # ファイル処理呼び出し
            if extracted_text:
                user_input += f"\n\n[添付ファイルの内容]:\n{extracted_text}"

        append_history("user", user_input)
        logger.debug("📝 ユーザー履歴追加完了")

        logger.debug("🔍 応答生成と感情推定 開始")
        response, emotion_data = run_response_pipeline(user_input)
        logger.debug("✅ 応答と感情データ取得 完了")

        logger.info(f"🧾 取得した感情データの内容: {emotion_data}")
        # LLMによる応答生成と感情構造抽出
        # 実体は module/llm/llm_client.py の generate_emotion_from_prompt_with_context() を呼び出す
        summary = extract_emotion_summary(emotion_data, emotion_data.get("主感情", "未定義"))
        logger.info(f"📊 構成比サマリ: {summary}")

        logger.debug("💬 最終応答内容（そのまま表示）:")
        logger.debug(f"💭{response}")
        cleaned = summary.replace(f"（主感情: {emotion_data.get('主感情')}｜構成比: ", "").rstrip("）")
        logger.debug(f"💞構成比（主感情: {emotion_data.get('主感情')}）: {cleaned}")

        append_history("system", response)
        logger.debug("📝 応答履歴追加完了")

        logger.debug("💾 感情保存処理（同期実行）開始")
        memory.handle_emotion(emotion_data)

        logger.debug("🧠 人格傾向の抽出 開始")
        tendency = extract_personality_tendency()
        logger.debug(f"🧭 現在人格傾向: {tendency}")

        logger.debug("📤 応答と履歴を返却")
        return JSONResponse(content={
            "message": response,
            "history": load_history(),
            "personality_tendency": tendency
        })

    except Exception as e:
        logger.error(f"[ERROR] /chat エンドポイントで例外発生: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
