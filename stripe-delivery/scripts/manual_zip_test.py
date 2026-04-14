"""Manual verification script for Session 3 — zips, uploads, prints signed URL.

Usage (from stripe-delivery/):
    python scripts/manual_zip_test.py

The script auto-loads ~/.sidebarcode-secrets.env if it exists, so you do
not need to source anything beforehand. You can also pass credentials via
real environment variables, which take precedence over the secrets file.

The script:
  1. Zips tests/fixtures/dummy_deliverable/ with a fresh purchase_id.
  2. Uploads to the R2 dev bucket under sp2-session3-manual/.
  3. Generates a 1-hour signed URL.
  4. Prints the URL — click it in your browser to confirm download.
  5. Does NOT delete the object — Kyle deletes manually after verification.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _autoload_secrets() -> None:
    """Auto-load credentials from ~/.sidebarcode-secrets.env if present.

    Variable name aliases: the secrets file uses `_TEST` / `_LIVE` suffixes
    for Stripe and the unsuffixed names for R2. This function maps the
    file's R2 vars onto the names the script expects, with strict
    preference for variables already set in the real environment.
    """
    secrets_path = Path.home() / ".sidebarcode-secrets.env"
    if not secrets_path.exists():
        return

    try:
        from dotenv import dotenv_values  # type: ignore[import-untyped]
    except ImportError:
        print(
            f"WARNING: python-dotenv not installed; cannot auto-load {secrets_path}\n"
            "         install with: pip install python-dotenv",
            file=sys.stderr,
        )
        return

    values = dotenv_values(secrets_path)
    # Strip surrounding whitespace and CRLF artifacts.
    cleaned = {k: (v or "").strip() for k, v in values.items()}

    # R2 vars — passthrough.
    for key in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"):
        if not os.environ.get(key) and cleaned.get(key):
            os.environ[key] = cleaned[key]

    # R2_BUCKET defaults to dev bucket from the file, then env, then literal.
    if not os.environ.get("R2_BUCKET"):
        bucket = cleaned.get("R2_BUCKET_DEV") or "sidebarcode-dev"
        os.environ["R2_BUCKET"] = bucket


_autoload_secrets()

# Make `api` importable when running this script from stripe-delivery/.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api.delivery import build_zip, sign_download_url, upload_to_r2  # noqa: E402

FIXTURE = _ROOT / "tests" / "fixtures" / "dummy_deliverable"


def main() -> int:
    required = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}", file=sys.stderr)
        print("       export them or source ~/.sidebarcode-secrets.env first", file=sys.stderr)
        return 1

    bucket = os.getenv("R2_BUCKET") or "sidebarcode-dev"
    purchase_id = f"sp2_session3_manual_{uuid.uuid4().hex[:8]}"
    object_key = f"sp2-session3-manual/{purchase_id}.zip"

    print(f"[1/3] Building zip from {FIXTURE} ...")
    zip_path = build_zip(FIXTURE, purchase_id)
    size_kb = zip_path.stat().st_size / 1024
    print(f"      -> {zip_path}  ({size_kb:.1f} KB)")

    print(f"[2/3] Uploading to R2 bucket '{bucket}' as {object_key} ...")
    upload_to_r2(zip_path, object_key, bucket=bucket)
    print("      -> uploaded")

    print("[3/3] Generating 1-hour signed URL ...")
    url = sign_download_url(object_key, bucket=bucket, ttl_seconds=3600)

    print("")
    print("=" * 78)
    print("MANUAL VERIFICATION URL  (click to download — expires in 1 hour)")
    print("=" * 78)
    print(url)
    print("=" * 78)
    print("")
    print(f"Generated at: {datetime.now(timezone.utc).isoformat()}")
    print(f"Object key:   {object_key}")
    print(f"Purchase id:  {purchase_id}")
    print("")
    print("After verifying the download works, you can delete the object via:")
    print(f"  python -c \"from api.delivery import delete_r2_object; "
          f"delete_r2_object('{object_key}', bucket='{bucket}')\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
