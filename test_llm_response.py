import sys
import os

# モジュールパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), "module"))

from llm.llm_client import (
    generate_emotion_from_prompt_with_context,
    extract_emotion_summary
)
from memory.current_emotion import load_current_emotion  # 現在の気分ベクトルを取得

if __name__ == "__main__":
    user_input = "今日はなんだか不安な気分です。"

    # 現在の感情状態を取得（ミキシングに使う前提）
    current_emotion = load_current_emotion()

    print("🔍 LLM応答と感情構造の取得を開始...")
    response, emotion_data = generate_emotion_from_prompt_with_context(user_input, current_emotion)

    print("\n=== 🗣 応答内容 ===")
    print(response)

    print("\n=== 🧠 感情構造 ===")
    for k, v in emotion_data.items():
        print(f"{k}: {v}")

    print("\n=== 📊 構成比サマリ ===")
    summary = extract_emotion_summary(emotion_data, emotion_data.get("主感情", "未定義"))
    print(summary)
