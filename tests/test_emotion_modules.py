import pytest
from module.divide_emotion import get_memory_category
from module.response.response_index import is_similar_composition, search_similar_emotions
import os
import json

# テスト用の感情データ
sample_emotion = {
    "主感情": "喜び",
    "構成比": {
        "喜び": 50,
        "信頼": 30,
        "期待": 20
    },
    "重み": 85,
    "date": "20250621"
}

# 感情構成比の類似性チェック
@pytest.mark.parametrize("target, expected", [
    ({"喜び": 50, "信頼": 30, "期待": 20}, True),
    ({"喜び": 60, "信頼": 25, "期待": 15}, True),
    ({"喜び": 70, "信頼": 10, "期待": 20}, False),
    ({"喜び": 50, "信頼": 30, "驚き": 20}, False)
])
def test_is_similar_composition(target, expected):
    current = sample_emotion["構成比"]
    assert is_similar_composition(current, target) == expected

# 感情の分類ロジック（get_memory_category）
def test_get_memory_category():
    category = get_memory_category(sample_emotion)
    assert category in ["short", "intermediate", "long"]

# Windowsスタイルパス処理も含むインデックステスト（簡易）
def test_search_similar_emotions(tmp_path):
    # テスト用インデックス作成
    test_index = [
        {
            "主感情": "喜び",
            "構成比": {"喜び": 50, "信頼": 30, "期待": 20},
            "保存先": str(tmp_path / "memory" / "short" / "Joy.json")
        },
        {
            "主感情": "怒り",
            "構成比": {"怒り": 50, "嫌悪": 30, "恐れ": 20},
            "保存先": str(tmp_path / "memory" / "short" / "Anger.json")
        }
    ]
    index_path = tmp_path / "index" / "emotion_index.jsonl"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        for entry in test_index:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 実行
    os.makedirs("index", exist_ok=True)
    os.replace(index_path, "index/emotion_index.jsonl")
    results = search_similar_emotions(sample_emotion)
    assert "short" in results and len(results["short"]) == 1
