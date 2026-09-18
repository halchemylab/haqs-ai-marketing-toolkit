import unittest
from unittest.mock import patch

from haqs_toolkit import intake


class IntakeTests(unittest.TestCase):
    def test_pasted_campaign_only_asks_for_missing_required_details(self):
        answers = [
            "1",
            "Campaign name: Fall launch",
            "Audience: Owners",
            "Goal: Signups",
            "CTA: Join",
            "URL: https://haqs.test/join",
            "END",
        ]
        with patch("builtins.input", side_effect=answers) as prompt:
            brief = intake.collect_brief("campaign")
        self.assertEqual(prompt.call_count, len(answers))
        self.assertEqual(brief["campaign_name"], "Fall launch")
        self.assertIn("Audience: Owners", brief["source_material"])

    def test_event_extracts_date_and_requests_unknown_audience(self):
        answers = [
            "1",
            "Workshop",
            "September 30, 2026",
            "https://haqs.test/event",
            "END",
            "Owners",
            "Registrations",
            "Register",
        ]
        with patch("builtins.input", side_effect=answers):
            brief = intake.collect_brief("event")
        self.assertEqual(brief["event_date"], "2026-09-30")
        self.assertEqual(brief["audience"], "Owners")

    def test_invalid_calendar_date_does_not_crash_extraction(self):
        brief = intake.parse_details("Workshop\nFebruary 30, 2026", "event")
        self.assertNotIn("event_date", brief)

    def test_explicit_event_fields_are_preserved_by_normalization(self):
        from haqs_toolkit.events import normalized_event_brief

        brief = intake.parse_details("Event name: Workshop\nAudience: Owners", "event")
        self.assertEqual(normalized_event_brief(brief)["audience"], "Owners")

    def test_plan_only_collects_planning_details(self):
        with patch(
            "builtins.input",
            side_effect=["2", "Launch", "offer", "2026-10-01", "email,linkedin"],
        ):
            brief = intake.collect_brief("campaign", ["project_plan"])
        self.assertEqual(brief["launch_date"], "2026-10-01")
        self.assertNotIn("audience", brief)
        self.assertNotIn("landing_page_url", brief)

    def test_bad_date_is_retried_before_the_next_field(self):
        with patch(
            "builtins.input",
            side_effect=["2", "Launch", "offer", "2026-02-30", "2026-10-01", "email"],
        ) as prompt:
            brief = intake.collect_brief("campaign", ["project_plan"])
        self.assertEqual(brief["launch_date"], "2026-10-01")
        self.assertIn("Launch Date", prompt.call_args_list[4].args[0])
        self.assertIn("Channels", prompt.call_args_list[5].args[0])

    def test_pasted_invalid_date_is_corrected_without_losing_other_details(self):
        with patch(
            "builtins.input",
            side_effect=[
                "1",
                "Campaign name: Launch",
                "Launch date: 2026-02-30",
                "END",
                "2026-10-01",
            ],
        ):
            brief = intake.collect_brief("campaign", ["project_plan"])
        self.assertEqual(brief["campaign_name"], "Launch")
        self.assertEqual(brief["launch_date"], "2026-10-01")

    def test_preview_edits_url_and_preserves_other_fields(self):
        brief = {"event_name": "Workshop", "registration_url": "https://haqs.test/old"}
        with patch("builtins.input", side_effect=["2", "https://haqs.test/new", ""]):
            self.assertTrue(intake.review_brief(brief, "event", ["qr_code"]))
        self.assertEqual(brief["registration_url"], "https://haqs.test/new")
        self.assertEqual(brief["event_name"], "Workshop")

    def test_preview_will_not_generate_with_an_invalid_date(self):
        brief = {"campaign_name": "Launch", "launch_date": "bad"}
        with patch("builtins.input", side_effect=["", "3", "2026-10-01", ""]):
            self.assertTrue(intake.review_brief(brief, "campaign", ["project_plan"]))
        self.assertEqual(brief["launch_date"], "2026-10-01")
