import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from haqs_toolkit import create, events


class EventScriptTests(unittest.TestCase):
    def test_parse_event_details_extracts_human_event_page_copy(self):
        brief = events.parse_event_details(
            """
Genius at Scale: How to Lead Innovation That Lasts with Emily Tedards
Thursday, September 17th, 2026 from 11:00 AM to 12:00 PM EDT

Event will begin in 7 days and 16 hours

displayed image

In today's hyper-competitive landscape, many organizations face a frustrating paradox.

Practical Tools and Strategies You'll Gain

Build a Culture of Co-creation: Design your organization as an Architect.

Ideal Participants for This Conversation

Current or aspiring leaders who want to stop guessing at innovation and start
applying a proven, science-based model for cultivating genius at scale.
https://example.com/register
""".strip()
        )

        self.assertEqual(
            brief["event_name"],
            "Genius at Scale: How to Lead Innovation That Lasts with Emily Tedards",
        )
        self.assertEqual(brief["event_date"], "2026-09-17")
        self.assertEqual(brief["event_time"], "11:00 AM to 12:00 PM")
        self.assertEqual(brief["timezone"], "EDT")
        self.assertIn("Current or aspiring leaders", str(brief["audience"]))
        self.assertNotIn("About the Author", str(brief["audience"]))
        self.assertIn("Build a Culture", "\n".join(brief["takeaways"]))
        self.assertEqual(brief["registration_url"], "https://example.com/register")

    def test_event_run_assets_use_source_aware_copy(self):
        brief = events.parse_event_details(
            """
Genius at Scale: How to Lead Innovation That Lasts with Emily Tedards
Thursday, September 17th, 2026 from 11:00 AM to 12:00 PM EDT

Drawing on research from her new book, Emily Tedards introduces a real-world
alternative to modern leadership challenges.

Practical Tools and Strategies You'll Gain

Build a Culture of Co-creation: Design your organization as an Architect.
Bridge the Gap to New Opportunities: Work outside boundaries as a Bridger.
Provide the Spark to Scale: Launch movements as a Catalyst.
Ideal Participants for This Conversation

Current or aspiring leaders.
https://example.com/register
""".strip()
        )

        with TemporaryDirectory() as directory:
            output_dir = Path(directory) / "outputs"
            create.write_event_run_assets(
                brief,
                output_dir,
                [
                    create.ASSET_EMAIL,
                    create.ASSET_SOCIAL,
                    create.ASSET_LANDING_PAGE,
                ],
            )
            email = (output_dir / "email-sequence.md").read_text(encoding="utf-8")
            social = (output_dir / "social-posts.md").read_text(encoding="utf-8")
            landing = (output_dir / "landing-page-copy.md").read_text(
                encoding="utf-8"
            )

        self.assertIn("Architect, Bridger, and Catalyst", email)
        self.assertIn("Mastercard, Pfizer", email)
        self.assertNotIn("https://example.com/register.", email)
        self.assertIn("## LinkedIn Post 1", social)
        self.assertIn("Read more:", social)
        self.assertIn("hashtag#Innovation", social)
        self.assertNotIn("1. Many leaders", social)
        self.assertIn("Build a Culture of Co-creation", landing)

    def test_event_renderers_normalize_bloated_existing_brief(self):
        source_material = """
Genius at Scale: How to Lead Innovation That Lasts with Emily Tedards
Thursday, September 17th, 2026 from 11:00 AM to 12:00 PM EDT

In today's hyper-competitive landscape, many organizations face a frustrating
paradox.

Practical Tools and Strategies You'll Gain

Build a Culture of Co-creation: Design your organization as an Architect.
Ideal Participants for This Conversation

Current or aspiring leaders.
Join Emily Tedards to discover how to drive innovation.

About the Author

Emily Tedards is a graduate researcher in organizational behavior.
""".strip()
        brief = {
            **events.parse_event_details(source_material),
            "audience": "Current or aspiring leaders. About the Author Emily bio.",
            "registration_url": "https://example.com/register",
        }

        landing = events.event_landing_page_copy(
            brief,
            "https://example.com/register",
        )

        self.assertIn("Current or aspiring leaders.", landing)
        self.assertNotIn("About the Author", landing)
        self.assertIn("Build a Culture of Co-creation", landing)

    def test_main_without_event_dir_creates_complete_run_from_paste(self):
        pasted_event = """
Spring Workshop
Thursday, September 17th, 2026 from 11:00 AM to 12:00 PM EDT

Practical marketing workflow for small business owners.

Ideal Participants for This Conversation

Small business owners
https://example.com/spring-workshop
""".strip()
        answers = iter(
            [
                *pasted_event.splitlines(),
                "END",
                "1",
            ]
        )

        with patch("builtins.input", side_effect=lambda *_args: next(answers)):
            with patch("haqs_toolkit.create.run_creation") as run_creation:
                exit_code = events.main([])

        self.assertEqual(exit_code, 0)
        run_creation.assert_called_once()
        call = run_creation.call_args.kwargs
        self.assertEqual(call["brief"]["event_name"], "Spring Workshop")
        self.assertEqual(call["brief"]["event_date"], "2026-09-17")
        self.assertEqual(call["job_type"], "event")
        self.assertEqual(call["scope"], "complete")
        self.assertIn("email", call["selected_assets"])

    def test_main_without_event_dir_can_create_selected_assets_from_paste(self):
        pasted_event = """
Spring Workshop
Thursday, September 17th, 2026 from 11:00 AM to 12:00 PM EDT

Practical marketing workflow for small business owners.
https://example.com/spring-workshop
""".strip()
        answers = iter(
            [
                *pasted_event.splitlines(),
                "END",
                "2",
                "1,3",
            ]
        )

        with patch("builtins.input", side_effect=lambda *_args: next(answers)):
            with patch("haqs_toolkit.create.run_creation") as run_creation:
                exit_code = events.main([])

        self.assertEqual(exit_code, 0)
        run_creation.assert_called_once()
        call = run_creation.call_args.kwargs
        self.assertEqual(call["scope"], "selected")
        self.assertEqual(call["selected_assets"], ["tracked_url", "email"])

    def test_out_without_event_dir_is_still_invalid(self):
        with TemporaryDirectory() as directory:
            output_dir = Path(directory) / "outputs"
            with self.assertRaises(SystemExit) as raised:
                events.main(["--out", str(output_dir)])

        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
