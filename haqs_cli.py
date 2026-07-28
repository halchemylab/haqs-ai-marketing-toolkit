"""Shared helpers for HAQS terminal marketing scripts."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path


OUTPUT_DIR = Path("output")
ROI_LOG_PATH = OUTPUT_DIR / "automation_roi.csv"
DEFAULT_HOURLY_RATE = 50.0
ROI_FIELDNAMES = [
    "timestamp",
    "script",
    "asset_type",
    "count",
    "minutes_per_item",
    "time_saved_minutes",
    "hourly_rate",
    "money_saved",
    "notes",
]


def welcome(task: str) -> None:
    print(f"Welcome Lord Haqua. Please let me assist you with {task}.")
    print()


def read_multiline(prompt: str) -> str:
    print(prompt)
    print("Paste your content below. When finished, enter a blank line.")
    lines: list[str] = []

    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def read_required(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Please enter a value.")


def read_optional(prompt: str) -> str:
    return input(prompt).strip()


def choose_option(prompt: str, options: list[str]) -> str:
    print(prompt)
    for index, option in enumerate(options, start=1):
        print(f"{index}. {option}")

    while True:
        choice = input("Choose an option number: ").strip()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(options):
                return options[index - 1]
        print("Please choose a valid option number.")


def timestamped_output_path(prefix: str, extension: str = "txt") -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    clean_extension = extension.lstrip(".")
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return OUTPUT_DIR / f"{prefix}_{stamp}.{clean_extension}"


def save_text(prefix: str, content: str) -> Path:
    path = timestamped_output_path(prefix)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def get_hourly_rate() -> float:
    raw_rate = os.getenv("HOURLY_RATE", "").strip()
    if not raw_rate:
        return DEFAULT_HOURLY_RATE

    try:
        return float(raw_rate)
    except ValueError:
        return DEFAULT_HOURLY_RATE


def log_roi_event(
    script: str,
    asset_type: str,
    count: int,
    minutes_per_item: int,
    notes: str = "",
) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    hourly_rate = get_hourly_rate()
    time_saved_minutes = count * minutes_per_item
    money_saved = round((time_saved_minutes / 60) * hourly_rate, 2)
    write_header = not ROI_LOG_PATH.exists()

    with ROI_LOG_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=ROI_FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "script": script,
                "asset_type": asset_type,
                "count": count,
                "minutes_per_item": minutes_per_item,
                "time_saved_minutes": time_saved_minutes,
                "hourly_rate": hourly_rate,
                "money_saved": f"{money_saved:.2f}",
                "notes": notes,
            }
        )

    return ROI_LOG_PATH


def print_roi_logged(count: int, time_saved_minutes: int, money_saved: float) -> None:
    print(
        f"ROI logged: {count} generated, "
        f"{time_saved_minutes} minutes saved, ${money_saved:.2f} saved."
    )


def get_openai_client():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it in your terminal before running this script."
        )
    from openai import OpenAI

    return OpenAI()


def generate_text(system_prompt: str, user_prompt: str, model: str = "gpt-4.1-mini") -> str:
    client = get_openai_client()
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.output_text.strip()
