import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from haqs_toolkit import create, runs


class OpenOutputTests(unittest.TestCase):
    def test_creation_opens_only_the_returned_runs_outputs(self):
        generated = Path("custom runs/campaign-selected-2026-09-14-1200-2")
        with (
            patch.object(create, "load_brief", return_value={}),
            patch.object(create, "run_creation", return_value=generated),
            patch("builtins.input") as prompt,
            patch.object(create, "open_output_folder") as opener,
        ):
            result = create.main(
                [
                    "--scope",
                    "complete",
                    "--job-type",
                    "event",
                    "--brief",
                    "brief.json",
                ]
            )
        self.assertEqual(result, 0)
        opener.assert_called_once_with(generated / "outputs")
        prompt.assert_not_called()

    def test_file_manager_receives_absolute_folder_path(self):
        folder = Path("custom runs/run-2/outputs")
        for platform, command in [
            ("win32", None),
            ("darwin", "open"),
            ("linux", "xdg-open"),
        ]:
            with self.subTest(platform=platform):
                with (
                    patch.object(runs.sys, "platform", platform),
                    patch.object(runs.os, "startfile", create=True) as startfile,
                    patch.object(runs.subprocess, "run") as launch,
                ):
                    runs.open_output_folder(folder)
                if command is None:
                    startfile.assert_called_once_with(str(folder.resolve()))
                    launch.assert_not_called()
                else:
                    launch.assert_called_once_with(
                        [command, str(folder.resolve())], check=True
                    )

    def test_open_failure_preserves_files_and_prints_path(self):
        folder = Path("custom runs/run-2/outputs")
        for error in (OSError("unavailable"), subprocess.CalledProcessError(1, "open")):
            with self.subTest(error=error):
                with (
                    patch.object(runs.sys, "platform", "darwin"),
                    patch.object(runs.subprocess, "run", side_effect=error),
                    patch("builtins.print") as output,
                ):
                    runs.open_output_folder(folder)
                output.assert_any_call(
                    f"Your generated files are at: {folder.resolve()}"
                )
