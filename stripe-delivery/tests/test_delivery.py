"""Tests for api/delivery.py — Session 3 scope.

Two layers:
  * Unit tests run in CI with no external dependencies (boto3 is mocked).
  * Integration tests hit the real R2 dev bucket and are skipped unless the
    R2_* env vars are set. Run locally with a .env.test file or exported
    env vars before pytest.
"""

from __future__ import annotations

import os
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from api import delivery
from api.delivery import (
    DOWNLOAD_URL_TTL_SECONDS,
    README_FILENAME,
    build_zip,
    sign_download_url,
    upload_to_r2,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dummy_deliverable"

R2_INTEGRATION_ENV_VARS = (
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
)
_r2_credentials_present = all(os.getenv(name) for name in R2_INTEGRATION_ENV_VARS)
r2_integration = pytest.mark.skipif(
    not _r2_credentials_present,
    reason="R2 credentials not set — integration test skipped (run locally with .env.test)",
)


# ---------------------------------------------------------------------------
# build_zip — unit tests
# ---------------------------------------------------------------------------
def test_build_zip_includes_readme(tmp_path: Path) -> None:
    purchase_id = "pi_test_readme"
    zip_path = build_zip(FIXTURE_DIR, purchase_id)
    assert zip_path.exists()

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert README_FILENAME in names
        readme_bytes = zf.read(README_FILENAME).decode("utf-8")

    assert purchase_id in readme_bytes
    assert "support@sidebarcode.com" in readme_bytes
    assert "License" in readme_bytes


def test_build_zip_preserves_folder_structure() -> None:
    purchase_id = "pi_test_structure"
    zip_path = build_zip(FIXTURE_DIR, purchase_id)

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())

    # Top-level folder name should be preserved (parking lot default).
    assert "dummy_deliverable/installation_notes.txt" in names
    assert "dummy_deliverable/sample_brief.pdf" in names
    assert "dummy_deliverable/nested_skill/SKILL.md" in names
    # README is at the zip root, not inside the folder.
    assert "README.txt" in names


def test_build_zip_raises_for_missing_source(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_zip(tmp_path / "does_not_exist", "pi_missing")


# ---------------------------------------------------------------------------
# sign_download_url — unit test (mocked boto3 client)
# ---------------------------------------------------------------------------
def test_sign_download_url_calls_boto_with_correct_params(monkeypatch) -> None:
    fake_client = MagicMock()
    fake_client.generate_presigned_url.return_value = "https://example/signed-url"
    monkeypatch.setattr(delivery, "_r2_client", lambda: fake_client)
    monkeypatch.setenv("R2_BUCKET", "sidebarcode-dev")

    url = sign_download_url("test/key.zip", ttl_seconds=600)

    assert url == "https://example/signed-url"
    fake_client.generate_presigned_url.assert_called_once_with(
        ClientMethod="get_object",
        Params={"Bucket": "sidebarcode-dev", "Key": "test/key.zip"},
        ExpiresIn=600,
    )


def test_sign_download_url_default_ttl_is_72_hours(monkeypatch) -> None:
    assert DOWNLOAD_URL_TTL_SECONDS == 72 * 60 * 60

    fake_client = MagicMock()
    fake_client.generate_presigned_url.return_value = "https://example/signed-url"
    monkeypatch.setattr(delivery, "_r2_client", lambda: fake_client)
    monkeypatch.setenv("R2_BUCKET", "sidebarcode-dev")

    sign_download_url("test/key.zip")

    args = fake_client.generate_presigned_url.call_args
    assert args.kwargs["ExpiresIn"] == 72 * 60 * 60


def test_sign_download_url_rejects_negative_ttl(monkeypatch) -> None:
    monkeypatch.setenv("R2_BUCKET", "sidebarcode-dev")
    with pytest.raises(ValueError):
        sign_download_url("test/key.zip", ttl_seconds=0)


# ---------------------------------------------------------------------------
# upload_to_r2 — unit test (mocked boto3 client)
# ---------------------------------------------------------------------------
def test_upload_to_r2_calls_boto_upload_file(monkeypatch, tmp_path: Path) -> None:
    fake_zip = tmp_path / "fake.zip"
    fake_zip.write_bytes(b"PK\x03\x04 not a real zip but a real file")

    fake_client = MagicMock()
    monkeypatch.setattr(delivery, "_r2_client", lambda: fake_client)
    monkeypatch.setenv("R2_BUCKET", "sidebarcode-dev")

    result = upload_to_r2(fake_zip, "test/key.zip")

    assert result == "test/key.zip"
    fake_client.upload_file.assert_called_once()
    call_kwargs = fake_client.upload_file.call_args.kwargs
    assert call_kwargs["Bucket"] == "sidebarcode-dev"
    assert call_kwargs["Key"] == "test/key.zip"
    assert call_kwargs["ExtraArgs"]["ContentType"] == "application/zip"
    fake_client.put_object_tagging.assert_called_once()


def test_upload_to_r2_raises_for_missing_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("R2_BUCKET", "sidebarcode-dev")
    monkeypatch.setattr(delivery, "_r2_client", lambda: MagicMock())
    with pytest.raises(FileNotFoundError):
        upload_to_r2(tmp_path / "missing.zip", "test/key.zip")


# ---------------------------------------------------------------------------
# Integration tests — gated on R2 env vars
# ---------------------------------------------------------------------------
@r2_integration
def test_upload_to_r2_roundtrip_against_dev_bucket(tmp_path: Path) -> None:
    """Full upload + presign + download cycle against the real R2 dev bucket."""
    import urllib.request

    bucket = os.environ.get("R2_BUCKET_DEV") or "sidebarcode-dev"
    purchase_id = f"sp2_session3_{uuid.uuid4().hex[:8]}"
    zip_path = build_zip(FIXTURE_DIR, purchase_id)
    object_key = f"sp2-session3-tests/{purchase_id}.zip"

    try:
        upload_to_r2(zip_path, object_key, bucket=bucket)
        url = sign_download_url(object_key, bucket=bucket, ttl_seconds=300)
        assert url.startswith("https://")

        with urllib.request.urlopen(url) as resp:  # noqa: S310 — trusted test URL
            assert resp.status == 200
            downloaded = resp.read()
        assert downloaded == zip_path.read_bytes()
    finally:
        # Cleanup so dev bucket doesn't accumulate test objects.
        delivery.delete_r2_object(object_key, bucket=bucket)


@r2_integration
def test_signed_url_returns_404_after_object_deleted(tmp_path: Path) -> None:
    """After delete_r2_object, the presigned URL must return 404."""
    import urllib.error
    import urllib.request

    bucket = os.environ.get("R2_BUCKET_DEV") or "sidebarcode-dev"
    purchase_id = f"sp2_session3_{uuid.uuid4().hex[:8]}"
    zip_path = build_zip(FIXTURE_DIR, purchase_id)
    object_key = f"sp2-session3-tests/{purchase_id}.zip"

    upload_to_r2(zip_path, object_key, bucket=bucket)
    url = sign_download_url(object_key, bucket=bucket, ttl_seconds=300)
    delivery.delete_r2_object(object_key, bucket=bucket)

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(url)  # noqa: S310 — trusted test URL
    assert exc_info.value.code in (403, 404)
