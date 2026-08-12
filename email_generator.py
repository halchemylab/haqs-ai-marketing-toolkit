"""Backward-compatible wrapper for the email generator."""

from haqs_toolkit.generators.email_generator import *  # noqa: F403
from haqs_toolkit.generators.email_generator import main

if __name__ == "__main__":
    main()
