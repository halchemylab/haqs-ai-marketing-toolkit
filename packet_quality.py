"""Legacy wrapper for the packaged packet quality checker."""

from haqs_toolkit.packet_quality import *  # noqa: F403
from haqs_toolkit.packet_quality import main

if __name__ == "__main__":
    raise SystemExit(main())
