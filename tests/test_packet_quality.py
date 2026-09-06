import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from haqs_toolkit import packet_quality


class PacketQualityTests(unittest.TestCase):
    def test_scan_path_uses_outputs_directory_for_packet(self):
        with TemporaryDirectory() as directory:
            packet_dir = Path(directory) / "campaign"
            outputs_dir = packet_dir / "outputs"
            outputs_dir.mkdir(parents=True)
            (outputs_dir / "email.md").write_text(
                "## Primary CTA\n\n[Register](https://example.com)\n",
                encoding="utf-8",
            )

            issues = packet_quality.scan_path(packet_dir)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "placeholder")

    def test_scan_file_flags_generation_note_and_url_placeholder(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "landing.md"
            path.write_text(
                "## Hero\n\nGeneration note: offline\n\n[Start]([url here])\n",
                encoding="utf-8",
            )

            issue_codes = {issue.code for issue in packet_quality.scan_file(path)}

        self.assertIn("generation-note", issue_codes)
        self.assertIn("placeholder", issue_codes)

    def test_scan_file_flags_missing_cta_link(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "email.md"
            path.write_text("## Final CTA\n\nRegister Now\n", encoding="utf-8")

            issues = packet_quality.scan_file(path)

        self.assertTrue(
            any(issue.code == "missing-cta-link" for issue in issues),
            issues,
        )

    def test_scan_file_allows_cta_link_on_next_line(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "email.md"
            path.write_text(
                "## Final CTA\n\nRegister Now\nhttps://haqs.com/event\n",
                encoding="utf-8",
            )

            issues = packet_quality.scan_file(path)

        self.assertFalse(
            any(issue.code == "missing-cta-link" for issue in issues),
            issues,
        )

    def test_scan_file_flags_empty_sections(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "landing.md"
            path.write_text(
                "# Page\n\n## Benefits\n\n## CTA\n\nDone\n",
                encoding="utf-8",
            )

            issues = packet_quality.scan_file(path)

        self.assertTrue(any(issue.code == "empty-section" for issue in issues))

    def test_main_returns_failure_when_issues_exist(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "social.md"
            path.write_text("Visit https://example.com\n", encoding="utf-8")

            exit_code = packet_quality.main([str(path)])

        self.assertEqual(exit_code, 1)

    def test_main_returns_success_when_clean(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "social.md"
            path.write_text(
                "## CTA\n\n[Register](https://haqs.com/event)\n",
                encoding="utf-8",
            )

            exit_code = packet_quality.main([str(path)])

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
