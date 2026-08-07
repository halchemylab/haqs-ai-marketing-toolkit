"""Interactive launcher for the HAQS AI Marketing Toolkit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from haqs_toolkit.generators import (
    campaign_url_builder,
    content_repurposer,
    email_generator,
    landing_page_copy_generator,
    project_plan_builder,
    qr_code_generator,
    roi_report,
    testimonial_formatter,
)


@dataclass(frozen=True)
class ToolOption:
    name: str
    description: str
    run: Callable[[], None]


TOOL_OPTIONS = [
    ToolOption(
        "Campaign URL Builder",
        "Build a tracked URL with UTM parameters.",
        campaign_url_builder.main,
    ),
    ToolOption(
        "Content Repurposer",
        "Turn source material into social posts, hooks, quotes, and blurbs.",
        content_repurposer.main,
    ),
    ToolOption(
        "Email Generator",
        "Generate three email draft options from source content.",
        email_generator.main,
    ),
    ToolOption(
        "Landing Page Copy Generator",
        "Create landing page copy from a guided mini-brief.",
        landing_page_copy_generator.main,
    ),
    ToolOption(
        "Project Plan Builder",
        "Build marketing project plan CSV files.",
        project_plan_builder.main,
    ),
    ToolOption(
        "QR Code Generator",
        "Generate a QR code PNG from a link.",
        qr_code_generator.main,
    ),
    ToolOption(
        "Testimonial Formatter",
        "Turn raw customer feedback into reusable social proof.",
        testimonial_formatter.main,
    ),
    ToolOption(
        "ROI Report",
        "View estimated time and money saved from generated assets.",
        roi_report.main,
    ),
]


def choose_tool() -> ToolOption | None:
    print("HAQS AI Marketing Toolkit")
    print()
    for index, option in enumerate(TOOL_OPTIONS, start=1):
        print(f"{index}. {option.name} - {option.description}")
    print("0. Exit")
    print()

    while True:
        try:
            choice = input("Choose a tool number: ").strip()
        except EOFError:
            return None
        if choice == "0":
            return None
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(TOOL_OPTIONS):
                return TOOL_OPTIONS[index - 1]
        print("Please choose a valid option number.")


def main() -> None:
    selected_tool = choose_tool()
    if selected_tool is None:
        print("Goodbye.")
        return

    print()
    selected_tool.run()


if __name__ == "__main__":
    main()
