"""Non-interactive event marketing packet generation."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from haqs_toolkit.runs import write_quality_check
from haqs_toolkit.utils.marketing import load_brand_voice, read_url

RECOMMENDED_FIELDS = [
    "event_name",
    "event_date",
    "event_time",
    "timezone",
    "location",
    "audience",
    "goal",
    "offer",
    "cta",
    "registration_url",
    "tone",
    "channels",
]
REQUIRED_FIELDS = [
    "event_name",
    "event_date",
    "audience",
    "goal",
    "cta",
    "registration_url",
]
MONTHS = {
    month.lower(): index
    for index, month in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}
DATE_LINE_PATTERN = re.compile(
    r"(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+)?"
    r"(?P<month>January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+"
    r"(?P<day>\d{1,2})(?:st|nd|rd|th)?,\s+"
    r"(?P<year>\d{4})"
    r"(?:\s+from\s+(?P<time>.+?)(?:\s+(?P<timezone>[A-Z]{2,5}))?)?$",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://[^\s)>\]]+")


class EventBriefError(ValueError):
    """Raised when an event brief cannot be loaded or validated."""


def ensure_event_packet_dirs(event_dir: Path) -> None:
    (event_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (event_dir / "outputs").mkdir(parents=True, exist_ok=True)


def load_event_brief(path: Path) -> dict[str, object]:
    if not path.exists():
        raise EventBriefError(f"Missing required file: {path}")

    try:
        brief = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EventBriefError(f"Invalid JSON in {path}: {exc.msg}") from exc

    if not isinstance(brief, dict):
        raise EventBriefError("brief.json must contain a JSON object.")

    validate_event_brief(brief)
    return brief


def validate_event_brief(brief: dict[str, object]) -> None:
    errors = []
    for field in REQUIRED_FIELDS:
        value = brief.get(field)
        if value is None or str(value).strip() == "":
            errors.append(f"Missing required field: {field}")

    event_date = str(brief.get("event_date", "")).strip()
    if event_date:
        try:
            datetime.strptime(event_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid event_date: use YYYY-MM-DD.")

    registration_url = str(brief.get("registration_url", "")).strip()
    if registration_url:
        parsed = urlparse(registration_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(
                "Invalid registration_url: use a full http:// or https:// URL."
            )

    channels = brief.get("channels")
    if channels is not None and (
        not isinstance(channels, list)
        or not all(str(channel).strip() for channel in channels)
    ):
        errors.append("Invalid channels: use a non-empty JSON array of channel names.")

    if errors:
        raise EventBriefError("\n".join(errors))


def read_pasted_event_details() -> str:
    print("Paste the event page text below.")
    print("When finished, type END on its own line and press Enter.")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def parse_event_date_line(line: str) -> tuple[str, str, str] | None:
    match = DATE_LINE_PATTERN.search(line.strip())
    if not match:
        return None

    month = MONTHS[match.group("month").lower()]
    day = int(match.group("day"))
    year = int(match.group("year"))
    event_date = datetime(year, month, day).strftime("%Y-%m-%d")
    event_time = (match.group("time") or "").strip()
    timezone = (match.group("timezone") or "").strip()
    if timezone and event_time.endswith(timezone):
        event_time = event_time[: -len(timezone)].strip()
    return event_date, event_time, timezone


def first_paragraph(lines: list[str]) -> str:
    paragraph = []
    for line in lines:
        stripped = line.strip()
        if paragraph and not stripped:
            break
        if stripped:
            paragraph.append(stripped)
    return " ".join(paragraph)


def audience_from_lines(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if line.strip().lower().startswith("ideal participants"):
            audience = first_paragraph(lines[index + 1 :])
            if audience:
                return audience
    return "Event attendees"


def parse_event_details(text: str) -> dict[str, object]:
    lines = [line.strip() for line in text.splitlines()]
    meaningful_lines = [
        line
        for line in lines
        if line and line.lower() not in {"displayed image"}
    ]
    if not meaningful_lines:
        raise EventBriefError("Paste event page text before typing END.")

    event_name = meaningful_lines[0]
    event_date = ""
    event_time = ""
    timezone = ""
    date_line_index = -1
    for index, line in enumerate(meaningful_lines[1:], start=1):
        parsed_date = parse_event_date_line(line)
        if parsed_date:
            event_date, event_time, timezone = parsed_date
            date_line_index = index
            break

    if date_line_index >= 0:
        body_lines = meaningful_lines[date_line_index + 1 :]
    else:
        body_lines = meaningful_lines[1:]
    body_lines = [
        line
        for line in body_lines
        if not line.lower().startswith("event will begin in")
    ]
    offer = first_paragraph(body_lines)
    urls = URL_PATTERN.findall(text)
    registration_url = urls[0].rstrip(".,") if urls else ""

    return {
        "event_name": event_name,
        "event_date": event_date,
        "event_time": event_time,
        "timezone": timezone,
        "location": "Online",
        "audience": audience_from_lines(body_lines),
        "goal": f"Drive registrations for {event_name}",
        "offer": offer,
        "cta": "Register Now",
        "registration_url": registration_url,
        "tone": "Clear and practical",
        "channels": ["email", "social"],
        "source_material": text,
    }


def brief_from_pasted_details() -> dict[str, object]:
    brief = parse_event_details(read_pasted_event_details())
    if not brief["registration_url"]:
        brief["registration_url"] = read_url("Registration URL: ")
    validate_event_brief(brief)
    return brief


def choose_event_run_options() -> tuple[str, list[str]]:
    from haqs_toolkit import create

    scope_label = create.choose_option(
        "What do you want to generate?",
        ["Complete event packet", "Selected assets"],
    )
    if scope_label == "Complete event packet":
        return create.SCOPE_COMPLETE, create.EVENT_COMPLETE_ASSETS.copy()

    return create.SCOPE_SELECTED, create.choose_assets(create.JOB_EVENT)


def brief_text(brief: dict[str, object]) -> str:
    lines = []
    for key, value in brief.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            rendered_value = ", ".join(str(item) for item in value)
        else:
            rendered_value = str(value)
        lines.append(f"- {label}: {rendered_value}")
    return "\n".join(lines)


def write_event_assets(brief: dict[str, object], output_dir: Path) -> list[Path]:
    print(f"Preparing output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    event_name = str(brief.get("event_name", "Event"))
    cta = str(brief.get("cta", "Register Now"))
    registration_url = str(brief.get("registration_url", "[url here]"))
    local_tone = str(brief.get("tone", "Use the brand voice."))
    brand_voice = load_brand_voice()
    source = brief_text(brief)

    assets = {
        "event-brief-summary.md": (
            f"# {event_name}\n\n"
            "## Source Brief\n\n"
            f"{source}\n\n"
            "## Brand Voice\n\n"
            f"{brand_voice}\n\n"
            "## Local Event Tone\n\n"
            f"{local_tone}\n"
        ),
        "email-sequence.md": (
            f"# Email Sequence: {event_name}\n\n"
            f"Local tone: {local_tone}\n\n"
            "## Email 1\n\n"
            f"Subject: You're invited to {event_name}\n\n"
            f"Join us for {event_name}. {cta}: {registration_url}\n\n"
            "## Email 2\n\n"
            f"Subject: Reminder: {event_name}\n\n"
            f"Save your spot for {event_name}. {cta}: {registration_url}\n"
        ),
        "social-posts.md": (
            f"# Social Posts: {event_name}\n\n"
            f"Local tone: {local_tone}\n\n"
            f"1. Join us for {event_name}. {cta}: {registration_url}\n"
            f"2. Planning to attend {event_name}? Details and registration: "
            f"{registration_url}\n"
            f"3. Last call for {event_name}. {cta}: {registration_url}\n"
        ),
        "landing-page-copy.md": (
            f"# Landing Page Copy: {event_name}\n\n"
            f"Local tone: {local_tone}\n\n"
            f"## Hero\n\n{event_name}\n\n"
            f"## Primary CTA\n\n[{cta}]({registration_url})\n"
        ),
    }

    paths = []
    for filename, content in assets.items():
        path = output_dir / filename
        print(f"Writing {filename}...")
        path.write_text(content.strip() + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate predictable marketing files from an event packet.",
        epilog=(
            "Examples: python marketing_event_ai_builder.py or "
            "python marketing_event_ai_builder.py events/<event-slug> "
            "--out events/<event-slug>/outputs"
        ),
    )
    parser.add_argument(
        "--list-fields",
        action="store_true",
        help="Print recommended brief.json fields and exit.",
    )
    parser.add_argument(
        "event_dir",
        type=Path,
        nargs="?",
        help=(
            "Path to an event packet directory containing brief.json. "
            "Omit it to answer prompts and create a run folder automatically."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output directory. Defaults to <event_dir>/outputs.",
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

    if args.event_dir is None:
        if args.out is not None:
            parser.error("--out requires an event_dir.")

        from haqs_toolkit import create

        brief = brief_from_pasted_details()
        try:
            validate_event_brief(brief)
        except EventBriefError as exc:
            print(f"Error: {exc}")
            return 1

        scope, selected_assets = choose_event_run_options()
        create.run_creation(
            brief=brief,
            job_type=create.JOB_EVENT,
            scope=scope,
            selected_assets=selected_assets,
        )
        return 0

    event_dir = args.event_dir
    brief_path = event_dir / "brief.json"
    print(f"Using event packet: {event_dir}")
    ensure_event_packet_dirs(event_dir)
    output_dir = args.out or event_dir / "outputs"

    try:
        print(f"Reading brief: {brief_path}")
        brief = load_event_brief(brief_path)
    except EventBriefError as exc:
        print(f"Error: {exc}")
        return 1
    print("Brief validation passed.")
    paths = write_event_assets(brief, output_dir)
    if args.out is None:
        quality_path, issues = write_quality_check(event_dir)
        paths.append(quality_path)

    print(f"Generated {len(paths)} event files:")
    for path in paths:
        print(f"- {path}")
    if args.out is None:
        print(f"Quality issues found: {len(issues)}")
    print(
        "\nNext step: Review the event brief summary first, then edit the "
        "generated email, social, and landing page files before publishing."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
