import os
import json
from .divide_emotion import divide_and_store
from .index_emotion import update_emotion_index
from utils import logger  # ロガーのインポート

# yumia_v5 という名前のディレクトリを上階層から探索して取得
def find_project_root(current_path, target_dir="yumia_v5"):
    while True:
        if os.path.basename(current_path) == target_dir:
            return current_path
        parent = os.path.dirname(current_path)
        if parent == current_path:
            raise FileNotFoundError("プロジェクトルート（yumia_v5）が見つかりませんでした。")
        current_path = parent

# 現在のファイルのパスから yumia_v5 のルートを探索
current_file_path = os.path.abspath(__file__)
BASE_DIR = find_project_root(current_file_path)

# 保存先パス設定
INDEX_PATH = os.path.join(BASE_DIR, "index", "emotion_index.jsonl")
index_dir = os.path.dirname(INDEX_PATH)

# 存在しなければ警告＋例外
logger.debug(f"[DEBUG] index_dir = {index_dir}")
if not index_dir.endswith(os.path.join("yumia_v5", "index")):
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
