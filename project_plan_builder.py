"""Backward-compatible wrapper for the project plan builder."""

from haqs_toolkit.generators.project_plan_builder import *  # noqa: F403
from haqs_toolkit.generators.project_plan_builder import main


if __name__ == "__main__":
    main()

