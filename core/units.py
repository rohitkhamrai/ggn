# core/units.py

def assert_mm(unit_str: str):
    if unit_str.strip().lower() != "mm":
        raise ValueError(f"Expected mm, got {unit_str}")
