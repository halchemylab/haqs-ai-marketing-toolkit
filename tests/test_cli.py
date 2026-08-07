import unittest
from unittest.mock import patch

from haqs_toolkit import cli


class CliTests(unittest.TestCase):
    def test_choose_tool_returns_selected_option(self):
        with patch("builtins.input", return_value="1"):
            option = cli.choose_tool()

        self.assertIs(option, cli.TOOL_OPTIONS[0])

    def test_choose_tool_returns_none_for_exit(self):
        with patch("builtins.input", return_value="0"):
            option = cli.choose_tool()

        self.assertIsNone(option)

    def test_choose_tool_returns_none_for_closed_input(self):
        with patch("builtins.input", side_effect=EOFError):
            option = cli.choose_tool()

        self.assertIsNone(option)

    def test_main_runs_selected_tool(self):
        calls = []
        option = cli.ToolOption(
            name="Test Tool",
            description="Test description.",
            run=lambda: calls.append("ran"),
        )

        with patch.object(cli, "choose_tool", return_value=option):
            cli.main()

        self.assertEqual(calls, ["ran"])


if __name__ == "__main__":
    unittest.main()
