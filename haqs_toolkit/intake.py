"""Guided brief intake shared by event and campaign creation."""

from __future__ import annotations

import re

from haqs_toolkit import campaigns, events
from haqs_toolkit.utils.marketing import (
    choose_option,
    read_optional,
    read_required,
    read_url,
)


def fields_for(job_type: str) -> list[str]:
    if job_type == "event":
        return events.RECOMMENDED_FIELDS.copy()
    return campaigns.RECOMMENDED_FIELDS[:10]


def required_for(job_type: str) -> list[str]:
    return (
        events.REQUIRED_FIELDS.copy()
        if job_type == "event"
        else campaigns.REQUIRED_FIELDS.copy()
    )


def parse_details(text: str, job_type: str) -> dict[str, object]:
    """Extract explicit details locally; retain all source text for generation."""
    brief: dict[str, object] = {"source_material": text}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return brief
    name_key = "event_name" if job_type == "event" else "campaign_name"
    url_key = "registration_url" if job_type == "event" else "landing_page_url"
    if job_type == "event":
        parsed = events.parse_event_details(text)
        for key in ("event_date", "event_time", "timezone", "offer", "takeaways"):
            if parsed.get(key):
                brief[key] = parsed[key]
        audience = events.section_paragraph_after_heading(
            text.splitlines(), "ideal participants"
        )
        if audience:
            brief["audience"] = audience
    if ":" not in lines[0]:
        brief[name_key] = lines[0]
    urls = events.URL_PATTERN.findall(text)
    if len(urls) == 1:
        brief[url_key] = urls[0].rstrip(".,")
    aliases = {
        "name": name_key,
        "url": url_key,
        "date": ("event_date" if job_type == "event" else "launch_date"),
    }
    for line in lines:
        label, separator, value = line.partition(":")
        key = re.sub(r"[\s-]+", "_", label.lower())
        key = aliases.get(key, key)
        if separator and key in fields_for(job_type) and value.strip():
            brief[key] = (
                [part.strip() for part in value.split(",") if part.strip()]
                if key == "channels"
                else value.strip()
            )
    # Explicit extracted values must survive the legacy event normalizer.
    brief["edited_fields"] = [key for key in brief if key != "source_material"]
    return brief


def read_field(field: str, required: bool) -> object:
    label = field.replace("_", " ").title()
    hint = " (YYYY-MM-DD)" if field.endswith("_date") else ""
    if field == "channels":
        value = read_optional(f"{label} (comma-separated): ")
        return [part.strip() for part in value.split(",") if part.strip()]
    if field.endswith("_url"):
        return read_url(f"{label}: ")
    reader = read_required if required else read_optional
    return reader(f"{label}{hint}: ")


def collect_brief(job_type: str) -> dict[str, object]:
    method = choose_option(
        "What do you need? Start with existing details or a guided brief.",
        ["Paste event description / campaign brief", "Answer guided questions"],
    )
    pasted = method.startswith("Paste")
    brief: dict[str, object] = {}
    if pasted:
        print("Paste your details. Type END on its own line when finished.")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        brief = parse_details("\n".join(lines), job_type)
    required = required_for(job_type)
    for field in fields_for(job_type):
        if not brief.get(field) and (not pasted or field in required):
            brief[field] = read_field(field, field in required)
            brief.setdefault("edited_fields", []).append(field)
    brief.setdefault("tone", "Clear and practical")
    if not brief.get("channels"):
        brief["channels"] = campaigns.DEFAULT_CHANNELS.copy()
    return brief
