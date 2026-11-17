from reservation import can_reserve


def test_accept_valid_reservation():
    assert can_reserve(5, 2) is True


def test_reject_insufficient_seats():
    assert can_reserve(1, 2) is False


def test_reject_zero_seats():
    assert can_reserve(5, 0) is False
