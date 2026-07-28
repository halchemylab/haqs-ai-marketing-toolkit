"""Repurpose source material into multiple marketing content formats."""

from __future__ import annotations

import json

from haqs_cli import generate_text, read_multiline, save_text, welcome


OUTPUT_FORMATS = {
    "linkedin_posts": "5 LinkedIn post ideas",
    "x_posts": "10 X post variations",
    "facebook_posts": "3 Facebook post variations",
    "email_subject_lines": "8 email subject lines",
    "newsletter_blurb": "1 short newsletter blurb",
    "hooks": "8 hook ideas",
    "pull_quotes": "5 pull quotes",
}


def build_prompt(source_content: str) -> str:
    format_list = "\n".join(
        f'- "{key}": {description}' for key, description in OUTPUT_FORMATS.items()
    )
    return f"""
Repurpose the source material below into a practical marketing content pack.

Return a valid JSON object only. Do not wrap it in Markdown. The JSON object must use
these exact keys, and each value must be a single formatted plain-text string:
{format_list}

Requirements:
- Preserve factual details from the source material.
- Do not invent dates, speakers, prices, venues, statistics, or promises.
- Include the exact placeholder [url here] anywhere a destination link is needed.
- Make each format ready to review, edit, and publish.
- Keep the writing clear, professional, and useful to a marketer.
- For list-style outputs, number each item inside the plain-text string.

Source material:
{source_content}
""".strip()


def parse_json_response(response_text: str) -> dict[str, str]:
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()

    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object from the AI response.")

    missing_keys = [key for key in OUTPUT_FORMATS if key not in parsed]
    if missing_keys:
        raise ValueError(f"AI response was missing keys: {', '.join(missing_keys)}")

    return {key: str(parsed[key]).strip() for key in OUTPUT_FORMATS}


def main() -> None:
    welcome("content repurposing")
    source_content = read_multiline("Enter or Paste the Content Here:")
    if not source_content:
        print("No content entered. Exiting.")
        return

    print("\nGenerating content pack...\n")
    response_text = generate_text(
        system_prompt="You are a precise marketing strategist and content repurposing assistant.",
        user_prompt=build_prompt(source_content),
    )
    content_pack = parse_json_response(response_text)

    saved_paths = []
    for format_name, content in content_pack.items():
        path = save_text(format_name, content)
        saved_paths.append(path)

        print(f"===== {format_name} =====")
        print(content)
        print()

    print("Saved files:")
    for path in saved_paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
