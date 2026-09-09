"""User-facing marketing asset creation flow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from haqs_toolkit import campaigns, events
from haqs_toolkit.generators import (
    email_generator,
    landing_page_copy_generator,
    qr_code_generator,
)
from haqs_toolkit.generators.campaign_url_builder import add_utm_parameters
from haqs_toolkit.runs import create_run_dir, write_packet_index, write_quality_check
from haqs_toolkit.utils.marketing import (
    choose_option,
    load_brand_voice,
    read_optional,
    read_required,
    read_url,
)

SCOPE_COMPLETE = "complete"
SCOPE_SELECTED = "selected"
JOB_EVENT = "event"
JOB_CAMPAIGN = "campaign"

ASSET_TRACKED_URL = "tracked_url"
ASSET_QR_CODE = "qr_code"
ASSET_EMAIL = "email"
ASSET_SOCIAL = "social"
ASSET_LANDING_PAGE = "landing_page"
ASSET_PROJECT_PLAN = "project_plan"

EVENT_COMPLETE_ASSETS = [
    ASSET_TRACKED_URL,
    ASSET_QR_CODE,
    ASSET_EMAIL,
    ASSET_SOCIAL,
    ASSET_LANDING_PAGE,
]
CAMPAIGN_COMPLETE_ASSETS = [
    ASSET_TRACKED_URL,
    ASSET_QR_CODE,
    ASSET_EMAIL,
    ASSET_SOCIAL,
    ASSET_LANDING_PAGE,
    ASSET_PROJECT_PLAN,
]
SELECTABLE_ASSETS = [
    ASSET_TRACKED_URL,
    ASSET_QR_CODE,
    ASSET_EMAIL,
    ASSET_SOCIAL,
    ASSET_LANDING_PAGE,
    ASSET_PROJECT_PLAN,
]
ASSET_LABELS = {
    ASSET_TRACKED_URL: "Tracked URL",
    ASSET_QR_CODE: "QR code",
    ASSET_EMAIL: "Email sequence",
    ASSET_SOCIAL: "Social posts",
    ASSET_LANDING_PAGE: "Landing page copy",
    ASSET_PROJECT_PLAN: "Project plan",
}


def parse_assets(raw_assets: str | None, job_type: str, scope: str) -> list[str]:
    if scope == SCOPE_COMPLETE:
        if job_type == JOB_EVENT:
            return EVENT_COMPLETE_ASSETS.copy()
        return CAMPAIGN_COMPLETE_ASSETS.copy()

    if not raw_assets:
        raise ValueError("--assets is required when --scope selected is used.")

    assets = [
        asset.strip().lower().replace("-", "_") for asset in raw_assets.split(",")
    ]
    invalid = [asset for asset in assets if asset not in SELECTABLE_ASSETS]
    if invalid:
        raise ValueError(f"Unknown asset(s): {', '.join(invalid)}")
    if job_type == JOB_EVENT and ASSET_PROJECT_PLAN in assets:
        raise ValueError("project_plan is only available for campaign runs.")
    return assets


def campaign_url_for_event(brief: dict[str, object]) -> str:
    event_name = str(brief["event_name"])
    return add_utm_parameters(
        landing_page_url=str(brief["registration_url"]),
        source=str(brief.get("utm_source") or "event"),
        medium=str(brief.get("utm_medium") or "marketing"),
        campaign_name=str(brief.get("utm_campaign") or event_name)
        .strip()
        .lower()
        .replace(" ", "_"),
        campaign_content=str(brief.get("utm_content") or ""),
    )


def write_json(path: Path, data: dict[str, object]) -> Path:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def write_event_run_assets(
    brief: dict[str, object],
    output_dir: Path,
    selected_assets: list[str],
) -> list[Path]:
    event_name = str(brief["event_name"])
    cta = str(brief["cta"])
    tone = str(brief.get("tone") or "Clear and practical")
    brand_voice = load_brand_voice()
    source = events.brief_text(brief)
    campaign_url = campaign_url_for_event(brief)
    paths = [
        write_text(
            output_dir / "event-summary.md",
            f"# {event_name}\n\n"
            f"## Source Brief\n\n{source}\n\n"
            f"## Brand Voice\n\n{brand_voice}\n\n"
            f"## Local Event Tone\n\n{tone}",
        )
    ]

    if ASSET_TRACKED_URL in selected_assets:
        paths.append(write_text(output_dir / "campaign-url.txt", campaign_url))
    if ASSET_QR_CODE in selected_assets:
        qr_path = output_dir / "qr-code.png"
        qr_code_generator.create_qr_code(campaign_url).save(qr_path)
        paths.append(qr_path)
    if ASSET_EMAIL in selected_assets:
        paths.append(
            write_text(
                output_dir / "email-sequence.md",
                f"# Email Sequence: {event_name}\n\n"
                f"Local tone: {tone}\n\n"
                "## Email 1\n\n"
                f"Subject: You're invited to {event_name}\n\n"
                f"Join us for {event_name}. {cta}: {campaign_url}\n\n"
                "## Email 2\n\n"
                f"Subject: Reminder: {event_name}\n\n"
                f"Save your spot for {event_name}. {cta}: {campaign_url}",
            )
        )
    if ASSET_SOCIAL in selected_assets:
        paths.append(
            write_text(
                output_dir / "social-posts.md",
                f"# Social Posts: {event_name}\n\n"
                f"Local tone: {tone}\n\n"
                f"1. Join us for {event_name}. {cta}: {campaign_url}\n"
                f"2. Planning to attend {event_name}? Details and registration: "
                f"{campaign_url}\n"
                f"3. Last call for {event_name}. {cta}: {campaign_url}",
            )
        )
    if ASSET_LANDING_PAGE in selected_assets:
        paths.append(
            write_text(
                output_dir / "landing-page-copy.md",
                f"# Landing Page Copy: {event_name}\n\n"
                f"Local tone: {tone}\n\n"
                f"## Hero\n\n{event_name}\n\n"
                f"## Primary CTA\n\n[{cta}]({campaign_url})",
            )
        )
    return paths


def write_campaign_run_assets(
    brief: dict[str, object],
    output_dir: Path,
    selected_assets: list[str],
) -> list[Path]:
    brand_voice = load_brand_voice()
    source_material = campaigns.campaign_source_material(brief, "")
    campaign_url = campaigns.build_campaign_url(brief)
    paths = [
        write_text(
            output_dir / "campaign-summary.md",
            f"# {brief['campaign_name']}\n\n"
            f"## Source Brief\n\n{campaigns.brief_text(brief)}\n\n"
            f"## Brand Voice\n\n{brand_voice}",
        )
    ]

    if ASSET_TRACKED_URL in selected_assets:
        paths.append(write_text(output_dir / "campaign-url.txt", campaign_url))
    if ASSET_QR_CODE in selected_assets:
        qr_path = output_dir / "qr-code.png"
        qr_code_generator.create_qr_code(campaign_url).save(qr_path)
        paths.append(qr_path)
    if ASSET_EMAIL in selected_assets:
        email_copy = campaigns.ai_or_fallback(
            system_prompt="You are a precise marketing email copywriter.",
            user_prompt=email_generator.build_prompt(
                source_content=source_material,
                purpose=str(brief["goal"]),
                brand_voice=brand_voice,
            ),
            fallback=campaigns.fallback_email_copy(brief, campaign_url),
        ).replace("[url here]", campaign_url)
        paths.append(write_text(output_dir / "email-drafts.md", email_copy))
    if ASSET_SOCIAL in selected_assets:
        social_copy = campaigns.ai_or_fallback(
            system_prompt=(
                "You are a precise marketing strategist and content "
                "repurposing assistant."
            ),
            user_prompt=campaigns.social_prompt(
                source_material,
                brand_voice,
                campaign_url,
            ),
            fallback=campaigns.fallback_social_copy(brief, campaign_url),
        )
        paths.append(write_text(output_dir / "social-posts.md", social_copy))
    if ASSET_LANDING_PAGE in selected_assets:
        landing_copy = campaigns.ai_or_fallback(
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
            fallback=campaigns.fallback_landing_copy(brief, campaign_url),
        ).replace("[url here]", campaign_url)
        paths.append(write_text(output_dir / "landing-page-copy.md", landing_copy))
    if ASSET_PROJECT_PLAN in selected_assets:
        project_plan_path = campaigns.write_project_plan(brief, output_dir)
        if project_plan_path:
            paths.append(project_plan_path)
    return paths


def run_creation(
    brief: dict[str, object],
    job_type: str,
    scope: str,
    selected_assets: list[str],
    *,
    runs_dir: Path = Path("runs"),
) -> Path:
    job_name_key = "event_name" if job_type == JOB_EVENT else "campaign_name"
    run_dir = create_run_dir(
        str(brief[job_name_key]),
        job_type,
        scope,
        runs_dir=runs_dir,
    )
    output_dir = run_dir / "outputs"
    write_json(run_dir / "brief.json", brief)

    if job_type == JOB_EVENT:
        output_paths = write_event_run_assets(brief, output_dir, selected_assets)
    else:
        output_paths = write_campaign_run_assets(brief, output_dir, selected_assets)

    quality_path, issues = write_quality_check(run_dir)
    index_path = write_packet_index(run_dir, output_paths, len(issues))

    print(f"Created marketing run: {run_dir}")
    print(f"Generated {len(output_paths)} output file(s):")
    for path in output_paths:
        print(f"- {path}")
    print(f"Quality check: {quality_path}")
    print(f"Packet index: {index_path}")
    print(f"Quality issues found: {len(issues)}")
    return run_dir


def brief_from_inputs(job_type: str) -> dict[str, object]:
    if job_type == JOB_EVENT:
        return {
            "event_name": read_required("Event name: "),
            "event_date": read_required("Event date (YYYY-MM-DD): "),
            "event_time": read_optional("Event time: "),
            "timezone": read_optional("Timezone: "),
            "location": read_optional("Location: "),
            "audience": read_required("Audience: "),
            "goal": read_required("Goal: "),
            "offer": read_optional("Offer or promise: "),
            "cta": read_required("CTA: "),
            "registration_url": read_url("Registration URL: "),
            "tone": read_optional("Tone: ") or "Clear and practical",
            "channels": ["email", "social"],
        }

    return {
        "campaign_name": read_required("Campaign name: "),
        "campaign_type": read_optional("Campaign type: ") or "offer",
        "audience": read_required("Audience: "),
        "goal": read_required("Goal: "),
        "offer": read_optional("Offer: "),
        "cta": read_required("CTA: "),
        "landing_page_url": read_url("Landing page URL: "),
        "launch_date": read_optional("Launch date (YYYY-MM-DD): "),
        "tone": read_optional("Tone: ") or "Clear and practical",
        "channels": campaigns.DEFAULT_CHANNELS,
    }


def choose_assets(job_type: str) -> list[str]:
    available_assets = [
        asset
        for asset in SELECTABLE_ASSETS
        if job_type == JOB_CAMPAIGN or asset != ASSET_PROJECT_PLAN
    ]
    print("Which assets do you need?")
    for index, asset in enumerate(available_assets, start=1):
        print(f"{index}. {ASSET_LABELS[asset]}")

    while True:
        raw_choices = input("Choose asset numbers separated by commas: ").strip()
        try:
            selected_indexes = [
                int(choice.strip()) for choice in raw_choices.split(",")
            ]
        except ValueError:
            print("Please enter numbers separated by commas.")
            continue
        if all(1 <= index <= len(available_assets) for index in selected_indexes):
            return [available_assets[index - 1] for index in selected_indexes]
        print("Please choose valid asset numbers.")


def load_brief(path: Path, job_type: str) -> dict[str, object]:
    if job_type == JOB_EVENT:
        return events.load_event_brief(path)
    return campaigns.load_campaign_brief(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create marketing assets in one self-contained run folder."
    )
    parser.add_argument("--scope", choices=[SCOPE_COMPLETE, SCOPE_SELECTED])
    parser.add_argument("--job-type", choices=[JOB_EVENT, JOB_CAMPAIGN])
    parser.add_argument("--brief", type=Path, help="Existing event or campaign brief.")
    parser.add_argument(
        "--assets",
        help=(
            "Comma-separated assets for selected scope: tracked_url, qr_code, "
            "email, social, landing_page, project_plan."
        ),
    )
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.scope:
        scope = args.scope
    else:
        scope_label = choose_option(
            "What are you creating?",
            ["Complete packet", "Selected assets"],
        )
        scope = SCOPE_COMPLETE if scope_label == "Complete packet" else SCOPE_SELECTED

    if args.job_type:
        job_type = args.job_type
    else:
        job_label = choose_option("What is this for?", ["Event", "Campaign / offer"])
        job_type = JOB_EVENT if job_label == "Event" else JOB_CAMPAIGN

    selected_assets: list[str] = []
    if scope == SCOPE_COMPLETE or args.assets:
        try:
            selected_assets = parse_assets(args.assets, job_type, scope)
        except ValueError as exc:
            parser.error(str(exc))
    elif args.scope == SCOPE_SELECTED:
        parser.error("--assets is required when --scope selected is used.")

    if args.brief:
        try:
            brief = load_brief(args.brief, job_type)
        except (campaigns.CampaignBriefError, events.EventBriefError) as exc:
            print(f"Error: {exc}")
            return 1
    else:
        brief = brief_from_inputs(job_type)
        try:
            if job_type == JOB_EVENT:
                events.validate_event_brief(brief)
            else:
                campaigns.validate_campaign_brief(brief)
        except (campaigns.CampaignBriefError, events.EventBriefError) as exc:
            print(f"Error: {exc}")
            return 1

    if scope == SCOPE_SELECTED and not args.assets:
        selected_assets = choose_assets(job_type)

    run_creation(
        brief=brief,
        job_type=job_type,
        scope=scope,
        selected_assets=selected_assets,
        runs_dir=args.runs_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
