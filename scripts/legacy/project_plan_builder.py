"""Legacy wrapper for the packaged project plan builder."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from haqs_toolkit.generators.project_plan_builder import *  # noqa: F403
from haqs_toolkit.generators.project_plan_builder import main

if __name__ == "__main__":
    main()
