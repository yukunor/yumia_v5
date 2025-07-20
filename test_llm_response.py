import sys
import os

# カレントディレクトリをPYTHONPATHに追加（Renderでは必須）
sys.path.append(os.path.dirname(__file__))

from module.llm.llm_client import (
    generate_emotion_from_prompt_with_context,
    extract_emotion_summary
)

if __name__ == "__main__":
    user_input = "今日はなんだか不安な気分です。"
    current_emotion = {}

    response, emotion_data = generate_emotion_from_prompt_with_context(user_input, current_emotion)

    print("\n=== 🗣 応答内容 ===")
    print(response)

    print("\n=== 🧠 感情構造 ===")
    for k, v in emotion_data.items():
        print(f"{k}: {v}")

    print("\n=== 📊 構成比サマリ ===")
    summary = extract_emotion_summary(emotion_data, emotion_data.get("主感情", "未定義"))
    print(summary)
