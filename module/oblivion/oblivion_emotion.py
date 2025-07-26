import json
import os
from datetime import datetime, timedelta
from module.utils.utils import logger # ロガーの読み込み

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INDEX_PATH = os.path.join(BASE_DIR, "index", "emotion_index.jsonl")
OBLIVION_PATH = os.path.join(BASE_DIR, "memory", "oblivion.jsonl")

# 保存期間設定
def get_expiry_days(path):
    if "/short/" in path or "\\short\\" in path:
        return 3
    elif "/intermediate/" in path or "\\intermediate\\" in path:
        return 30
    return None

def clean_old_emotions():
    if not os.path.exists(INDEX_PATH):
        return

    if not os.path.isdir(os.path.dirname(OBLIVION_PATH)):
        raise FileNotFoundError(f"oblivionフォルダが存在しません: {os.path.dirname(OBLIVION_PATH)}")

    new_index_entries = []

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            expiry_days = get_expiry_days(entry["保存先"])
            if expiry_days is None:
                new_index_entries.append(entry)
                continue

            date_str = entry["date"]
            date_obj = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            if datetime.now() - date_obj > timedelta(days=expiry_days):
                oblivion_entry = {
                    "date": entry["date"],
                    "主感情": entry["主感情"],
                    "構成比": entry["構成比"],
                    "キーワード": entry["キーワード"],
                    "移行日": datetime.now().strftime("%Y%m%d%H%M%S")
                }
                with open(OBLIVION_PATH, "a", encoding="utf-8") as oblivion_file:
                    oblivion_file.write(json.dumps(oblivion_entry, ensure_ascii=False) + "\n")

                try:
                    with open(entry["保存先"], "r", encoding="utf-8") as f2:
                        data = json.load(f2)
                    if isinstance(data, dict) and "履歴" in data:
                        filtered = [d for d in data["履歴"] if d.get("date") != entry["date"]]
                        data["履歴"] = filtered
                        with open(entry["保存先"], "w", encoding="utf-8") as f2:
                            json.dump(data, f2, ensure_ascii=False, indent=4)
                    else:
                        logger.warning(f"[WARN] 想定外の形式: {entry['保存先']}")
                except Exception as e:
                    logger.error(f"[ERROR] memory削除失敗: {e}")
            else:
                new_index_entries.append(entry)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        for entry in new_index_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    if os.path.exists(OBLIVION_PATH):
        updated_oblivion_entries = []
        with open(OBLIVION_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    migrated_str = entry.get("移行日")
                    if migrated_str:
                        migrated_date = datetime.strptime(migrated_str, "%Y%m%d%H%M%S")
                        if datetime.now() - migrated_date > timedelta(days=30):
                            continue
                    updated_oblivion_entries.append(entry)
                except Exception as e:
                    logger.error(f"[ERROR] oblivion削除判定中エラー: {e}")

        with open(OBLIVION_PATH, "w", encoding="utf-8") as f:
            for entry in updated_oblivion_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info("[INFO] 古い感情データをoblivionに移動・削除処理を実施し、indexとmemoryを更新しました。")

