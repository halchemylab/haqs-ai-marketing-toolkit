"""Quality checks for generated marketing packet outputs."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from haqs_toolkit.errors import UserError, command_errors, report_error

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
TEMPLATE_LEAK_PATTERNS = [
    re.compile(r"\$\{[^}]+\}|\{\{[^}]+\}\}"),
    re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}"),
    re.compile(r"\bNaN\b"),
    re.compile(r"\b(?:null|undefined)\b"),
]
SUBJECT_LINE_PATTERN = re.compile(
    r"^(?:#{1,6}\s+)?\*{0,2}Subject:\*{0,2}\s*(.+)$",
    re.IGNORECASE,
)
X_HEADING_PATTERN = re.compile(
    r"\b(x|twitter|tweet)\b",
    re.IGNORECASE,
)
NUMBERED_LIST_PATTERN = re.compile(r"^\d+[\.\)]\s*(.+)$")
URL_PATTERN = re.compile(r"https?://[^\s)>\]]+")
MARKDOWN_LINK_URL_PATTERN = re.compile(r"\[[^\]]*\]\((https?://[^)]+)\)")
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


def scan_x_post_lengths(path: Path, lines: list[str]) -> list[QualityIssue]:
    """Flag X/Twitter posts exceeding the 280-character platform limit."""
    issues: list[QualityIssue] = []
    file_name = path.name.lower()
    is_x_file = any(kw in file_name for kw in ["x_posts", "x-posts", "tweets"])

    if is_x_file:
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = NUMBERED_LIST_PATTERN.match(stripped)
            content = match.group(1).strip() if match else stripped
            if len(content) > 280:
                preview = content[:50] + "..." if len(content) > 50 else content
                issues.append(
                    QualityIssue(
                        path=path,
                        line_number=index + 1,
                        code="character-limit",
                        message=(
                            f"X/Twitter post exceeds 280 characters "
                            f"({len(content)} chars): {preview}"
                        ),
                    )
                )
        return issues

    headings = [
        (index, match.group(1), match.group(2).strip())
        for index, line in enumerate(lines)
        if (match := HEADING_PATTERN.match(line))
    ]

    for position, (index, marker, title) in enumerate(headings):
        if not X_HEADING_PATTERN.search(title):
            continue

        level = len(marker)
        next_index = len(lines)
        for following_index, following_marker, _ in headings[position + 1 :]:
            if len(following_marker) <= level:
                next_index = following_index
                break

        body_lines = [
            (idx, lines[idx].strip())
            for idx in range(index + 1, next_index)
            if lines[idx].strip()
        ]

        if not body_lines:
            continue

        numbered_items = [
            (idx, match.group(1).strip())
            for idx, text in body_lines
            if (match := NUMBERED_LIST_PATTERN.match(text))
        ]

        if numbered_items:
            for idx, content in numbered_items:
                if len(content) > 280:
                    preview = content[:50] + "..." if len(content) > 50 else content
                    issues.append(
                        QualityIssue(
                            path=path,
                            line_number=idx + 1,
                            code="character-limit",
                            message=(
                                f"X/Twitter post exceeds 280 characters "
                                f"({len(content)} chars): {preview}"
                            ),
                        )
                    )
        else:
            combined = "\n".join(text for _, text in body_lines)
            if len(combined) > 280:
                preview = combined[:50] + "..." if len(combined) > 50 else combined
                issues.append(
                    QualityIssue(
                        path=path,
                        line_number=body_lines[0][0] + 1,
                        code="character-limit",
                        message=(
                            f"X/Twitter post exceeds 280 characters "
                            f"({len(combined)} chars): {preview}"
                        ),
                    )
                )

    return issues


def check_url_string(path: Path, line_number: int, url_str: str) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    clean_url = url_str.rstrip(".,;:)")
    try:
        parsed = urlsplit(clean_url)
    except ValueError:
        issues.append(
            QualityIssue(
                path=path,
                line_number=line_number,
                code="malformed-url",
                message=f"Tracked URL is malformed: {clean_url}",
            )
        )
        return issues

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        issues.append(
            QualityIssue(
                path=path,
                line_number=line_number,
                code="malformed-url",
                message=f"Tracked URL is malformed: {clean_url}",
            )
        )
        return issues

    if parsed.query:
        query = parsed.query
        if (
            "&&" in query
            or query.startswith("&")
            or query.endswith("&")
            or clean_url.endswith("?")
        ):
            issues.append(
                QualityIssue(
                    path=path,
                    line_number=line_number,
                    code="malformed-url",
                    message=f"Tracked URL has malformed query parameters: {clean_url}",
                )
            )
        else:
            for part in query.split("&"):
                if "=" not in part or not part.split("=")[0].strip():
                    issues.append(
                        QualityIssue(
                            path=path,
                            line_number=line_number,
                            code="malformed-url",
                            message=(
                                f"Tracked URL has malformed query parameter: {part}"
                            ),
                        )
                    )
                    break
    return issues


def scan_file(path: Path) -> list[QualityIssue]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    issues: list[QualityIssue] = []
    is_subject_file = any(
        kw in path.name.lower()
        for kw in ["email_subject_lines", "email-subject-lines"]
    )

    for index, line in enumerate(lines):
        line_number = index + 1
        stripped = line.strip()

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
                            f"Unresolved placeholder or sample text: {stripped}"
                        ),
                    )
                )
                break

        for pattern in TEMPLATE_LEAK_PATTERNS:
            if match := pattern.search(line):
                issues.append(
                    QualityIssue(
                        path=path,
                        line_number=line_number,
                        code="template-leak",
                        message=(
                            f"Unrendered template tag or invalid value: "
                            f"{match.group(0)}"
                        ),
                    )
                )
                break

        # Subject line length check (exceeding 60 characters)
        if match := SUBJECT_LINE_PATTERN.match(stripped):
            subject = match.group(1).strip()
            if len(subject) > 60:
                issues.append(
                    QualityIssue(
                        path=path,
                        line_number=line_number,
                        code="subject-line-length",
                        message=(
                            f"Email subject line exceeds 60 characters "
                            f"({len(subject)} chars): {subject}"
                        ),
                    )
                )
        elif is_subject_file and (match := NUMBERED_LIST_PATTERN.match(stripped)):
            subject = match.group(1).strip()
            if len(subject) > 60:
                issues.append(
                    QualityIssue(
                        path=path,
                        line_number=line_number,
                        code="subject-line-length",
                        message=(
                            f"Email subject line exceeds 60 characters "
                            f"({len(subject)} chars): {subject}"
                        ),
                    )
                )

        # URL and markdown link integrity checks
        for link_match in MARKDOWN_LINK_URL_PATTERN.finditer(line):
            target_url = link_match.group(1).strip()
            if any(char.isspace() for char in target_url):
                issues.append(
                    QualityIssue(
                        path=path,
                        line_number=line_number,
                        code="malformed-url",
                        message=(
                            f"Tracked URL contains unescaped whitespace: "
                            f"{target_url}"
                        ),
                    )
                )
            else:
                issues.extend(check_url_string(path, line_number, target_url))

        for url_match in URL_PATTERN.finditer(line):
            issues.extend(check_url_string(path, line_number, url_match.group(0)))

        # Unescaped whitespace check for UTM URLs outside markdown links
        if "utm_" in line:
            utm_space_match = re.search(r"https?://[^\s)>\]]+\s+[^)>\]]*utm_", line)
            if utm_space_match:
                issues.append(
                    QualityIssue(
                        path=path,
                        line_number=line_number,
                        code="malformed-url",
                        message=(
                            f"Tracked URL contains unescaped whitespace: {stripped}"
                        ),
                    )
                )

        if CTA_PATTERN.search(line) and not line_has_link(lines, index):
            issues.append(
                QualityIssue(
                    path=path,
                    line_number=line_number,
                    code="missing-cta-link",
                    message=(
                        f"CTA-like line does not include a nearby link: {stripped}"
                    ),
                )
            )

    issues.extend(scan_empty_sections(path, lines))
    issues.extend(scan_x_post_lengths(path, lines))
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


@command_errors
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    scan_dir = resolve_scan_dir(args.path)

    try:
        issues = scan_path(args.path)
    except FileNotFoundError as exc:
        report_error(
            UserError(
                str(exc),
                "Check the supplied path and retry with an existing file or folder.",
            )
        )
        return 2

    print(format_report(issues, scan_dir if scan_dir.is_dir() else scan_dir.parent))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
