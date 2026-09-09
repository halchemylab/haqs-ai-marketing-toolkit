"""Quality checks for generated marketing packet outputs."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

CHECKED_EXTENSIONS = {".md", ".txt"}
PLACEHOLDER_PATTERNS = [
    re.compile(r"\[url here\]", re.IGNORECASE),
    re.compile(r"\bexample\.com\b", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\blorem ipsum\b", re.IGNORECASE),
    re.compile(r"\breplace (this|with|any|remaining)\b", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(
        r"\[(?:first name|name|company|date|time|link|insert[^\]]*)\]",
        re.IGNORECASE,
    ),
]
CTA_PATTERN = re.compile(
    r"\b("
    r"cta|call to action|primary cta|button|register|sign up|signup|"
    r"get started|learn more|book|schedule|download|reserve|apply"
    r")\b",
    re.IGNORECASE,
)
LINK_PATTERN = re.compile(r"https?://|mailto:|\[[^\]]+\]\([^)]+\)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
GENERATION_NOTE_PATTERN = re.compile(r"\bGeneration note:", re.IGNORECASE)


@dataclass(frozen=True)
class QualityIssue:
    path: Path
    line_number: int
    code: str
    message: str


def resolve_scan_dir(path: Path) -> Path:
    """Use packet outputs when a packet directory is supplied."""
    if (path / "outputs").is_dir():
        return path / "outputs"
    return path


def iter_checked_files(scan_dir: Path) -> list[Path]:
    if scan_dir.is_file():
        return [scan_dir] if scan_dir.suffix.lower() in CHECKED_EXTENSIONS else []

    return sorted(
        path
        for path in scan_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in CHECKED_EXTENSIONS
    )


def line_has_link(lines: list[str], index: int) -> bool:
    """Look for a CTA destination on the current line or the next few lines."""
    for line in lines[index : index + 5]:
        if LINK_PATTERN.search(line):
            return True
    return False


def scan_empty_sections(path: Path, lines: list[str]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    headings = [
        (index, match.group(1), match.group(2).strip())
        for index, line in enumerate(lines)
        if (match := HEADING_PATTERN.match(line))
    ]

    for position, (index, marker, title) in enumerate(headings):
        level = len(marker)
        next_index = len(lines)
        for following_index, following_marker, _ in headings[position + 1 :]:
            if len(following_marker) <= level:
                next_index = following_index
                break

        body = [line.strip() for line in lines[index + 1 : next_index]]
        if not any(body):
            issues.append(
                QualityIssue(
                    path=path,
                    line_number=index + 1,
                    code="empty-section",
                    message=f"Section has no content: {title}",
                )
            )

    return issues


def scan_file(path: Path) -> list[QualityIssue]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    issues: list[QualityIssue] = []

    for index, line in enumerate(lines):
        line_number = index + 1
        if GENERATION_NOTE_PATTERN.search(line):
            issues.append(
                QualityIssue(
                    path=path,
                    line_number=line_number,
                    code="generation-note",
                    message="AI fallback/generation note is still present.",
                )
            )

        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(line):
                issues.append(
                    QualityIssue(
                        path=path,
                        line_number=line_number,
                        code="placeholder",
                    message=(
                        "Unresolved placeholder or sample text: "
                        f"{line.strip()}"
                    ),
                    )
                )
                break

        if CTA_PATTERN.search(line) and not line_has_link(lines, index):
            issues.append(
                QualityIssue(
                    path=path,
                    line_number=line_number,
                    code="missing-cta-link",
                    message=(
                        "CTA-like line does not include a nearby link: "
                        f"{line.strip()}"
                    ),
                )
            )

    issues.extend(scan_empty_sections(path, lines))
    return issues


def scan_path(path: Path) -> list[QualityIssue]:
    scan_dir = resolve_scan_dir(path)
    if not scan_dir.exists():
        raise FileNotFoundError(f"Path does not exist: {scan_dir}")

    issues: list[QualityIssue] = []
    for file_path in iter_checked_files(scan_dir):
        issues.extend(scan_file(file_path))
    return issues


def format_report(issues: list[QualityIssue], base_dir: Path) -> str:
    if not issues:
        return "Packet quality check passed. No publish-blocking issues found."

    lines = [f"Packet quality check found {len(issues)} issue(s):", ""]
    for issue in issues:
        try:
            display_path = issue.path.relative_to(base_dir)
        except ValueError:
            display_path = issue.path
        lines.append(
            f"- {display_path}:{issue.line_number} [{issue.code}] {issue.message}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan generated packet outputs for pre-publish quality issues.",
        epilog="Quality checks are run automatically by haqs-create.",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Packet directory, outputs directory, or a single Markdown/text file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    scan_dir = resolve_scan_dir(args.path)

    try:
        issues = scan_path(args.path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 2

    print(format_report(issues, scan_dir if scan_dir.is_dir() else scan_dir.parent))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
