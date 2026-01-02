import unittest
from input_mapping import apply_deadzone, map_servo_value, slew_limit


class InputMappingTests(unittest.TestCase):
    def test_deadzone_snap(self):
        self.assertEqual(apply_deadzone(10, center=10, size=2), 10)
        self.assertEqual(apply_deadzone(11, center=10, size=2), 10)
        self.assertEqual(apply_deadzone(8, center=10, size=2), 10)
        self.assertEqual(apply_deadzone(13, center=10, size=2), 13)

    def test_map_servo_value(self):
        in_range = (0, 10)
        out_range = (0, 18)  # scaled by increment_size later
        # increment_size 1 means direct scaling to 0..18
        self.assertEqual(map_servo_value(0, in_range, out_range, increment_size=1), 0)
        self.assertEqual(map_servo_value(5, in_range, out_range, increment_size=1), 9)
        self.assertEqual(map_servo_value(10, in_range, out_range, increment_size=1), 18)
        # increment_size 6 mirrors the code path (0..180)
        self.assertEqual(map_servo_value(10, in_range, out_range, increment_size=6), 108)

    def test_slew_limit(self):
        self.assertEqual(slew_limit(target=100, last=90, max_step=5), 95)
        self.assertEqual(slew_limit(target=80, last=90, max_step=5), 85)
        self.assertEqual(slew_limit(target=93, last=90, max_step=5), 93)


if __name__ == "__main__":
    unittest.main()
