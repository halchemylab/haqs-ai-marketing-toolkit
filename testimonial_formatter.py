"""Turn raw customer feedback into reusable, fact-safe social proof."""

from __future__ import annotations

import json
from typing import Any

from utils.marketing import (
    choose_option,
    generate_text,
    get_hourly_rate,
    log_roi_event,
    print_roi_logged,
    read_multiline,
    read_optional,
    save_text,
    welcome,
)


OUTPUT_COUNTS = {
    "short_quotes": 5,
    "case_study_snippet": 1,
    "social_proof": 3,
    "website_testimonial": 1,
    "callouts": 3,
}


def build_attribution(
    customer_name: str,
    job_title: str,
    company: str,
    display_identity: bool,
) -> str:
    """Build the attribution the model is allowed to use."""
    if not display_identity:
        return job_title or "Verified customer"

    identity = customer_name or "Verified customer"
    role = job_title
    if role and company:
        return f"{identity}, {role} at {company}"
    if company:
        return f"{identity}, {company}"
    if role:
        return f"{identity}, {role}"
    return identity


def build_prompt(
    feedback: str,
    attribution: str,
    product_or_service: str,
) -> str:
    product_context = product_or_service or "Not provided"
    return f"""
Turn the customer feedback below into a reusable testimonial content pack.

Return a valid JSON object only. Do not wrap it in Markdown. Use exactly this shape:
{{
  "short_quotes": [
    {{"text": "...", "attribution": "..."}}
  ],
  "case_study_snippet": {{
    "challenge": "...",
    "experience": "...",
    "outcome": "..."
  }},
  "social_proof": ["..."],
  "website_testimonial": {{"text": "...", "attribution": "..."}},
  "callouts": ["..."]
}}

Required counts:
- Exactly 5 short_quotes.
- Exactly 3 social_proof variations.
- Exactly 3 callouts.

Accuracy and privacy rules:
- Preserve the customer's meaning and level of certainty.
- Never invent results, percentages, statistics, dates, features, customer details,
  or measurable claims.
- Do not turn general praise into a quantified or guaranteed outcome.
- For an absent case-study detail, write "Not provided".
- Use only the supplied attribution verbatim. Do not infer identity details.
- Shorten and lightly polish quotes, but do not materially change what the customer said.
- The case-study fields and social-proof variations are paraphrased marketing copy, not
  direct quotations. Do not add quotation marks unless quoting faithful customer words.
- Keep every item concise, professional, and ready for human review.

Allowed attribution:
{attribution}

Product or service:
{product_context}

Raw customer feedback:
{feedback}
""".strip()


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"AI response field '{field_name}' must be a non-empty string.")
    return value.strip()


def _require_string_list(value: Any, field_name: str, count: int) -> list[str]:
    if not isinstance(value, list) or len(value) != count:
        raise ValueError(f"AI response field '{field_name}' must contain {count} items.")
    return [_require_string(item, f"{field_name}[{index}]") for index, item in enumerate(value)]


def parse_testimonial_response(
    response_text: str,
    expected_attribution: str | None = None,
) -> dict[str, Any]:
    """Parse and validate the model's testimonial content pack."""
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()

    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object from the AI response.")

    expected_keys = set(OUTPUT_COUNTS)
    missing_keys = expected_keys - set(parsed)
    if missing_keys:
        raise ValueError(f"AI response was missing keys: {', '.join(sorted(missing_keys))}")

    raw_quotes = parsed["short_quotes"]
    if not isinstance(raw_quotes, list) or len(raw_quotes) != OUTPUT_COUNTS["short_quotes"]:
        raise ValueError("AI response field 'short_quotes' must contain 5 items.")
    quotes = []
    for index, quote in enumerate(raw_quotes):
        if not isinstance(quote, dict):
            raise ValueError(f"AI response field 'short_quotes[{index}]' must be an object.")
        quote_text = _require_string(quote.get("text"), f"short_quotes[{index}].text")
        quote_attribution = _require_string(
            quote.get("attribution"), f"short_quotes[{index}].attribution"
        )
        if expected_attribution and quote_attribution != expected_attribution:
            raise ValueError(
                f"AI response field 'short_quotes[{index}].attribution' did not use "
                "the approved attribution."
            )
        quotes.append({"text": quote_text, "attribution": quote_attribution})

    raw_case_study = parsed["case_study_snippet"]
    if not isinstance(raw_case_study, dict):
        raise ValueError("AI response field 'case_study_snippet' must be an object.")
    case_study = {
        field: _require_string(raw_case_study.get(field), f"case_study_snippet.{field}")
        for field in ("challenge", "experience", "outcome")
    }

    raw_website = parsed["website_testimonial"]
    if not isinstance(raw_website, dict):
        raise ValueError("AI response field 'website_testimonial' must be an object.")
    website_attribution = _require_string(
        raw_website.get("attribution"), "website_testimonial.attribution"
    )
    if expected_attribution and website_attribution != expected_attribution:
        raise ValueError(
            "AI response field 'website_testimonial.attribution' did not use the "
            "approved attribution."
        )
    website = {
        "text": _require_string(raw_website.get("text"), "website_testimonial.text"),
        "attribution": website_attribution,
    }

    return {
        "short_quotes": quotes,
        "case_study_snippet": case_study,
        "social_proof": _require_string_list(
            parsed["social_proof"], "social_proof", OUTPUT_COUNTS["social_proof"]
        ),
        "website_testimonial": website,
        "callouts": _require_string_list(
            parsed["callouts"], "callouts", OUTPUT_COUNTS["callouts"]
        ),
    }


def format_content_pack(content_pack: dict[str, Any]) -> dict[str, str]:
    """Convert validated structured content into readable text files."""
    quotes = "\n\n".join(
        f'{index}. “{quote["text"]}”\n— {quote["attribution"]}'
        for index, quote in enumerate(content_pack["short_quotes"], start=1)
    )
    case = content_pack["case_study_snippet"]
    case_study = (
        f"Challenge\n{case['challenge']}\n\n"
        f"Experience\n{case['experience']}\n\n"
        f"Outcome\n{case['outcome']}"
    )
    social_proof = "\n\n".join(
        f"SOCIAL PROOF {index}\n{item}"
        for index, item in enumerate(content_pack["social_proof"], start=1)
    )
    website = content_pack["website_testimonial"]
    website_testimonial = f'“{website["text"]}”\n— {website["attribution"]}'
    callouts = "\n".join(
        f"{index}. {item}" for index, item in enumerate(content_pack["callouts"], start=1)
    )
    return {
        "testimonial_quotes": quotes,
        "testimonial_case_study": case_study,
        "testimonial_social_proof": social_proof,
        "testimonial_website": website_testimonial,
        "testimonial_callouts": callouts,
    }


def main() -> None:
    welcome("testimonial formatting")
    feedback = read_multiline("Paste the raw customer feedback below:")
    if not feedback:
        print("No customer feedback entered. Exiting.")
        return

    customer_name = read_optional("Customer name (optional): ")
    job_title = read_optional("Job title (optional): ")
    company = read_optional("Company (optional): ")
    product_or_service = read_optional("Product or service used (optional): ")
    identity_choice = choose_option(
        "May the customer's name and company be displayed?",
        ["Yes", "No — keep the customer anonymous"],
    )
    attribution = build_attribution(
        customer_name=customer_name,
        job_title=job_title,
        company=company,
        display_identity=identity_choice == "Yes",
    )

    print("\nFormatting testimonial content...\n")
    response_text = generate_text(
        system_prompt=(
            "You are a precise testimonial editor. Preserve customer meaning, protect "
            "privacy, and never invent or quantify claims."
        ),
        user_prompt=build_prompt(feedback, attribution, product_or_service),
    )
    content_pack = parse_testimonial_response(response_text, expected_attribution=attribution)
    formatted_outputs = format_content_pack(content_pack)

    saved_paths = []
    for prefix, content in formatted_outputs.items():
        path = save_text(prefix, content)
        saved_paths.append(path)
        print(f"===== {prefix} =====")
        print(content)
        print()

    total_count = sum(OUTPUT_COUNTS.values())
    minutes_per_item = 10
    total_minutes = total_count * minutes_per_item
    money_saved = (total_minutes / 60) * get_hourly_rate()
    log_roi_event(
        script="testimonial_formatter",
        asset_type="testimonial_content",
        count=total_count,
        minutes_per_item=minutes_per_item,
        notes="Formatted customer feedback into a testimonial content pack",
    )

    print("Saved files:")
    for path in saved_paths:
        print(f"- {path}")
    print()
    print_roi_logged(total_count, total_minutes, money_saved)


if __name__ == "__main__":
    main()
