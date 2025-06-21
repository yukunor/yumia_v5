import pytest
from module.memory.divide_emotion import get_memory_category
from module.response.response_index import is_similar_composition

def test_get_memory_category():
    sample_emotion = {
        "主感情": "喜び",
        "構成比": {
            "喜び": 60,
            "信頼": 30,
            "期待": 10
        },
        "重み": 100
    }
    category = get_memory_category(sample_emotion["重み"])
    assert category in ["short", "intermediate", "long"], "不正なカテゴリ"

def test_is_similar_composition_exact_match():
    comp1 = {"喜び": 50, "信頼": 30, "期待": 20}
    comp2 = {"喜び": 50, "信頼": 30, "期待": 20}
    assert is_similar_composition(comp1, comp2) == True

def test_is_similar_composition_within_threshold():
    comp1 = {"喜び": 50, "信頼": 30, "期待": 20}
    comp2 = {"喜び": 55, "信頼": 25, "期待": 20}
    assert is_similar_composition(comp1, comp2) == True

def test_is_similar_composition_exceed_threshold():
    comp1 = {"喜び": 50, "信頼": 30, "期待": 20}
    comp2 = {"喜び": 70, "信頼": 15, "期待": 15}
    assert is_similar_composition(comp1, comp2) == False

def test_is_similar_composition_key_mismatch():
    comp1 = {"喜び": 50, "信頼": 30, "期待": 20}
    comp2 = {"喜び": 50, "信頼": 30}
    assert is_similar_composition(comp1, comp2) == False
