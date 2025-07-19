# config/params.py

# OpenAI設定
OPENAI_MODEL = "gpt-4o"
OPENAI_TEMPERATURE = 0.7
OPENAI_TOP_P = 1.0
OPENAI_MAX_TOKENS = 1500

# 感情関連パラメーター
EMOTION_THRESHOLD = 10  # 構成比がこの%未満の感情は無視
DEFAULT_MAIN_EMOTION = "未定義"

# データ保存設定
USE_MONGODB = True
MONGODB_URI = "your-mongo-uri-here"
EMOTION_DB_NAME = "emotion_db"
EMOTION_COLLECTION_NAME = "emotion_index"

# デバッグ・ログ設定
DEBUG_MODE = True
