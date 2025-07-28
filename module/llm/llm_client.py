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


#🔸 履歴ベース応答生成（感情未参照）
# 🔸 History-based response generation (without emotion reference)
def generate_gpt_response_from_history() -> tuple[str, dict]:
    logger.info("[START] generate_gpt_response_from_history")
    generation_time = datetime.now().strftime("%Y%m%d%H%M%S")

    system_prompt = load_system_prompt_cached()
    emotion_prompt = load_emotion_prompt()

    # 履歴取得（直近3件）
    # Load history (last 3 entries)
    logger.info("[INFO] 履歴取得中...")
    selected_history = load_history(3)
    logger.info(f"[INFO] 履歴件数: {len(selected_history)} 件")

    # 現在感情の取得
    # Load current emotion
    from module.emotion.emotion_stats import load_current_emotion
    current_emotion = load_current_emotion()
    logger.info(f"[INFO] 現在感情ベクトル: {current_emotion}")

    # 感情ベクトルをAIの内的感情として明示
    # Explicitly indicate emotion vector as AI's internal state
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

    try:
        logger.info("[INFO] OpenAI呼び出し開始")  # OpenAI call start
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": entry["role"], "content": entry["message"]} for entry in selected_history],
                {"role": "user", "content": f"{emotion_text}\n\n{emotion_prompt}"}
            ],
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
            top_p=OPENAI_TOP_P
        )
        logger.info("[INFO] OpenAI応答取得完了")  # OpenAI response received
        content = response.choices[0].message.content.strip()

        fallback_emotion_data = {
            "date": generation_time,
            "データ種別": "emotion",  # Data type
            "重み": 10,  # Weight
            "主感情": "未定",  # Main emotion: undefined
            "構成比": {},  # Composition ratio
            "状況": "履歴から感情未参照で応答生成",  # Situation: response generated without emotion reference from history
            "心理反応": "履歴のみで判断",  # Psychological reaction: judgment based on history only
            "関係性変化": "初期段階",  # Relationship change: initial stage
            "関連": [],  # Related
            "keywords": []
        }

        return content, fallback_emotion_data

    except Exception as e:
        logger.error(f"[ERROR] OpenAI呼び出し失敗: {e}")  # OpenAI call failed
        return "応答生成中にエラーが発生しました。", {}


# 🔸 応答生成 + 感情構造付き（マッチあり／なし）
# 🔸 Response generation with emotion structure (match or no match)
def generate_emotion_from_prompt_with_context(
    user_input: str,
    emotion_structure: dict,
    best_match: dict | None
) -> tuple[str, dict]:
    generation_time = datetime.now().strftime("%Y%m%d%H%M%S")

    system_prompt = (
        load_system_prompt_cached()
        + "\n\n"
        + load_dialogue_prompt()
    )

    top4_personality = get_top_long_emotions()
    personality_text = "\n【人格傾向】\nこのAIは以下の感情を持つ傾向があります：\n"
    # Personality tendency: This AI tends to have the following emotions:
    if top4_personality:
        for emotion, count in top4_personality:
            personality_text += f"・{emotion}（{count}回）\n"  # ・{emotion} ({count} times)
    else:
        personality_text += "傾向情報がまだ十分にありません。\n"  # Not enough tendency information yet.

    # 🔻 条件1：マッチなし → 履歴ベースで生成
    # Condition 1: No match → generate based on history
    if best_match is None:
        fallback_response, fallback_emotion_data = generate_gpt_response_from_history()
        fallback_emotion_data["date"] = generation_time
        return fallback_response, fallback_emotion_data

    # 🔻 条件2：マッチあり → 感情データ参照して応答構築
    # Condition 2: Match → build response referring to emotion data
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
    # [AI's own memories (reference emotion data)]
    # Below are memories of emotions you (the AI) have experienced and recorded.
    # Each case is recorded based on actual user interactions and saved as your internal memory.
    # Please refer to these memories to compose natural and consistent responses.

    for i, item in enumerate(reference_emotions, 1):
        reference_text += f"\n● 記憶ケース{i}\n"  # Memory case {i}
        reference_text += f"主感情: {item.get('主感情')}\n"  # Main emotion
        reference_text += f"構成比: {item.get('構成比')}\n"  # Composition ratio
        reference_text += f"状況: {item.get('状況')}\n"  # Situation
        reference_text += f"心理反応: {item.get('心理反応')}\n"  # Psychological reaction
        reference_text += f"キーワード: {', '.join(item.get('keywords', []))}\n"  # Keywords

    prompt = (
        f"{personality_text}\n"
        f"ユーザー発言: {user_input}\n"
        f"{reference_text}\n\n"
        f"【指示】上記の感情参照データと人格傾向を参考に、emotion_promptのルールに従って応答を生成してください。\n"
        f"自然な応答 + 構成比 + JSON形式の感情構造の順で出力してください。"
    )
    # Instruction: Based on the above emotion reference data and personality tendencies, generate a response following the rules of emotion_prompt.
    # Output natural response + composition ratio + emotion structure in JSON format in order.

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

        # ✅ JSON部分だけ抽出
        # Extract only JSON part
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
        if json_match:
            try:
                emotion_data = json.loads(json_match.group(1))
                emotion_data["date"] = generation_time

                if "構成比" in emotion_data:
                    while isinstance(emotion_data["構成比"], str):
                        try:
                            emotion_data["構成比"] = json.loads(emotion_data["構成比"])
                        except json.JSONDecodeError:
                            break

                clean_response = re.sub(r"```json\s*\{.*?\}\s*```", "", full_response, flags=re.DOTALL).strip()

                if "構成比" in emotion_data:
                    logger.debug("🧪 [DEBUG] 構成比デバッグ出力開始")
                    logger.debug("🧪 [DEBUG] 構成比 type:", type(emotion_data["構成比"]))
                    logger.debug("🧪 [DEBUG] 構成比 内容:", emotion_data["構成比"])

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
# 🔻 Function to run emotion vector merge, save, and summary asynchronously in a thread
def run_emotion_update_pipeline(new_vector: dict) -> tuple[str, dict]:
    try:
        from module.emotion.emotion_stats import (
            load_current_emotion,
            merge_emotion_vectors,
            save_current_emotion,
            summarize_feeling
        )

        current = load_current_emotion()
        logger.debug(f"[DEBUG] current type: {type(current)}")  # <class 'dict'>
        logger.debug(f"[DEBUG] new_vector type: {type(new_vector)}")  # ← たぶん <class 'str'>
        logger.debug(f"[DEBUG] new_vector content: {new_vector}")
        merged = merge_emotion_vectors(current, new_vector)
        save_current_emotion(merged)
        summary = summarize_feeling(merged)
        return "感情を更新しました。", summary  # Emotions updated.

    except Exception as e:
        logger.error(f"[ERROR] 感情更新処理に失敗: {e}")  # Failed emotion update process
        return "感情更新に失敗しました。", {}  # Failed to update emotions.
