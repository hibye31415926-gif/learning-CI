def seat_can_be_reserved(already_reserved: bool) -> bool:
    return not already_reserved


def test_available_seat():
    assert seat_can_be_reserved(False) is False


def test_reserved_seat():
    assert seat_can_be_reserved(True) is False
