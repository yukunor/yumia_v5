import os
import json
from collections import defaultdict
from module.memory.main_memory import ALL_EMOTIONS  # 感情リストを共通化
from utils import logger

# ファイルパス（リポジトリのルートを基準にする）
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HISTORY_PATH = os.path.join(BASE_DIR, "emotion_history.jsonl")
CURRENT_STATE_PATH = os.path.join(BASE_DIR, "current_emotion_state.json")  # 現在の気分出力先

# 指定件数の平均を計算する補助関数
def _average_emotions(data_list):
    total = defaultdict(float)
    count = len(data_list)
    if count == 0:
        return {emotion: 0 for emotion in ALL_EMOTIONS}

    for item in data_list:
        ratio = item.get("構成比", {})
        for emotion in ALL_EMOTIONS:
            total[emotion] += ratio.get(emotion, 0)

    return {emotion: round(total[emotion] / count, 2) for emotion in ALL_EMOTIONS}

# 短期・中期・長期の平均を計算
def get_emotion_averages():
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        data = [json.loads(line.strip()) for line in lines][-15:]  # 最新15件まで取得

        short = _average_emotions(data[-5:])
        intermediate = _average_emotions(data[-10:])
        long = _average_emotions(data)

        return {
            "短期": short,
            "中期": intermediate,
            "長期": long
        }

    except Exception as e:
        logger.error(f"[ERROR] 感情履歴の平均処理に失敗しました: {e}")
        return {
            "短期": {e: 0 for e in ALL_EMOTIONS},
            "中期": {e: 0 for e in ALL_EMOTIONS},
            "長期": {e: 0 for e in ALL_EMOTIONS}
        }

# 現在の気分を合成

def synthesize_current_emotion():
    try:
        averages = get_emotion_averages()
        short = averages.get("短期", {})
        intermediate = averages.get("中期", {})
        long = averages.get("長期", {})

        result = {}
        for emotion in ALL_EMOTIONS:
            result[emotion] = round(
                short.get(emotion, 0) * 0.5 +
                intermediate.get(emotion, 0) * 0.3 +
                long.get(emotion, 0) * 0.2,
                2
            )

        # 主感情を特定
        dominant = max(result.items(), key=lambda x: x[1])[0]
        output = {
            "現在の気分": result,
            "主感情": dominant
        }

        with open(CURRENT_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print("[✅] 現在の気分を合成し保存しました。")
        return output

    except Exception as e:
        logger.error(f"[ERROR] 現在の気分の合成に失敗しました: {e}")
        return {
            "現在の気分": {e: 0 for e in ALL_EMOTIONS},
            "主感情": "未定義"
        }
