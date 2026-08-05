"""Shared helpers for HAQS terminal marketing scripts."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse


DEFAULT_OUTPUT_DIR = "output"
OUTPUT_DIR = Path(os.getenv("HAQS_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))
ROI_LOG_PATH = OUTPUT_DIR / "automation_roi.csv"
DEFAULT_HOURLY_RATE = 50.0
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
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


class RoiResult(TypedDict):
    count: int
    minutes_per_item: int
    time_saved_minutes: int
    hourly_rate: float
    money_saved: float
    path: Path


class AiGenerationError(RuntimeError):
    """Raised when an AI generation request cannot be completed."""


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


def validate_url(url: str) -> str:
    value = url.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a full URL that starts with http:// or https://.")
    if any(char.isspace() for char in value):
        raise ValueError("Enter a URL without spaces.")
    return value


def read_url(prompt: str) -> str:
    while True:
        try:
            return validate_url(read_required(prompt))
        except ValueError as exc:
            print(exc)


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


def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL


def log_roi_event(
    script: str,
    asset_type: str,
    count: int,
    minutes_per_item: int,
    notes: str = "",
) -> RoiResult:
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

    return {
        "count": count,
        "minutes_per_item": minutes_per_item,
        "time_saved_minutes": time_saved_minutes,
        "hourly_rate": hourly_rate,
        "money_saved": money_saved,
        "path": ROI_LOG_PATH,
    }


def print_roi_logged(roi: RoiResult) -> None:
    print(
        f"ROI logged: {roi['count']} generated, "
        f"{roi['time_saved_minutes']} minutes saved, ${roi['money_saved']:.2f} saved."
    )


def combine_roi_results(results: list[RoiResult]) -> RoiResult:
    if not results:
        return {
            "count": 0,
            "minutes_per_item": 0,
            "time_saved_minutes": 0,
            "hourly_rate": get_hourly_rate(),
            "money_saved": 0.0,
            "path": ROI_LOG_PATH,
        }

    return {
        "count": sum(result["count"] for result in results),
        "minutes_per_item": 0,
        "time_saved_minutes": sum(result["time_saved_minutes"] for result in results),
        "hourly_rate": results[0]["hourly_rate"],
        "money_saved": round(sum(result["money_saved"] for result in results), 2),
        "path": results[0]["path"],
    }


def get_openai_client():
    if not os.getenv("OPENAI_API_KEY"):
        raise AiGenerationError(
            "OPENAI_API_KEY is not set. Set it in your terminal before running this script."
        )
    from openai import OpenAI

    return OpenAI()


def generate_text(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    text_format: dict | None = None,
) -> str:
    try:
        client = get_openai_client()
        request = {
            "model": model or get_openai_model(),
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if text_format:
            request["text"] = {"format": text_format}

        response = client.responses.create(
            **request,
        )
    except AiGenerationError:
        raise
    except Exception as exc:
        raise AiGenerationError(
            "AI generation failed. Check your model setting, network connection, "
            "API key, and OpenAI account status."
        ) from exc

    output_text = response.output_text.strip()
    if not output_text:
        raise AiGenerationError("AI generation returned an empty response.")
    return output_text
