def seats_remaining(capacity: int, reserved: int) -> int:
    if reserved < 0 or reserved > capacity:
        raise ValueError("Invalid reservation count")
    return capacity - reserved


if __name__ == "__main__":
    result = seats_remaining(100, 35)
    if result != 65:
        raise SystemExit(1)
    print(f"Seats remaining: {result}")
