"""Build import-ready marketing project plans as CSV files."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from importlib import resources
from pathlib import Path

from haqs_toolkit.utils.marketing import (
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


TEMPLATE_RESOURCE = "project_plan_templates.json"


def task_template_from_data(data: dict[str, object]) -> TaskTemplate:
    return TaskTemplate(
        name=str(data["name"]),
        description=str(data["description"]),
        section=str(data["section"]),
        owner_role=str(data["owner_role"]),
        due_offset=int(data["due_offset"]),
        duration_days=int(data["duration_days"]),
        priority=str(data.get("priority", "Medium")),
        depends_on=str(data.get("depends_on", "")),
        tags=tuple(str(tag) for tag in data.get("tags", [])),
        channels=tuple(str(channel) for channel in data.get("channels", [])),
    )


def load_campaign_templates() -> dict[str, list[TaskTemplate]]:
    raw_templates = json.loads(
        resources.files("haqs_toolkit.data")
        .joinpath(TEMPLATE_RESOURCE)
        .read_text(encoding="utf-8")
    )
    return {
        campaign_type: [task_template_from_data(task) for task in tasks]
        for campaign_type, tasks in raw_templates.items()
    }


CAMPAIGN_TEMPLATES = load_campaign_templates()

CHANNEL_ALIASES = {
    "paid": "paid_social",
    "paid social": "paid_social",
    "meta": "paid_social",
    "facebook ads": "paid_social",
    "google": "google_ads",
    "linkedin ads": "linkedin_ads",
    "twitter": "x",
}

PROJECT_PLAN_FIELDNAMES = [
    "Task Name",
    "Description",
    "Owner Role",
    "Assignee",
    "Start Date",
    "Due Date",
    "Section",
    "Priority",
    "Status",
    "Tags",
    "Dependencies",
    "Campaign",
    "Campaign Type",
]

ASANA_FIELDNAMES = [
    "Name",
    "Notes",
    "Assignee",
    "Start Date",
    "Due Date",
    "Section/Column",
    "Tags",
    "Dependencies",
]


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
        tags = sorted(
            set(task.tags + (campaign_type, campaign_name.lower().replace(" ", "_")))
        )

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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_readable_plan(
    path: Path, campaign_name: str, rows: list[dict[str, str]]
) -> None:
    sections: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        sections.setdefault(row["Section"], []).append(row)

    lines = [f"# {campaign_name} Project Plan", ""]
    if not rows:
        lines.append("No tasks generated.")

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
            "Channels, comma-separated "
            "(email, linkedin, paid_social, google_ads, etc.): "
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
    write_csv(generic_path, rows, PROJECT_PLAN_FIELDNAMES)

    asana_path = timestamped_output_path("project_plan_asana", "csv")
    asana_export = asana_rows(rows)
    write_csv(asana_path, asana_export, ASANA_FIELDNAMES)

    readable_path = timestamped_output_path("project_plan_review", "md")
    write_readable_plan(readable_path, campaign_name, rows)

    minutes_saved = 45
    roi = log_roi_event(
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
    print_roi_logged(roi)
    print(
        "\nNext step: Open the review Markdown first, then edit dates, "
        "assignees, or dependencies in the CSV before importing."
    )


if __name__ == "__main__":
    main()
