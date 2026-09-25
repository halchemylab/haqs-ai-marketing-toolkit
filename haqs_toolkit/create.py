"""User-facing marketing asset creation flow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from haqs_toolkit import campaigns, clients, events, intake
from haqs_toolkit.errors import command_errors, record_saved, report_error
from haqs_toolkit.generators import (
    email_generator,
    landing_page_copy_generator,
    qr_code_generator,
)
from haqs_toolkit.runs import (
    create_run_dir,
    open_output_folder,
    result_next_steps,
    write_packet_index,
    write_quality_check,
)
from haqs_toolkit.utils.marketing import (
    choose_option,
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


def write_json(path: Path, data: dict[str, object]) -> Path:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return record_saved(path)


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return record_saved(path)


def event_profile_copy(brief: dict[str, object], brand_voice: str, draft: str) -> str:
    if not brief.get("client_profile"):
        return draft
    return campaigns.ai_or_fallback(
        system_prompt="You are a precise event marketing copywriter.",
        user_prompt=(
            f"{brand_voice}\n\nEvent brief:\n{events.brief_text(brief)}\n\n"
            f"Draft structure and tracking links:\n{draft}\n\n"
            "Write copy for this event using the client voice. "
            "Keep the draft's asset structure and exact tracking links. "
            "Replace template-specific claims with facts from the brief. "
            "Do not invent facts or claims."
        ),
        fallback=draft,
    )


def write_event_run_assets(
    brief: dict[str, object],
    output_dir: Path,
    selected_assets: list[str],
) -> list[Path]:
    print("Preparing summary and tracking links...", flush=True)
    brand_voice = clients.voice_for(brief)
    tracking_urls = events.event_tracking_urls(brief)
    paths = [
        write_text(
            output_dir / "event-summary.txt",
            (
                events.event_summary_markdown(brief, brand_voice)
                if set(selected_assets)
                & {ASSET_EMAIL, ASSET_SOCIAL, ASSET_LANDING_PAGE}
                else f"# {brief['event_name']}\n\n{events.brief_text(brief)}"
            ),
        )
    ]

    if ASSET_TRACKED_URL in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_TRACKED_URL]}...", flush=True)
        paths.append(
            write_text(
                output_dir / "campaign-url.txt",
                events.event_tracking_urls_text(tracking_urls),
            )
        )
    if ASSET_QR_CODE in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_QR_CODE]}...", flush=True)
        qr_path = output_dir / "qr-code.png"
        qr_code_generator.create_qr_code(tracking_urls["qr_code"]).save(qr_path)
        paths.append(record_saved(qr_path))
    if ASSET_EMAIL in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_EMAIL]}...", flush=True)
        paths.append(
            write_text(
                output_dir / "email-sequence.txt",
                event_profile_copy(
                    brief,
                    brand_voice,
                    events.event_email_sequence(brief, tracking_urls["email"]),
                ),
            )
        )
    if ASSET_SOCIAL in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_SOCIAL]}...", flush=True)
        paths.append(
            write_text(
                output_dir / "social-posts.txt",
                event_profile_copy(
                    brief, brand_voice, events.event_social_posts(brief, tracking_urls)
                ),
            )
        )
    if ASSET_LANDING_PAGE in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_LANDING_PAGE]}...", flush=True)
        paths.append(
            write_text(
                output_dir / "landing-page-copy.txt",
                event_profile_copy(
                    brief,
                    brand_voice,
                    events.event_landing_page_copy(
                        brief, tracking_urls["landing_page"]
                    ),
                ),
            )
        )
    return paths


def write_campaign_run_assets(
    brief: dict[str, object],
    output_dir: Path,
    selected_assets: list[str],
) -> list[Path]:
    print("Preparing summary and tracking links...", flush=True)
    brand_voice = clients.voice_for(brief)
    source_material = campaigns.campaign_source_material(
        brief, str(brief.get("source_material", ""))
    )
    tracking_urls = (
        campaigns.campaign_tracking_urls(brief)
        if set(selected_assets) - {ASSET_PROJECT_PLAN}
        else {}
    )
    paths = [
        write_text(
            output_dir / "campaign-summary.txt",
            f"# {brief['campaign_name']}\n\n"
            f"## Source Brief\n\n{campaigns.brief_text(brief)}\n\n"
            f"## Brand Voice\n\n{brand_voice}",
        )
    ]

    if ASSET_TRACKED_URL in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_TRACKED_URL]}...", flush=True)
        paths.append(
            write_text(
                output_dir / "campaign-url.txt",
                campaigns.campaign_tracking_urls_text(tracking_urls),
            )
        )
    if ASSET_QR_CODE in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_QR_CODE]}...", flush=True)
        qr_path = output_dir / "qr-code.png"
        qr_code_generator.create_qr_code(tracking_urls["qr_code"]).save(qr_path)
        paths.append(record_saved(qr_path))
    if ASSET_EMAIL in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_EMAIL]}...", flush=True)
        email_copy = campaigns.ai_or_fallback(
            system_prompt="You are a precise marketing email copywriter.",
            user_prompt=email_generator.build_prompt(
                source_content=source_material,
                purpose=str(brief["goal"]),
                brand_voice=brand_voice,
            ),
            fallback=campaigns.fallback_email_copy(brief, tracking_urls["email"]),
        ).replace("[url here]", tracking_urls["email"])
        paths.append(write_text(output_dir / "email-drafts.txt", email_copy))
    if ASSET_SOCIAL in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_SOCIAL]}...", flush=True)
        social_copy = campaigns.ai_or_fallback(
            system_prompt=(
                "You are a precise marketing strategist and content "
                "repurposing assistant."
            ),
            user_prompt=campaigns.social_prompt(
                source_material,
                brand_voice,
                tracking_urls,
            ),
            fallback=campaigns.fallback_social_copy(brief, tracking_urls["linkedin"]),
        )
        paths.append(write_text(output_dir / "social-posts.txt", social_copy))
    if ASSET_LANDING_PAGE in selected_assets:
        print(f"Generating {ASSET_LABELS[ASSET_LANDING_PAGE]}...", flush=True)
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
                must_include=(
                    "Use this landing page tracking URL: "
                    f"{tracking_urls['landing_page']}"
                ),
                avoid="",
                brand_voice=brand_voice,
            ),
            fallback=campaigns.fallback_landing_copy(
                brief,
                tracking_urls["landing_page"],
            ),
        ).replace("[url here]", tracking_urls["landing_page"])
        paths.append(write_text(output_dir / "landing-page-copy.txt", landing_copy))
    if ASSET_PROJECT_PLAN in selected_assets:
        print("Generating Project plan...", flush=True)
        project_plan_path = campaigns.write_project_plan(brief, output_dir)
        if project_plan_path:
            paths.append(project_plan_path)
        else:
            print("Skipped project plan: add a launch date to generate it.", flush=True)
    return paths


def run_creation(
    brief: dict[str, object],
    job_type: str,
    scope: str,
    selected_assets: list[str],
    *,
    runs_dir: Path = Path("runs"),
) -> Path:
    clients.voice_for(brief)  # Validate saved profile before creating files.
    print("Starting generation...", flush=True)
    job_name_key = "event_name" if job_type == JOB_EVENT else "campaign_name"
    run_dir = create_run_dir(
        str(brief[job_name_key]),
        job_type,
        scope,
        runs_dir=runs_dir,
    )
    output_dir = run_dir / "outputs"
    write_json(run_dir / "brief.json", brief)
    if brief.get("client_profile"):
        write_text(run_dir / "client-profile.txt", str(brief["client_profile"]["text"]))

    if job_type == JOB_EVENT:
        output_paths = write_event_run_assets(brief, output_dir, selected_assets)
    else:
        output_paths = write_campaign_run_assets(brief, output_dir, selected_assets)

    print("Checking generated files...", flush=True)
    quality_path, issues = write_quality_check(run_dir)
    index_path = write_packet_index(run_dir, output_paths, len(issues))

    print(f"Created marketing run: {run_dir}")
    print(f"Generated {len(output_paths)} output file(s):")
    for path in output_paths:
        print(f"- {path}")
    print(f"Quality check: {quality_path}")
    print(f"Packet index: {index_path}")
    print(f"Quality issues found: {len(issues)}")
    print("Next steps:")
    for number, step in enumerate(result_next_steps(output_paths, len(issues)), 1):
        print(f"{number}. {step}")
    return run_dir


def brief_from_inputs(
    job_type: str,
    assets: list[str] | None = None,
    *,
    defaults: dict[str, object] | None = None,
) -> dict[str, object]:
    return intake.collect_brief(job_type, assets, defaults=defaults)


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


def load_brief(
    path: Path,
    job_type: str,
    assets: list[str] | None = None,
    *,
    defaults: dict[str, object] | None = None,
) -> dict[str, object]:
    if job_type == JOB_EVENT:
        return events.load_event_brief(
            path,
            required_fields=intake.required_for(job_type, assets),
            defaults=defaults,
        )
    return campaigns.load_campaign_brief(
        path, required_fields=intake.required_for(job_type, assets), defaults=defaults
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create marketing assets in one self-contained run folder."
    )
    parser.add_argument(
        "--brands",
        help="Brand filename or stem from brands/, or general for brand_voice.txt.",
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
    parser.add_argument(
        "--review",
        action="store_true",
        help="Review and edit a saved brief before generation.",
    )
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    return parser


@command_errors
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

    if scope == SCOPE_SELECTED and not args.assets:
        selected_assets = choose_assets(job_type)

    profile = None
    if args.brands and args.brands != "general":
        profile = clients.load_profile(args.brands)
    elif not args.brands and not args.brief:
        profile = clients.choose_profile()
    defaults = clients.profile_defaults(profile)

    intake_assets = selected_assets if scope == SCOPE_SELECTED else None
    if args.brief:
        try:
            brief = load_brief(args.brief, job_type, intake_assets, defaults=defaults)
        except (campaigns.CampaignBriefError, events.EventBriefError) as exc:
            report_error(exc)
            return 1
    else:
        brief = brief_from_inputs(job_type, intake_assets, defaults=defaults)
    if args.brands == "general":
        brief.pop("client_profile", None)
    elif profile:
        brief["client_profile"] = profile
    clients.voice_for(brief)
    if brief.get("client_profile"):
        print(f"Client profile: {brief['client_profile'].get('name', 'saved profile')}")
    if not args.brief or args.review:
        if not intake.review_brief(brief, job_type, intake_assets):
            print("Generation cancelled. No run was created.")
            return 0

    run_dir = run_creation(
        brief=brief,
        job_type=job_type,
        scope=scope,
        selected_assets=selected_assets,
        runs_dir=args.runs_dir,
    )
    open_output_folder(run_dir / "outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
