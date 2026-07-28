"""Shared helpers for HAQS terminal marketing scripts."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path


OUTPUT_DIR = Path("output")


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
