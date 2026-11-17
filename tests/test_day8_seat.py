def can_reserve_seat(already_reserved: bool) -> bool:
    return not already_reserved


def test_available_seat():
    assert can_reserve_seat(False) is True


def test_reserved_seat():
    assert can_reserve_seat(True) is False


def test_intentional_failure():
    assert 1 == 2
