import os
import json
from datetime import datetime
from .divide_emotion import divide_and_store
from .index_emotion import update_emotion_index
from utils import logger  # ロガーのインポート

# 全32感情リスト
ALL_EMOTIONS = [
    "喜び", "期待", "怒り", "嫌悪", "悲しみ", "驚き", "恐れ", "信頼", "楽観", "誇り",
    "病的状態", "積極性", "冷笑", "悲観", "軽蔑", "羨望", "憤慨", "自責", "不信", "恥",
    "失望", "絶望", "感傷", "畏敬", "好奇心", "歓喜", "服従", "罪悪感", "不安", "愛", "希望", "優位"
]

# BASE_DIR はリポジトリのルートに設定する
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INDEX_PATH = os.path.join(BASE_DIR, "index", "emotion_index.jsonl")
DATASET_PATH = os.path.join(BASE_DIR, "dataset_emotion.jsonl")
HISTORY_PATH = os.path.join(BASE_DIR, "emotion_history.jsonl")
index_dir = os.path.dirname(INDEX_PATH)

# ディレクトリ存在チェック
logger.debug(f"[DEBUG] index_dir = {index_dir}")
if not index_dir.endswith(os.path.join("index")):
    logger.warning(f"[WARNING] 不正な保存先候補: {index_dir}")
if not os.path.exists(index_dir):
    raise FileNotFoundError(f"[エラー] indexディレクトリが存在しません: {index_dir}")

# ベクトル補完関数
def pad_emotion_vector(vector):
    return {emotion: vector.get(emotion, 0) for emotion in ALL_EMOTIONS}

# 感情データ処理関数
def handle_emotion(emotion_data, user_input=None, response_text=None):
    try:
        memory_path = divide_and_store(emotion_data)
        update_emotion_index(emotion_data, memory_path)
        logger.info("[INFO] 感情データ処理が完了しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情データ処理中にエラー発生: {e}")
        raise

# 感情データ記録関数
def save_emotion_sample(input_text, response_text, emotion_vector):
    padded_vector = pad_emotion_vector(emotion_vector)
    record = {
        "input": input_text,
        "response": response_text,
        "emotion_vector": padded_vector,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(DATASET_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("[INFO] dataset_emotion.jsonl に感情データを記録しました。")
        print("[✅] dataset_emotion.jsonl に感情データを記録しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情データの記録に失敗しました: {e}")
        print(f"[❌] 感情データの記録に失敗しました: {e}")

# 感情履歴保存関数
def append_emotion_history(emotion_data):
    try:
        padded_vector = pad_emotion_vector(emotion_data.get("構成比", {}))
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "主感情": emotion_data.get("主感情", ""),
            "構成比": padded_vector
        }
        with open(HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("[INFO] emotion_history.jsonl に履歴を追加しました。")
        print("[✅] emotion_history.jsonl に履歴を追加しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情履歴の保存に失敗しました: {e}")
        print(f"[❌] 感情履歴の保存に失敗しました: {e}")

