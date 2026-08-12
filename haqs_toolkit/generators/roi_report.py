"""Report estimated ROI from automation usage logs."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from haqs_toolkit.utils.marketing import get_roi_log_path, welcome


def read_roi_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def as_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_report(rows: list[dict[str, str]], path: Path) -> str:
    if not rows:
        return "No ROI log found yet. Run one of the generator scripts first."

    total_runs = len(rows)
    total_assets = sum(as_int(row.get("count", "")) for row in rows)
    total_minutes = sum(as_int(row.get("time_saved_minutes", "")) for row in rows)
    total_money = sum(as_float(row.get("money_saved", "")) for row in rows)

    by_asset: dict[str, dict[str, float]] = defaultdict(
        lambda: {"runs": 0, "count": 0, "minutes": 0, "money": 0.0}
    )
    for row in rows:
        asset_type = row.get("asset_type", "unknown")
        by_asset[asset_type]["runs"] += 1
        by_asset[asset_type]["count"] += as_int(row.get("count", ""))
        by_asset[asset_type]["minutes"] += as_int(row.get("time_saved_minutes", ""))
        by_asset[asset_type]["money"] += as_float(row.get("money_saved", ""))

    lines = [
        f"Total logged runs: {total_runs}",
        f"Total generated assets: {total_assets}",
        f"Total time saved: {total_minutes / 60:.2f} hours",
        f"Estimated money saved: ${total_money:.2f}",
        "",
        "Breakdown by asset type:",
    ]

    for asset_type, totals in sorted(by_asset.items()):
        lines.append(
            f"- {asset_type}: {int(totals['count'])} generated across "
            f"{int(totals['runs'])} run(s), {totals['minutes'] / 60:.2f} hours saved, "
            f"${totals['money']:.2f} saved"
        )

    lines.extend(
        [
            "",
            f"ROI log: {path}",
            "",
            "Next step: Use these totals in your reporting, then check the CSV if "
            "you need the run-by-run details.",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report estimated automation ROI.")
    parser.add_argument(
        "--log-path",
        type=Path,
        default=get_roi_log_path(),
        help="Path to the ROI CSV log.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    welcome("automation ROI reporting")
    print(build_report(read_roi_rows(args.log_path), args.log_path))


if __name__ == "__main__":
    main()
