import os
import json
from .divide_emotion import divide_and_store
from .index_emotion import update_emotion_index
from utils import logger  # ロガーのインポート

# プロジェクトルートを src に固定（Render対応）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 保存先パス設定
INDEX_DIR = os.path.join(BASE_DIR, "index")
index_dir = os.path.dirname(INDEX_PATH)

# 存在しなければ警告＋例外
logger.debug(f"[DEBUG] index_dir = {index_dir}")
if not index_dir.endswith(os.path.join("index")):
    logger.warning(f"[WARNING] 不正な保存先候補: {index_dir}")
if not os.path.exists(index_dir):
    raise FileNotFoundError(f"[エラー] indexディレクトリが存在しません: {index_dir}")

# 感情データ処理関数
def handle_emotion(emotion_data):
    try:
        # ステップ1: memory に振り分け保存
        memory_path = divide_and_store(emotion_data)

        # ステップ2: emotion_index に登録
        update_emotion_index(emotion_data, memory_path)

        logger.info("[INFO] 感情データ処理が完了しました。")
    except Exception as e:
        logger.error(f"[ERROR] 感情データ処理中にエラー発生: {e}")
        raise
