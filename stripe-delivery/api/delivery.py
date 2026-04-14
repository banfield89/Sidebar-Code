"""Delivery pipeline: zip builder, R2 upload, signed URL generation, Postmark send.

Session 3 scope: build_zip, upload_to_r2, sign_download_url.
Session 7 wires the Postmark `build_and_deliver_zip` orchestration on top.
"""

from __future__ import annotations

import logging
import os
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults parked in DECISIONS_PARKING_LOT.md (Session 3)
# ---------------------------------------------------------------------------
ZIP_COMPRESSION_LEVEL = 6  # Python default; balanced speed vs ratio
ZIP_INCLUDE_TOP_LEVEL_FOLDER = True  # `parser_trial/file.md` not `file.md`
ZIP_SIZE_WARNING_BYTES = 500 * 1024 * 1024  # 500 MB — log warning if exceeded
DOWNLOAD_URL_TTL_SECONDS = 72 * 60 * 60  # 72 hours

SUPPORT_EMAIL = "support@sidebarcode.com"
README_FILENAME = "README.txt"


# ---------------------------------------------------------------------------
# README injection
# ---------------------------------------------------------------------------
def _build_readme(purchase_id: str, generated_at: Optional[datetime] = None) -> str:
    """Top-level README.txt content injected into every delivery zip."""
    when = generated_at or datetime.now(timezone.utc)
    return (
        "Sidebar Code — Customer Deliverable\n"
        "===================================\n"
        f"Purchase ID:   {purchase_id}\n"
        f"Generated at:  {when.isoformat()}\n"
        "\n"
        "License (placeholder — Aemon will finalize before launch):\n"
        "  Single-firm internal use license. May be deployed across all\n"
        "  attorneys and staff at the purchasing firm. Resale, sublicensing,\n"
        "  or redistribution outside the purchasing firm is prohibited.\n"
        "  No warranty of fitness for any particular legal matter.\n"
        "\n"
        f"Support: {SUPPORT_EMAIL}\n"
    )


# ---------------------------------------------------------------------------
# build_zip
# ---------------------------------------------------------------------------
def build_zip(source_dir: Path, purchase_id: str) -> Path:
    """Recursively zip `source_dir` and inject a README.txt at the top level.

    Returns a Path to the generated zip file. The caller is responsible for
    cleaning up the parent temp directory after upload.

    Folder layout inside the zip (with ZIP_INCLUDE_TOP_LEVEL_FOLDER=True):
        README.txt
        <source_dir.name>/
            <recursive contents>
    """
    source_dir = Path(source_dir)
    if not source_dir.exists() or not source_dir.is_dir():
        raise FileNotFoundError(f"source_dir not found or not a directory: {source_dir}")

    tmp_dir = Path(tempfile.mkdtemp(prefix="sidebarcode-zip-"))
    zip_path = tmp_dir / f"{purchase_id}.zip"

    top_level = source_dir.name if ZIP_INCLUDE_TOP_LEVEL_FOLDER else ""

    with zipfile.ZipFile(
        zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=ZIP_COMPRESSION_LEVEL,
    ) as zf:
        zf.writestr(README_FILENAME, _build_readme(purchase_id))

        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source_dir)
            arcname = f"{top_level}/{relative.as_posix()}" if top_level else relative.as_posix()
            zf.write(path, arcname=arcname)

    size = zip_path.stat().st_size
    if size > ZIP_SIZE_WARNING_BYTES:
        logger.warning(
            "build_zip produced a large zip: %s bytes (purchase_id=%s, source=%s)",
            size,
            purchase_id,
            source_dir,
        )

    return zip_path


# ---------------------------------------------------------------------------
# R2 client
# ---------------------------------------------------------------------------
def _r2_client():
    """Create a boto3 S3 client wired to Cloudflare R2.

    Reads credentials from the standard env vars set in Render.
    Raises RuntimeError if any required var is missing.
    """
    account_id = os.environ.get("R2_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    missing = [
        name
        for name, value in (
            ("R2_ACCOUNT_ID", account_id),
            ("R2_ACCESS_KEY_ID", access_key),
            ("R2_SECRET_ACCESS_KEY", secret_key),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"R2 credentials missing: {', '.join(missing)}")

    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def _resolve_bucket(bucket: Optional[str]) -> str:
    bucket = bucket or os.environ.get("R2_BUCKET")
    if not bucket:
        raise RuntimeError("R2_BUCKET is not set and no bucket was provided")
    return bucket


# ---------------------------------------------------------------------------
# upload_to_r2
# ---------------------------------------------------------------------------
def upload_to_r2(
    zip_path: Path,
    object_key: str,
    *,
    bucket: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> str:
    """Upload `zip_path` to R2 under `object_key` and tag it with expires_at.

    Returns the object_key on success. Raises on upload failure.
    Tagging failures are logged but do not abort the upload — the lifecycle
    rule on the bucket is the actual cleanup mechanism.
    """
    zip_path = Path(zip_path)
    if not zip_path.exists() or not zip_path.is_file():
        raise FileNotFoundError(f"zip_path not found or not a file: {zip_path}")

    bucket_name = _resolve_bucket(bucket)
    client = _r2_client()
    expires_at = expires_at or (
        datetime.now(timezone.utc) + timedelta(seconds=DOWNLOAD_URL_TTL_SECONDS)
    )

    client.upload_file(
        Filename=str(zip_path),
        Bucket=bucket_name,
        Key=object_key,
        ExtraArgs={"ContentType": "application/zip"},
    )

    try:
        client.put_object_tagging(
            Bucket=bucket_name,
            Key=object_key,
            Tagging={
                "TagSet": [
                    {"Key": "expires_at", "Value": expires_at.isoformat()},
                    {"Key": "service", "Value": "sidebarcode-sp2"},
                ]
            },
        )
    except (BotoCoreError, ClientError) as exc:  # pragma: no cover — non-fatal
        logger.warning("R2 object tagging failed for %s: %s", object_key, exc)

    return object_key


# ---------------------------------------------------------------------------
# sign_download_url
# ---------------------------------------------------------------------------
def sign_download_url(
    object_key: str,
    *,
    bucket: Optional[str] = None,
    ttl_seconds: int = DOWNLOAD_URL_TTL_SECONDS,
) -> str:
    """Generate a presigned GET URL for `object_key` that expires in ttl_seconds.

    Default TTL is 72 hours (259200 seconds) per spec Section 6.
    """
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")

    bucket_name = _resolve_bucket(bucket)
    client = _r2_client()
    return client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket_name, "Key": object_key},
        ExpiresIn=ttl_seconds,
    )


# ---------------------------------------------------------------------------
# delete_r2_object — used by refund handler in Session 6
# ---------------------------------------------------------------------------
def delete_r2_object(object_key: str, *, bucket: Optional[str] = None) -> None:
    """Delete an R2 object. Used to revoke access on refund."""
    bucket_name = _resolve_bucket(bucket)
    client = _r2_client()
    client.delete_object(Bucket=bucket_name, Key=object_key)


# ---------------------------------------------------------------------------
# Session 7 orchestration stubs — wired in Session 7 to Postmark
# ---------------------------------------------------------------------------
def build_and_deliver_zip(purchase) -> None:
    """Stub: in Session 7 this will resolve catalog → build zip → upload →
    sign URL → write fields to purchase row → send Postmark email.

    For Session 6, just logs that delivery would have happened so the
    end-to-end webhook → purchase row → delivery handoff is wired and
    testable without Postmark dependencies.
    """
    logger.info(
        "build_and_deliver_zip STUB called — purchase_id=%s tier_id=%s",
        getattr(purchase, "purchase_id", "unknown"),
        getattr(purchase, "tier_id", "unknown"),
    )


def notify_kyle_new_purchase(purchase, lead) -> None:
    """Stub: Session 7 sends Postmark emails to Kyle and the buyer."""
    logger.info(
        "notify_kyle_new_purchase STUB called — purchase_id=%s lead_id=%s tier_id=%s",
        getattr(purchase, "purchase_id", "unknown"),
        getattr(lead, "lead_id", "unknown"),
        getattr(purchase, "tier_id", "unknown"),
    )


def notify_kyle_refund(purchase) -> None:
    """Stub: Session 7 sends Postmark refund alert to Kyle."""
    logger.info(
        "notify_kyle_refund STUB called — purchase_id=%s tier_id=%s",
        getattr(purchase, "purchase_id", "unknown"),
        getattr(purchase, "tier_id", "unknown"),
    )
