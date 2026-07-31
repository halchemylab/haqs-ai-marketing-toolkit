"""Tests for testimonial content parsing and formatting."""

from __future__ import annotations

import json
import unittest

from testimonial_formatter import (
    build_attribution,
    build_prompt,
    format_content_pack,
    parse_testimonial_response,
)


def valid_response() -> dict:
    return {
        "short_quotes": [
            {"text": f"Faithful quote {index}", "attribution": "Jamie, Acme"}
            for index in range(1, 6)
        ],
        "case_study_snippet": {
            "challenge": "Manual work",
            "experience": "A stronger starting point",
            "outcome": "Faster drafting",
        },
        "social_proof": ["Website proof", "Social proof", "Sales proof"],
        "website_testimonial": {
            "text": "It gave us a strong starting point.",
            "attribution": "Jamie, Acme",
        },
        "callouts": ["Start stronger", "Stay consistent", "Simplify drafting"],
    }


class AttributionTests(unittest.TestCase):
    def test_full_public_attribution(self) -> None:
        self.assertEqual(
            build_attribution("Jamie", "Marketing Manager", "Acme", True),
            "Jamie, Marketing Manager at Acme",
        )

    def test_anonymous_attribution_hides_name_and_company(self) -> None:
        self.assertEqual(
            build_attribution("Jamie", "Marketing Manager", "Acme", False),
            "Marketing Manager",
        )

    def test_anonymous_attribution_has_safe_fallback(self) -> None:
        self.assertEqual(build_attribution("", "", "", False), "Verified customer")


class ResponseParsingTests(unittest.TestCase):
    def test_parses_valid_response(self) -> None:
        parsed = parse_testimonial_response(json.dumps(valid_response()))
        self.assertEqual(len(parsed["short_quotes"]), 5)
        self.assertEqual(len(parsed["social_proof"]), 3)
        self.assertEqual(parsed["case_study_snippet"]["challenge"], "Manual work")

    def test_parses_code_fenced_json(self) -> None:
        response = f"```json\n{json.dumps(valid_response())}\n```"
        parsed = parse_testimonial_response(response)
        self.assertEqual(parsed["website_testimonial"]["attribution"], "Jamie, Acme")

    def test_rejects_missing_field(self) -> None:
        response = valid_response()
        del response["callouts"]
        with self.assertRaisesRegex(ValueError, "missing keys: callouts"):
            parse_testimonial_response(json.dumps(response))

    def test_rejects_wrong_item_count(self) -> None:
        response = valid_response()
        response["short_quotes"].pop()
        with self.assertRaisesRegex(ValueError, "must contain 5 items"):
            parse_testimonial_response(json.dumps(response))

    def test_rejects_empty_nested_field(self) -> None:
        response = valid_response()
        response["case_study_snippet"]["outcome"] = ""
        with self.assertRaisesRegex(ValueError, "case_study_snippet.outcome"):
            parse_testimonial_response(json.dumps(response))

    def test_rejects_unapproved_attribution(self) -> None:
        response = valid_response()
        response["short_quotes"][0]["attribution"] = "Unapproved Company"
        with self.assertRaisesRegex(ValueError, "approved attribution"):
            parse_testimonial_response(
                json.dumps(response), expected_attribution="Jamie, Acme"
            )


class PromptAndFormattingTests(unittest.TestCase):
    def test_prompt_contains_claim_and_privacy_rules(self) -> None:
        prompt = build_prompt("Helpful feedback", "Verified customer", "Product")
        self.assertIn("Never invent results", prompt)
        self.assertIn("Use only the supplied attribution verbatim", prompt)
        self.assertIn("Verified customer", prompt)

    def test_formats_all_output_files(self) -> None:
        outputs = format_content_pack(valid_response())
        self.assertEqual(len(outputs), 5)
        self.assertIn("— Jamie, Acme", outputs["testimonial_quotes"])
        self.assertIn("Challenge\nManual work", outputs["testimonial_case_study"])


if __name__ == "__main__":
    unittest.main()
