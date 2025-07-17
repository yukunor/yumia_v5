import os
import pymongo
from bson.objectid import ObjectId

# MongoDB接続設定
MONGO_URL = os.environ.get("MONGODB_URI")
if not MONGO_URL:
    raise EnvironmentError("環境変数 'MONGODB_URI' が設定されていません")

DB_NAME = "emotion_db"
COLLECTION_NAME = "emotion_data"

client = pymongo.MongoClient(MONGO_URL)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
print("[DEBUG] MongoDB Atlas接続成功")

# 件数確認
count = 0
docs = list(collection.find({"category": "long"}))
print(f"[DEBUG] 該当ドキュメント数: {len(docs)}")

for doc in docs:
    _id = doc.get("_id")
    emotion = doc.get("emotion")
    data = doc.get("data")

    if isinstance(data, list):
        count += 1
        print(f"[対象] _id: {_id} | emotion: {emotion} | data形式: list → dictに変換")

        new_data = {"履歴": data}
        new_doc = doc.copy()
        new_doc["data"] = new_data
        new_doc["_id"] = ObjectId()  # 新しいIDを割り振る

        try:
            insert_result = collection.insert_one(new_doc)
            print(f"[完了] {_id} → 新ID: {insert_result.inserted_id} に移行完了")

        except Exception as e:
            print(f"[ERROR] {_id} | 例外発生: {e}")
    else:
        print(f"[スキップ] _id: {_id} | data形式: {type(data)}")

print(f"[結果] 修正済み件数: {count}")
