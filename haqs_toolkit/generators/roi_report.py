"""Report estimated ROI from automation usage logs."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from haqs_toolkit.utils.marketing import ROI_LOG_PATH, welcome


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


def main() -> None:
    welcome("automation ROI reporting")
    rows = read_roi_rows(ROI_LOG_PATH)
    if not rows:
        print("No ROI log found yet. Run one of the generator scripts first.")
        return

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

    print(f"Total logged runs: {total_runs}")
    print(f"Total generated assets: {total_assets}")
    print(f"Total time saved: {total_minutes / 60:.2f} hours")
    print(f"Estimated money saved: ${total_money:.2f}")
    print()
    print("Breakdown by asset type:")

    for asset_type, totals in sorted(by_asset.items()):
        print(
            f"- {asset_type}: {int(totals['count'])} generated across "
            f"{int(totals['runs'])} run(s), {totals['minutes'] / 60:.2f} hours saved, "
            f"${totals['money']:.2f} saved"
        )

    print()
    print(f"ROI log: {ROI_LOG_PATH}")


if __name__ == "__main__":
    main()
