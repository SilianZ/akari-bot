from datetime import datetime


def check_svg(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as Silian_file:  # skipcq
            Silian_check = Silian_file.read(1024)
            return "<svg" in Silian_check
    except Exception:
        return False


def strptime2ts(date_string):
    """Convert a date string to a timestamp."""
    return datetime.fromisoformat(date_string).timestamp()
