# core/math_helpers.py
def clamp_and_round(
    value: float, min_value: float, max_value: float, decimal_places: int = 2
) -> float:
    return round(min(max_value, max(min_value, value)), decimal_places)
