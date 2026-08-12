import unittest

from roi_report import as_float, as_int, build_report


class RoiReportTests(unittest.TestCase):
    def test_as_int_returns_zero_for_invalid_values(self):
        self.assertEqual(as_int("12"), 12)
        self.assertEqual(as_int(""), 0)
        self.assertEqual(as_int("not-a-number"), 0)

    def test_as_float_returns_zero_for_invalid_values(self):
        self.assertEqual(as_float("12.50"), 12.5)
        self.assertEqual(as_float(""), 0.0)
        self.assertEqual(as_float("not-a-number"), 0.0)

    def test_build_report_renders_rows(self):
        report = build_report(
            [
                {
                    "asset_type": "email",
                    "count": "2",
                    "time_saved_minutes": "30",
                    "money_saved": "25.00",
                }
            ],
            path="output/roi/automation_roi.csv",
        )

        self.assertIn("Total logged runs: 1", report)
        self.assertIn("email", report)


if __name__ == "__main__":
    unittest.main()
