"""Nightly R2 cleanup — delete delivery zips older than 7 days.

The bucket-level lifecycle rule should already handle this automatically,
but this cron exists as a belt-and-suspenders. It also produces a log
line we can grep for in the digest if cleanup falls behind.

Usage:
    python scripts/cleanup_r2.py
    python scripts/cleanup_r2.py --bucket sidebarcode-prod
    python scripts/cleanup_r2.py --max-age-days 30 --dry-run
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
    for key in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        if not os.environ.get(key) and cleaned.get(key):
            os.environ[key] = cleaned[key]


_autoload_secrets()

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api.delivery import _r2_client  # noqa: E402

logger = logging.getLogger("cleanup_r2")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DEFAULT_MAX_AGE_DAYS = 7
SKIP_PREFIXES = ("sqlite-backups/",)  # backups have their own retention


def cleanup_bucket(bucket: str, max_age_days: int, dry_run: bool) -> dict[str, int]:
    """Delete objects older than max_age_days. Skips backup prefixes.

    Returns counts: {scanned, deleted, skipped}
    """
    client = _r2_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    counts = {"scanned": 0, "deleted": 0, "skipped": 0}

    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents") or []:
            counts["scanned"] += 1
            key = obj["Key"]
            if any(key.startswith(p) for p in SKIP_PREFIXES):
                counts["skipped"] += 1
                continue

            last_modified = obj["LastModified"]
            if last_modified.tzinfo is None:
                last_modified = last_modified.replace(tzinfo=timezone.utc)
            if last_modified >= cutoff:
                continue

            if dry_run:
                logger.info("[DRY-RUN] would delete %s (age=%s)", key, last_modified.isoformat())
            else:
                client.delete_object(Bucket=bucket, Key=key)
                logger.info("deleted %s (age=%s)", key, last_modified.isoformat())
            counts["deleted"] += 1

    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bucket",
        default=os.environ.get("R2_BUCKET") or "sidebarcode-staging",
    )
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info(
        "cleanup_r2 starting — bucket=%s max_age_days=%d dry_run=%s",
        args.bucket, args.max_age_days, args.dry_run,
    )
    counts = cleanup_bucket(args.bucket, args.max_age_days, args.dry_run)
    logger.info(
        "cleanup_r2 done — scanned=%d deleted=%d skipped=%d",
        counts["scanned"], counts["deleted"], counts["skipped"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
