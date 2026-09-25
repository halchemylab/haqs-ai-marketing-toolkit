import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from haqs_toolkit import clients, create, intake
from haqs_toolkit.errors import UserError


class ClientTests(unittest.TestCase):
    def test_picker_loads_text_and_general_uses_no_profile(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "acme.txt").write_text("Voice: Friendly", encoding="utf-8")
            with patch("builtins.input", return_value="2"):
                self.assertEqual(
                    clients.choose_profile(root)["text"], "Voice: Friendly"
                )
            with patch("builtins.input", return_value="1"):
                self.assertIsNone(clients.choose_profile(root))
            with self.assertRaises(UserError):
                clients.load_profile("../acme", root)
            with self.assertRaises(UserError):
                clients.load_profile("missing", root)
            (root / "empty.txt").write_text("", encoding="utf-8")
            with self.assertRaises(UserError):
                clients.load_profile("empty", root)

    def test_defaults_preserve_explicit_brief_values(self):
        profile = {
            "text": (
                "Audience: Owners\nPreferred CTA: Book\n"
                "Channels: email, linkedin\nWebsite: https://acme.test"
            )
        }
        defaults = clients.profile_defaults(profile)
        brief = clients.apply_defaults({"audience": "Teachers", "cta": ""}, defaults)
        self.assertEqual(brief["audience"], "Teachers")
        self.assertEqual(brief["cta"], "Book")
        self.assertEqual(brief["channels"], ["email", "linkedin"])
        self.assertNotIn("landing_page_url", brief)

    def test_intake_uses_defaults_without_reasking(self):
        answers = [
            "1",
            "Name: Workshop",
            "Date: 2026-10-01",
            "Goal: Signups",
            "URL: https://acme.test/event",
            "END",
        ]
        with patch("builtins.input", side_effect=answers):
            brief = intake.collect_brief(
                "event", defaults={"audience": "Owners", "cta": "Register"}
            )
        self.assertEqual(brief["audience"], "Owners")
        self.assertEqual(brief["cta"], "Register")

    def test_saved_brief_defaults_are_applied_before_validation(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "brief.json"
            path.write_text(
                json.dumps(
                    {
                        "campaign_name": "Launch",
                        "goal": "Signups",
                        "landing_page_url": "https://acme.test",
                    }
                ),
                encoding="utf-8",
            )
            brief = create.load_brief(
                path,
                "campaign",
                ["email"],
                defaults={"audience": "Owners", "cta": "Book"},
            )
        self.assertEqual(brief["cta"], "Book")

    def test_run_saves_snapshot_and_reuses_it(self):
        profile = {"name": "acme", "text": "Voice: Friendly"}
        brief = {
            "event_name": "Workshop",
            "registration_url": "https://acme.test",
            "client_profile": profile,
        }
        with TemporaryDirectory() as directory:
            run = create.run_creation(
                brief, "event", "selected", ["tracked_url"], runs_dir=Path(directory)
            )
            self.assertEqual(
                (run / "client-profile.txt").read_text().strip(), profile["text"]
            )
            saved = create.load_brief(run / "brief.json", "event", ["tracked_url"])
            self.assertIn("Voice: Friendly", clients.voice_for(saved))

    def test_profile_reaches_event_ai_prompt(self):
        brief = {
            "event_name": "Workshop",
            "client_profile": {"name": "acme", "text": "Voice: Warm"},
        }
        with patch(
            "haqs_toolkit.campaigns.ai_or_fallback", return_value="Revised"
        ) as ai:
            self.assertEqual(
                create.event_profile_copy(brief, clients.voice_for(brief), "Draft"),
                "Revised",
            )
        self.assertIn("Voice: Warm", ai.call_args.kwargs["user_prompt"])
        self.assertIn("take priority", ai.call_args.kwargs["user_prompt"])

    def test_profile_reaches_campaign_ai_prompt(self):
        brief = {
            "campaign_name": "Launch",
            "goal": "Signups",
            "audience": "Owners",
            "cta": "Book",
            "landing_page_url": "https://acme.test",
            "client_profile": {"name": "acme", "text": "Voice: Warm"},
        }
        with (
            TemporaryDirectory() as directory,
            patch("haqs_toolkit.campaigns.ai_or_fallback", return_value="Copy") as ai,
        ):
            create.write_campaign_run_assets(brief, Path(directory), ["email"])
        self.assertIn("Voice: Warm", ai.call_args.kwargs["user_prompt"])

    def test_cli_profile_override_and_general(self):
        old = {"name": "old", "text": "Voice: Old"}
        new = {"name": "new", "text": "Voice: New"}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "brief.json"
            path.write_text(
                json.dumps(
                    {
                        "event_name": "Workshop",
                        "registration_url": "https://acme.test",
                        "client_profile": old,
                    }
                ),
                encoding="utf-8",
            )
            base = [
                "--scope",
                "selected",
                "--job-type",
                "event",
                "--assets",
                "tracked_url",
                "--brief",
                str(path),
            ]
            for option, flag, expected in [
                ("--brands", None, old),
                ("--brands", "new", new),
                ("--brands", "general", None),
            ]:
                with (
                    patch("haqs_toolkit.clients.load_profile", return_value=new),
                    patch(
                        "haqs_toolkit.create.run_creation", return_value=Path(directory)
                    ) as run,
                    patch("haqs_toolkit.create.open_output_folder"),
                    patch(
                        "builtins.input",
                        side_effect=AssertionError("Unexpected prompt"),
                    ),
                ):
                    self.assertEqual(
                        create.main(base + ([option, flag] if flag else [])), 0
                    )
                    self.assertEqual(
                        run.call_args.kwargs["brief"].get("client_profile"), expected
                    )
            self.assertEqual(json.loads(path.read_text())["client_profile"], old)
