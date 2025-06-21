from openai import OpenAI
import re
import json
import os
from datetime import datetime
from utils import load_system_prompt_cached, load_user_prompt, logger
from module.memory.main_memory import handle_emotion
from module.memory.oblivion_emotion import clean_old_emotions
from module.context.context_selector import select_contextual_history

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_emotion_summary(composition: dict) -> str:
    if not composition:
        return ""
    return "　（感情　" + ", ".join([f"{k}:{v}%" for k, v in composition.items()]) + "）"

def generate_gpt_response_from_history(history):
    logger.info("[START] generate_gpt_response_from_history")
    system_prompt = load_system_prompt_cached()
    user_prompt = load_user_prompt()

    logger.info("[INFO] 文脈選別開始")
    selected_history = select_contextual_history(history)
    logger.info(f"[INFO] 文脈選別結果: {len(selected_history)} 件")

    try:
        logger.info("[INFO] OpenAI呼び出し開始")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": entry["role"], "content": entry["message"]} for entry in selected_history],
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.7,
            top_p=1.0
        )
        logger.info("[INFO] OpenAI応答取得完了")
    except Exception as e:
        logger.error(f"[ERROR] OpenAI呼び出し失敗: {e}")
        return "申し訳ありません、ご主人。応答生成中にエラーが発生しました。"

    full_response = response.choices[0].message.content.strip()
    logger.debug(f"[DEBUG] 応答全文: {full_response[:200]}...")

    json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
    emotion_summary = ""
    if json_match:
        json_data_str = json_match.group(1)
        try:
            structured_data = json.loads(json_data_str)
            structured_data["date"] = datetime.now().strftime("%Y%m%d%H%M%S")

            if structured_data.get("データ種別") == "emotion":
                composition = structured_data.get("構成比", {})
                emotion_summary = extract_emotion_summary(composition)

                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                save_dir = os.path.join(base_dir, "yumia_v5", "dialogue_structured")
                save_path = os.path.join(save_dir, "emotion.json")

                logger.debug(f"[DEBUG] 構造化データ保存先: {save_path}")
                os.makedirs(save_dir, exist_ok=True)

                if os.path.exists(save_path):
                    with open(save_path, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            logger.warning("[WARNING] emotion.json が不正な形式のため初期化")
                            data = []
                else:
                    data = []

                data.append(structured_data)

                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                logger.info("[INFO] 感情データ保存完了")
                handle_emotion(structured_data)
                clean_old_emotions()
            else:
                logger.info(f"[INFO] データ種別が emotion ではない: {structured_data.get('データ種別')}")

        except Exception as e:
            logger.error(f"[ERROR] JSON処理失敗: {e}")
    else:
        logger.warning("[WARNING] 応答にJSONが含まれていません")

    display_text = full_response.split("```json")[0].strip()
    return f"{display_text}\n\n{emotion_summary}" if emotion_summary else display_text

def generate_emotion_from_prompt(user_input: str) -> tuple[str, dict]:
    prompt_rule = load_user_prompt()
    full_prompt = f"{prompt_rule}\nユーザー発言: {user_input}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": load_system_prompt_cached()},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            top_p=1.0
        )
        logger.info("[INFO] 感情推定完了")
    except Exception as e:
        logger.error(f"[ERROR] 感情推定失敗: {e}")
        return "", {}

    full_response = response.choices[0].message.content.strip()
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)

    if json_match:
        emotion_data = json.loads(json_match.group(1))
        if not emotion_data.get("date"):
            emotion_data["date"] = datetime.now().strftime("%Y%m%d%H%M%S")

        display_text = full_response.split("```json")[0].strip()
        composition = emotion_data.get("構成比", {})
        emotion_summary = extract_emotion_summary(composition)

        logger.debug(f"[DEBUG] 推定感情データ: {emotion_data}")
        return f"{display_text}\n\n{emotion_summary}", emotion_data
    else:
        logger.warning("[WARNING] 感情推定にJSONが含まれていません")
        return full_response, {}

def generate_gpt_response(user_input: str, reference_emotions: list) -> str:
    system_prompt = load_system_prompt_cached()
    user_prompt = load_user_prompt()

    reference_text = "\n\n【参考感情データ】\n"
    for i, item in enumerate(reference_emotions, 1):
        reference_text += f"\n● ケース{i}\n"
        reference_text += f"主感情: {item.get('主感情')}\n"
        reference_text += f"構成比: {item.get('構成比')}\n"
        reference_text += f"状況: {item.get('状況')}\n"
        reference_text += f"心理反応: {item.get('心理反応')}\n"
        reference_text += f"キーワード: {', '.join(item.get('keywords', []))}\n"

    prompt = f"{user_prompt}\n\nユーザー発言: {user_input}\n{reference_text}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            top_p=1.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[ERROR] 応答生成失敗: {e}")
        return "申し訳ありません、ご主人。応答生成でエラーが発生しました。"

