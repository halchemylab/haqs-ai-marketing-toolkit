"""Campaign packet generation from a single reusable brief."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from haqs_toolkit.generators import (
    campaign_url_builder,
    content_repurposer,
    email_generator,
    landing_page_copy_generator,
    project_plan_builder,
    qr_code_generator,
)
from haqs_toolkit.utils.marketing import (
    AiGenerationError,
    generate_text,
    load_brand_voice,
)

RECOMMENDED_FIELDS = [
    "campaign_name",
    "campaign_type",
    "audience",
    "goal",
    "offer",
    "cta",
    "landing_page_url",
    "launch_date",
    "tone",
    "channels",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
]
REQUIRED_FIELDS = [
    "campaign_name",
    "audience",
    "goal",
    "cta",
    "landing_page_url",
]
DEFAULT_CHANNELS = ["email", "linkedin", "facebook", "qr_code"]
CAMPAIGN_TYPE_TO_PLAN_TYPE = {
    "event": "webinar",
    "webinar": "webinar",
    "product_launch": "product_launch",
    "offer": "email_campaign",
    "newsletter": "content_campaign",
    "lead_magnet": "content_campaign",
    "content_campaign": "content_campaign",
    "email_campaign": "email_campaign",
    "paid_ads_campaign": "paid_ads_campaign",
}


class CampaignBriefError(ValueError):
    """Raised when a campaign brief cannot be loaded or validated."""


def ensure_campaign_packet_dirs(campaign_dir: Path) -> None:
    (campaign_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (campaign_dir / "outputs").mkdir(parents=True, exist_ok=True)


def load_campaign_brief(path: Path) -> dict[str, object]:
    if not path.exists():
        raise CampaignBriefError(f"Missing required file: {path}")

    try:
        brief = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CampaignBriefError(f"Invalid JSON in {path}: {exc.msg}") from exc

    if not isinstance(brief, dict):
        raise CampaignBriefError("brief.json must contain a JSON object.")

    validate_campaign_brief(brief)
    return brief


def validate_campaign_brief(brief: dict[str, object]) -> None:
    errors = []
    for field in REQUIRED_FIELDS:
        value = brief.get(field)
        if value is None or str(value).strip() == "":
            errors.append(f"Missing required field: {field}")

    landing_page_url = str(brief.get("landing_page_url", "")).strip()
    if landing_page_url:
        parsed = urlparse(landing_page_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(
                "Invalid landing_page_url: use a full http:// or https:// URL."
            )

    launch_date = str(brief.get("launch_date", "")).strip()
    if launch_date:
        try:
            project_plan_builder.parse_date(launch_date)
        except ValueError:
            errors.append("Invalid launch_date: use YYYY-MM-DD.")

    channels = brief.get("channels")
    if channels is not None and (
        not isinstance(channels, list)
        or not all(str(channel).strip() for channel in channels)
    ):
        errors.append("Invalid channels: use a non-empty JSON array of channel names.")

    if errors:
        raise CampaignBriefError("\n".join(errors))


def normalized_channels(brief: dict[str, object]) -> list[str]:
    channels = brief.get("channels", DEFAULT_CHANNELS)
    if not isinstance(channels, list):
        return DEFAULT_CHANNELS
    return [
        str(channel).strip().lower() for channel in channels if str(channel).strip()
    ]


def brief_text(brief: dict[str, object]) -> str:
    lines = []
    for key in RECOMMENDED_FIELDS:
        if key not in brief:
            continue
        value = brief[key]
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            rendered_value = ", ".join(str(item) for item in value)
        else:
            rendered_value = str(value)
        lines.append(f"- {label}: {rendered_value}")
    return "\n".join(lines)


def source_notes(campaign_dir: Path) -> str:
    path = campaign_dir / "inputs" / "source-notes.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def campaign_source_material(brief: dict[str, object], notes: str) -> str:
    material = ["Campaign brief:", brief_text(brief)]
    if notes:
        material.extend(["", "Source notes:", notes])
    return "\n".join(material).strip()


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def ai_or_fallback(system_prompt: str, user_prompt: str, fallback: str) -> str:
    try:
        return generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
    except AiGenerationError as exc:
        return f"{fallback}\n\nGeneration note: {exc}"


def build_campaign_url(brief: dict[str, object]) -> str:
    landing_page_url = str(brief["landing_page_url"]).strip()
    source = str(brief.get("utm_source") or "campaign").strip()
    medium = str(brief.get("utm_medium") or "marketing").strip()
    campaign_name = (
        str(brief.get("utm_campaign") or brief["campaign_name"])
        .strip()
        .lower()
        .replace(" ", "_")
    )
    campaign_content = str(brief.get("utm_content") or "").strip()
    return campaign_url_builder.add_utm_parameters(
        landing_page_url=landing_page_url,
        source=source,
        medium=medium,
        campaign_name=campaign_name,
        campaign_content=campaign_content,
    )


def fallback_email_copy(brief: dict[str, object], campaign_url: str) -> str:
    name = str(brief["campaign_name"])
    audience = str(brief["audience"])
    goal = str(brief["goal"])
    cta = str(brief["cta"])
    offer = str(brief.get("offer") or name)
    return f"""
Subject: {offer}

Hi [first name],

We created this for {audience}.

{offer} is designed to help with this goal: {goal}.

{cta}: {campaign_url}

=====
Subject: A practical next step for {audience}

Hi [first name],

If {goal.lower()} is a priority, this may be useful.

Review the details for {offer}, then use the link below when you are ready.

{cta}: {campaign_url}

=====
Subject: Quick reminder: {offer}

Hi [first name],

One more reminder to review {offer}.

{cta}: {campaign_url}
""".strip()


def fallback_social_copy(brief: dict[str, object], campaign_url: str) -> str:
    name = str(brief["campaign_name"])
    cta = str(brief["cta"])
    audience = str(brief["audience"])
    return f"""
# Social Posts: {name}

1. Built for {audience}: {name}. {cta}: {campaign_url}
2. Looking for a practical next step? Review {name}: {campaign_url}
3. {cta}. Details here: {campaign_url}
""".strip()


def social_prompt(
    source_material: str,
    brand_voice: str,
    campaign_url: str,
) -> str:
    return f"""
{content_repurposer.brand_voice_prompt_block(brand_voice)}

Create review-ready social posts from this campaign material.

Requirements:
- Write 5 LinkedIn posts.
- Write 3 Facebook posts.
- Write 5 short X posts.
- Preserve factual details from the source material.
- Do not invent dates, speakers, prices, venues, statistics, or promises.
- Use this exact campaign URL anywhere a destination link is needed:
  {campaign_url}
- Return Markdown only.

Source material:
{source_material}
""".strip()


def fallback_landing_copy(brief: dict[str, object], campaign_url: str) -> str:
    name = str(brief["campaign_name"])
    audience = str(brief["audience"])
    goal = str(brief["goal"])
    cta = str(brief["cta"])
    offer = str(brief.get("offer") or name)
    return f"""
# Landing Page Copy: {name}

## Hero
### Headline Options
1. {offer}
2. A practical next step for {audience}
3. Make progress on {goal}

### Subheadline
Use this offer to help {audience} move toward: {goal}.

### Primary CTA
[{cta}]({campaign_url})

## Benefits
- Clear next step for {audience}
- Focused around the campaign goal
- Easy CTA path

## Final CTA
Ready to take the next step?

[{cta}]({campaign_url})
""".strip()


def write_project_plan(brief: dict[str, object], output_dir: Path) -> Path | None:
    launch_date = str(brief.get("launch_date") or "").strip()
    if not launch_date:
        return None

    campaign_type = str(brief.get("campaign_type") or "content_campaign").strip()
    plan_type = CAMPAIGN_TYPE_TO_PLAN_TYPE.get(campaign_type, "content_campaign")
    channels = project_plan_builder.parse_channels(
        ", ".join(normalized_channels(brief))
    )
    rows = project_plan_builder.build_rows(
        campaign_name=str(brief["campaign_name"]),
        launch_date=project_plan_builder.parse_date(launch_date),
        campaign_type=plan_type,
        selected_channels=channels,
        team={},
        buffer_days=2,
    )
    path = output_dir / "project-plan.csv"
    project_plan_builder.write_csv(
        path,
        rows,
        project_plan_builder.PROJECT_PLAN_FIELDNAMES,
    )
    return path


def write_packet_index(
    output_dir: Path,
    paths: list[Path],
    skipped: list[str],
) -> Path:
    lines = ["# Campaign Packet Index", ""]
    lines.append("## Generated Files")
    lines.append("")
    for path in paths:
        if path.name == "packet-index.md":
            continue
        lines.append(f"- [{path.name}]({path.name})")

    if skipped:
        lines.extend(["", "## Needs Attention", ""])
        for item in skipped:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Review Checklist",
            "",
            "- Replace any remaining placeholders.",
            "- Confirm claims, dates, prices, names, and links before publishing.",
            "- Test the campaign URL and QR code before using them in live assets.",
        ]
    )
    return write_text(output_dir / "packet-index.md", "\n".join(lines))


def write_campaign_assets(
    brief: dict[str, object],
    campaign_dir: Path,
    output_dir: Path,
) -> list[Path]:
    print(f"Preparing output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    notes = source_notes(campaign_dir)
    brand_voice = load_brand_voice()
    source_material = campaign_source_material(brief, notes)
    campaign_url = build_campaign_url(brief)
    channels = normalized_channels(brief)

    paths: list[Path] = []
    skipped: list[str] = []

    paths.append(
        write_text(
            output_dir / "campaign-brief-summary.md",
            f"# {brief['campaign_name']}\n\n"
            f"## Source Brief\n\n{brief_text(brief)}\n\n"
            f"## Brand Voice\n\n{brand_voice}\n\n"
            f"## Source Notes\n\n{notes or 'No source notes provided.'}",
        )
    )
    paths.append(write_text(output_dir / "campaign-url.txt", campaign_url))

    email_copy = ai_or_fallback(
        system_prompt="You are a precise marketing email copywriter.",
        user_prompt=email_generator.build_prompt(
            source_content=source_material,
            purpose=str(brief["goal"]),
            brand_voice=brand_voice,
        ),
        fallback=fallback_email_copy(brief, campaign_url),
    ).replace("[url here]", campaign_url)
    paths.append(write_text(output_dir / "email-drafts.md", email_copy))

    social_copy = ai_or_fallback(
        system_prompt=(
            "You are a precise marketing strategist and content repurposing assistant."
        ),
        user_prompt=social_prompt(source_material, brand_voice, campaign_url),
        fallback=fallback_social_copy(brief, campaign_url),
    )
    paths.append(write_text(output_dir / "social-posts.md", social_copy))

    landing_copy = ai_or_fallback(
        system_prompt="You are a precise conversion copywriter for landing pages.",
        user_prompt=landing_page_copy_generator.build_prompt(
            offer_name=str(brief["campaign_name"]),
            offer_type=str(brief.get("campaign_type") or "Offer"),
            offer_description=str(brief.get("offer") or brief["goal"]),
            audience=str(brief["audience"]),
            page_goal=str(brief["goal"]),
            tone=str(brief.get("tone") or "Clear and practical"),
            audience_problem=str(brief["goal"]),
            main_benefit=str(brief.get("offer") or brief["goal"]),
            primary_cta=str(brief["cta"]),
            credibility="",
            must_include=f"Use this campaign URL: {campaign_url}",
            avoid="",
            brand_voice=brand_voice,
        ),
        fallback=fallback_landing_copy(brief, campaign_url),
    ).replace("[url here]", campaign_url)
    paths.append(write_text(output_dir / "landing-page-copy.md", landing_copy))

    if "qr_code" in channels or "qr" in channels:
        qr_path = output_dir / "qr-code.png"
        qr_code_generator.create_qr_code(campaign_url).save(qr_path)
        paths.append(qr_path)

    project_plan_path = write_project_plan(brief, output_dir)
    if project_plan_path:
        paths.append(project_plan_path)
    else:
        skipped.append("Add launch_date to brief.json to generate project-plan.csv.")

    index_path = write_packet_index(output_dir, paths, skipped)
    paths.append(index_path)
    return paths


def generate_campaign_packet(
    campaign_dir: Path,
    output_dir: Path | None = None,
) -> list[Path]:
    ensure_campaign_packet_dirs(campaign_dir)
    brief = load_campaign_brief(campaign_dir / "brief.json")
    resolved_output_dir = output_dir or campaign_dir / "outputs"
    return write_campaign_assets(brief, campaign_dir, resolved_output_dir)


def starter_brief(campaign_name: str) -> dict[str, object]:
    today = date.today().isoformat()
    return {
        "campaign_name": campaign_name,
        "campaign_type": "offer",
        "audience": "Describe the target audience",
        "goal": "Describe the campaign goal",
        "offer": "Describe the offer",
        "cta": "Get started",
        "landing_page_url": "https://example.com",
        "launch_date": today,
        "tone": "Clear and practical",
        "channels": DEFAULT_CHANNELS,
        "utm_source": "campaign",
        "utm_medium": "marketing",
        "utm_campaign": campaign_name.lower().replace(" ", "_"),
    }


def create_campaign_packet(campaign_dir: Path) -> Path:
    ensure_campaign_packet_dirs(campaign_dir)
    brief_path = campaign_dir / "brief.json"
    if brief_path.exists():
        raise CampaignBriefError(f"brief.json already exists: {brief_path}")
    campaign_name = campaign_dir.name.replace("-", " ").replace("_", " ").title()
    brief_path.write_text(
        json.dumps(starter_brief(campaign_name), indent=2) + "\n",
        encoding="utf-8",
    )
    (campaign_dir / "inputs" / "source-notes.md").write_text(
        (
            "# Source Notes\n\n"
            "Add campaign details, customer language, or offer notes here.\n"
        ),
        encoding="utf-8",
    )
    return brief_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a complete campaign asset packet from one brief.",
        epilog="Example: haqs-campaign campaigns/fall-workshop",
    )
    parser.add_argument(
        "--list-fields",
        action="store_true",
        help="Print recommended brief.json fields and exit.",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="Create a starter campaign packet instead of generating assets.",
    )
    parser.add_argument(
        "campaign_dir",
        type=Path,
        nargs="?",
        help="Path to a campaign packet directory containing brief.json.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output directory. Defaults to <campaign_dir>/outputs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_fields:
        print("Recommended brief.json fields:")
        for field in RECOMMENDED_FIELDS:
            print(f"- {field}")
        return 0

    if args.campaign_dir is None:
        parser.error("campaign_dir is required unless --list-fields is used.")

    try:
        if args.new:
            brief_path = create_campaign_packet(args.campaign_dir)
            print(f"Created starter campaign packet: {brief_path}")
            return 0

        print(f"Using campaign packet: {args.campaign_dir}")
        paths = generate_campaign_packet(args.campaign_dir, args.out)
    except CampaignBriefError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Generated {len(paths)} campaign files:")
    for path in paths:
        print(f"- {path}")
    print("\nNext step: Open packet-index.md and review the checklist.")
    return 0


def interactive_main() -> None:
    raw_path = input("Campaign packet path, e.g. campaigns/fall-workshop: ").strip()
    if not raw_path:
        print("No campaign packet path entered. Exiting.")
        return
    raise SystemExit(main([raw_path]))


if __name__ == "__main__":
    raise SystemExit(main())
