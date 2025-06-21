import sys
import os
import re
import threading
import traceback

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse

sys.path.append(os.path.join(os.path.dirname(__file__), "module"))

from utils import append_history, load_history
from module.response.main_response import run_response_pipeline
import module.memory.main_memory as memory
from utils import logger

app = FastAPI()

class UserMessage(BaseModel):
    message: str

def sanitize_output_for_display(text: str) -> str:
    # JSONコードブロックだけを削除（emotion_summaryには触れない）
    text = re.sub(r"```json\s*\{.*?\}\s*```", "", text, flags=re.DOTALL)
    return text.strip()

@app.post("/chat")
def chat(user_message: UserMessage):
    print("✅ /chat エンドポイントに到達")
    try:
        user_input = user_message.message
        print("✅ ユーザー入力:", user_input)

        append_history("user", user_input)
        print("✅ ユーザー履歴追加完了")

        response, emotion_data = run_response_pipeline(user_input)
        print("✅ 応答生成完了")

        sanitized_response = sanitize_output_for_display(response)
        append_history("system", sanitized_response)
        print("✅ 応答履歴追加完了")

        threading.Thread(target=memory.handle_emotion, args=(emotion_data,)).start()
        print("✅ 感情保存スレッド開始")

        return {
            "message": sanitized_response,
            "history": load_history()
        }

    except Exception as e:
        print("❌ 例外発生:", traceback.format_exc())
        logger.exception("チャット中に例外が発生しました")
        raise HTTPException(status_code=500, detail="チャット中にエラーが発生しました。")

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


