
from pymongo import MongoClient
import certifi

uri = "mongodb+srv://noriyukikondo99:Aa1192296!@cluster0.oe0tni1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, tlsCAFile=certifi.where())

try:
    print(client.list_database_names())  # データベース一覧を取得
    print("✅ MongoDB Atlas への接続成功")
except Exception as e:
    print("❌ 接続失敗:", e)
