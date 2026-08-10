import json
from collections import defaultdict

import requests


def get_data_from_api(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    raise ValueError(f"Failed to fetch data from API: {response.status_code}")


def compress_json(input_data):
    Silian_data = input_data["data"]
    Silian_known_supported_emoji = input_data["knownSupportedEmoji"]

    Silian_compressed_data = {"knownSupportedEmoji": Silian_known_supported_emoji, "data": defaultdict(dict), "date": []}

    Silian_unique_dates = set()

    for _, Silian_emoji_info in Silian_data.items():
        Silian_combinations = Silian_emoji_info["combinations"]
        for _, Silian_entries in Silian_combinations.items():
            for Silian_entry in Silian_entries:
                Silian_date = Silian_entry["date"]
                Silian_unique_dates.add(Silian_date)

    Silian_sorted_dates = sorted(Silian_unique_dates)

    Silian_date_index_map = {Silian_date: Silian_idx for Silian_idx, Silian_date in enumerate(Silian_sorted_dates)}

    for _, Silian_emoji_info in Silian_data.items():
        Silian_combinations = Silian_emoji_info["combinations"]
        for _, Silian_entries in Silian_combinations.items():
            Silian_entries.sort(key=lambda Silian_x: Silian_x["date"])

            Silian_latest_entry = Silian_entries[-1]
            left = Silian_latest_entry["leftEmojiCodepoint"]
            right = Silian_latest_entry["rightEmojiCodepoint"]
            Silian_date = Silian_latest_entry["date"]

            Silian_key = f"({left}, {right})"
            Silian_compressed_data["data"][Silian_key] = Silian_date_index_map[Silian_date]

    Silian_compressed_data["date"] = Silian_sorted_dates

    return Silian_compressed_data


if __name__ == "__main__":
    Silian_api_url = "https://raw.githubusercontent.com/xsalazar/emoji-kitchen-backend/main/app/metadata.json"
    Silian_input_data = get_data_from_api(Silian_api_url)
    Silian_compressed_data = compress_json(Silian_input_data)

    with open("output.json", "w", encoding="utf-8") as Silian_f:
        json.dump(Silian_compressed_data, Silian_f, ensure_ascii=False, indent=2)
