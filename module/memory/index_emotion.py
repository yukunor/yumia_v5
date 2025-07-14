import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from utils import logger  # ロガーのインポート
from pymongo import MongoClient
import certifi

# === EMOTION_MAPから日本語キーを抽出 ===
EMOTION_MAP = {
    "喜び": "Joy", "期待": "Anticipation", "怒り": "Anger", "嫌悪": "Disgust",
    "悲しみ": "Sadness", "驚き": "Surprise", "恐れ": "Fear", "信頼": "Trust",
    "楽観": "Optimism", "誇り": "Pride", "病的状態": "Morbidness", "積極性": "Aggressiveness",
    "冷笑": "Cynicism", "悲観": "Pessimism", "軽蔑": "Contempt", "羨望": "Envy",
    "憤慨": "Outrage", "自責": "Remorse", "不信": "Unbelief", "恥": "Shame",
    "失望": "Disappointment", "絶望": "Despair", "感傷": "Sentimentality", "畏敬": "Awe",
    "好奇心": "Curiosity", "歓喜": "Delight", "服従": "Submission", "罪悪感": "Guilt",
    "不安": "Anxiety", "愛": "Love", "希望": "Hope", "優位": "Dominance"
}

# 全感情語を固定順で抽出（日本語）
EMOTION_KEYS = list(EMOTION_MAP.keys())

# === 感情カテゴリ分類 ===
def get_memory_category(weight):
    if weight >= 95:
        return "long"
    elif weight >= 80:
        return "intermediate"
    else:
        return "short"

# === 構成比を固定順・0補完で正規化 ===
def normalize_emotion_vector(構成比: dict) -> dict:
    return {emotion: 構成比.get(emotion, 0) for emotion in EMOTION_KEYS}

# === MongoDBへのインデックス保存 ===
def update_emotion_index(emotion_data, memory_path):
    print("📥 MongoDBへのインデックス保存を開始します...")
    try:
        uri = "mongodb+srv://noriyukikondo99:Aa1192296%21@cluster0.oe0tni1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(uri, tlsCAFile=certifi.where())
        db = client["emotion_db"]
        collection = db["emotion_index"]

        index_entry = {
            "date": emotion_data.get("date", datetime.now().strftime("%Y%m%d%H%M%S")),
            "主感情": emotion_data.get("主感情", "Unknown"),
            "構成比": normalize_emotion_vector(emotion_data.get("構成比", {})),
            "キーワード": emotion_data.get("keywords", []),
            "emotion": EMOTION_MAP.get(emotion_data.get("主感情"), "Unknown"),
            "category": get_memory_category(emotion_data.get("重み", 0))
        }

        collection.insert_one(index_entry)
        print(f"[✅] MongoDBにemotion_indexを登録しました: {index_entry['date']}")
        logger.info(f"[MongoDB] emotion_index に登録: {index_entry['date']}")
    except Exception as e:
        print(f"[❌] MongoDB登録エラー: {e}")
        logger.error(f"[ERROR] MongoDB登録失敗: {e}")

# === 人格傾向抽出 ===
def extract_personality_tendency(directory="memory/long/") -> dict:
    emotion_counter = Counter()
    for filename in os.listdir(directory):
        if not filename.endswith(".json"):
            continue
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get("データ種別") == "emotion":
                    main_emotion = data.get("主感情")
                    if main_emotion:
                        emotion_counter[main_emotion] += 1
                elif isinstance(data, dict) and "履歴" in data:
                    for item in data["履歴"]:
                        main_emotion = item.get("主感情")
                        if main_emotion:
                            emotion_counter[main_emotion] += 1
        except Exception as e:
            logger.warning(f"[WARN] 人格傾向データ読み込み失敗（無視）: {file_path} | {e}")

    print("📊 現在の人格傾向（long保存データの主感情カウント）:")
    for emotion, count in emotion_counter.most_common():
        print(f"  - {emotion}: {count}件")

    return dict(emotion_counter.most_common(4))
