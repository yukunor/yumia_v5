import jsonlines
from pymongo import MongoClient
import os

# MongoDB接続URI（Renderなどの環境変数に事前設定）
MONGODB_URI = os.environ.get("MONGODB_URI")

# MongoDBへ接続
client = MongoClient(MONGODB_URI)
db = client["emotion_db"]
collection = db["dialogue_history"]

# 対象ファイルのパス
file_path = "dialogue_history.jsonl"

# JSONLファイルを読み込んでリスト化
with jsonlines.open(file_path) as reader:
    data = list(reader)

# データが存在すればMongoDBに挿入
if data:
    result = collection.insert_many(data)
    print(f"✅ {len(result.inserted_ids)} 件のドキュメントを挿入しました。")
else:
    print("⚠️ データが見つかりませんでした。")
