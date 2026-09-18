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
