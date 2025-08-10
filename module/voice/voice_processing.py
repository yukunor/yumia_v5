# module/voice/voice_processing.py

import requests
from module.utils.utils import logger

# 32感情 → VoiceVox合成パラメータ
# 32 emotions → VoiceVox parameter presets
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

# 🔧 クリップ関数
# Clamp helper
def _clip(v, lo, hi):
    return max(lo, min(hi, v))

# 🎚 スムージング（指数移動平均）
# Exponential moving average smoothing
def _ema(prev, cur, alpha=0.7):
    return alpha * cur + (1 - alpha) * prev

# 32感情ベクトル → VoiceVox設定（ずんだもん固定）
# 32-emotion composition → VoiceVox settings (Zundamon fixed)
def generate_voicevox_settings_from_composition(
    composition: dict[str, float],
    speaker_id: int = 3,
    topn: int = 5,
    prev_settings: dict | None = None,
    smooth_alpha: float = 0.7
) -> dict:
    # 🔸 空/ゼロ対策
    # Guard for empty/zero vector
    total = sum(composition.values()) if composition else 0.0
    if total <= 0:
        base = {
            "speaker": speaker_id,
            "pitchScale": 0.0,
            "speedScale": 1.0,
            "intonationScale": 1.0,
            "volumeScale": 1.0,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1
        }
        if prev_settings:
            for k in ["pitchScale", "speedScale", "intonationScale", "volumeScale"]:
                base[k] = round(_ema(prev_settings.get(k, base[k]), base[k], smooth_alpha), 3)
        return base

    # 🔸 未定義キーの無視（ログのみ）
    # Ignore unknown emotion keys
    unknown = [k for k in composition.keys() if k not in VOICEVOX_EMOTION_MAP]
    if unknown:
        logger.debug(f"[VoiceVox] 未定義の感情キーを無視: {unknown}")

    # 🔸 上位N感情のみで合成（ノイズ低減）
    # Use top-N emotions only to reduce noise
    items = sorted(composition.items(), key=lambda kv: kv[1], reverse=True)[:max(1, topn)]
    subtotal = sum(w for _, w in items) or 1.0

    pitch = speed = intonation = volume = 0.0
    for emotion, weight in items:
        preset = VOICEVOX_EMOTION_MAP.get(emotion)
        if not preset:
            continue
        ratio = weight / subtotal
        pitch       += preset["pitchScale"]      * ratio
        speed       += preset["speedScale"]      * ratio
        intonation  += preset["intonationScale"] * ratio
        volume      += preset["volumeScale"]     * ratio

    # 🔸 安全レンジにクリップ
    # Clip to safe ranges
    pitch      = _clip(round(pitch, 3),      -0.6, 0.6)
    speed      = _clip(round(speed, 3),       0.5, 1.5)
    intonation = _clip(round(intonation, 3),  0.5, 1.6)
    volume     = _clip(round(volume, 3),      0.7, 1.3)

    settings = {
        "speaker": speaker_id,
        "pitchScale": pitch,
        "speedScale": speed,
        "intonationScale": intonation,
        "volumeScale": volume,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
    }

    # 🔸 前回値があればスムージング
    # Smooth with previous settings if available
    if prev_settings:
        for k in ["pitchScale", "speedScale", "intonationScale", "volumeScale"]:
            settings[k] = round(_ema(prev_settings.get(k, settings[k]), settings[k], smooth_alpha), 3)

    return settings


# VoiceVoxで音声合成
# Synthesize with VoiceVox
def synthesize_voice(text: str, settings: dict, base_url: str = "http://localhost:50021") -> bytes:
    try:
        query_resp = requests.post(
            f"{base_url}/audio_query",
            params={"text": text, "speaker": settings["speaker"]},
            timeout=10
        )
        query_resp.raise_for_status()
        audio_query = query_resp.json()

        for key in ["pitchScale", "speedScale", "intonationScale", "volumeScale", "prePhonemeLength", "postPhonemeLength"]:
            audio_query[key] = settings[key]

        synth_resp = requests.post(
            f"{base_url}/synthesis",
            params={"speaker": settings["speaker"]},
            json=audio_query,
            timeout=20
        )
        synth_resp.raise_for_status()

        return synth_resp.content

    except Exception as e:
        logger.error(f"[VoiceVox] 音声生成失敗: {e}")
        return b""
