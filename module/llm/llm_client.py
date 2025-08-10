from openai import OpenAI
import re
import json
import os
import threading
from datetime import datetime

from module.utils.utils import load_system_prompt_cached, load_dialogue_prompt, logger
from module.params import (
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_TOP_P,
    OPENAI_MAX_TOKENS
)
from module.emotion.basic_personality import get_top_long_emotions
from module.voice.voice_processing import generate_voicevox_settings_from_composition
from module.live2d.live2d_processing import generate_live2d_from_composition

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 応答テキスト末尾からJSONブロックを抽出
def extract_emotion_json_block(response_text: str) -> dict | None:
    logger.info("JSON抽出プロセス開始")

    # パターン1：```json ... ``` ブロック
    match = re.search(r"```json\s*({.*?})\s*```", response_text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            logger.info("Markdown形式でのJSON抽出成功")
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Markdown JSON抽出失敗: {e}")

    # パターン2：普通の {...} ブロック
    matches = re.findall(r'({.*})', response_text, re.DOTALL)
    for raw in reversed(matches):
        try:
            parsed = json.loads(raw)
            logger.info("フォールバック正規表現でのJSON抽出成功")
            return parsed
        except json.JSONDecodeError:
            continue

    logger.warning("JSON抽出失敗。response_textは構造化されていない可能性あり")
    return None


# 参照データ（best_match）を加味して最終応答を生成（LLMはここでのみ呼ぶ）
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

    # 人格傾向
    top4_personality = get_top_long_emotions()
    personality_text = "\n【人格傾向】\nこのAIは以下の感情を持つ傾向があります：\n"
    if top4_personality:
        for emotion, count in top4_personality:
            personality_text += f"・{emotion}（{count}回）\n"
    else:
        personality_text += "傾向情報がまだ十分にありません。\n"

    # 参照データ
    reference_text = "\n\n【AI自身の記憶（参考感情データ）】\n"
    if best_match is None:
        reference_text += "参照可能な記憶は見つかりませんでした。通常の方針で応答してください。\n"
    else:
        from module.response.main_response import collect_all_category_responses

        emotion_name = best_match.get("emotion")
        date_str = best_match.get("date")
        history_data = collect_all_category_responses(emotion_name, date_str)

        reference_emotions = []
        for category in ["short", "intermediate", "long"]:
            data = history_data.get(category)
            if data:
                reference_emotions.append(data)

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

    # プロンプト
    prompt = (
        f"{personality_text}\n"
        f"ユーザー発言: {user_input}\n"
        f"{reference_text}\n\n"
        f"【指示】上記の（あれば）感情参照データと人格傾向を参考に、emotion_promptのルールに従って応答を生成してください。\n"
        f"自然な応答 + 構成比 + JSON形式の感情構造の順で出力してください。"
    )

    try:
        # LLM呼び出し
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

        # LLMからの生テキスト応答
        full_response = response.choices[0].message.content.strip()

        # JSON抽出
        emotion_data = extract_emotion_json_block(full_response)

        if emotion_data:
            emotion_data["date"] = generation_time

            # 構成比が文字列ならパース
            if "構成比" in emotion_data:
                while isinstance(emotion_data["構成比"], str):
                    try:
                        emotion_data["構成比"] = json.loads(emotion_data["構成比"])
                    except json.JSONDecodeError:
                        break

            logger.debug(f"[DEBUG] 構成比 type: {type(emotion_data.get('構成比'))}")
            logger.debug(f"[DEBUG] 構成比 内容: {emotion_data.get('構成比')}")

            if isinstance(emotion_data.get("構成比"), dict):
                # VoiceVox設定
                vv_settings = generate_voicevox_settings_from_composition(
                    composition=emotion_data["構成比"],
                    speaker_id=3,     # ずんだもん固定
                    topn=5,
                    prev_settings=None,
                    smooth_alpha=0.7
                )
                emotion_data["voicevox_settings"] = vv_settings

                # Live2D設定
                live2d_settings = generate_live2d_from_composition(
                    composition=emotion_data["構成比"],
                    topn=None,
                    prev_params=None,
                    smooth_alpha=0.6,
                    min_ratio=None
                )
                emotion_data["live2d"] = live2d_settings

                # 感情更新を別スレッドで実行
                threading.Thread(
                    target=run_emotion_update_pipeline,
                    args=(emotion_data["構成比"],)
                ).start()

            # 応答テキストからJSON部分を除去
            clean_response = re.sub(r"```json\s*\{.*?\}\s*```", "", full_response, flags=re.DOTALL).strip()
            return clean_response, emotion_data

        return full_response, {}

    except Exception as e:
        logger.error(f"[ERROR] 応答生成失敗: {e}")
        return "応答生成でエラーが発生しました。", {}


# 感情ベクトルのマージ＆保存＆要約
def run_emotion_update_pipeline(new_vector: dict) -> tuple[str, dict]:
    try:
        from module.emotion.emotion_stats import (
            load_current_emotion,
            merge_emotion_vectors,
            save_current_emotion,
            summarize_feeling
        )

        current = load_current_emotion()
        logger.debug(f"[DEBUG] current type: {type(current)}")
        logger.debug(f"[DEBUG] new_vector type: {type(new_vector)}")
        logger.debug(f"[DEBUG] new_vector content: {new_vector}")

        merged = merge_emotion_vectors(current, new_vector)
        save_current_emotion(merged)
        summary = summarize_feeling(merged)
        return "感情を更新しました。", summary

    except Exception as e:
        logger.error(f"[ERROR] 感情更新処理に失敗: {e}")
        return "感情更新に失敗しました。", {}