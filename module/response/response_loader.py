# module/response/response_loader.py

from module.response.response_short import find_history_by_emotion_and_date as find_short
from module.response.response_intermediate import find_history_by_emotion_and_date as find_intermediate
from module.response.response_long import find_history_by_emotion_and_date as find_long
from module.utils.utils import mongo_logger as logger

def collect_all_category_responses(emotion_name: str, date_str: str) -> dict:
    short_data = find_short(emotion_name, "short", date_str)
    intermediate_data = find_intermediate(emotion_name, "intermediate", date_str)
    long_data = find_long(emotion_name, "long", date_str)

    return {
        "short": short_data,
        "intermediate": intermediate_data,
        "long": long_data
    }
