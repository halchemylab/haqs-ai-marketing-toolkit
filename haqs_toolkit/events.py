"""Non-interactive event marketing packet generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


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


def load_event_brief(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    output_dir.mkdir(parents=True, exist_ok=True)
    event_name = str(brief.get("event_name", "Event"))
    cta = str(brief.get("cta", "Register Now"))
    registration_url = str(brief.get("registration_url", "[url here]"))
    source = brief_text(brief)

    assets = {
        "event-brief-summary.md": (
            f"# {event_name}\n\n"
            "## Source Brief\n\n"
            f"{source}\n"
        ),
        "email-sequence.md": (
            f"# Email Sequence: {event_name}\n\n"
            "## Email 1\n\n"
            f"Subject: You're invited to {event_name}\n\n"
            f"Join us for {event_name}. {cta}: {registration_url}\n\n"
            "## Email 2\n\n"
            f"Subject: Reminder: {event_name}\n\n"
            f"Save your spot for {event_name}. {cta}: {registration_url}\n"
        ),
        "social-posts.md": (
            f"# Social Posts: {event_name}\n\n"
            f"1. Join us for {event_name}. {cta}: {registration_url}\n"
            f"2. Planning to attend {event_name}? Details and registration: {registration_url}\n"
            f"3. Last call for {event_name}. {cta}: {registration_url}\n"
        ),
        "landing-page-copy.md": (
            f"# Landing Page Copy: {event_name}\n\n"
            f"## Hero\n\n{event_name}\n\n"
            f"## Primary CTA\n\n[{cta}]({registration_url})\n"
        ),
    }

    paths = []
    for filename, content in assets.items():
        path = output_dir / filename
        path.write_text(content.strip() + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate predictable marketing files from an event packet.",
        epilog=(
            "Example: python scripts/run_event_pipeline.py "
            "events/demo-event --out events/demo-event/outputs"
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
        help="Path to an event packet directory containing brief.json.",
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
        parser.error("event_dir is required unless --list-fields is used.")

    event_dir = args.event_dir
    brief_path = event_dir / "brief.json"
    output_dir = args.out or event_dir / "outputs"

    brief = load_event_brief(brief_path)
    paths = write_event_assets(brief, output_dir)

    print(f"Generated {len(paths)} event files:")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
