def can_reserve(available_seats: int, requested_seats: int) -> bool:
    return 0 < requested_seats <= available_seats
