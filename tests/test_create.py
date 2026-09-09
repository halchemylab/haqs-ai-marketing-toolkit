import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from haqs_toolkit import create
from haqs_toolkit.runs import create_run_dir, slugify


class CreateFlowTests(unittest.TestCase):
    def test_slugify_makes_readable_folder_parts(self):
        self.assertEqual(slugify("Demo Growth Workshop!"), "demo-growth-workshop")

    def test_create_run_dir_uses_flat_job_type_scope_date_name(self):
        with TemporaryDirectory() as directory:
            run_dir = create_run_dir(
                "Demo Growth Workshop",
                "event",
                "selected",
                runs_dir=Path(directory),
                now=datetime(2026, 9, 9, 13, 45),
            )

        self.assertEqual(
            run_dir.name,
            "demo-growth-workshop-event-selected-2026-09-09-1345",
        )

    def test_selected_event_run_writes_one_folder_outputs_and_quality_check(self):
        brief = {
            "event_name": "Demo Growth Workshop",
            "event_date": "2026-09-18",
            "audience": "Small business owners",
            "goal": "Drive registrations",
            "cta": "Register Now",
            "registration_url": "https://example.com/demo-growth-workshop",
        }

        with TemporaryDirectory() as directory:
            with patch("haqs_toolkit.runs.datetime") as fake_datetime:
                fake_datetime.now.return_value = datetime(2026, 9, 9, 13, 45)
                run_dir = create.run_creation(
                    brief=brief,
                    job_type=create.JOB_EVENT,
                    scope=create.SCOPE_SELECTED,
                    selected_assets=[
                        create.ASSET_TRACKED_URL,
                        create.ASSET_QR_CODE,
                        create.ASSET_SOCIAL,
                    ],
                    runs_dir=Path(directory),
                )

            self.assertTrue((run_dir / "brief.json").exists())
            self.assertTrue((run_dir / "outputs" / "campaign-url.txt").exists())
            self.assertTrue((run_dir / "outputs" / "qr-code.png").exists())
            self.assertTrue((run_dir / "outputs" / "social-posts.md").exists())
            self.assertFalse((run_dir / "outputs" / "email-sequence.md").exists())
            self.assertTrue((run_dir / "quality-check.md").exists())
            self.assertTrue((run_dir / "packet-index.md").exists())

            quality_report = (run_dir / "quality-check.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("example.com", quality_report)

    def test_main_can_create_selected_event_from_existing_brief(self):
        with TemporaryDirectory() as directory:
            brief_path = Path(directory) / "brief.json"
            brief_path.write_text(
                """
{
  "event_name": "Demo Growth Workshop",
  "event_date": "2026-09-18",
  "audience": "Small business owners",
  "goal": "Drive registrations",
  "cta": "Register Now",
  "registration_url": "https://example.com/demo-growth-workshop"
}
""".strip()
                + "\n",
                encoding="utf-8",
            )

            exit_code = create.main(
                [
                    "--scope",
                    "selected",
                    "--job-type",
                    "event",
                    "--brief",
                    str(brief_path),
                    "--assets",
                    "tracked_url,qr_code",
                    "--runs-dir",
                    str(Path(directory) / "runs"),
                ]
            )

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
