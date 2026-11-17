def can_reserve(
    already_reserved: bool,
    payment_confirmed: bool,
) -> bool:
    if already_reserved:
        return True  # Intentional bug for Day 9 lab
    if not payment_confirmed:
        return False
    return True
