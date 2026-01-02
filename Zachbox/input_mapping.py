def apply_deadzone(raw_value: int, center: int, size: int) -> int:
    """Snap input to center if within the deadzone band."""
    if abs(raw_value - center) <= size:
        return center
    return raw_value


def _interp_scalar(raw_value: int | float, in_range, out_range) -> float:
    in_min, in_max = in_range
    out_min, out_max = out_range
    if in_max == in_min:
        return out_min
    if raw_value < in_min:
        raw_value = in_min
    elif raw_value > in_max:
        raw_value = in_max
    ratio = (raw_value - in_min) / (in_max - in_min)
    return out_min + ratio * (out_max - out_min)


def map_servo_value(raw_value: int, in_range, out_range, increment_size: int) -> int:
    """Map joystick value to servo degrees using interpolation."""
    return round(_interp_scalar(raw_value, in_range, out_range) * increment_size)


def slew_limit(target: int, last: int, max_step: int) -> int:
    """Clamp how much the target can change from the last value."""
    delta = target - last
    if delta > max_step:
        return last + max_step
    if delta < -max_step:
        return last - max_step
    return target
