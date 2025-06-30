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

ALLOWED_EMOTIONS = [
    "喜び", "期待", "怒り", "嫌悪", "悲しみ", "驚き", "恐れ", "信頼",
    "楽観", "誇り", "病的状態", "積極性", "冷笑", "悲観", "軽蔑", "羨望",
    "憤慨", "自責", "不信", "恥", "失望", "絶望", "感傷", "畏敬",
    "好奇心", "歓喜", "服従", "罪悪感", "不安", "愛", "希望", "優位"
]

# emotion_map の読み込み
emotion_map_path = os.path.join(os.path.dirname(__file__), "emotion_map.json")
if os.path.exists(emotion_map_path):
    with open(emotion_map_path, "r", encoding="utf-8") as f:
        EMOTION_MAP = json.load(f)
else:
    EMOTION_MAP = {}

def normalize_emotion_data(emotion_data: dict) -> dict:
    composition = emotion_data.get("構成比", {})
    normalized = {}
    for k, v in composition.items():
        if isinstance(v, (int, float)):
            std_emotion = EMOTION_MAP.get(k, k)
            if std_emotion in ALLOWED_EMOTIONS:
                normalized[std_emotion] = normalized.get(std_emotion, 0) + v
    if normalized:
        main = max(normalized, key=normalized.get)
        emotion_data["構成比"] = normalized
        emotion_data["主感情"] = main
    else:
        emotion_data["構成比"] = {}
        emotion_data["主感情"] = emotion_data.get("主感情", "未定義") or "未定義"
    return emotion_data

def extract_emotion_summary(emotion_data: dict, main_emotion: str = "未定義") -> str:
    if not emotion_data:
        return f"（主感情: {main_emotion}）"
    composition = emotion_data.get("構成比")
    if not isinstance(composition, dict):
        logger.warning("[WARNING] '構成比' が存在しないか辞書ではありません")
        return f"（主感情: {main_emotion}）"
    filtered = {k: v for k, v in composition.items() if isinstance(v, (int, float))}
    ratio = ", ".join([f"{k}:{v}%" for k, v in filtered.items()])
    return f"（主感情: {main_emotion}｜構成比: {ratio}）"

def parse_emotion_summary_from_text(text: str) -> dict:
    pattern = r"（感情\s+([^\n)]+)）"
    match = re.search(pattern, text)
    if not match:
        return {}
    content = match.group(1)
    parts = [p.strip() for p in content.split("、") if ":" in p]
    result = {}
    for part in parts:
        try:
            emotion, percent = part.split(":")
            emotion = emotion.strip()
            if not emotion:
                continue
            percent_value = int(percent.replace("%", "").strip())
            if emotion in ALLOWED_EMOTIONS:
                result[emotion] = percent_value
        except Exception:
            continue
    return result

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
    system_prompt = load_system_prompt_cached()
    user_prompt = load_user_prompt()
    prompt = f"{user_prompt}\nユーザー発言: {user_input}"
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
    except Exception as e:
        logger.error(f"[ERROR] 感情推定中にエラー発生: {e}")
        return "申し訳ありません、ご主人。応答生成に失敗しました。", {}
    full_response = response.choices[0].message.content.strip()
    full_response = normalize_json_text(full_response)
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
    if json_match:
        try:
            emotion_data = json.loads(json_match.group(1))
        except Exception as e:
            logger.error(f"[ERROR] JSONパース失敗: {e}")
            emotion_data = {}
    else:
        emotion_data = {}
    composition = parse_emotion_summary_from_text(full_response)
    if composition:
        emotion_data["構成比"] = composition
    if not emotion_data.get("date"):
        emotion_data["date"] = datetime.now().strftime("%Y%m%d%H%M%S")
    if "データ種別" not in emotion_data:
        emotion_data["データ種別"] = "emotion"
    emotion_data = normalize_emotion_data(emotion_data)
    main_emotion = emotion_data.get("主感情", "未定義")
    emotion_summary = extract_emotion_summary(emotion_data, main_emotion)
    clean_text = re.sub(r"```json\s*\{.*?\}\s*```", "", full_response, flags=re.DOTALL).strip()
    return f"{clean_text}\n\n{emotion_summary}", emotion_data

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
