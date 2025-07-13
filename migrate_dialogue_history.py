import jsonlines
from pymongo import MongoClient
import os

# MongoDB接続URI（環境変数から取得）
MONGODB_URI = os.environ.get("MONGODB_URI")

# MongoDB接続
client = MongoClient(MONGODB_URI)
db = client["emotion_db"]
collection = db["dialogue_history"]

# ファイル読み込み＆MongoDBへ一括挿入
file_path = "dialogue_history.jsonl"

with jsonlines.open(file_path) as reader:
    data = list(reader)

if data:
    result = collection.insert_many(data)
    print(f"✅ {len(result.inserted_ids)} 件のドキュメントを挿入しました。")
else:
    print("⚠️ データが見つかりませんでした。")
