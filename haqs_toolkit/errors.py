"""Actionable terminal errors shared by all commands."""

from __future__ import annotations

import errno
import os
import sys
from contextvars import ContextVar
from functools import wraps
from pathlib import Path

_saved_paths: ContextVar[list[Path] | None] = ContextVar("saved_paths", default=None)


class UserError(ValueError):
    """An expected problem the user can resolve."""

    def __init__(self, message: str, fix: str = "", path: Path | None = None):
        self.message = message
        self.fix = fix
        self.path = path
        details = message
        if path is not None:
            details += f"\nFile: {path}"
        if fix:
            details += f"\nHow to fix: {fix}"
        super().__init__(details)


def record_saved(path: Path) -> Path:
    paths = _saved_paths.get()
    if paths is not None and path not in paths:
        paths.append(path)
    return path


def friendly_error(exc: Exception) -> UserError:
    if isinstance(exc, UserError):
        return exc
    path = getattr(exc, "filename", None)
    if isinstance(exc, FileNotFoundError):
        return UserError(
            "A required file or folder was not found.",
            "Check the path and create or restore the missing file, then retry.",
            path,
        )
    if isinstance(exc, PermissionError):
        return UserError(
            "Permission denied while accessing a file or folder.",
            "Close applications using this file and check its permissions. "
            "For output, choose a writable folder using the command's output "
            "option or HAQS_OUTPUT_DIR where supported.",
            path,
        )
    if isinstance(exc, (IsADirectoryError, NotADirectoryError, FileExistsError)):
        return UserError(
            "The path has the wrong type or already exists.",
            "Check whether this path should be a file or folder, "
            "or choose a different output location.",
            path,
        )
    if isinstance(exc, OSError):
        fix = (
            "Free some disk space and retry."
            if exc.errno == errno.ENOSPC
            else "Check that the location is available and writable, then retry."
        )
        return UserError("Could not access or save a file.", fix, path)
    if isinstance(exc, UnicodeError):
        return UserError(
            "A text file could not be read as UTF-8.",
            "Save the input file with UTF-8 encoding, then retry.",
        )
    if isinstance(exc, ModuleNotFoundError):
        return UserError(
            f"A required Python dependency is missing: {exc.name}.",
            "From the toolkit folder, run python -m pip install -e . "
            "using the same Python environment, then retry.",
        )
    if isinstance(exc, EOFError):
        return UserError(
            "Input ended before all required answers were supplied.",
            "Run the command again in an interactive terminal and "
            "complete the prompts, or supply its command-line arguments.",
        )
    return UserError(
        "The tool stopped because of an unexpected error.",
        'For technical details, set $env:HAQS_DEBUG="1" in PowerShell '
        "and repeat the command. Include those details when reporting the issue.",
    )


def report_error(exc: Exception) -> None:
    if os.getenv("HAQS_DEBUG") == "1":
        raise exc
    print(f"Error: {friendly_error(exc)}", file=sys.stderr)


def command_errors(function):
    """Keep tracebacks at the command boundary; preserve errors in library calls."""

    @wraps(function)
    def wrapped(*args, **kwargs):
        token = None
        if _saved_paths.get() is None:
            token = _saved_paths.set([])
        try:
            return function(*args, **kwargs) or 0
        except KeyboardInterrupt:
            print("Cancelled. Run the command again when ready.", file=sys.stderr)
            return 130
        except Exception as exc:
            report_error(exc)
            paths = _saved_paths.get()
            if paths:
                print("Files saved before the error:", file=sys.stderr)
                for path in paths:
                    print(f"- {path}", file=sys.stderr)
            return 1
        finally:
            if token is not None:
                _saved_paths.reset(token)

    return wrapped
