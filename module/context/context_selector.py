from openai import OpenAI
import json
from datetime import datetime, timedelta
from utils import logger

client = OpenAI()

def parse_timestamp(entry):
    try:
        return datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"タイムスタンプの解析に失敗: {e}")
        return datetime.now()

def is_contextually_related(message_a, message_b):
    prompt = (
        "次の2つの発言は会話として文脈的につながっていますか？"
        "それぞれの発言は以下のようになっています：\n"
        f"発言A: {message_a}\n"
        f"発言B: {message_b}\n"
        "文脈がつながっている場合は 'はい'、そうでなければ 'いいえ' とだけ返してください。"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは日本語に堪能な対話分析AIです。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.0
        )
        answer = response.choices[0].message.content.strip()
        print(f"[DEBUG] GPT文脈判定応答: {answer}")  # ← 追加
        return "はい" in answer
    except Exception as e:
        logger.error(f"つながり判定のGPT呼び出しに失敗: {e}")
        return False

def select_contextual_history(full_history, max_turns=10):
    if not full_history:
        return []

    latest = full_history[-1]
    latest_time = parse_timestamp(latest)

    selected = [latest]
    cutoff_time = latest_time - timedelta(minutes=5)
    index = len(full_history) - 2
    related = True

    while index >= 0 and len(selected) < max_turns:
        current = full_history[index]
        current_time = parse_timestamp(current)

        print(f"[DEBUG] チェック中: {current['message']}")  # ← 追加

        if current_time < cutoff_time:
            related = is_contextually_related(current["message"], selected[0]["message"])
            print(f"[DEBUG] 文脈判定結果: {related}")  # ← 追加
            if not related:
                break

        selected.insert(0, current)
        index -= 1

    print(f"[DEBUG] 抽出された履歴数: {len(selected)}")  # ← 追加
    return selected

