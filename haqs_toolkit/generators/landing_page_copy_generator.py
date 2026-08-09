"""Generate landing page copy from a guided mini-brief."""

from __future__ import annotations

from pathlib import Path

from haqs_toolkit.utils.marketing import (
    AiGenerationError,
    brand_voice_prompt_block,
    choose_option,
    generate_text,
    load_brand_voice,
    log_roi_event,
    print_roi_logged,
    read_optional,
    read_required,
    timestamped_output_path,
    welcome,
)

OFFER_TYPES = [
    "Service",
    "Product",
    "Course / workshop",
    "Download / lead magnet",
    "Event",
    "Software / app",
    "Other",
]

AUDIENCES = [
    "Small business owners",
    "Solo founders",
    "Marketing teams",
    "Local service businesses",
    "Coaches / consultants",
    "Ecommerce brands",
    "Custom audience",
]

PAGE_GOALS = [
    "Book a call",
    "Get signups",
    "Sell a product",
    "Download a resource",
    "Register for an event",
    "Request a quote",
    "Contact the business",
]

TONES = [
    "Clear and practical",
    "Premium and polished",
    "Friendly and conversational",
    "Bold and persuasive",
    "Professional and trustworthy",
    "Warm and local",
]

AUDIENCE_PROBLEMS = [
    "Not enough time",
    "Too expensive",
    "Too confusing",
    "Not getting enough leads",
    "Inconsistent marketing",
    "Low confidence / uncertainty",
    "Custom problem",
]

MAIN_BENEFITS = [
    "Save time",
    "Get more leads",
    "Look more professional",
    "Make better decisions",
    "Simplify the process",
    "Increase conversions",
    "Custom benefit",
]

CTA_OPTIONS = [
    "Book a Call",
    "Get Started",
    "Download Now",
    "Request a Quote",
    "Sign Up",
    "Register Now",
    "Contact Us",
    "Custom CTA",
]


def choose_or_custom(prompt: str, options: list[str], custom_label: str) -> str:
    selected = choose_option(prompt, options)
    if selected == custom_label:
        return read_required("Enter your custom answer: ")
    return selected


def save_markdown(prefix: str, content: str) -> Path:
    path = timestamped_output_path(prefix, "md")
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def build_prompt(
    offer_name: str,
    offer_type: str,
    offer_description: str,
    audience: str,
    page_goal: str,
    tone: str,
    audience_problem: str,
    main_benefit: str,
    primary_cta: str,
    credibility: str,
    must_include: str,
    avoid: str,
    brand_voice: str | None = None,
) -> str:
    credibility_text = credibility or "No extra proof points provided."
    must_include_text = must_include or "No required details provided."
    avoid_text = avoid or "No restricted claims, words, or topics provided."

    return f"""
{brand_voice_prompt_block(brand_voice)}

Create polished landing page copy from this brief.

Brief:
- Offer name: {offer_name}
- Offer type: {offer_type}
- Offer description: {offer_description}
- Audience: {audience}
- Main page goal: {page_goal}
- Tone: {tone}
- Audience problem: {audience_problem}
- Main benefit: {main_benefit}
- Primary CTA: {primary_cta}
- What makes it different or credible: {credibility_text}
- Details that must be included: {must_include_text}
- Claims, words, or topics to avoid: {avoid_text}

Requirements:
- Return Markdown only.
- Do not invent prices, guarantees, deadlines, statistics, testimonials,
  locations, or company history.
- Use [url here] anywhere a button or link destination is needed.
- Keep the copy specific to the brief and ready to paste into a landing page.
- Use the selected tone as the local page tone while preserving the selected
  brand voice.
- Provide multiple options where useful, but do not over-explain the strategy.
- Avoid hype, vague filler, and unsupported claims.

Use this exact structure:
# Landing Page Copy: {offer_name}

## Hero
### Headline Options
Provide 5 headline options.

### Subheadline
Provide 2 subheadline options.

### Primary CTA
Provide the button text and link placeholder.

### Secondary CTA
Provide an optional lower-commitment CTA.

## Problem Section
Provide a section headline and 1-2 short paragraphs.

## Solution Section
Provide a section headline and 1-2 short paragraphs.

## Benefits
Provide 5 benefit bullets with short supporting copy.

## How It Works
Provide 3-4 clear steps.

## Feature Blocks
Provide 3 concise feature/value blocks.

## Proof / Credibility Section
Write copy using only the credibility details provided. If none were provided,
write a credibility section that does not imply external proof.

## FAQ
Provide 5 FAQs with concise answers.

## Final CTA
Provide a final conversion section with headline, short copy, and CTA.

## SEO
Provide a meta title and meta description.
""".strip()


def main() -> None:
    welcome("landing page copy generation")

    offer_name = read_required(
        "What is the name of the business, product, service, or offer? "
    )
    offer_type = choose_or_custom(
        "\nWhat are you promoting?",
        OFFER_TYPES,
        "Other",
    )
    audience = choose_or_custom(
        "\nWho is this for?",
        AUDIENCES,
        "Custom audience",
    )
    page_goal = choose_option("\nWhat is the main goal of the page?", PAGE_GOALS)
    tone = choose_option("\nWhat tone should the copy use?", TONES)
    audience_problem = choose_or_custom(
        "\nWhat is the main audience problem?",
        AUDIENCE_PROBLEMS,
        "Custom problem",
    )
    main_benefit = choose_or_custom(
        "\nWhat is the main benefit?",
        MAIN_BENEFITS,
        "Custom benefit",
    )
    primary_cta = choose_or_custom(
        "\nWhat should the primary CTA say?",
        CTA_OPTIONS,
        "Custom CTA",
    )

    print("\nNow add a few short details so the copy is specific.")
    offer_description = read_required("Describe the offer in one sentence: ")
    credibility = read_optional(
        "What makes this offer different or credible? Optional, press Enter to skip: "
    )
    must_include = read_optional(
        "Anything that must be included? Optional, press Enter to skip: "
    )
    avoid = read_optional(
        "Anything to avoid saying? Optional, press Enter to skip: "
    )

    print("\nGenerating landing page copy...\n")
    brand_voice = load_brand_voice()

    try:
        landing_page_copy = generate_text(
            system_prompt="You are a precise conversion copywriter for landing pages.",
            user_prompt=build_prompt(
                offer_name=offer_name,
                offer_type=offer_type,
                offer_description=offer_description,
                audience=audience,
                page_goal=page_goal,
                tone=tone,
                audience_problem=audience_problem,
                main_benefit=main_benefit,
                primary_cta=primary_cta,
                credibility=credibility,
                must_include=must_include,
                avoid=avoid,
                brand_voice=brand_voice,
            ),
        )
    except AiGenerationError as exc:
        print(f"Error: {exc}")
        return

    path = save_markdown("landing_page_copy", landing_page_copy)
    minutes_saved = 90
    roi = log_roi_event(
        script="landing_page_copy_generator",
        asset_type="landing_page_copy",
        count=1,
        minutes_per_item=minutes_saved,
        notes=f"Generated landing page copy for {offer_name}",
    )

    print(landing_page_copy)
    print(f"\nSaved to: {path}")
    print_roi_logged(roi)


if __name__ == "__main__":
    main()
