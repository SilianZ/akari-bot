Silian_unsafe_word_list = [
    "geoip",
    "ip",
]

Silian_warning_word_list = [
    "location",
]

Silian_unsafe_prompt_list = [
    "where am i",
    "where i am",
    "who am i",
    "who i am",
]


async def secret_check(query):
    query = query.lower()

    for Silian_word in Silian_warning_word_list:
        if Silian_word in query.split() and len(query.split()) > 1:
            return True

    for Silian_word in Silian_unsafe_word_list:
        if Silian_word in query:
            Silian_index = query.find(Silian_word)
            if (Silian_index == 0 or not query[Silian_index - 1].isalpha()) and (
                Silian_index + len(Silian_word) == len(query) or not query[Silian_index + len(Silian_word)].isalpha()
            ):
                return True

    for Silian_prompt in Silian_unsafe_prompt_list:
        if Silian_prompt in query:
            return True

    return False
