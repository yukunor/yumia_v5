# module/llm/llm_client.py
from openai import OpenAI
import re
import json
import os
import threading
from datetime import datetime

from module.utils.utils import load_history, load_system_prompt_cached, load_emotion_prompt, load_dialogue_prompt, logger
from module.params import OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_TOP_P, OPENAI_MAX_TOKENS
from module.mongo.emotion_dataset import get_recent_dialogue_history
from module.emotion.basic_personality import get_top_long_emotions
from module.emotion.emotion_stats import load_current_emotion


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_gpt_response_from_history() -> str:
    """
    MongoDBから直近3件の対話履歴と現在感情を取得し、それをもとにGPT応答を生成。
    応答内容は文字列で返却（JSON抽出は別モジュールで処理）。
    """
    logger.info("[START] generate_gpt_response_from_history")

    system_prompt = load_system_prompt_cached()
    user_prompt = load_dialogue_prompt()

    # 履歴取得（直近3件）
    logger.info("[INFO] 履歴取得中...")
    selected_history = load_history(3)
    logger.info(f"[INFO] 履歴件数: {len(selected_history)} 件")

    # 現在感情の取得
    from module.emotion.emotion_stats import load_current_emotion
    current_emotion = load_current_emotion()
    logger.info(f"[INFO] 現在感情ベクトル: {current_emotion}")

    # 感情ベクトルをAIの内的感情として明示
    if current_emotion:
        emotion_text = (
            "\n【現在の感情状態（AI自身の内的状態）】\n"
            "あなた（AI）は以下の感情を現在抱いています。\n"
            "この感情に従って、言葉遣いや態度、語尾などを自然に調整してください。\n"
            + ", ".join([f"{k}: {v}%" for k, v in current_emotion.items()])
        )
    else:
        emotion_text = (
            "\n【現在の感情状態（AI自身の内的状態）】\n"
            "現在の感情はまだ十分に蓄積されていません。通常の口調で応答してください。"
        )

    # GPTへのメッセージ構築
    try:
        logger.info("[INFO] OpenAI呼び出し開始")
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": entry["role"], "content": entry["message"]} for entry in selected_history],
                {"role": "user", "content": f"{emotion_text}\n\n{user_prompt}"}
            ],
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
            top_p=OPENAI_TOP_P
        )
        logger.info("[INFO] OpenAI応答取得完了")
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"[ERROR] OpenAI呼び出し失敗: {e}")
        return "応答生成中にエラーが発生しました。"


def generate_emotion_from_prompt_with_context(
    user_input: str,
    emotion_structure: dict,
    best_match: dict | None
) -> tuple[str, dict]:
    """
    感情構造と参照感情データを用いて、GPTに応答生成を行わせる。
    best_match が None の場合は履歴ベースで応答を生成する。
    """
    system_prompt = load_system_prompt_cached()
    user_prompt = load_dialogue_prompt()

    # 🔸 人格傾向の取得と整形（longカテゴリの頻出emotion）
    top4_personality = get_top_long_emotions()
    personality_text = "\n【人格傾向】\nこのAIは以下の感情を持つ傾向があります：\n"
    if top4_personality:
        for emotion, count in top4_personality:
            personality_text += f"・{emotion}（{count}回）\n"
    else:
        personality_text += "傾向情報がまだ十分にありません。\n"

    # 🔻 条件1：マッチなし → 履歴ベースで生成
    if best_match is None:
        fallback_response = generate_gpt_response_from_history()

        prompt = (
            f"{user_prompt}\n\n"
            f"{personality_text}\n"
            f"ユーザー発言: {user_input}\n"
            f"履歴応答: {fallback_response}\n\n"
            f"【指示】上記の人格傾向と履歴を参考に、自然な応答のみを生成してください。\n"
            f"構成比や感情構造は不要です。"
        )
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=OPENAI_TEMPERATURE,
                top_p=OPENAI_TOP_P
            )
            return response.choices[0].message.content.strip(), {}
        except Exception as e:
            logger.error(f"[ERROR] 応答生成失敗: {e}")
            return "応答生成でエラーが発生しました。", {}

    # 🔻 条件2：マッチあり → 感情データ参照して応答構築
    from module.response.main_response import collect_all_category_responses

    emotion_name = best_match.get("emotion")
    date_str = best_match.get("date")
    history_data = collect_all_category_responses(emotion_name, date_str)

    reference_emotions = []
    for category in ["short", "intermediate", "long"]:
        data = history_data.get(category)
        if data:
            reference_emotions.append(data)

    reference_text = "\n\n【AI自身の記憶（参考感情データ）】\n"
    reference_text += (
        "以下は、あなた自身（AI）がこれまでに経験・記録した感情の記憶です。\n"
        "各ケースは実際のユーザーとの対話に基づいて記録されたものであり、あなたの内的な記憶として保存されています。\n"
        "これらの記憶を参照しながら、自然で一貫性のある応答を構成してください。\n"
    )

    for i, item in enumerate(reference_emotions, 1):
        reference_text += f"\n● 記憶ケース{i}\n"
        reference_text += f"主感情: {item.get('主感情')}\n"
        reference_text += f"構成比: {item.get('構成比')}\n"
        reference_text += f"状況: {item.get('状況')}\n"
        reference_text += f"心理反応: {item.get('心理反応')}\n"
        reference_text += f"キーワード: {', '.join(item.get('keywords', []))}\n"

    prompt = (
        f"{user_prompt}\n\n"
        f"{personality_text}\n"
        f"ユーザー発言: {user_input}\n"
        f"{reference_text}\n\n"
        f"【指示】上記の感情参照データと人格傾向を参考に、emotion_promptのルールに従って応答を生成してください。"
        f"自然な応答 + 構成比 + JSON形式の感情構造の順で出力してください。"
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
            top_p=OPENAI_TOP_P
        )
        full_response = response.choices[0].message.content.strip()
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
        if json_match:
            try:
                emotion_data = json.loads(json_match.group(1))
                emotion_data["date"] = datetime.now().strftime("%Y%m%d%H%M%S")
                clean_response = re.sub(r"```json\s*\{.*?\}\s*```", "", full_response, flags=re.DOTALL).strip()

                # 🔸 非同期スレッドで感情統合処理を実行
                if "構成比" in emotion_data:
                    threading.Thread(
                        target=run_emotion_update_pipeline,
                        args=(emotion_data["構成比"],)
                    ).start()

                return clean_response, emotion_data
            except Exception as e:
                logger.error(f"[ERROR] JSONパース失敗: {e}")
                return full_response, {}
        else:
            return full_response, {}

    except Exception as e:
        logger.error(f"[ERROR] 応答生成失敗: {e}")
        return "応答生成でエラーが発生しました。", {}


# 🔻 非同期スレッドで感情ベクトル合成・保存・サマリーを実行する関数
async def run_emotion_update_pipeline(new_vector: dict):
    try:
        from module.emotion.emotion_stats import (
            load_current_emotion,
            merge_emotion_vectors,
            save_current_emotion,
            summarize_feeling
        )

        current = load_current_emotion()
        merged = merge_emotion_vectors(current, new_vector)
        save_current_emotion(merged)
        summarize_feeling(merged)

    except Exception as e:
        logger.error(f"[ERROR] 感情更新処理に失敗: {e}")
