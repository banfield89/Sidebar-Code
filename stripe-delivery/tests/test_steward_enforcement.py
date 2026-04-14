"""Unit tests for api/steward/enforcement.py — CHDB separation hard rule.

The CHDB Law inbox is hard-prohibited in Sidebar Code. These tests assert
that every documented enforcement helper rejects any payload, recipient,
or buyer_email that touches @chdblaw.com (case-insensitive), and that
the rejection raises the specific ChdbSeparationViolation exception.

There is no override flag. These tests should NEVER be marked xfail or
relaxed without a new spec.
"""

from __future__ import annotations

import pytest

from api.steward.enforcement import (
    ChdbSeparationViolation,
    contains_chdb,
    enforce_inbound,
    enforce_lead_email,
    enforce_outbound,
)


# ---------------------------------------------------------------------------
# contains_chdb — recursive scanner
# ---------------------------------------------------------------------------
class TestContainsChdb:
    def test_string_with_chdb_returns_true(self) -> None:
        assert contains_chdb("kyle@chdblaw.com") is True

    def test_string_without_chdb_returns_false(self) -> None:
        assert contains_chdb("kyle@sidebarcode.com") is False

    def test_case_insensitive(self) -> None:
        assert contains_chdb("KYLE@CHDBLAW.COM") is True
        assert contains_chdb("Kyle@CHDBlaw.com") is True
        assert contains_chdb("ChdbLaw.Com") is True

    def test_substring_in_longer_string(self) -> None:
        assert contains_chdb("Reply <reply+kyle@chdblaw.com>") is True

    def test_dict_nested_value(self) -> None:
        payload = {"From": "kyle@sidebarcode.com", "ReplyTo": "kyle@chdblaw.com"}
        assert contains_chdb(payload) is True

    def test_list_nested_value(self) -> None:
        headers = [
            {"Name": "Subject", "Value": "Test"},
            {"Name": "Reply-To", "Value": "kyle@chdblaw.com"},
        ]
        assert contains_chdb(headers) is True

    def test_deeply_nested_value(self) -> None:
        payload = {
            "From": "client@example.com",
            "Headers": [
                {"Name": "X-Forward", "Value": "via kyle@chdblaw.com"},
            ],
        }
        assert contains_chdb(payload) is True

    def test_none_returns_false(self) -> None:
        assert contains_chdb(None) is False

    def test_int_returns_false(self) -> None:
        assert contains_chdb(42) is False

    def test_empty_string_returns_false(self) -> None:
        assert contains_chdb("") is False

    def test_clean_payload_returns_false(self) -> None:
        payload = {
            "From": "buyer@example.com",
            "To": "kyle@sidebarcode.com",
            "Subject": "Question about Foundation tier",
            "TextBody": "Hi Kyle, what's included?",
            "Headers": [{"Name": "Message-ID", "Value": "<abc123@example.com>"}],
        }
        assert contains_chdb(payload) is False


# ---------------------------------------------------------------------------
# enforce_inbound — wraps contains_chdb for inbound payloads
# ---------------------------------------------------------------------------
class TestEnforceInbound:
    def test_clean_payload_passes(self) -> None:
        payload = {
            "From": "buyer@example.com",
            "To": "kyle@sidebarcode.com",
            "Subject": "Hello",
        }
        enforce_inbound(payload)  # should not raise

    def test_chdb_in_from_raises(self) -> None:
        payload = {"From": "kyle@chdblaw.com", "To": "kyle@sidebarcode.com"}
        with pytest.raises(ChdbSeparationViolation):
            enforce_inbound(payload)

    def test_chdb_in_to_raises(self) -> None:
        payload = {"From": "buyer@example.com", "To": "kyle@chdblaw.com"}
        with pytest.raises(ChdbSeparationViolation):
            enforce_inbound(payload)

    def test_chdb_in_cc_raises(self) -> None:
        payload = {
            "From": "buyer@example.com",
            "To": "kyle@sidebarcode.com",
            "Cc": "associate@chdblaw.com",
        }
        with pytest.raises(ChdbSeparationViolation):
            enforce_inbound(payload)

    def test_chdb_in_bcc_raises(self) -> None:
        payload = {
            "From": "buyer@example.com",
            "To": "kyle@sidebarcode.com",
            "Bcc": "kyle@chdblaw.com",
        }
        with pytest.raises(ChdbSeparationViolation):
            enforce_inbound(payload)

    def test_chdb_in_reply_to_raises(self) -> None:
        payload = {
            "From": "buyer@example.com",
            "To": "kyle@sidebarcode.com",
            "ReplyTo": "kyle@chdblaw.com",
        }
        with pytest.raises(ChdbSeparationViolation):
            enforce_inbound(payload)

    def test_chdb_in_headers_array_raises(self) -> None:
        payload = {
            "From": "buyer@example.com",
            "To": "kyle@sidebarcode.com",
            "Headers": [
                {"Name": "Reply-To", "Value": "kyle@chdblaw.com"},
            ],
        }
        with pytest.raises(ChdbSeparationViolation):
            enforce_inbound(payload)

    def test_chdb_case_insensitive_raises(self) -> None:
        payload = {"From": "KYLE@CHDBLAW.COM", "To": "kyle@sidebarcode.com"}
        with pytest.raises(ChdbSeparationViolation):
            enforce_inbound(payload)


# ---------------------------------------------------------------------------
# enforce_outbound — single recipient string
# ---------------------------------------------------------------------------
class TestEnforceOutbound:
    def test_clean_recipient_passes(self) -> None:
        enforce_outbound("buyer@example.com")

    def test_sidebarcode_recipient_passes(self) -> None:
        enforce_outbound("kyle@sidebarcode.com")

    def test_none_recipient_passes(self) -> None:
        enforce_outbound(None)

    def test_chdb_recipient_raises(self) -> None:
        with pytest.raises(ChdbSeparationViolation):
            enforce_outbound("kyle@chdblaw.com")

    def test_chdb_uppercase_raises(self) -> None:
        with pytest.raises(ChdbSeparationViolation):
            enforce_outbound("KYLE@CHDBLAW.COM")

    def test_chdb_substring_in_display_name_raises(self) -> None:
        with pytest.raises(ChdbSeparationViolation):
            enforce_outbound('"Kyle" <kyle@chdblaw.com>')


# ---------------------------------------------------------------------------
# enforce_lead_email — used as a hardening pass on crm.insert_lead
# ---------------------------------------------------------------------------
class TestEnforceLeadEmail:
    def test_clean_email_passes(self) -> None:
        enforce_lead_email("buyer@example.com")

    def test_none_passes(self) -> None:
        enforce_lead_email(None)

    def test_chdb_raises(self) -> None:
        with pytest.raises(ChdbSeparationViolation):
            enforce_lead_email("kyle@chdblaw.com")

    def test_chdb_subdomain_or_substring_raises(self) -> None:
        with pytest.raises(ChdbSeparationViolation):
            enforce_lead_email("kyle@mail.chdblaw.com")
