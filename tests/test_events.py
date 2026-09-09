import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from haqs_toolkit import events


class EventScriptTests(unittest.TestCase):
    def test_main_without_event_dir_creates_interactive_complete_run(self):
        answers = iter(
            [
                "Spring Workshop",
                "2026-09-18",
                "10:00 AM",
                "America/Los_Angeles",
                "Online",
                "Small business owners",
                "Drive registrations",
                "Practical marketing workflow",
                "Register Now",
                "https://example.com/spring-workshop",
                "Clear and practical",
            ]
        )

        with TemporaryDirectory() as directory:
            with patch("builtins.input", side_effect=lambda _prompt: next(answers)):
                with patch("haqs_toolkit.create.run_creation") as run_creation:
                    exit_code = events.main([])

        self.assertEqual(exit_code, 0)
        run_creation.assert_called_once()
        call = run_creation.call_args.kwargs
        self.assertEqual(call["brief"]["event_name"], "Spring Workshop")
        self.assertEqual(call["job_type"], "event")
        self.assertEqual(call["scope"], "complete")
        self.assertIn("email", call["selected_assets"])

    def test_out_without_event_dir_is_still_invalid(self):
        with TemporaryDirectory() as directory:
            output_dir = Path(directory) / "outputs"
            with self.assertRaises(SystemExit) as raised:
                events.main(["--out", str(output_dir)])

        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
