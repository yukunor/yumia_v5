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

VALID_EMOTIONS = {
    "喜び", "期待", "怒り", "嫌悪", "悲しみ", "驚き", "恐れ", "信頼",
    "楽観", "誇り", "病的状態", "積極性", "冷笑", "悲観", "軽蔑", "羨望",
    "憤慨", "自責", "不信", "恥", "失望", "絶望", "感傷", "畏敬", "好奇心",
    "歓喜", "服従", "罪悪感", "不安", "愛", "希望", "優位"
}

def extract_emotion_summary(emotion_data: dict, main_emotion: str = "未定義") -> str:
    print("[DEBUG] extract_emotion_summary 呼び出し")
    print("[DEBUG] 入力 emotion_data:", emotion_data)
    composition = emotion_data.get("構成比", {})

    # 無効な感情名を除外
    filtered = {k: v for k, v in composition.items() if k in VALID_EMOTIONS and isinstance(v, (int, float))}
    print("[DEBUG] フィルタ後の構成比:", filtered)

    # 主感情補完（未定義または不正な場合）
    if not main_emotion or main_emotion == "未定義" or main_emotion not in filtered:
        if filtered:
            main_emotion = max(filtered, key=filtered.get)
        else:
            main_emotion = "未定義"

    ratio = ", ".join([f"{k}:{v}%" for k, v in filtered.items()])
    return f"　（感情　{main_emotion}: {ratio}）"

def normalize_json_text(text):
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("：", ":").replace("，", ",")
    text = text.replace("「", '"').replace("」", '"')
    return text

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
    full_response = normalize_json_text(full_response)

    json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
    if json_match:
        json_data_str = json_match.group(1)
        try:
            structured_data = json.loads(json_data_str)
            structured_data["date"] = datetime.now().strftime("%Y%m%d%H%M%S")

            if structured_data.get("データ種別") == "emotion":
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

    full_response_clean = re.sub(r"```json\s*\{.*?\}\s*```", "", full_response, flags=re.DOTALL)
    full_response_clean = re.sub(r"\{\s*\"date\"\s*:\s*\".*?\".*?\"keywords\"\s*:\s*\[.*?\]\s*\}", "", full_response_clean, flags=re.DOTALL)

    return full_response_clean.strip()

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
    print("[DEBUG] 推定応答内容:", full_response)
    full_response = normalize_json_text(full_response)
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)

    if json_match:
        emotion_data = json.loads(json_match.group(1))
        print("[DEBUG] パース後 emotion_data:", emotion_data)
        if not emotion_data.get("date"):
            emotion_data["date"] = datetime.now().strftime("%Y%m%d%H%M%S")

        composition = emotion_data.get("構成比", {})
        # 無効な感情を除外
        emotion_data["構成比"] = {k: v for k, v in composition.items() if k in VALID_EMOTIONS and isinstance(v, (int, float))}

        main_emotion = emotion_data.get("主感情", "未定義")
        if not main_emotion or main_emotion == "未定義" or main_emotion not in emotion_data["構成比"]:
            if emotion_data["構成比"]:
                main_emotion = max(emotion_data["構成比"], key=emotion_data["構成比"].get)
                emotion_data["主感情"] = main_emotion
            else:
                main_emotion = "未定義"

        emotion_summary = extract_emotion_summary(emotion_data, main_emotion)
        print("[DEBUG] 構成比 summary:", emotion_summary)

        display_text = re.sub(r"```json\s*\{.*?\}\s*```", "", full_response, flags=re.DOTALL)
        display_text = re.sub(r"\{\s*\"date\"\s*:\s*\".*?\".*?\"keywords\"\s*:\s*\[.*?\]\s*\}", "", display_text, flags=re.DOTALL)
        clean_text = display_text.strip()
        return f"{clean_text}\n\n{emotion_summary}", emotion_data
    else:
        logger.warning("[WARNING] 感情推定にJSONが含まれていません")
        return full_response, {}
