from day11_reservation import can_reserve


def test_available_and_paid():
    assert can_reserve(False, True) is True


def test_already_reserved():
    assert can_reserve(True, True) is False


def test_payment_not_confirmed():
    assert can_reserve(False, False) is False
