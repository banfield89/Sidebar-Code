"""Webhook debug log cleanup cron — HTTP client.

Like send_daily_digest, this is a thin HTTP wrapper that calls
/admin/cron/cleanup-webhook-log on the web service. The actual SQL
DELETE runs in the web service because the SQLite file lives on the
web service's persistent disk only.

Usage:
    python scripts/cleanup_webhook_debug_log.py
    python scripts/cleanup_webhook_debug_log.py --retention-days 14
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
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
    for key in ("SP2_API_URL", "CRON_SECRET"):
        if not os.environ.get(key) and cleaned.get(key):
            os.environ[key] = cleaned[key]


_autoload_secrets()

DEFAULT_API_URL = "https://sidebarcode-api.onrender.com"
ENDPOINT = "/admin/cron/cleanup-webhook-log"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retention-days", type=int, default=30)
    args = parser.parse_args()

    api_url = os.environ.get("SP2_API_URL") or DEFAULT_API_URL
    secret = os.environ.get("CRON_SECRET")
    if not secret:
        print("ERROR: CRON_SECRET not set", file=sys.stderr)
        return 1

    url = f"{api_url.rstrip('/')}{ENDPOINT}?retention_days={args.retention_days}"
    print(f"POST {url}")
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            print(f"HTTP {resp.status} — {body}")
            payload = json.loads(body)
            print(f"cleanup deleted {payload.get('deleted_rows')} rows")
            return 0
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} — {e.read().decode('utf-8')}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
