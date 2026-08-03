"""Repurpose source material into multiple marketing content formats."""

from __future__ import annotations

import json

from utils.marketing import (
    AiGenerationError,
    combine_roi_results,
    generate_text,
    log_roi_event,
    print_roi_logged,
    read_multiline,
    save_text,
    welcome,
)


OUTPUT_FORMATS = {
    "linkedin_posts": "5 LinkedIn post ideas",
    "x_posts": "10 X post variations",
    "facebook_posts": "3 Facebook post variations",
    "email_subject_lines": "8 email subject lines",
    "newsletter_blurb": "1 short newsletter blurb",
    "hooks": "8 hook ideas",
    "pull_quotes": "5 pull quotes",
}

ROI_RULES = {
    "linkedin_posts": {"count": 5, "minutes_per_item": 15},
    "x_posts": {"count": 10, "minutes_per_item": 15},
    "facebook_posts": {"count": 3, "minutes_per_item": 15},
    "email_subject_lines": {"count": 8, "minutes_per_item": 5},
    "newsletter_blurb": {"count": 1, "minutes_per_item": 15},
    "hooks": {"count": 8, "minutes_per_item": 5},
    "pull_quotes": {"count": 5, "minutes_per_item": 5},
}

CONTENT_PACK_SCHEMA = {
    "type": "json_schema",
    "name": "content_repurposing_pack",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            key: {"type": "string", "minLength": 1}
            for key in OUTPUT_FORMATS
        },
        "required": list(OUTPUT_FORMATS),
        "additionalProperties": False,
    },
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
    try:
        response_text = generate_text(
            system_prompt="You are a precise marketing strategist and content repurposing assistant.",
            user_prompt=build_prompt(source_content),
            text_format=CONTENT_PACK_SCHEMA,
        )
    except AiGenerationError as exc:
        print(f"Error: {exc}")
        return

    try:
        content_pack = parse_json_response(response_text)
    except ValueError as exc:
        path = save_text("content_repurposer_raw_response", response_text)
        print(f"Error: AI response could not be parsed: {exc}")
        print(f"Raw response saved to: {path}")
        return

    saved_paths = []
    roi_results = []
    for format_name, content in content_pack.items():
        path = save_text(format_name, content)
        saved_paths.append(path)
        roi_rule = ROI_RULES[format_name]
        roi = log_roi_event(
            script="content_repurposer",
            asset_type=format_name,
            count=roi_rule["count"],
            minutes_per_item=roi_rule["minutes_per_item"],
            notes=f"Generated {OUTPUT_FORMATS[format_name]}",
        )
        roi_results.append(roi)

        print(f"===== {format_name} =====")
        print(content)
        print()

    print("Saved files:")
    for path in saved_paths:
        print(f"- {path}")
    print()
    print_roi_logged(combine_roi_results(roi_results))


if __name__ == "__main__":
    main()
