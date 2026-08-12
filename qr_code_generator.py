"""Backward-compatible wrapper for the QR code generator."""

from haqs_toolkit.generators.qr_code_generator import *  # noqa: F403
from haqs_toolkit.generators.qr_code_generator import main

if __name__ == "__main__":
    main()
