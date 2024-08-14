import re


def clean_file_name(name: str) -> str:
    """Removes common and unnecessary strings from file names"""
    reg_exps = [
        r"\((?:\D.+?|.+?\D)\)|\[(?:\D.+?|.+?\D)\]",  # (2016), [2016], etc
        r"\(?(?:240|360|480|720|1080|1440|2160)p?\)?",  # 1080p, 720p, etc
        r"\b(?:mp4|mkv|wmv|m4v|mov|avi|flv|webm|flac|mka|m4a|aac|ogg)\b",  # file types
        r"season ?\d+?",  # season 1, season 2, etc
        # more stuffs
        r"(?:S\d{1,3}|\d+?bit|dsnp|web\-dl|ddp\d+? ? \d|hevc|hdrip|\-?Vyndros)",
        # URLs in filenames
        r"^(?:https?:\/\/)?(?:www.)?[a-z0-9]+\.[a-z]+(?:\/[a-zA-Z0-9#]+\/?)*$",
    ]
    for reg in reg_exps:
        name = re.sub(reg, "", name)
    return name.strip().rstrip(".-_")


def readable_time(runtime_minutes):
    hours = runtime_minutes // 60
    minutes = runtime_minutes % 60
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"