import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils import marketing


class MarketingRoiTests(unittest.TestCase):
    def test_timestamped_output_path_uses_date_and_category_folder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with patch.dict(os.environ, {"HAQS_OUTPUT_DIR": str(output_dir)}):
                path = marketing.timestamped_output_path("campaign_url", "txt")

            self.assertEqual(path.parent.name, "campaign_urls")
            self.assertEqual(
                path.parent.parent.name,
                marketing.datetime.now().strftime("%Y-%m-%d"),
            )
            self.assertEqual(path.parent.parent.parent, output_dir)
            self.assertTrue(path.name.startswith("campaign_url_"))
            self.assertEqual(path.suffix, ".txt")
            self.assertTrue(path.parent.exists())

    def test_output_dir_is_read_from_environment_at_runtime(self):
        with tempfile.TemporaryDirectory() as first_dir:
            with tempfile.TemporaryDirectory() as second_dir:
                with patch.dict(os.environ, {"HAQS_OUTPUT_DIR": first_dir}):
                    first_path = marketing.timestamped_output_path("campaign_url")

                with patch.dict(os.environ, {"HAQS_OUTPUT_DIR": second_dir}):
                    second_path = marketing.timestamped_output_path("campaign_url")

        self.assertEqual(first_path.parent.parent.parent, Path(first_dir))
        self.assertEqual(second_path.parent.parent.parent, Path(second_dir))

    def test_log_roi_event_returns_calculated_totals_and_writes_row(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            roi_path = output_dir / "roi" / "automation_roi.csv"

            with (
                patch.dict(os.environ, {"HAQS_OUTPUT_DIR": str(output_dir)}),
                patch.dict(os.environ, {"HOURLY_RATE": "75"}),
            ):
                roi = marketing.log_roi_event(
                    script="test_script",
                    asset_type="test_asset",
                    count=2,
                    minutes_per_item=30,
                    notes="test notes",
                )

            self.assertEqual(roi["count"], 2)
            self.assertEqual(roi["minutes_per_item"], 30)
            self.assertEqual(roi["time_saved_minutes"], 60)
            self.assertEqual(roi["hourly_rate"], 75.0)
            self.assertEqual(roi["money_saved"], 75.0)
            self.assertEqual(roi["path"], roi_path)

            with roi_path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["script"], "test_script")
            self.assertEqual(rows[0]["asset_type"], "test_asset")
            self.assertEqual(rows[0]["time_saved_minutes"], "60")
            self.assertEqual(rows[0]["money_saved"], "75.00")

    def test_combine_roi_results_sums_totals(self):
        combined = marketing.combine_roi_results(
            [
                {
                    "count": 2,
                    "minutes_per_item": 30,
                    "time_saved_minutes": 60,
                    "hourly_rate": 75.0,
                    "money_saved": 75.0,
                    "path": Path("output/automation_roi.csv"),
                },
                {
                    "count": 3,
                    "minutes_per_item": 10,
                    "time_saved_minutes": 30,
                    "hourly_rate": 75.0,
                    "money_saved": 37.5,
                    "path": Path("output/automation_roi.csv"),
                },
            ]
        )

        self.assertEqual(combined["count"], 5)
        self.assertEqual(combined["time_saved_minutes"], 90)
        self.assertEqual(combined["money_saved"], 112.5)


class BrandVoiceTests(unittest.TestCase):
    def test_load_brand_voice_reads_existing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "voice.md"
            path.write_text("Plainspoken and practical.", encoding="utf-8")

            self.assertEqual(
                marketing.load_brand_voice(path),
                "Plainspoken and practical.",
            )

    def test_load_brand_voice_uses_builtin_default_when_file_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.md"

            self.assertEqual(
                marketing.load_brand_voice(path),
                marketing.DEFAULT_BRAND_VOICE,
            )

    def test_brand_voice_prompt_block_explains_global_and_local_tone(self):
        block = marketing.brand_voice_prompt_block("Direct and useful.")

        self.assertIn("Brand voice", block)
        self.assertIn("Direct and useful.", block)
        self.assertIn("local adjustments", block)


class MarketingAiGenerationTests(unittest.TestCase):
    def test_generate_text_requires_openai_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(marketing.AiGenerationError, "OPENAI_API_KEY"):
                marketing.generate_text("system", "user")

    def test_generate_text_rejects_empty_response(self):
        class FakeResponses:
            def create(self, **kwargs):
                return type("FakeResponse", (), {"output_text": "   "})()

        class FakeClient:
            responses = FakeResponses()

        with patch.object(marketing, "get_openai_client", return_value=FakeClient()):
            with self.assertRaisesRegex(marketing.AiGenerationError, "empty response"):
                marketing.generate_text("system", "user")


if __name__ == "__main__":
    unittest.main()
