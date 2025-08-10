# module/emotion/emotion_stats.py
import os
import json
import math
from datetime import datetime, timezone

from module.utils.utils import logger
from module.mongo.mongo_client import get_mongo_client
from module.params import emotion_map, emotion_map_reverse

# =========================
# 基本ユーティリティ
# =========================

def _now_utc_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z")

def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        # 旧形式（ローカル時刻）も取り込み
        return datetime.fromisoformat(ts.replace(" ", "T").replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

def _seconds_since(ts_str: str | None) -> float:
    ts = _parse_ts(ts_str)
    if not ts:
        return 0.0
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - ts).total_seconds())

# 🔸 構成比を32感情に正規化（日本語キー順）
def normalize_composition_vector(raw_composition: dict) -> dict:
    return {emotion: float(raw_composition.get(emotion, 0)) for emotion in emotion_map_reverse.keys()}

# =========================
# 現在感情：読み書き
# =========================

def load_current_emotion():
    """互換：ベクトルのみ返す（従来通り）"""
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            col = db["current_emotion"]
            latest = col.find_one(sort=[("timestamp", -1)])
            return latest.get("emotion_vector", {}) if latest else {}
    except Exception as e:
        logger.error(f"[ERROR] 現在感情の読み込みに失敗: {e}")
    return {}

def load_current_emotion_with_meta():
    """新規：ベクトル＋メタ（timestamp）を返す"""
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            col = db["current_emotion"]
            latest = col.find_one(sort=[("timestamp", -1)])
            if latest:
                return {
                    "emotion_vector": latest.get("emotion_vector", {}),
                    "timestamp": latest.get("timestamp")
                }
    except Exception as e:
        logger.error(f"[ERROR] 現在感情(with meta)の読み込みに失敗: {e}")
    return {"emotion_vector": {}, "timestamp": None}

def save_current_emotion(emotion_vector: dict):
    try:
        client = get_mongo_client()
        if client:
            db = client["emotion_db"]
            col = db["current_emotion"]
            entry = {
                "timestamp": _now_utc_str(),
                "emotion_vector": emotion_vector
            }
            col.insert_one(entry)
            logger.info("[INFO] 現在感情をMongoDBに保存しました")
    except Exception as e:
        logger.error(f"[ERROR] 現在感情の保存に失敗: {e}")

# =========================
# 感情ダイナミクス設定
# =========================

# 半減期（秒）：時間経過で v *= 0.5 ** (dt/half_life)
# 速く冷める：驚き/怒り/嫌悪　遅く尾を引く：悲しみ/恥/罪悪感/信頼/愛
HALF_LIFE_SEC = {
    "驚き": 15, "怒り": 40, "嫌悪": 60, "恐れ": 60,
    "喜び": 120, "楽観": 120, "歓喜": 90, "期待": 90, "好奇心": 90,
    "悲しみ": 180, "失望": 150, "絶望": 240, "感傷": 200,
    "恥": 200, "罪悪感": 220, "自責": 220,
    "信頼": 300, "愛": 300, "希望": 180, "優位": 150,
    # その他が来ても既定値で処理
}
DEFAULT_HALF_LIFE = 120

FAST_DECAY = {"驚き", "怒り", "嫌悪"}
STICKY = {"悲しみ", "恥", "罪悪感", "自責", "信頼", "愛", "絶望"}

# 相互抑制（弱め）：怒り↑で信頼/愛/恐れ↓、悲しみ↑で怒り↓ 等
CROSS_INHIBIT = {
    "怒り": {"信頼": 0.08, "愛": 0.05, "恐れ": 0.03, "悲しみ": 0.02},
    "悲しみ": {"怒り": 0.04, "楽観": 0.05},
    "驚き": {"信頼": 0.02},
    "恐れ": {"優位": 0.05},
    "信頼": {"不信": 0.08, "怒り": 0.03},
    "愛": {"軽蔑": 0.06, "怒り": 0.02},
}

# スパイク制御
MAX_DELTA_UP = 25.0   # 1回の更新で増加できる最大ポイント
MAX_DELTA_DOWN = 20.0 # 1回の更新で減少できる最大ポイント
REFRACTORY_SEC = 20.0 # 大スパイク後の再上昇を抑える期間
BIG_SPIKE_THRESHOLD = 35.0

# ホメオスタシス：ニュートラルへ引き戻す微弱バイアス
HOMEOSTASIS_STRENGTH = 0.02  # 0..1 小さいほど弱い

# 適応的ブレンド：高覚醒（怒/驚/恐）時は反応速く、低覚醒時はゆっくり
ALPHA_MIN, ALPHA_MAX = 0.15, 0.45  # 新規ベクトルへの重み範囲

HIGH_AROUSAL = {"怒り", "驚き", "恐れ"}

# =========================
# ダイナミクス関数
# =========================

def _apply_time_decay(vec: dict, dt_sec: float) -> dict:
    if dt_sec <= 0:
        return dict(vec)
    out = {}
    for k, v in vec.items():
        try:
            v = float(v)
        except (ValueError, TypeError):
            continue
        hl = HALF_LIFE_SEC.get(k, DEFAULT_HALF_LIFE)
        decay = 0.5 ** (dt_sec / max(1.0, hl))
        out[k] = max(0.0, v * decay)
    return out

def _bounded_delta(prev: float, target: float) -> float:
    delta = target - prev
    if delta >= 0:
        return prev + min(delta, MAX_DELTA_UP)
    else:
        return prev + max(delta, -MAX_DELTA_DOWN)

def _adaptive_alpha(new_vec: dict) -> float:
    # 高覚醒感情の総和(0..100) → 0..1 に正規化
    arousal = sum(new_vec.get(e, 0.0) for e in HIGH_AROUSAL)
    arousal = max(0.0, min(100.0, arousal)) / 100.0
    return ALPHA_MIN + (ALPHA_MAX - ALPHA_MIN) * arousal

def _cross_inhibit(vec: dict) -> dict:
    out = dict(vec)
    for src, sinks in CROSS_INHIBIT.items():
        s_val = out.get(src, 0.0)
        if s_val <= 0:
            continue
        for tgt, coeff in sinks.items():
            out[tgt] = max(0.0, out.get(tgt, 0.0) * (1.0 - coeff * s_val / 100.0))
    return out

def _homeostasis_pull(vec: dict) -> dict:
    # 総量=100想定。平均化方向へ微調整（過度に尖った状態を少し丸める）
    if not vec:
        return vec
    mean = sum(vec.values()) / len(vec)
    out = {}
    for k, v in vec.items():
        out[k] = v + (mean - v) * HOMEOSTASIS_STRENGTH
        if out[k] < 0:
            out[k] = 0.0
    return out

def _normalize(vec: dict) -> dict:
    total = sum(max(0.0, float(v)) for v in vec.values())
    if total <= 0:
        return {k: 0.0 for k in vec.keys()}
    return {k: round(100.0 * max(0.0, float(v)) / total, 2) for k in vec.keys()}

# =========================
# 感情ベクトル合成
# =========================

def merge_emotion_vectors(
    current: dict,
    new: dict,
    weight_new: float | None = None,
    decay_factor: float | None = None,
    normalize: bool = True,
    current_timestamp: str | None = None
) -> dict:
    """
    既存ベクトル current と新規ベクトル new を“時間依存+適応的”に合成。
    - 時間減衰（半減期）
    - スパイク抑制（1回の上げ下げ量に限界）
    - 相互抑制（弱）
    - ホメオスタシス（弱）
    - 適応的ブレンド（高覚醒時は反応速い）

    互換のため weight_new/decay_factor 引数は受け取るが内部では未使用。
    """
    # 1) 型補正
    corr_new = {}
    for k, v in new.items():
        kk = k.split(":", 1)[0].strip() if isinstance(k, str) and ":" in k else k
        try:
            corr_new[kk] = float(v)
        except (ValueError, TypeError):
            continue

    # 2) 時間減衰（currentに対して）
    dt = _seconds_since(current_timestamp)
    decayed = _apply_time_decay(current, dt)

    # 3) 適応アルファ（新規寄与）
    alpha = _adaptive_alpha(corr_new) if weight_new is None else float(weight_new)

    # 4) ブレンド（素の目標）
    keys = set(decayed.keys()) | set(corr_new.keys())
    target = {}
    for k in keys:
        old = float(decayed.get(k, 0.0))
        nv  = float(corr_new.get(k, 0.0))
        # 急騰しやすい感情は伸びやすく/冷めやすくなるよう微差を付与
        a = alpha
        if k in FAST_DECAY:
            a = min(1.0, a * 1.15)
        if k in STICKY:
            a = max(0.0, a * 0.85)
        val = (1.0 - a) * old + a * nv
        target[k] = max(0.0, val)

    # 5) スパイク制御＋リフラクトリ（簡易）
    merged = {}
    big_spike = any(corr_new.get(k, 0.0) - decayed.get(k, 0.0) >= BIG_SPIKE_THRESHOLD for k in keys)
    for k in keys:
        prev = float(decayed.get(k, 0.0))
        val  = float(target.get(k, 0.0))
        if big_spike and k in FAST_DECAY:
            # 大スパイク直後は再上昇を抑える
            val = min(val, prev + MAX_DELTA_UP * 0.5)
        merged[k] = _bounded_delta(prev, val)

    # 6) 相互抑制 → ホメオスタシス → 正規化
    merged = _cross_inhibit(merged)
    merged = _homeostasis_pull(merged)
    if normalize:
        merged = _normalize(merged)

    return merged

# =========================
# 32感情 → 6感情要約
# =========================

def summarize_feeling(feeling_vector: dict) -> dict:
    """
    32→6軸へ縮約。軸ごとの代表感情に重み付け（丸め込みの偏りを緩和）。
    出力は0..10の整数スコア。
    """
    w = lambda x: feeling_vector.get(x, 0.0)
    # 重み（例）：代表>補助
    joy = 0.45*w("喜び") + 0.25*w("楽観") + 0.15*w("歓喜") + 0.15*w("愛")
    anger = 0.6*w("怒り") + 0.25*w("憤慨") + 0.15*w("軽蔑")
    sadness = 0.4*w("悲しみ") + 0.25*w("失望") + 0.2*w("絶望") + 0.15*w("感傷")
    fun = 0.5*w("好奇心") + 0.3*w("期待") + 0.2*w("喜び")
    confidence = 0.6*w("優位") + 0.4*w("誇り")
    confusion = 0.45*w("恐れ") + 0.35*w("不安") + 0.2*w("不信")

    summary = {
        "喜び": joy, "怒り": anger, "悲しみ": sadness,
        "楽しさ": fun, "自信": confidence, "困惑": confusion
    }
    # 0..100 → 0..10
    summary = {k: int(round(min(100.0, max(0.0, v)) / 10.0)) for k, v in summary.items()}

    logger.info("【6感情サマリー】")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary
