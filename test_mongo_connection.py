from fastapi import FastAPI
from pymongo import MongoClient
import os

app = FastAPI()

MONGODB_URI = os.environ.get("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["emotion_db"]

@app.get("/mongo-test")
def mongo_test():
    try:
        collections = db.list_collection_names()
        return {"status": "✅ 接続成功", "collections": collections}
    except Exception as e:
        return {"status": "❌ 接続失敗", "error": str(e)}
