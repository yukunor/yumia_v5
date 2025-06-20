import openai
import re
import json
import os
from datetime import datetime
from utils import load_system_prompt, load_user_prompt, logger
from module.memory.main_memory import handle_emotion
from module.memory.oblivion_emotion import clean_old_emotions
from module.context.context_selector import select_contextual_history

openai.api_key = os.getenv("OPENAI_API_KEY")  # ← 明示的に環境変数から取得

def extract_emotion_summary(composition: dict) -> str:
    if not composition:
        return ""
    return "\u3000\uff08\u611f\u60c5\u3000" + ", ".join([f"{k}:{v}%" for k, v in composition.items()]) + "\uff09"

def generate_gpt_response_from_history(history):
    logger.info("[START] generate_gpt_response_from_history")
    system_prompt = load_system_prompt()
    user_prompt = load_user_prompt()

    logger.info("[INFO] \u6587\u8108\u9078\u5225\u958b\u59cb")
    selected_history = select_contextual_history(history)
    logger.info(f"[INFO] \u6587\u8108\u9078\u5225\u7d50\u679c: {len(selected_history)} \u4ef6")

    try:
        logger.info("[INFO] OpenAI\u547c\u3073\u51fa\u3057\u958b\u59cb")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": entry["role"], "content": entry["message"]} for entry in selected_history],
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.7,
            top_p=1.0,
            stream=False,
            timeout=30
        )
        logger.info("[INFO] OpenAI\u5fdc\u7b54\u53d6\u5f97\u5b8c\u4e86")
    except Exception as e:
        logger.error(f"[ERROR] OpenAI\u547c\u3073\u51fa\u3057\u5931\u6557: {e}")
        return "\u7533\u3057\u8a33\u3042\u308a\u307e\u305b\u3093\u3001\u3054\u4e3b\u4eba\u3002\u5fdc\u7b54\u751f\u6210\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f\u3002"

    full_response = response.choices[0].message.content.strip()
    logger.debug(f"[DEBUG] \u5fdc\u7b54\u5168\u6587: {full_response[:200]}...")

    json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
    emotion_summary = ""
    if json_match:
        json_data_str = json_match.group(1)
        try:
            structured_data = json.loads(json_data_str)
            structured_data["date"] = datetime.now().strftime("%Y%m%d%H%M%S")

            if structured_data.get("\u30c7\u30fc\u30bf\u7a2e\u5225") == "emotion":
                composition = structured_data.get("\u69cb\u6210\u6bd4", {})
                emotion_summary = extract_emotion_summary(composition)

                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                save_dir = os.path.join(base_dir, "yumia_v5", "dialogue_structured")
                save_path = os.path.join(save_dir, "emotion.json")

                logger.debug(f"[DEBUG] \u69cb\u9020\u5316\u30c7\u30fc\u30bf\u4fdd\u5b58\u5148: {save_path}")

                if not os.path.isdir(save_dir):
                    logger.error(f"\u4fdd\u5b58\u30c7\u30a3\u30ec\u30af\u30c8\u30ea\u304c\u5b58\u5728\u3057\u307e\u305b\u3093: {save_dir}")
                    return full_response.split("```json")[0].strip()

                if os.path.exists(save_path):
                    with open(save_path, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            logger.warning("[WARNING] emotion.json \u304c\u4e0d\u6b63\u306a\u5f62\u5f0f\u306e\u305f\u3081\u521d\u671f\u5316")
                            data = []
                else:
                    data = []

                data.append(structured_data)

                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                logger.info("[INFO] \u611f\u60c5\u30c7\u30fc\u30bf\u4fdd\u5b58\u5b8c\u4e86")
                handle_emotion(structured_data)
                clean_old_emotions()
            else:
                logger.info(f"[INFO] \u30c7\u30fc\u30bf\u7a2e\u5225\u304c emotion \u3067\u306f\u306a\u3044: {structured_data.get('データ種別')}")

        except Exception as e:
            logger.error(f"[ERROR] JSON\u51e6\u7406\u5931\u6557: {e}")
    else:
        logger.warning("[WARNING] \u5fdc\u7b54\u306bJSON\u304c\u542b\u307e\u308c\u3066\u3044\u307e\u305b\u3093")

    display_text = full_response.split("```json")[0].strip()
    return f"{display_text}\n\n{emotion_summary}" if emotion_summary else display_text

def generate_emotion_from_prompt(user_input: str) -> tuple[str, dict]:
    with open("user_prompt.txt", encoding="utf-8") as f:
        prompt_rule = f.read()

    full_prompt = f"{prompt_rule}\n\u30e6\u30fc\u30b6\u30fc\u767a\u8a00: {user_input}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": load_system_prompt()},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            top_p=1.0,
            stream=False,
            timeout=30
        )
        logger.info("[INFO] \u611f\u60c5\u63a8\u5b9a\u5b8c\u4e86")
    except Exception as e:
        logger.error(f"[ERROR] \u611f\u60c5\u63a8\u5b9a\u5931\u6557: {e}")
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
    system_prompt = load_system_prompt()
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
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            top_p=1.0,
            stream=False,
            timeout=30
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[ERROR] 応答生成失敗: {e}")
        return "申し訳ありません、ご主人。応答生成でエラーが発生しました。"
