"""Delivery pipeline: zip builder, R2 upload, signed URL, Postmark send.

Session 3 scope: build_zip, upload_to_r2, sign_download_url.
Session 7 scope: real build_and_deliver_zip, notify_kyle_new_purchase,
notify_kyle_refund — all wired through Postmark.
"""

from __future__ import annotations

import logging
import os
import tempfile
import traceback
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Postmark template aliases — must match scripts/sync_postmark_templates.py
# ---------------------------------------------------------------------------
TEMPLATE_PRODUCT_DOWNLOAD = "sp2-product-download"
TEMPLATE_CONSULTING_RECEIPT = "sp2-consulting-receipt"
TEMPLATE_KYLE_NEW_CONSULTING = "sp2-kyle-new-consulting-purchase"
TEMPLATE_DELIVERY_FAILURE_ALERT = "sp2-delivery-failure-alert"

DEFAULT_FROM_ADDRESS = "kyle@sidebarcode.com"
DEFAULT_REPLY_TO = "kyle@sidebarcode.com"

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # Side Bar Code/

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
# Postmark client
# ---------------------------------------------------------------------------
def _postmark_client():
    """Lazily build a PostmarkClient. Imported lazily so tests can mock."""
    from postmarker.core import PostmarkClient

    token = os.environ.get("POSTMARK_API_TOKEN")
    if not token:
        raise RuntimeError("POSTMARK_API_TOKEN is not set")
    return PostmarkClient(server_token=token)


def _from_address() -> str:
    return os.environ.get("POSTMARK_FROM_ADDRESS") or DEFAULT_FROM_ADDRESS


def _reply_to() -> str:
    return os.environ.get("POSTMARK_REPLY_TO") or DEFAULT_REPLY_TO


def _kyle_alert_email() -> str:
    return os.environ.get("KYLE_ALERT_EMAIL") or DEFAULT_FROM_ADDRESS


def _send_template_email(
    *,
    template_alias: str,
    to: str,
    template_model: dict[str, Any],
) -> None:
    """Send a Postmark email using a template alias."""
    client = _postmark_client()
    client.emails.send_with_template(
        TemplateAlias=template_alias,
        From=_from_address(),
        To=to,
        ReplyTo=_reply_to(),
        TemplateModel=template_model,
    )
    logger.info("postmark template send ok — alias=%s to=%s", template_alias, to)


def _send_plain_email(*, to: str, subject: str, text_body: str) -> None:
    """Send a plain-text email (used for refund alerts which have no template)."""
    client = _postmark_client()
    client.emails.send(
        From=_from_address(),
        To=to,
        Subject=subject,
        TextBody=text_body,
        ReplyTo=_reply_to(),
    )
    logger.info("postmark plain send ok — to=%s subject=%s", to, subject)


# ---------------------------------------------------------------------------
# Catalog + tier resolution
# ---------------------------------------------------------------------------
def _resolve_delivery_source_path(delivery_source: str) -> Path:
    """Resolve a catalog delivery_source string to an absolute path.

    delivery_source values are expressed relative to the repo root, e.g.:
      stripe-delivery/tests/fixtures/dummy_deliverable/
      Product Catalog/products/01_parser_trial/_customer_deliverables/
    """
    return (_REPO_ROOT / delivery_source).resolve()


def _format_amount(amount_cents: int, currency: str) -> str:
    return f"${amount_cents / 100:.2f} {currency.upper()}"


def _stripe_dashboard_link(payment_intent_id: Optional[str], charge_id: Optional[str]) -> str:
    if payment_intent_id:
        return f"https://dashboard.stripe.com/test/payments/{payment_intent_id}"
    if charge_id:
        return f"https://dashboard.stripe.com/test/payments/{charge_id}"
    return "https://dashboard.stripe.com/test/payments"


# ---------------------------------------------------------------------------
# build_and_deliver_zip — the zip_download branch
# ---------------------------------------------------------------------------
def build_and_deliver_zip(purchase) -> None:
    """Build → upload → sign → email → mark delivered.

    On any exception inside the try block: write a delivery_failures row,
    send Kyle a delivery failure alert, then re-raise so Stripe retries
    the webhook via its built-in exponential backoff.
    """
    # Imported here to avoid circular imports (delivery <-> crm <-> webhook).
    from api import crm
    from api.catalog import load_catalog_index

    try:
        catalog = load_catalog_index()
        tier = catalog.get(purchase.tier_id)
        if not tier.delivery_source:
            raise RuntimeError(f"tier {tier.tier_id} has no delivery_source")

        source_path = _resolve_delivery_source_path(tier.delivery_source)
        if not source_path.exists():
            raise FileNotFoundError(f"delivery_source not found on disk: {source_path}")

        zip_path = build_zip(source_path, purchase.purchase_id)
        try:
            object_key = f"{tier.tier_id}/{purchase.purchase_id}.zip"
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=DOWNLOAD_URL_TTL_SECONDS)
            upload_to_r2(zip_path, object_key, expires_at=expires_at)
            download_url = sign_download_url(object_key, ttl_seconds=DOWNLOAD_URL_TTL_SECONDS)
        finally:
            # Clean up the local temp zip even if upload failed.
            try:
                zip_path.unlink(missing_ok=True)
                zip_path.parent.rmdir()
            except OSError:
                pass

        crm.update_purchase_status(
            purchase.purchase_id,
            crm.PurchaseStatus.DELIVERED,
            zip_object_key=object_key,
            download_url_expires_at=expires_at.isoformat(),
        )

        _send_template_email(
            template_alias=TEMPLATE_PRODUCT_DOWNLOAD,
            to=purchase.buyer_email,
            template_model={
                "buyer_name": purchase.buyer_name or "there",
                "tier_name": tier.stripe_product_name,
                "tier_id": tier.tier_id,
                "purchase_id": purchase.purchase_id,
                "download_url": download_url,
                "expires_at": expires_at.isoformat(),
                "purchased_at": purchase.created_at,
                "support_email": _from_address(),
            },
        )
        logger.info(
            "build_and_deliver_zip success — purchase_id=%s tier_id=%s",
            purchase.purchase_id, tier.tier_id,
        )

    except Exception as exc:
        tb = traceback.format_exc()
        logger.exception("build_and_deliver_zip FAILED — purchase_id=%s", purchase.purchase_id)
        try:
            crm.record_delivery_failure(
                purchase.purchase_id,
                error_msg=str(exc),
                traceback=tb,
            )
        except Exception:
            logger.exception("failed to record delivery_failure row")

        try:
            _send_template_email(
                template_alias=TEMPLATE_DELIVERY_FAILURE_ALERT,
                to=_kyle_alert_email(),
                template_model={
                    "purchase_id": purchase.purchase_id,
                    "tier_id": purchase.tier_id,
                    "buyer_email": purchase.buyer_email,
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": str(exc),
                    "traceback": tb,
                    "render_logs_link": "https://dashboard.render.com",
                    "stripe_event_link": _stripe_dashboard_link(
                        purchase.stripe_payment_intent_id, purchase.stripe_charge_id
                    ),
                },
            )
        except Exception:
            logger.exception("failed to send delivery_failure_alert email")

        raise  # re-raise so Stripe retries the webhook


# ---------------------------------------------------------------------------
# notify_kyle_new_purchase — the notify_kyle branch
# ---------------------------------------------------------------------------
def notify_kyle_new_purchase(purchase, lead) -> None:
    """Send Kyle the alert email and the buyer the consulting receipt.

    No exception suppression — if either email fails, the webhook handler
    surfaces a 500 and Stripe retries. Lead row is already inserted at
    this point and is idempotent on charge_id, so retries don't duplicate.
    """
    from api.catalog import load_catalog_index

    catalog = load_catalog_index()
    tier = catalog.get(purchase.tier_id)
    scheduling_link = tier.scheduling_link or "https://cal.com/kylebanfield"

    common = {
        "buyer_name": purchase.buyer_name or "there",
        "buyer_email": purchase.buyer_email,
        "buyer_phone": purchase.buyer_phone or "(not provided)",
        "tier_name": tier.stripe_product_name,
        "tier_id": tier.tier_id,
        "purchase_id": purchase.purchase_id,
        "lead_id": lead.lead_id,
        "amount_formatted": _format_amount(purchase.amount_cents, purchase.currency),
        "scheduling_link": scheduling_link,
        "kyle_email": _from_address(),
        "purchased_at": purchase.created_at,
        "stripe_dashboard_link": _stripe_dashboard_link(
            purchase.stripe_payment_intent_id, purchase.stripe_charge_id
        ),
    }

    # Buyer-facing receipt
    _send_template_email(
        template_alias=TEMPLATE_CONSULTING_RECEIPT,
        to=purchase.buyer_email,
        template_model=common,
    )

    # Kyle-facing alert
    _send_template_email(
        template_alias=TEMPLATE_KYLE_NEW_CONSULTING,
        to=_kyle_alert_email(),
        template_model=common,
    )

    logger.info(
        "notify_kyle_new_purchase success — purchase_id=%s lead_id=%s",
        purchase.purchase_id, lead.lead_id,
    )


# ---------------------------------------------------------------------------
# notify_kyle_refund — internal Kyle alert, plain text (no template)
# ---------------------------------------------------------------------------
def notify_kyle_refund(purchase) -> None:
    subject = f"REFUND: {purchase.tier_id} ({_format_amount(purchase.amount_cents, purchase.currency)})"
    body = (
        f"A refund was processed in SP2.\n\n"
        f"Purchase ID:  {purchase.purchase_id}\n"
        f"Tier:         {purchase.tier_id}\n"
        f"Buyer:        {purchase.buyer_email}\n"
        f"Amount:       {_format_amount(purchase.amount_cents, purchase.currency)}\n"
        f"Charge ID:    {purchase.stripe_charge_id or '(none)'}\n"
        f"Payment IID:  {purchase.stripe_payment_intent_id or '(none)'}\n"
        f"Originally:   {purchase.created_at}\n\n"
        f"Stripe dashboard: "
        f"{_stripe_dashboard_link(purchase.stripe_payment_intent_id, purchase.stripe_charge_id)}\n\n"
        f"Status was already set to 'refunded' in SQLite. "
        f"R2 object {'was deleted' if purchase.zip_object_key else 'was not present'}.\n"
    )
    _send_plain_email(to=_kyle_alert_email(), subject=subject, text_body=body)
    logger.info("notify_kyle_refund sent — purchase_id=%s", purchase.purchase_id)
