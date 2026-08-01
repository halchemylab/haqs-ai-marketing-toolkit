import unittest

from content_repurposer import OUTPUT_FORMATS, parse_json_response


class ContentRepurposerTests(unittest.TestCase):
    def test_parse_json_response_accepts_expected_keys(self):
        response = "{" + ",".join(f'"{key}": "value"' for key in OUTPUT_FORMATS) + "}"

        parsed = parse_json_response(response)

        self.assertEqual(set(parsed), set(OUTPUT_FORMATS))
        self.assertTrue(all(value == "value" for value in parsed.values()))

    def test_parse_json_response_strips_markdown_fence(self):
        response = (
            "```json\n"
            + "{"
            + ",".join(f'"{key}": "value"' for key in OUTPUT_FORMATS)
            + "}\n```"
        )

        parsed = parse_json_response(response)

        self.assertEqual(set(parsed), set(OUTPUT_FORMATS))

    def test_parse_json_response_rejects_missing_keys(self):
        response = '{"linkedin_posts": "value"}'

        with self.assertRaisesRegex(ValueError, "missing keys"):
            parse_json_response(response)


if __name__ == "__main__":
    unittest.main()
