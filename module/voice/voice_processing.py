# module/voice/voice_processing.py

import requests
from module.utils.utils import logger
from module.params import (
    voicevox_emotion_map,   # 32感情 → VoiceVoxパラメータ（英語キー）
    emotion_map,            # EN → JA
    emotion_map_reverse,    # JA → EN
    VOICEVOX_CLIP,          # クリップ範囲 dict
    EMOTION_TOPN_VOICEVOX,  # 合成に使う上位N
)

# 任意：デフォルト話者IDを params に置いておくとさらに楽
try:
    from module.params import VOICEVOX_DEFAULT_SPEAKER
except Exception:
    VOICEVOX_DEFAULT_SPEAKER = 3  # ずんだもん

# クリップ
def _clip(v, lo, hi):
    return max(lo, min(hi, v))

# スムージング（指数移動平均）
def _ema(prev, cur, alpha=0.7):
    return alpha * cur + (1 - alpha) * prev

# 日本語/英語キー自動対応（VoiceVoxマップは英語キー前提）
def _to_en_keys(composition: dict[str, float]) -> dict[str, float]:
    out = {}
    for k, v in (composition or {}).items():
        if k in voicevox_emotion_map:                # 既に英語キー
            out[k] = v
        elif k in emotion_map_reverse:               # 日本語 → 英語
            out[emotion_map_reverse[k]] = v
        else:
            logger.debug(f"[VoiceVox] 未定義の感情キーを無視: {k}")
    return out

# 32感情ベクトル → VoiceVox設定（ずんだもん固定）
def generate_voicevox_settings_from_composition(
    composition: dict[str, float],
    speaker_id: int = VOICEVOX_DEFAULT_SPEAKER,
    topn: int | None = None,
    prev_settings: dict | None = None,
    smooth_alpha: float = 0.7
) -> dict:
    # 空/ゼロ
    total = sum((composition or {}).values()) if composition else 0.0
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

    comp_en = _to_en_keys(composition)
    if not comp_en:
        logger.warning("[VoiceVox] 有効な感情キーなし → Neutral設定で返却")
        return {
            "speaker": speaker_id,
            "pitchScale": 0.0,
            "speedScale": 1.0,
            "intonationScale": 1.0,
            "volumeScale": 1.0,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1
        }

    # 上位N抽出
    if topn is None:
        topn = int(EMOTION_TOPN_VOICEVOX)
    items = sorted(comp_en.items(), key=lambda kv: kv[1], reverse=True)[:max(1, topn)]
    subtotal = sum(w for _, w in items) or 1.0

    pitch = speed = intonation = volume = 0.0
    for emo_en, weight in items:
        preset = voicevox_emotion_map.get(emo_en)
        if not preset:
            continue
        ratio = weight / subtotal
        pitch      += preset["pitchScale"]      * ratio
        speed      += preset["speedScale"]      * ratio
        intonation += preset["intonationScale"] * ratio
        volume     += preset["volumeScale"]     * ratio

    # クリップ範囲を params から
    p_lo, p_hi = VOICEVOX_CLIP["pitchScale"]
    s_lo, s_hi = VOICEVOX_CLIP["speedScale"]
    i_lo, i_hi = VOICEVOX_CLIP["intonationScale"]
    v_lo, v_hi = VOICEVOX_CLIP["volumeScale"]

    settings = {
        "speaker": speaker_id,
        "pitchScale": _clip(round(pitch, 3), p_lo, p_hi),
        "speedScale": _clip(round(speed, 3), s_lo, s_hi),
        "intonationScale": _clip(round(intonation, 3), i_lo, i_hi),
        "volumeScale": _clip(round(volume, 3), v_lo, v_hi),
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
    }

    # スムージング
    if prev_settings:
        for k in ["pitchScale", "speedScale", "intonationScale", "volumeScale"]:
            settings[k] = round(_ema(prev_settings.get(k, settings[k]), settings[k], smooth_alpha), 3)

    return settings

# VoiceVoxで音声合成
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