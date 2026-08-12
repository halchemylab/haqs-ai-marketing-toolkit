"""Run the event marketing pipeline from a packet directory."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from haqs_toolkit.events import main

if __name__ == "__main__":
    raise SystemExit(main())
