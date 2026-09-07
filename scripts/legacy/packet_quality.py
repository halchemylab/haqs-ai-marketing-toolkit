"""Legacy wrapper for the packaged packet quality checker."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from haqs_toolkit.packet_quality import *  # noqa: F403
from haqs_toolkit.packet_quality import main

if __name__ == "__main__":
    raise SystemExit(main())
