import jsonlines
from pymongo import MongoClient
import os

# MongoDB接続URI（環境変数から取得）
MONGODB_URI = os.environ.get("MONGODB_URI")

# MongoDB接続（SRV形式 + TLS対策）
client = MongoClient(MONGODB_URI, tlsAllowInvalidCertificates=True)
db = client["emotion_db"]
collection = db["dialogue_history"]

# JSONLファイルからデータを読み込む
file_path = "dialogue_history.jsonl"
with jsonlines.open(file_path) as reader:
    data = list(reader)

# データが存在すれば一括挿入
if data:
    result = collection.insert_many(data)
    print(f"✅ {len(result.inserted_ids)} 件のドキュメントを挿入しました。")
else:
    print("⚠️ データが見つかりませんでした。")
