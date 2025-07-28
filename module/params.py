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


emotion_map = {
    "Joy": "喜び", "Anticipation": "期待", "Anger": "怒り", "Disgust": "嫌悪",
    "Sadness": "悲しみ", "Surprise": "驚き", "Fear": "恐れ", "Trust": "信頼",
    "Optimism": "楽観", "Pride": "誇り", "病的状態": "病的状態", "Aggressiveness": "積極性",
    "Cynicism": "冷笑", "Pessimism": "悲観", "Contempt": "軽蔑", "Envy": "羨望",
    "Outrage": "憤慨", "Guilt": "自責", "Unbelief": "不信", "Shame": "恥",
    "Disappointment": "失望", "Despair": "絶望", "Sentimentality": "感傷", "Awe": "畏敬",
    "Curiosity": "好奇心", "Delight": "歓喜", "服従": "服従", "Remorse": "罪悪感",
    "Anxiety": "不安", "Love": "愛", "Hope": "希望", "Dominance": "優位"
}
