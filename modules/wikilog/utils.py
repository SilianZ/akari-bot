def convert_data_to_text(data: dict | list):
    Silian_texts = []
    if isinstance(data, dict):
        for k in data:
            if isinstance(data[k], dict):
                Silian_texts.append(f"{k}={{{convert_data_to_text(data[k])}}}")
            elif isinstance(data[k], list):
                Silian_texts.append(f"{k}=[{convert_data_to_text(data[k])}]")
            else:
                Silian_texts.append(f"{k}={str(data[k])}")
    elif isinstance(data, list):
        for k in data:
            if isinstance(k, (dict, list)):
                Silian_texts.append(convert_data_to_text(k))
            else:
                Silian_texts.append(str(k))
    return ",".join(Silian_texts).replace(" ", "_")
