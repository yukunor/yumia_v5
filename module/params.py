# module/params.py

# OpenAI設定
# OpenAI settings
OPENAI_MODEL = "gpt-5"
OPENAI_TEMPERATURE = 0.7
OPENAI_TOP_P = 1.0
OPENAI_MAX_TOKENS = 1500

# 感情関連パラメーター
# Emotion-related parameters
EMOTION_THRESHOLD = 10  # 構成比がこの%未満の感情は無視
DEFAULT_MAIN_EMOTION = "未定義"  # Undefined main emotion

# 合成時の上位N
# Top-N emotions used for synthesis
EMOTION_TOPN_VOICEVOX = 5
EMOTION_TOPN_LIVE2D   = 4

# VoiceVoxパラメータの安全レンジ（クリップ）
# Safe clip ranges for VoiceVox parameters
VOICEVOX_CLIP = {
    "pitchScale": (-0.6, 0.6),
    "speedScale": (0.5, 1.5),
    "intonationScale": (0.5, 1.6),
    "volumeScale": (0.7, 1.3),
}

# データ保存設定
# Data storage settings
USE_MONGODB = True
MONGODB_URI = "your-mongo-uri-here"
EMOTION_DB_NAME = "emotion_db"
EMOTION_COLLECTION_NAME = "emotion_index"

# デバッグ・ログ設定
# Debug/log settings
DEBUG_MODE = True

# 感情辞書（英→日）※固定32感情
# Emotion dictionary (EN → JA) - fixed 32 emotions
emotion_map = {
    "Joy": "喜び", "Anticipation": "期待", "Anger": "怒り", "Disgust": "嫌悪",
    "Sadness": "悲しみ", "Surprise": "驚き", "Fear": "恐れ", "Trust": "信頼",
    "Optimism": "楽観", "Pride": "誇り", "Morbidness": "病的状態", "Aggressiveness": "積極性",
    "Cynicism": "冷笑", "Pessimism": "悲観", "Contempt": "軽蔑", "Envy": "羨望",
    "Outrage": "憤慨", "Guilt": "自責", "Unbelief": "不信", "Shame": "恥",
    "Disappointment": "失望", "Despair": "絶望", "Sentimentality": "感傷", "Awe": "畏敬",
    "Curiosity": "好奇心", "Delight": "歓喜", "Obedience": "服従", "Remorse": "罪悪感",
    "Anxiety": "不安", "Love": "愛", "Hope": "希望", "Dominance": "優位"
}

# 日本語 → 英語変換
# Japanese to English conversion
emotion_map_reverse = {v: k for k, v in emotion_map.items()}

# ─────────────────────────────────────────────────────────────
# VoiceVox: 32感情 → パラメータ（英キー）
# 値はあなたの既存マップ（日本語キー版）を英語キーに移植済み
# ─────────────────────────────────────────────────────────────
voicevox_emotion_map = {
    "Joy":            {"pitchScale":  0.20, "speedScale": 0.53, "intonationScale": 0.78, "volumeScale": 0.83},
    "Anticipation":   {"pitchScale":  0.33, "speedScale": 1.18, "intonationScale": 1.39, "volumeScale": 0.75},
    "Anger":          {"pitchScale": -0.11, "speedScale": 0.53, "intonationScale": 0.72, "volumeScale": 1.00},
    "Disgust":        {"pitchScale": -0.66, "speedScale": 0.70, "intonationScale": 1.15, "volumeScale": 1.03},
    "Sadness":        {"pitchScale": -0.39, "speedScale": 1.09, "intonationScale": 1.31, "volumeScale": 0.70},
    "Surprise":       {"pitchScale": -0.57, "speedScale": 1.25, "intonationScale": 1.47, "volumeScale": 1.03},
    "Fear":           {"pitchScale":  0.21, "speedScale": 0.73, "intonationScale": 0.58, "volumeScale": 0.76},
    "Trust":          {"pitchScale": -0.63, "speedScale": 1.36, "intonationScale": 1.11, "volumeScale": 1.24},
    "Optimism":       {"pitchScale":  0.58, "speedScale": 1.04, "intonationScale": 0.96, "volumeScale": 0.98},
    "Pride":          {"pitchScale": -0.52, "speedScale": 0.97, "intonationScale": 1.02, "volumeScale": 1.14},
    "Morbidness":     {"pitchScale": -0.37, "speedScale": 1.04, "intonationScale": 0.75, "volumeScale": 0.77},
    "Aggressiveness": {"pitchScale":  0.18, "speedScale": 1.30, "intonationScale": 0.96, "volumeScale": 0.93},
    "Cynicism":       {"pitchScale": -0.41, "speedScale": 0.99, "intonationScale": 0.54, "volumeScale": 1.14},
    "Pessimism":      {"pitchScale":  0.26, "speedScale": 1.14, "intonationScale": 0.68, "volumeScale": 0.95},
    "Contempt":       {"pitchScale": -0.67, "speedScale": 0.93, "intonationScale": 1.06, "volumeScale": 0.89},
    "Envy":           {"pitchScale": -0.20, "speedScale": 1.03, "intonationScale": 0.87, "volumeScale": 0.79},
    "Outrage":        {"pitchScale": -0.61, "speedScale": 0.92, "intonationScale": 0.83, "volumeScale": 1.08},
    "Guilt":          {"pitchScale": -0.60, "speedScale": 1.46, "intonationScale": 0.93, "volumeScale": 1.13},
    "Unbelief":       {"pitchScale":  0.41, "speedScale": 1.45, "intonationScale": 1.03, "volumeScale": 0.87},
    "Shame":          {"pitchScale": -0.21, "speedScale": 1.33, "intonationScale": 1.10, "volumeScale": 1.24},
    "Disappointment": {"pitchScale": -0.27, "speedScale": 0.65, "intonationScale": 0.65, "volumeScale": 1.08},
    "Despair":        {"pitchScale": -0.35, "speedScale": 1.18, "intonationScale": 0.89, "volumeScale": 1.02},
    "Sentimentality": {"pitchScale": -0.66, "speedScale": 1.22, "intonationScale": 0.69, "volumeScale": 1.13},
    "Awe":            {"pitchScale":  0.26, "speedScale": 0.72, "intonationScale": 1.46, "volumeScale": 1.02},
    "Curiosity":      {"pitchScale":  0.32, "speedScale": 0.91, "intonationScale": 1.10, "volumeScale": 1.16},
    "Delight":        {"pitchScale": -0.39, "speedScale": 1.12, "intonationScale": 1.18, "volumeScale": 1.12},
    "Obedience":      {"pitchScale": -0.65, "speedScale": 1.09, "intonationScale": 1.12, "volumeScale": 0.94},
    "Remorse":        {"pitchScale":  0.05, "speedScale": 1.33, "intonationScale": 1.26, "volumeScale": 0.91},
    "Anxiety":        {"pitchScale":  0.37, "speedScale": 1.36, "intonationScale": 0.86, "volumeScale": 1.09},
    "Love":           {"pitchScale": -0.58, "speedScale": 1.04, "intonationScale": 1.27, "volumeScale": 0.77},
    "Hope":           {"pitchScale": -0.06, "speedScale": 0.73, "intonationScale": 0.87, "volumeScale": 1.03},
    "Dominance":      {"pitchScale": -0.24, "speedScale": 1.45, "intonationScale": 1.12, "volumeScale": 1.01},
}

# ─────────────────────────────────────────────────────────────
# Live2D: 32感情 → 表情/モーション/連続パラメータ（英キー）
# Mouth/Eye/Browは 0..1、BodyAngleX は -10..10（度イメージ）
# ─────────────────────────────────────────────────────────────
live2d_emotion_map = {
    "Joy":            {"expression": "Smile",      "motion": "Idle_Happy",       "w": {"MouthOpen":0.35,"EyeSmile":0.70,"EyeOpen":0.35,"BrowUp":0.20,"BrowDown":0.00,"BodyAngleX": 4}},
    "Anticipation":   {"expression": "Expect",     "motion": "Idle_Shy",         "w": {"MouthOpen":0.25,"EyeSmile":0.30,"EyeOpen":0.40,"BrowUp":0.15,"BrowDown":0.00,"BodyAngleX": 3}},
    "Anger":          {"expression": "Angry",      "motion": "Idle_Angry",       "w": {"MouthOpen":0.20,"EyeSmile":0.00,"EyeOpen":0.25,"BrowUp":0.00,"BrowDown":0.60,"BodyAngleX":-2}},
    "Disgust":        {"expression": "Disgust",    "motion": "Idle_Contempt",    "w": {"MouthOpen":0.10,"EyeSmile":0.00,"EyeOpen":0.20,"BrowUp":0.00,"BrowDown":0.55,"BodyAngleX": 0}},
    "Sadness":        {"expression": "Sad",        "motion": "Idle_Sad",         "w": {"MouthOpen":0.10,"EyeSmile":0.00,"EyeOpen":0.15,"BrowUp":0.00,"BrowDown":0.45,"BodyAngleX":-5}},
    "Surprise":       {"expression": "Surprise",   "motion": "Idle_Surprise",    "w": {"MouthOpen":0.50,"EyeSmile":0.00,"EyeOpen":0.75,"BrowUp":0.45,"BrowDown":0.00,"BodyAngleX": 6}},
    "Fear":           {"expression": "Fear",       "motion": "Idle_Think",       "w": {"MouthOpen":0.15,"EyeSmile":0.00,"EyeOpen":0.45,"BrowUp":0.00,"BrowDown":0.30,"BodyAngleX":-3}},
    "Trust":          {"expression": "Calm",       "motion": "Idle_Calm",        "w": {"MouthOpen":0.20,"EyeSmile":0.20,"EyeOpen":0.35,"BrowUp":0.10,"BrowDown":0.00,"BodyAngleX": 1}},
    "Optimism":       {"expression": "Bright",     "motion": "Idle_Optimistic",  "w": {"MouthOpen":0.30,"EyeSmile":0.50,"EyeOpen":0.40,"BrowUp":0.20,"BrowDown":0.00,"BodyAngleX": 3}},
    "Pride":          {"expression": "Proud",      "motion": "Pose_Proud",       "w": {"MouthOpen":0.20,"EyeSmile":0.25,"EyeOpen":0.35,"BrowUp":0.30,"BrowDown":0.00,"BodyAngleX": 3}},
    "Morbidness":     {"expression": "Sick",       "motion": "Idle_Sick",        "w": {"MouthOpen":0.05,"EyeSmile":0.00,"EyeOpen":0.10,"BrowUp":0.00,"BrowDown":0.30,"BodyAngleX":-6}},
    "Aggressiveness": {"expression": "Active",     "motion": "Talk_Active",      "w": {"MouthOpen":0.35,"EyeSmile":0.35,"EyeOpen":0.40,"BrowUp":0.15,"BrowDown":0.00,"BodyAngleX": 4}},
    "Cynicism":       {"expression": "Sarcasm",    "motion": "Idle_Sarcastic",   "w": {"MouthOpen":0.15,"EyeSmile":0.20,"EyeOpen":0.25,"BrowUp":0.00,"BrowDown":0.35,"BodyAngleX": 0}},
    "Pessimism":      {"expression": "Gloom",      "motion": "Idle_Pessimistic", "w": {"MouthOpen":0.10,"EyeSmile":0.00,"EyeOpen":0.20,"BrowUp":0.00,"BrowDown":0.35,"BodyAngleX":-2}},
    "Contempt":       {"expression": "Contempt",   "motion": "Idle_Contempt",    "w": {"MouthOpen":0.10,"EyeSmile":0.00,"EyeOpen":0.20,"BrowUp":0.00,"BrowDown":0.50,"BodyAngleX": 1}},
    "Envy":           {"expression": "Envy",       "motion": "Idle_Envy",        "w": {"MouthOpen":0.12,"EyeSmile":0.00,"EyeOpen":0.25,"BrowUp":0.00,"BrowDown":0.20,"BodyAngleX":-1}},
    "Outrage":        {"expression": "Indignant",  "motion": "Idle_Indignant",   "w": {"MouthOpen":0.18,"EyeSmile":0.00,"EyeOpen":0.25,"BrowUp":0.00,"BrowDown":0.70,"BodyAngleX":-1}},
    "Guilt":          {"expression": "Guilt",      "motion": "Idle_Guilt",       "w": {"MouthOpen":0.08,"EyeSmile":0.00,"EyeOpen":0.12,"BrowUp":0.00,"BrowDown":0.50,"BodyAngleX":-4}},
    "Unbelief":       {"expression": "Distrust",   "motion": "Idle_Distrust",    "w": {"MouthOpen":0.12,"EyeSmile":0.00,"EyeOpen":0.18,"BrowUp":0.00,"BrowDown":0.30,"BodyAngleX":-1}},
    "Shame":          {"expression": "Shame",      "motion": "Idle_Shame",       "w": {"MouthOpen":0.05,"EyeSmile":0.00,"EyeOpen":0.05,"BrowUp":0.00,"BrowDown":0.40,"BodyAngleX":-5}},
    "Disappointment": {"expression": "Disappoint", "motion": "Idle_Disappointed","w": {"MouthOpen":0.08,"EyeSmile":0.00,"EyeOpen":0.10,"BrowUp":0.00,"BrowDown":0.30,"BodyAngleX":-4}},
    "Despair":        {"expression": "Despair",    "motion": "Idle_Despair",     "w": {"MouthOpen":0.05,"EyeSmile":0.00,"EyeOpen":0.05,"BrowUp":0.00,"BrowDown":0.60,"BodyAngleX":-7}},
    "Sentimentality": {"expression": "Sentimental","motion": "Idle_Sentimental", "w": {"MouthOpen":0.12,"EyeSmile":0.10,"EyeOpen":0.20,"BrowUp":0.10,"BrowDown":0.10,"BodyAngleX":-2}},
    "Awe":            {"expression": "Awe",        "motion": "Idle_Awe",         "w": {"MouthOpen":0.30,"EyeSmile":0.00,"EyeOpen":0.60,"BrowUp":0.50,"BrowDown":0.00,"BodyAngleX": 2}},
    "Curiosity":      {"expression": "Curious",    "motion": "Idle_Curious",     "w": {"MouthOpen":0.20,"EyeSmile":0.15,"EyeOpen":0.50,"BrowUp":0.20,"BrowDown":0.00,"BodyAngleX": 3}},
    "Delight":        {"expression": "Ecstatic",   "motion": "Idle_Ecstatic",    "w": {"MouthOpen":0.50,"EyeSmile":0.80,"EyeOpen":0.45,"BrowUp":0.30,"BrowDown":0.00,"BodyAngleX": 6}},
    "Obedience":      {"expression": "Submissive", "motion": "Idle_Submissive",  "w": {"MouthOpen":0.10,"EyeSmile":0.00,"EyeOpen":0.20,"BrowUp":0.00,"BrowDown":0.20,"BodyAngleX":-3}},
    "Remorse":        {"expression": "Remorse",    "motion": "Idle_Remorse",     "w": {"MouthOpen":0.08,"EyeSmile":0.00,"EyeOpen":0.12,"BrowUp":0.00,"BrowDown":0.50,"BodyAngleX":-4}},
    "Anxiety":        {"expression": "Anxious",    "motion": "Idle_Anxious",     "w": {"MouthOpen":0.15,"EyeSmile":0.00,"EyeOpen":0.40,"BrowUp":0.00,"BrowDown":0.30,"BodyAngleX":-2}},
    "Love":           {"expression": "Loving",     "motion": "Idle_Love",        "w": {"MouthOpen":0.20,"EyeSmile":0.50,"EyeOpen":0.30,"BrowUp":0.20,"BrowDown":0.00,"BodyAngleX": 2}},
    "Hope":           {"expression": "Hope",       "motion": "Idle_Hope",        "w": {"MouthOpen":0.20,"EyeSmile":0.30,"EyeOpen":0.40,"BrowUp":0.20,"BrowDown":0.00,"BodyAngleX": 3}},
    "Dominance":      {"expression": "Superior",   "motion": "Pose_Superior",    "w": {"MouthOpen":0.18,"EyeSmile":0.20,"EyeOpen":0.30,"BrowUp":0.30,"BrowDown":0.00,"BodyAngleX": 4}},
}
