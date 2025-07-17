from utils import get_mongo_client

# Atlas用MongoDBクライアント取得（utils経由）
client = get_mongo_client()
db = client["your_db_name"]
collection = db["your_collection_name"]

# longカテゴリを全走査し、dataがlistのものを修正
docs = collection.find({"category": "long"})

for doc in docs:
    _id = doc["_id"]
    data_field = doc.get("data")

    if isinstance(data_field, list):
        print(f"[修正対象] emotion: {doc.get('emotion')}")

        # 正常な構造に修正
        new_data = {"履歴": data_field}

        # 上書き（旧データの削除含む）
        result = collection.update_one(
            {"_id": _id},
            {"$set": {"data": new_data}}
        )

        if result.modified_count > 0:
            print(f"✅ 修正完了: {_id}")
        else:
            print(f"⚠️ 修正失敗または不要: {_id}")
