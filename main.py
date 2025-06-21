import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "module"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
import threading

from utils import append_history, load_history
from module.response.main_response import run_response_pipeline
import module.memory.main_memory as memory  # memory形式で保存（関数名を指定しない）
from utils import logger  # utils/logger.py のロガーを使用

# FastAPIアプリケーション
app = FastAPI()

# ユーザーからの入力スキーマ
class UserMessage(BaseModel):
    message: str

# チャットエンドポイント（responseモード）
@app.post("/chat")
def chat(user_message: UserMessage):
    try:
        user_input = user_message.message

        # ステップ①：ユーザー発話を履歴に追加
        append_history("user", user_input)

        # ステップ②：感情推定＋応答生成（response系）
        append_history("system", response_text)

        # ステップ③：応答を履歴に追加
        append_history("system", response["response_text"])

        # ステップ④：感情保存を非同期実行（保存失敗しても応答は返す）
        threading.Thread(target=memory.handle_emotion, args=(emotion_data,)).start()

        # ステップ⑤：応答と履歴を返す
        return {
            "message": response,
            "history": load_history()
        }

    except Exception as e:
        logger.error(f"チャットエラー: {e}")
        raise HTTPException(status_code=500, detail="チャット中にエラーが発生しました。")

# UI配信用エンドポイント
@app.get("/")
def get_ui():
    return FileResponse("static/index.html")

# 履歴取得エンドポイント（初期ロードなどに使用）
@app.get("/history")
def get_history():
    try:
        return {"history": load_history()}
    except Exception as e:
        logger.error(f"履歴取得エラー: {e}")
        raise HTTPException(status_code=500, detail="履歴の取得中にエラーが発生しました。")
