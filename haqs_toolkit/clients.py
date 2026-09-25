"""Editable client profiles for marketing creation."""

from pathlib import Path

from haqs_toolkit.errors import UserError
from haqs_toolkit.utils.marketing import REPO_ROOT, choose_option, load_brand_voice

CLIENTS_DIR = REPO_ROOT / "brands"


def load_profile(name: str, directory: Path = CLIENTS_DIR) -> dict[str, str]:
    filename = name if name.endswith(".txt") else name + ".txt"
    if Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise UserError("Use a client filename from the brands folder.")
    path = directory / filename
    if not path.is_file():
        raise UserError(
            f"Client profile not found: {path}",
            "Add a .txt file to brands/ or choose --brands general.",
        )
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise UserError(
            f"Client profile is empty: {path}",
            "Add client instructions before using this profile.",
        )
    return {"name": path.stem, "text": text}


def choose_profile(directory: Path = CLIENTS_DIR) -> dict[str, str] | None:
    paths = sorted(directory.glob("*.txt"), key=lambda path: path.name.lower())
    if not paths:
        return None
    general = "General brand voice"
    labels = [general] + [path.name for path in paths]
    choice = choose_option("Which client profile should this run use?", labels)
    return None if choice == general else load_profile(choice, directory)


def profile_defaults(profile: dict[str, str] | None) -> dict[str, object]:
    defaults: dict[str, object] = {}
    aliases = {
        "audience": "audience",
        "preferred cta": "cta",
        "cta": "cta",
        "channels": "channels",
    }
    if profile:
        for line in profile["text"].splitlines():
            label, separator, value = line.partition(":")
            key = aliases.get(label.strip().lower())
            if separator and key and value.strip():
                defaults[key] = (
                    [part.strip() for part in value.split(",") if part.strip()]
                    if key == "channels"
                    else value.strip()
                )
    return defaults


def apply_defaults(
    brief: dict[str, object], defaults: dict[str, object]
) -> dict[str, object]:
    merged = brief.copy()
    for key, value in defaults.items():
        if not merged.get(key):
            merged[key] = value
    return merged


def voice_for(brief: dict[str, object]) -> str:
    profile = brief.get("client_profile")
    if not profile:
        return load_brand_voice()
    if (
        not isinstance(profile, dict)
        or not isinstance(profile.get("text"), str)
        or not profile["text"].strip()
    ):
        raise UserError(
            "Invalid client_profile in brief.",
            "Use --brands to select a valid client text file.",
        )
    return (
        "Client profile (defaults and background):\n"
        + profile["text"]
        + "\n\nExplicit campaign/event brief details and asset instructions "
        "take priority over client defaults. "
        "Use the supplied campaign links, not the profile website, for calls to action."
    )
