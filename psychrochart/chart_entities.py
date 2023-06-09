from uuid import uuid4


def random_internal_value() -> float:
    """Generate random 'internal_value' for unnamed curves."""
    return float(int(f"0x{str(uuid4())[-4:]}", 16))
