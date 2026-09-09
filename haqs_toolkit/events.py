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
        if paragraph and stripped.lower().startswith(("about the author", "join ")):
            break
        if URL_PATTERN.fullmatch(stripped):
            continue
        if stripped:
            paragraph.append(stripped)
    return " ".join(paragraph)


def section_paragraph_after_heading(lines: list[str], heading: str) -> str:
    normalized_heading = heading.strip().lower()
    for index, line in enumerate(lines):
        if line.strip().lower().startswith(normalized_heading):
            return first_paragraph(lines[index + 1 :])
    return ""


def audience_from_lines(lines: list[str]) -> str:
    return section_paragraph_after_heading(lines, "ideal participants") or (
        "Current and aspiring leaders"
    )


def offer_from_lines(lines: list[str]) -> str:
    details = []
    stop_headings = {
        "practical tools and strategies",
        "ideal participants",
        "about the author",
    }
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if details:
                break
            continue
        lowered = stripped.lower()
        if lowered.startswith("event will begin in") or lowered == "displayed image":
            continue
        if any(lowered.startswith(heading) for heading in stop_headings):
            break
        details.append(stripped)
    return " ".join(details)


def tools_from_lines(lines: list[str]) -> list[str]:
    tools = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        lowered = stripped.lower()
        if lowered.startswith("practical tools and strategies"):
            in_section = True
            continue
        if in_section and lowered.startswith(
            ("ideal participants", "about the author")
        ):
            break
        if in_section and ":" in stripped:
            tools.append(stripped)
    return tools


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
        date_line = meaningful_lines[date_line_index]
        body_start = next(
            (
                index + 1
                for index, line in enumerate(lines)
                if line.strip() == date_line
            ),
            1,
        )
        body_lines = lines[body_start:]
    else:
        body_lines = lines[1:]
    body_lines = [
        line
        for line in body_lines
        if not line.lower().startswith("event will begin in")
    ]
    offer = offer_from_lines(body_lines)
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
        "takeaways": tools_from_lines(body_lines),
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


def normalized_event_brief(brief: dict[str, object]) -> dict[str, object]:
    source_material = str(brief.get("source_material") or "").strip()
    if not source_material:
        return brief

    try:
        parsed = parse_event_details(source_material)
    except EventBriefError:
        return brief

    normalized = brief.copy()
    for key in ["audience", "offer", "takeaways"]:
        value = parsed.get(key)
        if value:
            normalized[key] = value
    return normalized


def event_datetime_text(brief: dict[str, object]) -> str:
    brief = normalized_event_brief(brief)
    event_date = str(brief.get("event_date") or "").strip()
    try:
        date_text = datetime.strptime(event_date, "%Y-%m-%d").strftime("%B %-d, %Y")
    except ValueError:
        try:
            date_text = datetime.strptime(event_date, "%Y-%m-%d").strftime("%B %#d, %Y")
        except ValueError:
            date_text = event_date

    event_time = str(brief.get("event_time") or "").strip()
    timezone = str(brief.get("timezone") or "").strip()
    if event_time and timezone:
        return f"{date_text}, {event_time} {timezone}"
    if event_time:
        return f"{date_text}, {event_time}"
    return date_text


def takeaways_text(brief: dict[str, object]) -> str:
    brief = normalized_event_brief(brief)
    takeaways = brief.get("takeaways")
    if isinstance(takeaways, list) and takeaways:
        return "\n".join(f"- {takeaway}" for takeaway in takeaways)
    offer = str(brief.get("offer") or "").strip()
    if offer:
        return f"- {offer}"
    return "- Practical ideas from the source event brief"


def clean_sentence(value: object) -> str:
    return str(value or "").strip().rstrip(".")


def event_summary_markdown(brief: dict[str, object], brand_voice: str) -> str:
    brief = normalized_event_brief(brief)
    event_name = str(brief["event_name"])
    return f"""
# {event_name}

## Event Details

- Date and time: {event_datetime_text(brief)}
- Location: {brief.get("location") or "Online"}
- Audience: {brief["audience"]}
- CTA: {brief["cta"]}
- Registration URL: {brief["registration_url"]}

## Positioning

{brief.get("offer") or brief["goal"]}

## Practical Takeaways

{takeaways_text(brief)}

## Brand Voice

{brand_voice}
""".strip()


def event_email_sequence(brief: dict[str, object], registration_url: str) -> str:
    brief = normalized_event_brief(brief)
    event_name = str(brief["event_name"])
    audience = clean_sentence(brief["audience"])
    offer = clean_sentence(brief.get("offer") or brief["goal"])
    cta = str(brief["cta"])
    return f"""
# Email Sequence: {event_name}

## Email 1: Invitation

Subject: A practical conversation on leading innovation that lasts

Hi [first name],

Innovation pressure is real, but forcing creativity often creates burnout
instead of better ideas.

This session shares a research-based framework for helping leaders build
environments where co-creation can scale.

Audience: {audience}.

You will hear how leaders can use the Architect, Bridger, and Catalyst roles to
create stronger conditions for innovation.

Date and time: {event_datetime_text(brief)}

[{cta}]({registration_url})

## Email 2: Reminder

Subject: Reminder: Genius at Scale with Emily Tedards

Hi [first name],

This is a reminder to register for {event_name}.

The conversation will focus on practical ways to lead innovation through
collaboration, experimentation, and learning from others. It moves beyond theory
and uses examples from organizations including Mastercard, Pfizer, and Procter &
Gamble.

{offer}.

[{cta}]({registration_url})

## Email 3: Last Call

Subject: Last call to register for Emily Tedards' innovation session

Hi [first name],

If you are working on how to make innovation more repeatable, scalable, and
sustainable, this session is a useful next step.

Join Emily Tedards for a focused conversation on co-creation and the leadership
roles that help innovation last.

[{cta}]({registration_url})
""".strip()


def event_social_posts(brief: dict[str, object], registration_url: str) -> str:
    brief = normalized_event_brief(brief)
    event_name = str(brief["event_name"])
    return f"""
# Social Posts: {event_name}

## LinkedIn Post 1

Innovation pressure can create a strange contradiction.

The more an organization tries to force breakthroughs, the easier it becomes to
exhaust the very people it depends on for original thinking.

Innovation that lasts is not usually the result of pressure alone. It comes from
the conditions leaders create: the culture, connections, and momentum that make
co-creation possible.

Emily Tedards will explore this idea in Genius at Scale, including the three
leadership roles behind scalable innovation: the Architect, the Bridger, and the
Catalyst.

Read more: {registration_url}

hashtag#Innovation hashtag#Leadership hashtag#CoCreation
hashtag#OrganizationalDesign hashtag#HalchemyLabs

## LinkedIn Post 2

A lot of innovation work starts with the wrong question.

It asks, "How do we get more ideas?" when the deeper question is, "What kind of
environment allows good ideas to keep developing?"

That distinction matters. Ideas rarely scale because one person has a flash of
genius. They scale when leaders build the structures, partnerships, and energy
that let many people contribute to the work.

That is the focus of Emily Tedards' upcoming session, Genius at Scale: How to
Lead Innovation That Lasts.

Read more: {registration_url}

hashtag#Innovation hashtag#LeadershipDevelopment hashtag#Strategy
hashtag#Creativity hashtag#HalchemyLabs

## LinkedIn Post 3

The Architect builds the conditions.

The Bridger connects across boundaries.

The Catalyst helps the work spread.

Together, these roles offer a more practical way to think about innovation
leadership. Not as a demand for constant originality, but as the work of making
co-creation easier, stronger, and more repeatable.

Emily Tedards will unpack this framework in Genius at Scale, drawing on research
and stories from global organizations including Mastercard, Pfizer, and Procter
& Gamble.

Read more: {registration_url}

hashtag#Innovation hashtag#Leadership hashtag#Management
hashtag#BusinessStrategy hashtag#HalchemyLabs
""".strip()


def event_landing_page_copy(brief: dict[str, object], registration_url: str) -> str:
    brief = normalized_event_brief(brief)
    event_name = str(brief["event_name"])
    cta = str(brief["cta"])
    return f"""
# Landing Page Copy: {event_name}

## Hero

### Headline
Genius at Scale: How to Lead Innovation That Lasts

### Subheadline
Join Emily Tedards for a practical conversation on how leaders can create the
conditions for co-creation, experimentation, and scalable innovation.

### Event Details
{event_datetime_text(brief)}

[{cta}]({registration_url})

## Why Attend

Many organizations are under pressure to innovate, but traditional approaches
can lead to burnout, false promises, and stalled creativity. This session offers
a research-based alternative grounded in co-creation.

## What You Will Learn

{takeaways_text(brief)}

## Ideal For

{brief["audience"]}

## Final CTA

Reserve your spot for the live session.

[{cta}]({registration_url})
""".strip()


def write_event_assets(brief: dict[str, object], output_dir: Path) -> list[Path]:
    print(f"Preparing output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    registration_url = str(brief.get("registration_url", "[url here]"))
    brand_voice = load_brand_voice()

    assets = {
        "event-brief-summary.md": event_summary_markdown(brief, brand_voice),
        "email-sequence.md": event_email_sequence(brief, registration_url),
        "social-posts.md": event_social_posts(brief, registration_url),
        "landing-page-copy.md": event_landing_page_copy(brief, registration_url),
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
