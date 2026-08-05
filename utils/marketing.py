"""Backward-compatible alias for the packaged marketing utilities."""

from __future__ import annotations

import sys

from haqs_toolkit.utils import marketing as _marketing

sys.modules[__name__] = _marketing
