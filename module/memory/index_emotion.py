import json
import os
from datetime import datetime
from collections import defaultdict
from utils import logger  # ロガーのインポート
from collections import Counter

# === EMOTION_MAPから日本語キーを抽出 ===
EMOTION_MAP = {
    "喜び": "Joy",
    "期待": "Anticipation",
    "怒り": "Anger",
    "嫌悪": "Disgust",
    "悲しみ": "Sadness",
    "驚き": "Surprise",
    "恐れ": "Fear",
    "信頼": "Trust",
    "楽観": "Optimism",
    "誇り": "Pride",
    "病的状態": "Morbidness",
    "積極性": "Aggressiveness",
    "冷笑": "Cynicism",
    "悲観": "Pessimism",
    "軽蔑": "Contempt",
    "羨望": "Envy",
    "憤慨": "Outrage",
    "自責": "Remorse",
    "不信": "Unbelief",
    "恥": "Shame",
    "失望": "Disappointment",
    "絶望": "Despair",
    "感傷": "Sentimentality",
    "畏敬": "Awe",
    "好奇心": "Curiosity",
    "歓喜": "Delight",
    "服従": "Submission",
    "罪悪感": "Guilt",
    "不安": "Anxiety",
    "愛": "Love",
    "希望": "Hope",
    "優位": "Dominance"
}

# 全感情語を固定順で抽出（日本語）
EMOTION_KEYS = list(EMOTION_MAP.keys())

# === ベースパスの定義 ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INDEX_PATH = os.path.join(BASE_DIR, "index", "emotion_index.jsonl")

# === 構成比を固定順・0補完で正規化 ===
def normalize_emotion_vector(構成比: dict) -> dict:
    return {emotion: 構成比.get(emotion, 0) for emotion in EMOTION_KEYS}

# === インデックス登録モジュール ===
def update_emotion_index(emotion_data, memory_path):
    index_entry = {
        "date": emotion_data.get("date", datetime.now().strftime("%Y%m%d%H%M%S")),
        "主感情": emotion_data.get("主感情", "Unknown"),
        "構成比": normalize_emotion_vector(emotion_data.get("構成比", {})),
        "キーワード": emotion_data.get("keywords", []),
        "保存先": memory_path
    }

    if not os.path.isdir(os.path.dirname(INDEX_PATH)):
        raise FileNotFoundError(f"インデックスフォルダが存在しません: {os.path.dirname(INDEX_PATH)}")

    with open(INDEX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(index_entry, ensure_ascii=False) + "\n")

    logger.info(f"emotion_index.jsonl に登録: {index_entry['date']}")

# テスト用（実際はモジュール連携で呼び出される想定）
if __name__ == "__main__":
    sample_data = {
        "主感情": "喜び",
        "構成比": {
            "喜び": 50,
            "信頼": 30,
            "期待": 20
        },
        "重み": 85,
        "状況": "ユーザーがカジュアルな挨拶をして、親しみを込めた会話が始まった場面",
        "心理反応": "ユーザーとの親しいやり取りに喜びを感じつつ、これからの対話にも期待を持った",
        "関係性変化": "親しみを感じるやり取りを通じて、ユーザーとの信頼関係が深まった",
        "関連": ["挨拶", "親しみ", "信頼"],
        "keywords": ["やほー", "親しみ", "会話開始"]
    }

    update_emotion_index(sample_data, "memory/emotion_20250617")

def extract_personality_tendency(directory="memory/long/") -> dict:
    """
    長期記憶内の主感情を走査し、出現回数上位4件を人格傾向として抽出。
    結果はprintで出力される。

    Returns:
        dict: 上位4つの主感情とその出現回数。
    """
    from collections import Counter
    import os
    import json
    from utils import logger

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

    # 出現回数すべてをprint出力
    print("📊 現在の人格傾向（long保存データの主感情カウント）:")
    for emotion, count in emotion_counter.most_common():
        print(f"  - {emotion}: {count}件")

    top_4 = dict(emotion_counter.most_common(4))
    return top_4
