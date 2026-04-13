"""Pytest config: loads `.env.test` so tests run against sandbox services only."""

from pathlib import Path

from dotenv import load_dotenv

_ENV_TEST = Path(__file__).resolve().parent.parent / ".env.test"
if _ENV_TEST.exists():
    load_dotenv(_ENV_TEST, override=True)
