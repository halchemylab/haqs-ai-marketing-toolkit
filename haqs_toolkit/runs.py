"""Run folder and automatic quality-check helpers."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from haqs_toolkit import packet_quality
from haqs_toolkit.errors import record_saved

RUNS_DIR = Path("runs")


def open_output_folder(output_dir: Path) -> None:
    """Open the generated folder in the system file manager."""
    output_dir = output_dir.resolve()
    try:
        if sys.platform == "win32":
            os.startfile(str(output_dir))
        else:
            command = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.run([command, str(output_dir)], check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Could not open output folder: {exc}")
        print(f"Your generated files are at: {output_dir}")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "marketing-run"


def create_run_dir(
    job_name: str,
    job_type: str,
    scope: str,
    *,
    runs_dir: Path = RUNS_DIR,
    now: datetime | None = None,
) -> Path:
    timestamp = (now or datetime.now()).strftime("%Y-%m-%d-%H%M")
    base_name = f"{slugify(job_name)}-{slugify(job_type)}-{slugify(scope)}-{timestamp}"
    run_dir = runs_dir / base_name
    suffix = 2
    while run_dir.exists():
        run_dir = runs_dir / f"{base_name}-{suffix}"
        suffix += 1

    (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
    return run_dir


def write_quality_check(
    run_dir: Path,
) -> tuple[Path, list[packet_quality.QualityIssue]]:
    issues = packet_quality.scan_path(run_dir)
    report = packet_quality.format_report(issues, run_dir)
    path = run_dir / "quality-check.md"
    path.write_text(f"# Quality Check\n\n{report}\n", encoding="utf-8")
    return record_saved(path), issues


def result_next_steps(output_paths: list[Path], quality_issue_count: int) -> list[str]:
    """Give actions only for files that were actually generated."""
    steps = []
    if quality_issue_count:
        steps.append(
            f"Fix the {quality_issue_count} issue(s) listed in quality-check.md first."
        )
    steps.append("Confirm dates, links, prices, claims, and names before publishing.")
    actions = {
        "campaign-url.txt": (
            "Test the links in campaign-url.txt, then use them in your campaign."
        ),
        "qr-code.png": (
            "Scan qr-code.png to check its destination before sharing or printing."
        ),
        "email-sequence.txt": (
            "Edit email-sequence.txt, then copy it into your email tool."
        ),
        "email-drafts.txt": "Edit email-drafts.txt, then copy it into your email tool.",
        "social-posts.txt": (
            "Review social-posts.txt, then schedule the posts on your channels."
        ),
        "landing-page-copy.txt": (
            "Review landing-page-copy.txt, then copy it into your page editor."
        ),
        "project-plan.csv": (
            "Open project-plan.csv in a spreadsheet and assign owners and dates."
        ),
    }
    steps.extend(actions[path.name] for path in output_paths if path.name in actions)
    return steps


def write_packet_index(
    run_dir: Path,
    output_paths: list[Path],
    quality_issue_count: int,
) -> Path:
    lines = ["# Marketing Run Index", "", "## Generated Files", ""]
    for path in output_paths:
        try:
            display_path = path.relative_to(run_dir)
        except ValueError:
            display_path = path
        lines.append(f"- [{path.name}]({display_path.as_posix()})")

    lines.extend(["", "## Quality Check", ""])
    if quality_issue_count:
        lines.append(
            f"- Review quality-check.md before publishing. "
            f"{quality_issue_count} issue(s) found."
        )
    else:
        lines.append(
            "- Automated checks found no issues. Review the files before publishing."
        )

    lines.extend(["", "## Next Steps", ""])
    for number, step in enumerate(
        result_next_steps(output_paths, quality_issue_count), 1
    ):
        lines.append(f"{number}. {step}")

    path = run_dir / "packet-index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return record_saved(path)
