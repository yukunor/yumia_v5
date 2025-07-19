from openai import OpenAI
import re
import json
import os
from datetime import datetime
from utils import (
    load_system_prompt_cached,
    load_emotion_prompt,
    load_dialogue_prompt,
    logger
)
from module.memory.oblivion_emotion import clean_old_emotions
from module.context.context_selector import select_contextual_history
from module.memory.index_emotion import extract_personality_tendency
from module.params import (
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_TOP_P,
    OPENAI_MAX_TOKENS
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_gpt_response_from_history(history):
    logger.info("[START] generate_gpt_response_from_history")
    system_prompt = load_system_prompt_cached()
    user_prompt = load_dialogue_prompt()
    logger.info("[INFO] 文脈選別開始")
    selected_history = select_contextual_history(history)
    logger.info(f"[INFO] 文脈選別結果: {len(selected_history)} 件")
    try:
        logger.info("[INFO] OpenAI呼び出し開始")
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": entry["role"], "content": entry["message"]} for entry in selected_history],
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
            top_p=OPENAI_TOP_P
        )
        logger.info("[INFO] OpenAI応答取得完了")
    except Exception as e:
        logger.error(f"[ERROR] OpenAI呼び出し失敗: {e}")
        return "申し訳ありません、ご主人。応答生成中にエラーが発生しました。"

    full_response = response.choices[0].message.content.strip()
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
    if json_match:
        try:
            structured_data = json.loads(json_match.group(1))
            structured_data["date"] = datetime.now().strftime("%Y%m%d%H%M%S")
            return structured_data, re.sub(r"```json\s*\{.*?\}\s*```", "", full_response, flags=re.DOTALL).strip()
        except Exception as e:
            logger.error(f"[ERROR] JSON処理失敗: {e}")
            return full_response, {}
    else:
        logger.warning("[WARNING] 応答にJSONが含まれていません")
        return full_response, {}


def generate_emotion_from_prompt_with_context(user_input: str, reference_emotions: list) -> tuple[str, dict]:
    system_prompt = load_system_prompt_cached()
    user_prompt = load_dialogue_prompt()

    # 人格傾向の取得と整形
    personality = extract_personality_tendency()
    personality_text = "\n【人格傾向】\nこのAIは以下の感情を持つ傾向があります：\n"
    if personality:
        for emotion, count in personality.items():
            personality_text += f"・{emotion}（{count}回）\n"
    else:
        personality_text += "傾向情報がまだ十分にありません。\n"

    # 参考感情データの整形
    reference_text = "\n\n【参考感情データ】\n"
    for i, item in enumerate(reference_emotions, 1):
        reference_text += f"\n● ケース{i}\n"
        reference_text += f"主感情: {item.get('主感情')}\n"
        reference_text += f"構成比: {item.get('構成比')}\n"
        reference_text += f"状況: {item.get('状況')}\n"
        reference_text += f"心理反応: {item.get('心理反応')}\n"
        reference_text += f"キーワード: {', '.join(item.get('keywords', []))}\n"

    # プロンプト生成
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
                return re.sub(r"```json\s*\{.*?\}\s*```", "", full_response, flags=re.DOTALL).strip(), emotion_data
            except Exception as e:
                logger.error(f"[ERROR] JSONパース失敗: {e}")
                return full_response, {}
        else:
            return full_response, {}

    except Exception as e:
        logger.error(f"[ERROR] 応答生成失敗: {e}")
        return "応答生成でエラーが発生しました。", {}
