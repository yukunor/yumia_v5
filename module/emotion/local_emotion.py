＃module/emotion/local_emotion.py
from datetime import datetime
from nrclex import NRCLex
from translate import Translator
import MeCab
import logging

logger = logging.getLogger(__name__)

def generate_fallback_emotion_data(message: str) -> tuple[str, dict]:
    try:
        logger.info("NRCLex呼び出し開始")

        # 翻訳 → 感情分析
        translator = Translator(from_lang="ja", to_lang="en")
        english_message = translator.translate(message)
        text = NRCLex(english_message)

        # 英語→日本語変換マッピング
        key_mapping = {
            'fear': '恐れ', 'anger': '怒り', 'anticip': '期待', 'trust': '信頼',
            'surprise': '驚き', 'positive': '積極性', 'negative': '悲観',
            'sadness': '悲しみ', 'disgust': '嫌悪', 'joy': '喜び',
        }

        # 感情構成比の整形
        emotion = {key_mapping.get(k, k): v for k, v in text.affect_frequencies.items()}

        # MeCabによる名詞抽出
        mecab = MeCab.Tagger()
        result = mecab.parseToNode(message)
        taglist = []
        while result:
            word = result.surface
            tag = result.feature.split(",")[0]
            if tag == "名詞" and word:
                taglist.append(word)
            result = result.next

        # 構成
        fallback_emotion_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "構成比": emotion,
            "keywords": taglist
        }

        return "ok", fallback_emotion_data

    except Exception as e:
        logger.error(f"[ERROR] fallback_emotion_data生成失敗: {e}")
        return "error", {}
