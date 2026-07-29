"""Build import-ready marketing project plans as CSV files."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from utils.marketing import (
    OUTPUT_DIR,
    get_hourly_rate,
    log_roi_event,
    print_roi_logged,
    read_optional,
    read_required,
    timestamped_output_path,
    welcome,
)


@dataclass(frozen=True)
class TaskTemplate:
    name: str
    description: str
    section: str
    owner_role: str
    due_offset: int
    duration_days: int
    priority: str = "Medium"
    depends_on: str = ""
    tags: tuple[str, ...] = ()
    channels: tuple[str, ...] = ()


CAMPAIGN_TEMPLATES: dict[str, list[TaskTemplate]] = {
    "product_launch": [
        TaskTemplate("Finalize launch brief", "Confirm offer, audience, goals, core message, budget, and success metrics.", "Strategy", "Strategy", -30, 2, "High", tags=("brief",)),
        TaskTemplate("Approve launch timeline", "Review milestones, owners, dependencies, and launch-day responsibilities.", "Strategy", "Marketing Ops", -28, 1, "High", "Finalize launch brief"),
        TaskTemplate("Write landing page copy", "Draft hero, value props, proof points, FAQs, and primary CTA.", "Copy", "Copy", -24, 4, "High", "Finalize launch brief", tags=("landing-page",)),
        TaskTemplate("Review landing page copy", "Collect stakeholder feedback and resolve copy edits before design starts.", "Review", "Strategy", -20, 2, "High", "Write landing page copy", tags=("buffer", "review")),
        TaskTemplate("Design landing page", "Create desktop and mobile designs for the campaign landing page.", "Design", "Design", -17, 4, "High", "Review landing page copy", tags=("landing-page",)),
        TaskTemplate("Build landing page", "Build, connect forms, add tracking, and prepare QA checklist.", "Production", "Marketing Ops", -12, 4, "High", "Design landing page", tags=("landing-page",)),
        TaskTemplate("Draft launch email", "Write launch email copy with subject line options and CTA.", "Copy", "Copy", -14, 2, "High", "Finalize launch brief", channels=("email",), tags=("email",)),
        TaskTemplate("Build launch email", "Load the approved email into the email platform and confirm links.", "Production", "Marketing Ops", -9, 2, "High", "Draft launch email", channels=("email",), tags=("email",)),
        TaskTemplate("Create social launch posts", "Draft launch posts and supporting variations for selected social channels.", "Copy", "Copy", -12, 3, "Medium", "Finalize launch brief", channels=("linkedin", "facebook", "x", "instagram"), tags=("social",)),
        TaskTemplate("Design social assets", "Create channel-ready graphics and thumbnails for social launch posts.", "Design", "Design", -8, 3, "Medium", "Create social launch posts", channels=("linkedin", "facebook", "x", "instagram"), tags=("social",)),
        TaskTemplate("Create paid ad variants", "Draft ad copy variants and map each to target audience and offer angle.", "Paid Media", "Paid Media", -11, 3, "Medium", "Finalize launch brief", channels=("paid_social", "google_ads", "linkedin_ads"), tags=("ads",)),
        TaskTemplate("Build paid campaigns", "Set targeting, budgets, creative, URLs, and conversion tracking.", "Paid Media", "Paid Media", -6, 3, "High", "Create paid ad variants", channels=("paid_social", "google_ads", "linkedin_ads"), tags=("ads",)),
        TaskTemplate("QA launch assets", "Check landing page, forms, emails, URLs, UTMs, ads, and mobile rendering.", "QA", "Marketing Ops", -4, 2, "High", "Build landing page", tags=("qa", "buffer")),
        TaskTemplate("Final launch approval", "Confirm go/no-go with stakeholders after QA fixes are complete.", "Launch", "Strategy", -2, 1, "High", "QA launch assets", tags=("approval", "buffer")),
        TaskTemplate("Launch campaign", "Publish campaign assets and verify tracking after launch.", "Launch", "Marketing Ops", 0, 1, "High", "Final launch approval", tags=("launch",)),
        TaskTemplate("Post-launch performance check", "Review early data, conversion paths, and urgent optimization needs.", "Reporting", "Marketing Ops", 3, 1, "Medium", "Launch campaign", tags=("reporting",)),
        TaskTemplate("First optimization pass", "Adjust copy, budgets, creative, or audience settings based on early results.", "Optimization", "Marketing Ops", 7, 1, "Medium", "Post-launch performance check", tags=("optimization",)),
    ],
    "webinar": [
        TaskTemplate("Finalize webinar brief", "Confirm topic, audience, speakers, CTA, registration goal, and follow-up offer.", "Strategy", "Strategy", -28, 2, "High", tags=("brief",)),
        TaskTemplate("Confirm speaker details", "Collect speaker bios, headshots, talking points, and availability.", "Strategy", "Marketing Ops", -25, 2, "High", "Finalize webinar brief"),
        TaskTemplate("Write registration page copy", "Draft webinar title, abstract, speaker section, and registration CTA.", "Copy", "Copy", -23, 3, "High", "Finalize webinar brief", tags=("landing-page",)),
        TaskTemplate("Build registration page", "Create page, connect form, confirmation message, and tracking.", "Production", "Marketing Ops", -18, 3, "High", "Write registration page copy", tags=("landing-page",)),
        TaskTemplate("Create promotional email sequence", "Draft invite, reminder, last-chance, and post-event follow-up emails.", "Copy", "Copy", -17, 4, "High", "Finalize webinar brief", channels=("email",), tags=("email",)),
        TaskTemplate("Build promotional emails", "Load emails, test links, and schedule sends.", "Production", "Marketing Ops", -11, 3, "High", "Create promotional email sequence", channels=("email",), tags=("email",)),
        TaskTemplate("Create social promo posts", "Draft social posts for announcement, reminders, and final call.", "Copy", "Copy", -15, 3, "Medium", "Finalize webinar brief", channels=("linkedin", "facebook", "x", "instagram"), tags=("social",)),
        TaskTemplate("Design promo assets", "Create speaker graphic, event banner, and social assets.", "Design", "Design", -12, 3, "Medium", "Create social promo posts", tags=("design",)),
        TaskTemplate("Set up webinar platform", "Configure event, registration integration, reminders, recording, and attendee settings.", "Production", "Marketing Ops", -10, 2, "High", "Confirm speaker details"),
        TaskTemplate("Run technical rehearsal", "Confirm speaker audio, slides, screen share, recording, and event flow.", "QA", "Marketing Ops", -5, 1, "High", "Set up webinar platform", tags=("qa", "buffer")),
        TaskTemplate("Final promotion check", "Review registrations, scheduled sends, social posts, and paid support.", "Launch", "Marketing Ops", -3, 1, "High", "Run technical rehearsal", tags=("buffer",)),
        TaskTemplate("Host webinar", "Run the live event and capture recording assets.", "Launch", "Marketing Ops", 0, 1, "High", "Final promotion check", tags=("event",)),
        TaskTemplate("Send follow-up email", "Send recording, offer, and next-step CTA to attendees and no-shows.", "Follow-up", "Marketing Ops", 1, 1, "High", "Host webinar", channels=("email",), tags=("follow-up",)),
        TaskTemplate("Publish webinar recap", "Create a recap post or short summary asset from the webinar.", "Follow-up", "Copy", 4, 2, "Medium", "Host webinar", tags=("content",)),
        TaskTemplate("Report webinar performance", "Summarize registrations, attendance, engagement, conversions, and next actions.", "Reporting", "Marketing Ops", 7, 1, "Medium", "Send follow-up email", tags=("reporting",)),
    ],
    "email_campaign": [
        TaskTemplate("Finalize email campaign brief", "Confirm audience, offer, segment, CTA, timing, and success metrics.", "Strategy", "Strategy", -14, 1, "High", tags=("brief",)),
        TaskTemplate("Draft email copy", "Write email body, subject line options, preview text, and CTA.", "Copy", "Copy", -11, 3, "High", "Finalize email campaign brief", channels=("email",), tags=("email",)),
        TaskTemplate("Review email copy", "Collect edits, confirm offer details, and approve final copy.", "Review", "Strategy", -8, 2, "High", "Draft email copy", tags=("review", "buffer")),
        TaskTemplate("Build email", "Load email into the platform, add links, UTMs, personalization, and tracking.", "Production", "Marketing Ops", -5, 2, "High", "Review email copy", channels=("email",), tags=("email",)),
        TaskTemplate("QA email", "Send test emails, check rendering, proof links, and validate list rules.", "QA", "Marketing Ops", -3, 1, "High", "Build email", tags=("qa", "buffer")),
        TaskTemplate("Schedule email", "Schedule the approved send and confirm suppression/exclusion rules.", "Launch", "Marketing Ops", -1, 1, "High", "QA email", channels=("email",), tags=("launch",)),
        TaskTemplate("Send email", "Send or monitor the scheduled campaign.", "Launch", "Marketing Ops", 0, 1, "High", "Schedule email", channels=("email",), tags=("launch",)),
        TaskTemplate("Review email performance", "Check opens, clicks, conversions, unsubscribes, and recommended follow-up.", "Reporting", "Marketing Ops", 3, 1, "Medium", "Send email", tags=("reporting",)),
    ],
    "paid_ads_campaign": [
        TaskTemplate("Finalize paid campaign brief", "Confirm offer, objective, target audience, budget, channels, and conversion goal.", "Strategy", "Strategy", -21, 2, "High", tags=("brief",)),
        TaskTemplate("Confirm tracking plan", "Define UTMs, conversion events, pixels, and reporting views.", "Measurement", "Marketing Ops", -18, 2, "High", "Finalize paid campaign brief", tags=("tracking",)),
        TaskTemplate("Draft ad copy variants", "Create headline, body, description, and CTA variants by audience angle.", "Copy", "Copy", -16, 3, "High", "Finalize paid campaign brief", channels=("paid_social", "google_ads", "linkedin_ads"), tags=("ads",)),
        TaskTemplate("Design ad creative", "Create ad graphics or video cutdowns for selected placements.", "Design", "Design", -13, 4, "High", "Draft ad copy variants", channels=("paid_social", "linkedin_ads"), tags=("ads",)),
        TaskTemplate("Review ads", "Approve copy, creative, claims, landing page, and budget before buildout.", "Review", "Strategy", -8, 2, "High", "Design ad creative", tags=("review", "buffer")),
        TaskTemplate("Build campaign in ad platforms", "Set campaign structure, audience, placements, budgets, creative, and URLs.", "Production", "Paid Media", -5, 2, "High", "Review ads", channels=("paid_social", "google_ads", "linkedin_ads"), tags=("ads",)),
        TaskTemplate("QA campaign setup", "Check URLs, tracking, budget pacing, audience exclusions, and creative previews.", "QA", "Paid Media", -3, 1, "High", "Build campaign in ad platforms", tags=("qa", "buffer")),
        TaskTemplate("Launch paid campaign", "Publish ads and verify delivery, tracking, and spend.", "Launch", "Paid Media", 0, 1, "High", "QA campaign setup", tags=("launch",)),
        TaskTemplate("First performance review", "Review spend, CTR, CPC, conversions, and initial optimization needs.", "Reporting", "Paid Media", 3, 1, "Medium", "Launch paid campaign", tags=("reporting",)),
        TaskTemplate("Optimize campaign", "Adjust budget, bids, audiences, creative, and low-performing variants.", "Optimization", "Paid Media", 7, 1, "Medium", "First performance review", tags=("optimization",)),
    ],
    "content_campaign": [
        TaskTemplate("Finalize content campaign brief", "Confirm theme, audience, channels, primary CTA, and publishing cadence.", "Strategy", "Strategy", -21, 2, "High", tags=("brief",)),
        TaskTemplate("Create content outline", "Draft structure, key points, proof, and distribution hooks.", "Copy", "Copy", -18, 2, "High", "Finalize content campaign brief", tags=("content",)),
        TaskTemplate("Draft core content asset", "Write the main article, guide, newsletter, or campaign asset.", "Copy", "Copy", -15, 4, "High", "Create content outline", tags=("content",)),
        TaskTemplate("Review core content asset", "Collect edits and approve the asset before design or publishing.", "Review", "Strategy", -10, 2, "High", "Draft core content asset", tags=("review", "buffer")),
        TaskTemplate("Create supporting visuals", "Design graphics, thumbnails, charts, or downloadable assets as needed.", "Design", "Design", -7, 3, "Medium", "Review core content asset", tags=("design",)),
        TaskTemplate("Repurpose into channel posts", "Create social, newsletter, and short-form versions from the core asset.", "Copy", "Copy", -6, 3, "Medium", "Review core content asset", channels=("email", "linkedin", "facebook", "x", "instagram"), tags=("repurpose",)),
        TaskTemplate("Prepare publishing setup", "Load content, format page, check links, add UTMs, and prepare metadata.", "Production", "Marketing Ops", -3, 2, "High", "Create supporting visuals", tags=("production",)),
        TaskTemplate("QA publishing setup", "Review formatting, links, mobile view, metadata, and tracking.", "QA", "Marketing Ops", -1, 1, "High", "Prepare publishing setup", tags=("qa", "buffer")),
        TaskTemplate("Publish content campaign", "Publish the content and distribute through selected channels.", "Launch", "Marketing Ops", 0, 1, "High", "QA publishing setup", tags=("launch",)),
        TaskTemplate("Review content performance", "Check traffic, engagement, conversions, and recommended repromotion opportunities.", "Reporting", "Marketing Ops", 7, 1, "Medium", "Publish content campaign", tags=("reporting",)),
    ],
}

CHANNEL_ALIASES = {
    "paid": "paid_social",
    "paid social": "paid_social",
    "meta": "paid_social",
    "facebook ads": "paid_social",
    "google": "google_ads",
    "linkedin ads": "linkedin_ads",
    "twitter": "x",
}


def parse_date(raw_value: str) -> date:
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Use YYYY-MM-DD format, for example 2026-09-15.") from exc


def parse_channels(raw_value: str) -> set[str]:
    channels: set[str] = set()
    for item in raw_value.split(","):
        normalized = item.strip().lower().replace("-", "_")
        normalized = CHANNEL_ALIASES.get(normalized, normalized.replace(" ", "_"))
        if normalized:
            channels.add(normalized)
    return channels


def parse_team(raw_value: str) -> dict[str, str]:
    team: dict[str, str] = {}
    for item in raw_value.split(","):
        if "=" not in item:
            continue
        name, role = item.split("=", 1)
        if name.strip() and role.strip():
            team[role.strip().lower()] = name.strip()
    return team


def add_business_days(start_date: date, days: int) -> date:
    if days == 0:
        return start_date

    direction = 1 if days > 0 else -1
    remaining = abs(days)
    current = start_date

    while remaining:
        current += timedelta(days=direction)
        if current.weekday() < 5:
            remaining -= 1

    return current


def task_applies(task: TaskTemplate, selected_channels: set[str]) -> bool:
    return not task.channels or bool(selected_channels.intersection(task.channels))


def resolve_assignee(owner_role: str, team: dict[str, str]) -> str:
    return team.get(owner_role.lower(), "")


def build_rows(
    campaign_name: str,
    launch_date: date,
    campaign_type: str,
    selected_channels: set[str],
    team: dict[str, str],
    buffer_days: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    tasks = CAMPAIGN_TEMPLATES[campaign_type]
    included_names = {
        task.name for task in tasks if task_applies(task, selected_channels)
    }

    for task in tasks:
        if task.name not in included_names:
            continue

        due_date = add_business_days(launch_date, task.due_offset - buffer_days)
        if task.due_offset >= 0:
            due_date = add_business_days(launch_date, task.due_offset)

        start_offset = task.due_offset - task.duration_days + 1 - buffer_days
        if task.due_offset >= 0:
            start_offset = task.due_offset
        start_date = add_business_days(launch_date, start_offset)
        dependency = task.depends_on if task.depends_on in included_names else ""
        tags = sorted(set(task.tags + (campaign_type, campaign_name.lower().replace(" ", "_"))))

        rows.append(
            {
                "Task Name": task.name,
                "Description": task.description,
                "Owner Role": task.owner_role,
                "Assignee": resolve_assignee(task.owner_role, team),
                "Start Date": start_date.isoformat(),
                "Due Date": due_date.isoformat(),
                "Section": task.section,
                "Priority": task.priority,
                "Status": "Not Started",
                "Tags": ", ".join(tags),
                "Dependencies": dependency,
                "Campaign": campaign_name,
                "Campaign Type": campaign_type,
            }
        )

    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_readable_plan(path: Path, campaign_name: str, rows: list[dict[str, str]]) -> None:
    sections: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        sections.setdefault(row["Section"], []).append(row)

    lines = [f"# {campaign_name} Project Plan", ""]
    for section, section_rows in sections.items():
        lines.extend([f"## {section}", ""])
        for row in section_rows:
            assignee = f" - {row['Assignee']}" if row["Assignee"] else ""
            lines.append(f"- {row['Due Date']}: {row['Task Name']}{assignee}")
        lines.append("")

    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def asana_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "Name": row["Task Name"],
            "Notes": row["Description"],
            "Assignee": row["Assignee"],
            "Start Date": row["Start Date"],
            "Due Date": row["Due Date"],
            "Section/Column": row["Section"],
            "Tags": row["Tags"],
            "Dependencies": row["Dependencies"],
        }
        for row in rows
    ]


def choose_campaign_type() -> str:
    options = list(CAMPAIGN_TEMPLATES)
    print("Campaign type:")
    for index, option in enumerate(options, start=1):
        print(f"{index}. {option}")

    while True:
        choice = input("Choose a campaign type number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Please choose a valid option number.")


def read_buffer_days() -> int:
    raw_value = read_optional("Buffer business days before pre-launch due dates [2]: ")
    if not raw_value:
        return 2
    try:
        return max(0, int(raw_value))
    except ValueError:
        print("Invalid buffer. Using 2 business days.")
        return 2


def main() -> None:
    welcome("marketing project plan building")
    campaign_name = read_required("Campaign/project name: ")
    campaign_type = choose_campaign_type()

    while True:
        try:
            launch_date = parse_date(read_required("Launch date (YYYY-MM-DD): "))
            break
        except ValueError as exc:
            print(exc)

    channels = parse_channels(
        read_optional(
            "Channels, comma-separated (email, linkedin, paid_social, google_ads, etc.): "
        )
    )
    if not channels:
        channels = {"email", "linkedin"}

    team = parse_team(
        read_optional(
            "Team mapping, comma-separated like Alex=Strategy, Sam=Copy (optional): "
        )
    )
    buffer_days = read_buffer_days()

    rows = build_rows(
        campaign_name=campaign_name,
        launch_date=launch_date,
        campaign_type=campaign_type,
        selected_channels=channels,
        team=team,
        buffer_days=buffer_days,
    )

    generic_path = timestamped_output_path("project_plan", "csv")
    write_csv(generic_path, rows, list(rows[0].keys()))

    asana_path = timestamped_output_path("project_plan_asana", "csv")
    asana_export = asana_rows(rows)
    write_csv(asana_path, asana_export, list(asana_export[0].keys()))

    readable_path = timestamped_output_path("project_plan_review", "md")
    write_readable_plan(readable_path, campaign_name, rows)

    minutes_saved = 45
    money_saved = (minutes_saved / 60) * get_hourly_rate()
    log_roi_event(
        script="project_plan_builder",
        asset_type=f"project_plan_{campaign_type}",
        count=1,
        minutes_per_item=minutes_saved,
        notes=f"Generated {len(rows)} tasks for {campaign_name}",
    )

    print(f"\nGenerated {len(rows)} tasks.")
    print(f"Generic CSV: {generic_path}")
    print(f"Asana CSV: {asana_path}")
    print(f"Review plan: {readable_path}")
    print_roi_logged(1, minutes_saved, money_saved)
    print("\nTip: Adjust dates, assignees, or dependencies directly in the CSV before importing.")


if __name__ == "__main__":
    main()
