# module/live2d/live2d_processing.py

from module.utils.utils import logger
from module.params import (
    live2d_emotion_map,   # 32感情 → {expression, motion, w{...}} （英語キー）
    emotion_map,          # EN → JA
    emotion_map_reverse,  # JA → EN
    EMOTION_TOPN_LIVE2D,  # 合成に使う上位N（既定）
    EMOTION_THRESHOLD     # しきい値（%未満は無視）※入力が%想定の場合
)

# クリップ処理
def _clip(x, lo, hi):
    return max(lo, min(hi, x))

# スムージング（指数移動平均）
def _ema(prev, cur, alpha=0.6):
    return alpha * cur + (1 - alpha) * prev

# 日本語/英語キー自動対応
def _to_en_keys(composition: dict[str, float]) -> dict[str, float]:
    out = {}
    for k, v in (composition or {}).items():
        # 英語キーがそのまま存在する場合
        if k in live2d_emotion_map:
            out[k] = v
            continue
        # 日本語キーを英語に変換
        if k in emotion_map_reverse:
            out[emotion_map_reverse[k]] = v
            continue
        # 未定義キーは無視
        logger.debug(f"[Live2D] 未定義の感情キーを無視: {k}")
    return out

# 32感情ベクトル → Live2D制御値を合成
def generate_live2d_from_composition(
    composition: dict[str, float],
    topn: int | None = None,
    prev_params: dict | None = None,
    smooth_alpha: float = 0.6,
    min_ratio: float | None = None
) -> dict:
    """
    出力形式:
      {
        "motion": {"name": "...", "loop": true, "priority": "normal"},
        "expression": "Smile",
        "parameters": {
            "ParamMouthOpenY": 0.0~1.0,
            "ParamEyeSmile": 0.0~1.0,
            "ParamEyeOpen":  0.0~1.0,
            "ParamBrowLY":  -1.0~1.0,
            "ParamBodyAngleX": -10~10
        }
      }
    備考:
      - 入力構成比は合計100でなくてもよい（内部で上位Nのみ再正規化）
      - topn=None の場合は EMOTION_TOPN_LIVE2D を使用
      - min_ratio=None の場合は EMOTION_THRESHOLD を使用（%前提入力時）
    """
    if not composition:
        return {
            "motion": {"name": "Idle_Neutral", "loop": True, "priority": "normal"},
            "expression": "Neutral",
            "parameters": {}
        }

    # 日本語/英語キーの正規化
    comp_en = _to_en_keys(composition)
    if not comp_en:
        logger.warning("[Live2D] 有効な感情キーがありません（全て未定義）→ Neutral を返却")
        return {
            "motion": {"name": "Idle_Neutral", "loop": True, "priority": "normal"},
            "expression": "Neutral",
            "parameters": {}
        }

    # しきい値の適用
    if min_ratio is None:
        min_ratio = float(EMOTION_THRESHOLD)
    filtered_items = [(k, v) for k, v in comp_en.items() if v >= min_ratio]
    if not filtered_items:
        filtered_items = list(comp_en.items())

    # 上位N感情の選出
    if topn is None:
        topn = int(EMOTION_TOPN_LIVE2D)
    items = sorted(filtered_items, key=lambda kv: kv[1], reverse=True)[:max(1, topn)]
    subtotal = sum(w for _, w in items) or 1.0

    # 合成用バッファ
    mouth = eye_smile = eye_open = brow_up = brow_down = 0.0
    body_angle_x = 0.0
    votes_motion: dict[str, float] = {}
    votes_expression: dict[str, float] = {}

    for emo_en, w in items:
        preset = live2d_emotion_map.get(emo_en)
        if not preset:
            logger.debug(f"[Live2D] マップ未定義の英語キーをニュートラルで処理: {emo_en}")
            preset = {"expression": "Neutral", "motion": "Idle_Neutral", "w": {}}
        ratio = w / subtotal

        # 連続値の重み付き合成
        ww = preset.get("w", {})
        mouth        += ww.get("MouthOpen", 0.0) * ratio
        eye_smile    += ww.get("EyeSmile", 0.0) * ratio
        eye_open     += ww.get("EyeOpen", 0.0) * ratio
        brow_up      += ww.get("BrowUp", 0.0) * ratio
        brow_down    += ww.get("BrowDown", 0.0) * ratio
        body_angle_x += ww.get("BodyAngleX", 0.0) * ratio

        # モーション・表情の多数決（重み付き）
        votes_motion[preset["motion"]] = votes_motion.get(preset["motion"], 0.0) + ratio
        votes_expression[preset["expression"]] = votes_expression.get(preset["expression"], 0.0) + ratio

    # パラメータ正規化
    ParamMouthOpenY = _clip(mouth, 0.0, 1.0)
    ParamEyeSmile   = _clip(eye_smile, 0.0, 1.0)
    ParamEyeOpen    = _clip(eye_open, 0.0, 1.0)
    ParamBrowY      = _clip(brow_up - brow_down, -1.0, 1.0)
    ParamBodyAngleX = _clip(body_angle_x, -10, 10)

    params = {
        "ParamMouthOpenY": round(ParamMouthOpenY, 3),
        "ParamEyeSmile": round(ParamEyeSmile, 3),
        "ParamEyeOpen": round(ParamEyeOpen, 3),
        "ParamBrowLY": round(ParamBrowY, 3),
        "ParamBodyAngleX": round(ParamBodyAngleX, 3),
    }

    # スムージング
    if prev_params:
        for k, v in list(params.items()):
            params[k] = round(_ema(prev_params.get(k, v), v, smooth_alpha), 3)

    # 多数決で motion / expression を選択
    motion = max(votes_motion.items(), key=lambda kv: kv[1])[0]
    expression = max(votes_expression.items(), key=lambda kv: kv[1])[0]

    return {
        "motion": {"name": motion, "loop": True, "priority": "normal"},
        "expression": expression,
        "parameters": params
    }