import unittest

from roi_report import as_float, as_int


class RoiReportTests(unittest.TestCase):
    def test_as_int_returns_zero_for_invalid_values(self):
        self.assertEqual(as_int("12"), 12)
        self.assertEqual(as_int(""), 0)
        self.assertEqual(as_int("not-a-number"), 0)

    def test_as_float_returns_zero_for_invalid_values(self):
        self.assertEqual(as_float("12.50"), 12.5)
        self.assertEqual(as_float(""), 0.0)
        self.assertEqual(as_float("not-a-number"), 0.0)


if __name__ == "__main__":
    unittest.main()
