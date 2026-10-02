import errno
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

import httpx
import openai

from haqs_toolkit import campaigns, cli, events
from haqs_toolkit.errors import UserError, command_errors, friendly_error
from haqs_toolkit.generators import email_generator
from haqs_toolkit.utils import marketing


class FriendlyErrorTests(unittest.TestCase):
    def test_direct_commands_fail_without_tracebacks(self):
        cases = [
            (
                ["haqs_toolkit.generators.qr_code_generator", "--link", "invalid"],
                "https://example.com",
            ),
            (
                [
                    "haqs_toolkit.generators.project_plan_builder",
                    "--campaign-name",
                    "Test",
                    "--campaign-type",
                    "webinar",
                    "--launch-date",
                    "bad-date",
                ],
                "YYYY-MM-DD",
            ),
            (
                [
                    "haqs_toolkit.create",
                    "--scope",
                    "complete",
                    "--job-type",
                    "event",
                    "--brief",
                    "missing-test-brief.json",
                ],
                "missing-test-brief.json",
            ),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, "-m", *args],
                    capture_output=True,
                    text=True,
                    env={**os.environ, "HAQS_DEBUG": "0"},
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_brief_errors_include_path_and_location_or_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "brief.json"
            for loader, error in [
                (campaigns.load_campaign_brief, campaigns.CampaignBriefError),
                (events.load_event_brief, events.EventBriefError),
            ]:
                path.write_text('{\n "name":\n}', encoding="utf-8")
                with self.assertRaises(error) as caught:
                    loader(path)
                self.assertIn("line 3, column 1", str(caught.exception))
                self.assertIn(str(path), str(caught.exception))
                path.write_text("{}", encoding="utf-8")
                with self.assertRaises(error) as caught:
                    loader(path)
                self.assertIn("audience", str(caught.exception))
                self.assertIn("goal", str(caught.exception))
                self.assertIn("Edit the listed fields", str(caught.exception))

    def test_file_errors_explain_recovery(self):
        for error, expected in [
            (PermissionError(errno.EACCES, "denied", "output/test.txt"), "permissions"),
            (OSError(errno.ENOSPC, "full", "output/test.txt"), "disk space"),
            (FileNotFoundError(errno.ENOENT, "missing", "output/test.txt"), "path"),
        ]:
            message = str(friendly_error(error))
            self.assertIn(expected, message)
            self.assertIn("output/test.txt", message)

    def test_partial_outputs_are_reported_and_context_is_reset(self):
        @command_errors
        def fail_after_save():
            marketing.save_text("email", "Saved content")
            raise PermissionError(errno.EACCES, "denied", "roi.csv")

        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(os.environ, {"HAQS_OUTPUT_DIR": folder, "HAQS_DEBUG": "0"}),
        ):
            output = io.StringIO()
            with redirect_stderr(output):
                self.assertEqual(fail_after_save(), 1)
            self.assertIn("Files saved before the error:", output.getvalue())
            self.assertIn("email_", output.getvalue())
            output = io.StringIO()
            with redirect_stderr(output):
                command_errors(lambda: (_ for _ in ()).throw(EOFError()))()
            self.assertNotIn("Files saved", output.getvalue())

    def test_launcher_preserves_failure_status(self):
        option = cli.ToolOption("Test", "Test", lambda: 1)
        with patch.object(cli, "choose_tool", return_value=option):
            self.assertEqual(cli.main(), 1)

    def test_debug_rethrows_unexpected_error(self):
        @command_errors
        def broken():
            raise RuntimeError("test bug")

        with patch.dict(os.environ, {"HAQS_DEBUG": "1"}):
            with self.assertRaisesRegex(RuntimeError, "test bug"):
                broken()
        with patch.dict(os.environ, {"HAQS_DEBUG": "0"}):
            output = io.StringIO()
            with redirect_stderr(output):
                self.assertEqual(broken(), 1)
            self.assertIn("HAQS_DEBUG", output.getvalue())
            self.assertNotIn("test bug", output.getvalue())

    def test_input_cancellation(self):
        for exception, code, expected in [
            (EOFError(), 1, "complete the prompts"),
            (KeyboardInterrupt(), 130, "Cancelled"),
        ]:
            with patch("builtins.input", side_effect=exception):
                output = io.StringIO()
                with redirect_stderr(output):
                    self.assertEqual(command_errors(lambda: input())(), code)
                self.assertIn(expected, output.getvalue())


class AiErrorTests(unittest.TestCase):
    def test_sdk_failures_have_specific_fixes(self):
        request = httpx.Request("POST", "https://example.com")
        for cls, code, status, expected in [
            (
                openai.AuthenticationError,
                "invalid_api_key",
                401,
                "Replace OPENAI_API_KEY",
            ),
            (openai.RateLimitError, "insufficient_quota", 429, "credits"),
            (openai.RateLimitError, "rate_limit_exceeded", 429, "Wait a moment"),
            (openai.NotFoundError, "model_not_found", 404, "OPENAI_MODEL"),
            (openai.PermissionDeniedError, "denied", 403, "permissions"),
            (openai.BadRequestError, "invalid", 400, "output format"),
            (openai.InternalServerError, "server", 500, "Retry"),
        ]:
            with self.subTest(cls=cls, code=code):
                exc = cls(
                    "secret provider details",
                    response=httpx.Response(status, request=request),
                    body={"code": code},
                )
                with patch.object(marketing, "get_openai_client", side_effect=exc):
                    with self.assertRaises(marketing.AiGenerationError) as caught:
                        marketing.generate_text("system", "user")
                self.assertIn(expected, str(caught.exception))
                self.assertNotIn("secret provider details", str(caught.exception))
        for exc in [
            openai.APIConnectionError(request=request),
            openai.APITimeoutError(request=request),
        ]:
            self.assertIn("retry", str(marketing.ai_request_error(exc)))

    def test_dotenv_loads_key_and_preserves_existing_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".env").write_text(
                "OPENAI_API_KEY=file-key\nOPENAI_MODEL=gpt-6-luna\n",
                encoding="utf-8",
            )
            code = (
                "import os; from haqs_toolkit.utils import marketing; "
                "print(os.environ['OPENAI_API_KEY']); "
                "print(marketing.get_openai_model())"
            )
            cases = ((None, "file-key"), ("terminal-key", "terminal-key"))
            for existing_key, expected_key in cases:
                env = os.environ.copy()
                env.pop("OPENAI_API_KEY", None)
                env.pop("OPENAI_MODEL", None)
                env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
                if existing_key:
                    env["OPENAI_API_KEY"] = existing_key
                result = subprocess.run(
                    [sys.executable, "-c", code],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(
                    result.stdout.splitlines(), [expected_key, "gpt-6-luna"]
                )

    def test_fallback_warns_without_polluting_copy(self):
        error = marketing.AiGenerationError("No key", "Set OPENAI_API_KEY")
        with (
            patch.object(campaigns, "generate_text", side_effect=error),
            patch.dict(os.environ, {"HAQS_DEBUG": "0"}),
        ):
            output = io.StringIO()
            with redirect_stderr(output):
                self.assertEqual(campaigns.ai_or_fallback("s", "u", "Draft"), "Draft")
            self.assertIn("template content", output.getvalue())
            self.assertIn("OPENAI_API_KEY", output.getvalue())

    def test_generator_ai_failure_returns_nonzero(self):
        with (
            patch.object(email_generator, "read_multiline", return_value="Content"),
            patch.object(email_generator, "read_required", return_value="Purpose"),
            patch.object(
                email_generator,
                "generate_text",
                side_effect=UserError("No key", "Set OPENAI_API_KEY"),
            ),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(email_generator.main(), 1)
