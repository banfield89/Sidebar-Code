"""Daily digest cron — HTTP client that triggers the digest endpoint.

Render persistent disks are per-service, not shared. The cron container
has no /var/data SQLite file. So this script is a thin HTTP client that
calls /admin/cron/daily-digest on the web service, which has the disk
and runs the actual logic.

Usage (cron context — set in render.yaml startCommand):
    python scripts/send_daily_digest.py

Usage (local manual testing):
    SP2_API_URL=https://sidebarcode-api.onrender.com \
    CRON_SECRET=<secret> \
    python scripts/send_daily_digest.py

Auto-loads ~/.sidebarcode-secrets.env when running locally.
"""

from __future__ import annotations

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
ENDPOINT = "/admin/cron/daily-digest"


def main() -> int:
    api_url = os.environ.get("SP2_API_URL") or DEFAULT_API_URL
    secret = os.environ.get("CRON_SECRET")
    if not secret:
        print("ERROR: CRON_SECRET not set", file=sys.stderr)
        return 1

    url = api_url.rstrip("/") + ENDPOINT
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
            print(f"daily digest sent — purchases={payload.get('purchase_count')}")
            return 0
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} — {e.read().decode('utf-8')}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
