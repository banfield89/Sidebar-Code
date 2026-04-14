"""Nightly cron — prune webhook_debug_log rows older than retention window.

Default retention: 30 days. webhook_debug_log accumulates one row per
incoming Stripe event for audit/debugging. At >100 events/day this would
grow unbounded; this cron keeps it bounded.

Usage:
    python scripts/cleanup_webhook_debug_log.py
    python scripts/cleanup_webhook_debug_log.py --retention-days 14 --dry-run
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _autoload_secrets() -> None:
    secrets_path = Path.home() / ".sidebarcode-secrets.env"
    if not secrets_path.exists():
        return
    try:
        from dotenv import dotenv_values  # type: ignore[import-untyped]
    except ImportError:
        return
    values = dotenv_values(secrets_path)
    cleaned = {k: (v or "").strip() for k, v in values.items()}
    if not os.environ.get("SQLITE_PATH") and cleaned.get("SQLITE_PATH"):
        os.environ["SQLITE_PATH"] = cleaned["SQLITE_PATH"]


_autoload_secrets()

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api.db import get_connection  # noqa: E402

logger = logging.getLogger("cleanup_webhook_debug_log")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DEFAULT_RETENTION_DAYS = 30


def cleanup(retention_days: int, dry_run: bool) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with get_connection() as conn:
        if dry_run:
            row = conn.execute(
                "SELECT COUNT(*) FROM webhook_debug_log WHERE created_at < ?",
                (cutoff,),
            ).fetchone()
            count = row[0]
            logger.info("[DRY-RUN] would delete %d rows older than %s", count, cutoff)
            return count
        result = conn.execute(
            "DELETE FROM webhook_debug_log WHERE created_at < ?", (cutoff,)
        )
        deleted = result.rowcount
    logger.info("deleted %d rows older than %s", deleted, cutoff)
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cleanup(args.retention_days, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
