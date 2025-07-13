import os
from pymongo import MongoClient
from dotenv import load_dotenv

# .env がある場合は読み込み（Render では不要）
load_dotenv()

# 環境変数から MongoDB URI を取得
mongo_uri = os.environ.get("MONGODB_URI")

# MongoDB に接続
client = MongoClient(mongo_uri)

# 確認用：データベース一覧を表示
try:
    db_list = client.list_database_names()
    print("✅ 接続成功！データベース一覧:", db_list)
except Exception as e:
    print("❌ 接続エラー:", e)
