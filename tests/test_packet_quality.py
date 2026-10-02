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

    def test_scan_file_flags_long_email_subject_line(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "email.txt"
            long_subject = "Subject: " + "A" * 65 + "\n"
            valid_subject = "Subject: A concise and punchy subject line\n"
            path.write_text(long_subject + "\n" + valid_subject, encoding="utf-8")

            issues = packet_quality.scan_file(path)

        subject_issues = [i for i in issues if i.code == "subject-line-length"]
        self.assertEqual(len(subject_issues), 1)
        self.assertEqual(subject_issues[0].line_number, 1)
        self.assertIn("exceeds 60 characters", subject_issues[0].message)

    def test_scan_file_flags_long_x_post_under_heading(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "social-posts.txt"
            long_post = "x" * 285
            content = f"## X Post 1\n\n{long_post}\n\n## LinkedIn Post 1\n\nValid post."
            path.write_text(content, encoding="utf-8")

            issues = packet_quality.scan_file(path)

        x_issues = [i for i in issues if i.code == "character-limit"]
        self.assertEqual(len(x_issues), 1)
        self.assertIn("exceeds 280 characters", x_issues[0].message)

    def test_scan_file_flags_long_x_post_in_x_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "x_posts_2026.txt"
            long_post = "1. " + "y" * 285
            valid_post = "2. Short tweet under 280."
            path.write_text(f"{long_post}\n{valid_post}\n", encoding="utf-8")

            issues = packet_quality.scan_file(path)

        x_issues = [i for i in issues if i.code == "character-limit"]
        self.assertEqual(len(x_issues), 1)
        self.assertEqual(x_issues[0].line_number, 1)

    def test_scan_file_flags_template_leaks(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "email.txt"
            content = (
                "Hello {audience},\n"
                "Welcome to ${event_name} with {{speaker}}!\n"
                "The score was NaN and status is null.\n"
            )
            path.write_text(content, encoding="utf-8")

            issues = packet_quality.scan_file(path)

        leak_issues = [i for i in issues if i.code == "template-leak"]
        self.assertGreaterEqual(len(leak_issues), 3)
        messages = " ".join(i.message for i in leak_issues)
        self.assertIn("{audience}", messages)
        self.assertIn("${event_name}", messages)
        self.assertIn("NaN", messages)

    def test_scan_file_flags_malformed_urls(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "campaign-url.txt"
            content = (
                "[Link with space]"
                "(https://haqs.com/register?utm_campaign=fall launch)\n"
                "Visit https://haqs.com/register?utm_source=email&utm_medium=email&&\n"
                "Visit https://haqs.com/register?utm_source=email&\n"
                "Visit https://haqs.com/register?&=missingkey\n"
            )
            path.write_text(content, encoding="utf-8")

            issues = packet_quality.scan_file(path)

        url_issues = [i for i in issues if i.code == "malformed-url"]
        self.assertGreaterEqual(len(url_issues), 4)


if __name__ == "__main__":
    unittest.main()
