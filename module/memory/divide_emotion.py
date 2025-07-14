import os
import json
from datetime import datetime
from utils import logger  # ロガーのインポート

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MEMORY_BASE_PATH = os.path.join(BASE_DIR, "memory")

# 日本語感情名 → 英語ファイル名の対応辞書
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

# 感情の重みによる保存先の分類
def get_memory_category(weight):
    if weight >= 95:
        return "long"
    elif weight >= 80:
        return "intermediate"
    else:
        return "short"

# 感情データを既存ファイルに追記（新規作成なし）
def divide_and_store(emotion_data: dict) -> str:
    weight = emotion_data.get("重み", 0)
    category = get_memory_category(weight)
    base_dir = os.path.join("memory", category)

    logger.debug(f"[DEBUG] カテゴリ: {category}")
    logger.debug(f"[DEBUG] 基底ディレクトリ: {os.path.abspath(base_dir)}")

    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"[エラー] 保存対象のディレクトリが存在しません: {base_dir}")

    main_emotion = emotion_data.get("主感情", "")
    logger.debug(f"[DEBUG] 主感情: {repr(main_emotion)}")

    english_filename = EMOTION_MAP.get(main_emotion)
    logger.debug(f"[DEBUG] 英語ファイル名: {english_filename}")

    if not english_filename:
        logger.warning(f"[WARNING] 主感情 '{main_emotion}' に対応するファイル名が見つかりません。EMOTION_MAPを確認してください。処理をスキップします。")
        return ""

    target_file = None

    for file in os.listdir(base_dir):
        if not file.endswith(".json"):
            continue

        if os.path.splitext(file)[0].lower() == english_filename.lower():
            target_file = os.path.join(base_dir, file)
            break

    logger.debug(f"[DEBUG] 対象ファイル: {target_file}")

    if not target_file:
        raise FileNotFoundError(f"[エラー] 主感情 '{main_emotion}' に一致する保存ファイルが {base_dir} に存在しません。保存を中断します。")

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    except FileNotFoundError:
        existing_data = {}

    if "履歴" not in existing_data:
        existing_data["履歴"] = []

    existing_data["主感情"] = main_emotion
    existing_data["構成比"] = emotion_data["構成比"]
    existing_data["履歴"].append(emotion_data)

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

    logger.info(f"[INFO] 感情データを {target_file} に保存しました。")
    return target_file
