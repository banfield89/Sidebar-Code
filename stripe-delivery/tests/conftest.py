"""Pytest config: loads `.env.test` and makes the `api` package importable."""

from __future__ import annotations

import sys
from pathlib import Path

_STRIPE_DELIVERY_ROOT = Path(__file__).resolve().parent.parent
if str(_STRIPE_DELIVERY_ROOT) not in sys.path:
    sys.path.insert(0, str(_STRIPE_DELIVERY_ROOT))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover — dotenv may be absent in minimal CI
    load_dotenv = None  # type: ignore[assignment]

_ENV_TEST = _STRIPE_DELIVERY_ROOT / ".env.test"
if load_dotenv is not None and _ENV_TEST.exists():
    load_dotenv(_ENV_TEST, override=True)
