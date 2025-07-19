import sys
import os
import re
import traceback

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse

# モジュールパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), "module"))

from utils import append_history, load_history
from module.response.main_response import run_response_pipeline
import module.memory.main_memory as memory
from utils import logger
from llm_client import extract_emotion_summary
from module.memory.index_emotion import extract_personality_tendency

app = FastAPI()

class UserMessage(BaseModel):
    message: str

def sanitize_output_for_display(text: str) -> str:
    text = re.sub(r"```json\s*\{.*?\}\s*```", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\s*\"date\"\s*:\s*\".*?\".*?\"keywords\"\s*:\s*\[.*?\]\s*\}", "", text, flags=re.DOTALL)
    return text.strip()

@app.post("/chat")
def chat(user_message: UserMessage):
    print("✅ /chat エンドポイントに到達")
    try:
        user_input = user_message.message
        print("📥 ユーザー入力取得完了:", user_input)

        append_history("user", user_input)
        print("📝 ユーザー履歴追加完了")

        print("🔍 応答生成と感情推定 開始")
        response, emotion_data = run_response_pipeline(user_input)
        print("✅ 応答と感情データ取得 完了")

        #print("🧾 取得した感情データの内容:", emotion_data)
        #summary = extract_emotion_summary(emotion_data, emotion_data.get("主感情", "未定義"))
        #print("📊 構成比サマリ:", summary)

        #print("🧼 応答のサニタイズ 開始")
        #sanitized_response = sanitize_output_for_display(response)
        #print("✅ サニタイズ完了:", sanitized_response)

        print("💬 最終応答内容（再掲）:")
        print(f"💭{sanitized_response}")
        cleaned = summary.replace(f"（主感情: {emotion_data.get('主感情')}｜構成比: ", "").rstrip("）")
        print(f"💞構成比（主感情: {emotion_data.get('主感情')}）: {cleaned}")

        append_history("system", sanitized_response)
        print("📝 応答履歴追加完了")

        print("💾 感情保存処理（同期実行）開始")
        memory.handle_emotion(emotion_data)

        print("🧠 人格傾向の抽出 開始")
        tendency = extract_personality_tendency()
        print("🧭 現在人格傾向:", tendency)

        print("📤 応答と履歴を返却")
        return {
            "message": sanitized_response,
            "history": load_history(),
            "personality_tendency": tendency
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
