def common_not_eq_value(a, b):
    try:
        return bool(a != b)
    except ValueError:
        return True
