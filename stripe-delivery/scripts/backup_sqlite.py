"""Nightly SQLite backup to R2.

Copies the SQLite database to R2 as `sqlite-backups/sidebarcode-{date}.db`
and prunes backups older than RETENTION_DAYS. Designed to run as a Render
cron job in Session 8; can also run manually for testing.

Uses sqlite3.Connection.backup() so the copy is consistent even if the
service is mid-write.

Usage:
    python scripts/backup_sqlite.py
    python scripts/backup_sqlite.py --bucket sidebarcode-prod
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Auto-load secrets
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
    for key in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "SQLITE_PATH"):
        if not os.environ.get(key) and cleaned.get(key):
            os.environ[key] = cleaned[key]


_autoload_secrets()

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api.db import get_db_path  # noqa: E402
from api.delivery import _r2_client  # noqa: E402

logger = logging.getLogger("backup_sqlite")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RETENTION_DAYS = 30
BACKUP_PREFIX = "sqlite-backups/"


def make_consistent_copy(source: Path, destination: Path) -> None:
    """Use sqlite3.backup to safely copy a possibly-live database."""
    src = sqlite3.connect(str(source))
    dst = sqlite3.connect(str(destination))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def upload_backup(local_path: Path, bucket: str, object_key: str) -> None:
    client = _r2_client()
    client.upload_file(
        Filename=str(local_path),
        Bucket=bucket,
        Key=object_key,
        ExtraArgs={"ContentType": "application/octet-stream"},
    )


def prune_old_backups(bucket: str, retention_days: int) -> int:
    """Delete backups older than retention_days. Returns count deleted."""
    client = _r2_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = 0
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=BACKUP_PREFIX):
        for obj in page.get("Contents") or []:
            last_modified = obj["LastModified"]
            if last_modified.tzinfo is None:
                last_modified = last_modified.replace(tzinfo=timezone.utc)
            if last_modified < cutoff:
                client.delete_object(Bucket=bucket, Key=obj["Key"])
                deleted += 1
                logger.info("pruned old backup: %s", obj["Key"])
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bucket",
        default=os.environ.get("R2_BUCKET") or "sidebarcode-dev",
        help="R2 bucket to upload backups to",
    )
    parser.add_argument("--retention-days", type=int, default=RETENTION_DAYS)
    args = parser.parse_args()

    db_path = get_db_path()
    if not db_path.exists():
        logger.error("SQLite file does not exist: %s", db_path)
        return 1

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    object_key = f"{BACKUP_PREFIX}sidebarcode-{timestamp}.db"
    logger.info("backing up %s -> r2://%s/%s", db_path, args.bucket, object_key)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        tmp_path = Path(tf.name)
    try:
        make_consistent_copy(db_path, tmp_path)
        upload_backup(tmp_path, args.bucket, object_key)
        size_kb = tmp_path.stat().st_size / 1024
        logger.info("upload complete (%.1f KB)", size_kb)
    finally:
        tmp_path.unlink(missing_ok=True)

    pruned = prune_old_backups(args.bucket, args.retention_days)
    logger.info("backup done — pruned %d old backup(s)", pruned)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
