"""Run folder and automatic quality-check helpers."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from haqs_toolkit import packet_quality

RUNS_DIR = Path("runs")


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
    base_name = (
        f"{slugify(job_name)}-{slugify(job_type)}-{slugify(scope)}-{timestamp}"
    )
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
    return path, issues


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
        lines.append("- quality-check.md passed with no publish-blocking issues.")

    lines.extend(
        [
            "",
            "## Next Steps",
            "",
            "- Confirm dates, links, prices, claims, and names before publishing.",
            "- Test the campaign URL and QR code when those assets are generated.",
        ]
    )

    path = run_dir / "packet-index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
