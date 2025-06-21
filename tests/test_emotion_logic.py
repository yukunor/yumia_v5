import pytest
import os
import json
from datetime import datetime, timedelta

from module.response.response_index import search_similar_emotions
from module.memory.divide_emotion import get_memory_category
from module.memory.oblivion_emotion import clean_old_emotions

# パス分割のためのモックデータ
def test_search_similar_emotions_windows_path(monkeypatch):
    sample_emotion = {
        "主感情": "喜び",
        "構成比": {
            "喜び": 60,
            "信頼": 30,
            "期待": 10
        }
    }

    test_index = [
        {
            "主感情": "喜び",
            "構成比": {
                "喜び": 60,
                "信頼": 30,
                "期待": 10
            },
            "保存先": "memory\\short\\Joy.json"
        }
    ]

    monkeypatch.setattr("module.response.response_index.load_index", lambda: test_index)
    result = search_similar_emotions(sample_emotion)
    assert "short" in result
    assert len(result["short"]) == 1

# get_memory_category の重み境界テスト
@pytest.mark.parametrize("weight,expected", [
    (50, "short"),
    (80, "intermediate"),
    (95, "long")
])
def test_get_memory_category_param(weight, expected):
    assert get_memory_category(weight) == expected

# clean_old_emotions 削除ロジックテスト
def test_clean_old_emotions(tmp_path):
    index_path = tmp_path / "emotion_index.jsonl"
    memory_path = tmp_path / "memory"
    memory_path.mkdir()
    memory_file = memory_path / "short.json"
    oblivion_path = tmp_path / "oblivion.jsonl"

    old_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d%H%M%S")

    index_entry = {
        "date": old_date,
        "主感情": "喜び",
        "構成比": {"喜び": 100},
        "保存先": str(memory_file),
        "キーワード": ["テスト"]
    }
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(index_entry, ensure_ascii=False) + "\n")

    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump({"履歴": [index_entry]}, f, ensure_ascii=False)

    # パスを一時的に上書き
    from module.memory import oblivion_emotion
    oblivion_emotion.INDEX_PATH = str(index_path)
    oblivion_emotion.OBLIVION_PATH = str(oblivion_path)

    clean_old_emotions()

    with open(oblivion_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1

    with open(memory_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["履歴"] == []
