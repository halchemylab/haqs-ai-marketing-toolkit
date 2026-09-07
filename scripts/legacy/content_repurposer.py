"""Legacy wrapper for the packaged content repurposer."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from haqs_toolkit.generators.content_repurposer import *  # noqa: F403
from haqs_toolkit.generators.content_repurposer import main

if __name__ == "__main__":
    main()
