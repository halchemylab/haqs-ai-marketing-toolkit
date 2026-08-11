import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from haqs_toolkit import campaigns


class CampaignTests(unittest.TestCase):
    def test_validate_campaign_brief_accepts_required_fields(self):
        campaigns.validate_campaign_brief(
            {
                "campaign_name": "Fall Workshop",
                "audience": "Small business owners",
                "goal": "Drive registrations",
                "cta": "Register now",
                "landing_page_url": "https://example.com/workshop",
            }
        )

    def test_validate_campaign_brief_rejects_missing_required_field(self):
        with self.assertRaisesRegex(campaigns.CampaignBriefError, "campaign_name"):
            campaigns.validate_campaign_brief(
                {
                    "audience": "Small business owners",
                    "goal": "Drive registrations",
                    "cta": "Register now",
                    "landing_page_url": "https://example.com/workshop",
                }
            )

    def test_validate_campaign_brief_rejects_invalid_url(self):
        with self.assertRaisesRegex(campaigns.CampaignBriefError, "landing_page_url"):
            campaigns.validate_campaign_brief(
                {
                    "campaign_name": "Fall Workshop",
                    "audience": "Small business owners",
                    "goal": "Drive registrations",
                    "cta": "Register now",
                    "landing_page_url": "example.com/workshop",
                }
            )

    def test_create_campaign_packet_writes_starter_files(self):
        with TemporaryDirectory() as directory:
            campaign_dir = Path(directory) / "fall-workshop"

            brief_path = campaigns.create_campaign_packet(campaign_dir)

            self.assertTrue(brief_path.exists())
            self.assertTrue((campaign_dir / "inputs" / "source-notes.md").exists())
            self.assertTrue((campaign_dir / "outputs").is_dir())

    def test_generate_campaign_packet_writes_expected_files(self):
        with TemporaryDirectory() as directory:
            campaign_dir = Path(directory) / "fall-workshop"
            campaigns.create_campaign_packet(campaign_dir)

            with patch.object(
                campaigns,
                "generate_text",
                side_effect=campaigns.AiGenerationError("offline"),
            ):
                paths = campaigns.generate_campaign_packet(campaign_dir)

            names = {path.name for path in paths}
            self.assertIn("campaign-url.txt", names)
            self.assertIn("email-drafts.md", names)
            self.assertIn("social-posts.md", names)
            self.assertIn("landing-page-copy.md", names)
            self.assertIn("qr-code.png", names)
            self.assertIn("project-plan.csv", names)
            self.assertIn("packet-index.md", names)

            index = (campaign_dir / "outputs" / "packet-index.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("campaign-url.txt", index)
            self.assertIn("project-plan.csv", index)

    def test_main_list_fields(self):
        self.assertEqual(campaigns.main(["--list-fields"]), 0)


if __name__ == "__main__":
    unittest.main()
