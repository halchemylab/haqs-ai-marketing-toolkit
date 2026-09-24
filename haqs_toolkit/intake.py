"""Guided brief intake shared by event and campaign creation."""

from __future__ import annotations

import re
from datetime import datetime

from haqs_toolkit import campaigns, events
from haqs_toolkit.utils.marketing import (
    choose_option,
    read_optional,
    read_required,
    read_url,
    validate_url,
)


def fields_for(job_type: str, assets: list[str] | None = None) -> list[str]:
    fields = (
        events.RECOMMENDED_FIELDS.copy()
        if job_type == "event"
        else campaigns.RECOMMENDED_FIELDS[:10]
    )
    if assets is None or set(assets) & {"email", "social", "landing_page"}:
        return fields
    needed = {"event_name" if job_type == "event" else "campaign_name"}
    if set(assets) & {"tracked_url", "qr_code"}:
        needed.add("registration_url" if job_type == "event" else "landing_page_url")
    if "project_plan" in assets:
        needed.update({"campaign_type", "launch_date", "channels"})
    return [field for field in fields if field in needed]


def required_for(job_type: str, assets: list[str] | None = None) -> list[str]:
    required = (
        events.REQUIRED_FIELDS.copy()
        if job_type == "event"
        else campaigns.REQUIRED_FIELDS.copy()
    )
    fields = fields_for(job_type, assets)
    required = [field for field in required if field in fields]
    if assets is not None and "project_plan" in assets:
        required.append("launch_date")
    return required


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
    while True:
        value = reader(f"{label}{hint}: ")
        try:
            validate_field(field, value)
        except ValueError as exc:
            print(exc)
            continue
        return value


def validate_field(field: str, value: object) -> None:
    if not value:
        return
    if field.endswith("_date"):
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
                raise ValueError
            datetime.strptime(str(value), "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Enter a valid date in YYYY-MM-DD format.") from exc
    if field.endswith("_url"):
        validate_url(str(value))


def collect_brief(
    job_type: str,
    assets: list[str] | None = None,
    *,
    defaults: dict[str, object] | None = None,
) -> dict[str, object]:
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
    from haqs_toolkit.clients import apply_defaults

    brief = apply_defaults(brief, defaults or {})
    required = required_for(job_type, assets)
    for field in fields_for(job_type, assets):
        if brief.get(field):
            try:
                validate_field(field, brief[field])
            except ValueError as exc:
                print(f"{field.replace('_', ' ').title()}: {exc}")
                brief[field] = read_field(field, field in required)
                brief.setdefault("edited_fields", []).append(field)
        if not brief.get(field) and (not pasted or field in required):
            brief[field] = read_field(field, field in required)
            brief.setdefault("edited_fields", []).append(field)
    brief.setdefault("tone", "Clear and practical")
    if not brief.get("channels"):
        brief["channels"] = campaigns.DEFAULT_CHANNELS.copy()
    return brief


def review_brief(
    brief: dict[str, object], job_type: str, assets: list[str] | None = None
) -> bool:
    fields = fields_for(job_type, assets)
    # Show supplied optional fields too, including tracking overrides.
    extras = events.RECOMMENDED_FIELDS + campaigns.RECOMMENDED_FIELDS + ["takeaways"]
    fields += [
        field
        for field in dict.fromkeys(extras)
        if field in brief and field not in fields
    ]
    required = required_for(job_type, assets)
    while True:
        print("\nBrief preview")
        for number, field in enumerate(fields, 1):
            value = brief.get(field, "")
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            print(
                f"{number}. {field.replace('_', ' ').title()}: {value or '[not set]'}"
            )
        valid = True
        try:
            validator = (
                events.validate_event_brief
                if job_type == "event"
                else campaigns.validate_campaign_brief
            )
            validator(brief, required_fields=required)
            for field in fields:
                validate_field(field, brief.get(field))
        except ValueError as exc:
            print(f"Please fix: {exc}")
            valid = False
        choice = input(
            "Field number to edit, Enter to generate, or Q to cancel: "
        ).strip()
        if choice.lower() == "q":
            return False
        if not choice and valid:
            return True
        if not choice:
            continue
        if not choice.isdigit() or not 1 <= int(choice) <= len(fields):
            print("Please choose a listed field number.")
            continue
        field = fields[int(choice) - 1]
        if field == "takeaways":
            value = read_optional("Takeaways (separate items with |): ")
            brief[field] = [item.strip() for item in value.split("|") if item.strip()]
        else:
            brief[field] = read_field(field, field in required)
        edited = list(brief.get("edited_fields", []))
        if field not in edited:
            edited.append(field)
        brief["edited_fields"] = edited
