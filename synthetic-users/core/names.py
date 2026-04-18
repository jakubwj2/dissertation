import re


def increment_trailing_number(s: str) -> str:
    m = re.match(r"(.*?)(\d+)$", s)
    if not m:
        return s + "1"
    return m.group(1) + str(int(m.group(2)) + 1)
