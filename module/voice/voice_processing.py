# module/voice/voice_processing.py

import requests
from module.utils.utils import logger

VOICEVOX_EMOTION_MAP = {
    "喜び":     {"pitchScale": 0.20, "speedScale": 0.53, "intonationScale": 0.78, "volumeScale": 0.83},
    "期待":     {"pitchScale": 0.33, "speedScale": 1.18, "intonationScale": 1.39, "volumeScale": 0.75},
    "怒り":     {"pitchScale": -0.11, "speedScale": 0.53, "intonationScale": 0.72, "volumeScale": 1.00},
    "嫌悪":     {"pitchScale": -0.66, "speedScale": 0.70, "intonationScale": 1.15, "volumeScale": 1.03},
    "悲しみ":   {"pitchScale": -0.39, "speedScale": 1.09, "intonationScale": 1.31, "volumeScale": 0.70},
    "驚き":     {"pitchScale": -0.57, "speedScale": 1.25, "intonationScale": 1.47, "volumeScale": 1.03},
    "恐れ":     {"pitchScale": 0.21, "speedScale": 0.73, "intonationScale": 0.58, "volumeScale": 0.76},
    "信頼":     {"pitchScale": -0.63, "speedScale": 1.36, "intonationScale": 1.11, "volumeScale": 1.24},
    "楽観":     {"pitchScale": 0.58, "speedScale": 1.04, "intonationScale": 0.96, "volumeScale": 0.98},
    "誇り":     {"pitchScale": -0.52, "speedScale": 0.97, "intonationScale": 1.02, "volumeScale": 1.14},
    "病的状態": {"pitchScale": -0.37, "speedScale": 1.04, "intonationScale": 0.75, "volumeScale": 0.77},
    "積極性":   {"pitchScale": 0.18, "speedScale": 1.30, "intonationScale": 0.96, "volumeScale": 0.93},
    "冷笑":     {"pitchScale": -0.41, "speedScale": 0.99, "intonationScale": 0.54, "volumeScale": 1.14},
    "悲観":     {"pitchScale": 0.26, "speedScale": 1.14, "intonationScale": 0.68, "volumeScale": 0.95},
    "軽蔑":     {"pitchScale": -0.67, "speedScale": 0.93, "intonationScale": 1.06, "volumeScale": 0.89},
    "羨望":     {"pitchScale": -0.20, "speedScale": 1.03, "intonationScale": 0.87, "volumeScale": 0.79},
    "憤慨":     {"pitchScale": -0.61, "speedScale": 0.92, "intonationScale": 0.83, "volumeScale": 1.08},
    "自責":     {"pitchScale": -0.60, "speedScale": 1.46, "intonationScale": 0.93, "volumeScale": 1.13},
    "不信":     {"pitchScale": 0.41, "speedScale": 1.45, "intonationScale": 1.03, "volumeScale": 0.87},
    "恥":       {"pitchScale": -0.21, "speedScale": 1.33, "intonationScale": 1.10, "volumeScale": 1.24},
    "失望":     {"pitchScale": -0.27, "speedScale": 0.65, "intonationScale": 0.65, "volumeScale": 1.08},
    "絶望":     {"pitchScale": -0.35, "speedScale": 1.18, "intonationScale": 0.89, "volumeScale": 1.02},
    "感傷":     {"pitchScale": -0.66, "speedScale": 1.22, "intonationScale": 0.69, "volumeScale": 1.13},
    "畏敬":     {"pitchScale": 0.26, "speedScale": 0.72, "intonationScale": 1.46, "volumeScale": 1.02},
    "好奇心":   {"pitchScale": 0.32, "speedScale": 0.91, "intonationScale": 1.10, "volumeScale": 1.16},
    "歓喜":     {"pitchScale": -0.39, "speedScale": 1.12, "intonationScale": 1.18, "volumeScale": 1.12},
    "服従":     {"pitchScale": -0.65, "speedScale": 1.09, "intonationScale": 1.12, "volumeScale": 0.94},
    "罪悪感":   {"pitchScale": 0.05, "speedScale": 1.33, "intonationScale": 1.26, "volumeScale": 0.91},
    "不安":     {"pitchScale": 0.37, "speedScale": 1.36, "intonationScale": 0.86, "volumeScale": 1.09},
    "愛":       {"pitchScale": -0.58, "speedScale": 1.04, "intonationScale": 1.27, "volumeScale": 0.77},
    "希望":     {"pitchScale": -0.06, "speedScale": 0.73, "intonationScale": 0.87, "volumeScale": 1.03},
    "優位":     {"pitchScale": -0.24, "speedScale": 1.45, "intonationScale": 1.12, "volumeScale": 1.01}
}

def generate_voicevox_settings_from_composition(composition: dict[str, float], speaker_id: int = 3) -> dict:
    total = sum(composition.values())
    if total == 0:
        return {
            "speaker": speaker_id,
            "pitchScale": 0.0,
            "speedScale": 1.0,
            "intonationScale": 1.0,
            "volumeScale": 1.0,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1
        }

    pitch, speed, intonation, volume = 0.0, 0.0, 0.0, 0.0
    for emotion, weight in composition.items():
        if emotion not in VOICEVOX_EMOTION_MAP:
            continue
        ratio = weight / total
        preset = VOICEVOX_EMOTION_MAP[emotion]
        pitch += preset["pitchScale"] * ratio
        speed += preset["speedScale"] * ratio
        intonation += preset["intonationScale"] * ratio
        volume += preset["volumeScale"] * ratio

    return {
        "speaker": speaker_id,
        "pitchScale": round(pitch, 3),
        "speedScale": round(speed, 3),
        "intonationScale": round(intonation, 3),
        "volumeScale": round(volume, 3),
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
    }

def synthesize_voice(text: str, settings: dict, base_url: str = "http://localhost:50021") -> bytes:
    try:
        query_resp = requests.post(
            f"{base_url}/audio_query",
            params={"text": text, "speaker": settings["speaker"]},
        )
        query_resp.raise_for_status()
        audio_query = query_resp.json()

        for key in ["pitchScale", "speedScale", "intonationScale", "volumeScale", "prePhonemeLength", "postPhonemeLength"]:
            audio_query[key] = settings[key]

        synth_resp = requests.post(
            f"{base_url}/synthesis",
            params={"speaker": settings["speaker"]},
            json=audio_query,
        )
        synth_resp.raise_for_status()

        return synth_resp.content

    except Exception as e:
        logger.error(f"[VoiceVox] 音声生成失敗: {e}")
        return b""
