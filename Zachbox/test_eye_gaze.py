import unittest
from eye_gaze import gaze_intensity


class EyeGazeTests(unittest.TestCase):
    def test_center_gaze_all_on(self):
        intensities = gaze_intensity((0, 0))
        self.assertEqual(len(intensities), 7)
        self.assertTrue(all(abs(x - 1.0) < 1e-6 for x in intensities))

    def test_right_gaze_full(self):
        intensities = gaze_intensity((1, 0))
        self.assertEqual(intensities, [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0])

    def test_top_gaze_full(self):
        intensities = gaze_intensity((0, 1))
        self.assertEqual(intensities, [0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])

    def test_bottom_gaze_full(self):
        intensities = gaze_intensity((0, -1))
        self.assertEqual(intensities, [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0])

    def test_left_gaze_full(self):
        intensities = gaze_intensity((-1, 0))
        self.assertEqual(intensities, [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0])

    def test_gaze_has_soft_edge(self):
        intensities = gaze_intensity((0.5, 0))
        self.assertTrue(any(0.0 < x < 1.0 for x in intensities))


if __name__ == "__main__":
    unittest.main()
