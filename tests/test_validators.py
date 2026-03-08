"""
Unit tests for services/validators.py — all centralized validation functions.
"""
import datetime
import pytest
from services.validators import (
    validate_required, validate_gst, validate_phone, validate_phone_required,
    validate_email, validate_positive_float, validate_percentage,
    validate_batch_id, validate_password, validate_username,
    validate_temp_range, validate_date_order, collect_errors
)


# ─── validate_required ───

class TestValidateRequired:
    def test_empty_string(self):
        valid, msg = validate_required("", "Name")
        assert not valid
        assert "required" in msg.lower()

    def test_whitespace_only(self):
        valid, msg = validate_required("   ", "Name")
        assert not valid

    def test_none(self):
        valid, msg = validate_required(None, "Name")
        assert not valid

    def test_valid(self):
        valid, msg = validate_required("Hello", "Name")
        assert valid
        assert msg == ""


# ─── validate_gst ───

class TestValidateGST:
    def test_empty_is_optional(self):
        valid, msg = validate_gst("")
        assert valid

    def test_none_is_optional(self):
        valid, msg = validate_gst(None)
        assert valid

    def test_valid_gst(self):
        valid, msg = validate_gst("33AAAAA0000A1Z5")
        assert valid

    def test_valid_gst_lowercase_normalized(self):
        valid, msg = validate_gst("33aaaaa0000a1z5")
        assert valid  # auto-uppercased

    def test_invalid_gst_too_short(self):
        valid, msg = validate_gst("33AAAA")
        assert not valid
        assert "Invalid GST" in msg

    def test_invalid_gst_wrong_format(self):
        valid, msg = validate_gst("ABCDEFGHIJKLMNO")
        assert not valid


# ─── validate_phone ───

class TestValidatePhone:
    def test_empty_is_optional(self):
        valid, msg = validate_phone("")
        assert valid

    def test_valid_10_digit(self):
        valid, msg = validate_phone("9876543210")
        assert valid

    def test_valid_with_plus91(self):
        valid, msg = validate_phone("+91 9876543210")
        assert valid

    def test_valid_with_leading_zero(self):
        valid, msg = validate_phone("09876543210")
        assert valid

    def test_invalid_starts_with_5(self):
        valid, msg = validate_phone("5876543210")
        assert not valid

    def test_invalid_too_short(self):
        valid, msg = validate_phone("98765")
        assert not valid

    def test_invalid_too_long(self):
        valid, msg = validate_phone("98765432101")
        assert not valid

    def test_invalid_letters(self):
        valid, msg = validate_phone("abcdefghij")
        assert not valid


# ─── validate_phone_required ───

class TestValidatePhoneRequired:
    def test_empty_rejected(self):
        valid, msg = validate_phone_required("")
        assert not valid
        assert "required" in msg.lower()

    def test_valid(self):
        valid, msg = validate_phone_required("9876543210")
        assert valid


# ─── validate_email ───

class TestValidateEmail:
    def test_empty_is_optional(self):
        valid, msg = validate_email("")
        assert valid

    def test_valid_email(self):
        valid, msg = validate_email("user@example.com")
        assert valid

    def test_valid_complex_email(self):
        valid, msg = validate_email("user.name+tag@sub.domain.com")
        assert valid

    def test_invalid_no_at(self):
        valid, msg = validate_email("userexample.com")
        assert not valid

    def test_invalid_no_tld(self):
        valid, msg = validate_email("user@")
        assert not valid


# ─── validate_positive_float ───

class TestValidatePositiveFloat:
    def test_empty_defaults_to_zero(self):
        valid, msg, val = validate_positive_float("", "Cost")
        assert valid
        assert val == 0.0

    def test_valid_number(self):
        valid, msg, val = validate_positive_float("150.5", "Cost")
        assert valid
        assert val == 150.5

    def test_negative_rejected(self):
        valid, msg, val = validate_positive_float("-10", "Cost")
        assert not valid
        assert val is None

    def test_zero_allowed_by_default(self):
        valid, msg, val = validate_positive_float("0", "Cost")
        assert valid
        assert val == 0.0

    def test_zero_rejected_when_disallowed(self):
        valid, msg, val = validate_positive_float("0", "Cost", allow_zero=False)
        assert not valid

    def test_non_numeric(self):
        valid, msg, val = validate_positive_float("abc", "Cost")
        assert not valid
        assert val is None


# ─── validate_percentage ───

class TestValidatePercentage:
    def test_valid(self):
        valid, msg, val = validate_percentage("18", "Tax")
        assert valid
        assert val == 18.0

    def test_over_100(self):
        valid, msg, val = validate_percentage("101", "Tax")
        assert not valid

    def test_zero(self):
        valid, msg, val = validate_percentage("0", "Tax")
        assert valid
        assert val == 0.0

    def test_boundary_100(self):
        valid, msg, val = validate_percentage("100", "Tax")
        assert valid
        assert val == 100.0


# ─── validate_batch_id ───

class TestValidateBatchID:
    def test_empty_rejected(self):
        valid, msg = validate_batch_id("")
        assert not valid
        assert "required" in msg.lower()

    def test_valid_alphanumeric(self):
        valid, msg = validate_batch_id("BATCH-2026-001")
        assert valid

    def test_valid_with_underscore(self):
        valid, msg = validate_batch_id("batch_001")
        assert valid

    def test_invalid_special_chars(self):
        valid, msg = validate_batch_id("batch@001")
        assert not valid

    def test_invalid_spaces(self):
        valid, msg = validate_batch_id("batch 001")
        assert not valid


# ─── validate_password ───

class TestValidatePassword:
    def test_empty_rejected(self):
        valid, msg = validate_password("")
        assert not valid
        assert "required" in msg.lower()

    def test_none_rejected(self):
        valid, msg = validate_password(None)
        assert not valid

    def test_too_short(self):
        valid, msg = validate_password("abc")
        assert not valid
        assert "4 characters" in msg

    def test_exactly_4(self):
        valid, msg = validate_password("abcd")
        assert valid

    def test_long_password(self):
        valid, msg = validate_password("securepassword123")
        assert valid


# ─── validate_username ───

class TestValidateUsername:
    def test_empty_rejected(self):
        valid, msg = validate_username("")
        assert not valid

    def test_too_short(self):
        valid, msg = validate_username("ab")
        assert not valid
        assert "3 characters" in msg

    def test_special_chars_rejected(self):
        valid, msg = validate_username("user@name")
        assert not valid
        assert "letters, numbers" in msg

    def test_spaces_rejected(self):
        valid, msg = validate_username("user name")
        assert not valid

    def test_valid_alphanumeric(self):
        valid, msg = validate_username("admin_user1")
        assert valid

    def test_exactly_3_chars(self):
        valid, msg = validate_username("abc")
        assert valid


# ─── validate_temp_range ───

class TestValidateTempRange:
    def test_valid_range(self):
        valid, msg = validate_temp_range(5.0, 35.0)
        assert valid

    def test_equal_temps(self):
        valid, msg = validate_temp_range(25.0, 25.0)
        assert valid

    def test_min_greater_than_max(self):
        valid, msg = validate_temp_range(40.0, 10.0)
        assert not valid
        assert "cannot be greater" in msg

    def test_none_values_ok(self):
        valid, msg = validate_temp_range(None, None)
        assert valid

    def test_negative_range_valid(self):
        valid, msg = validate_temp_range(-20.0, -5.0)
        assert valid


# ─── validate_date_order ───

class TestValidateDateOrder:
    def test_valid_order(self):
        start = datetime.date(2025, 1, 1)
        end = datetime.date(2026, 1, 1)
        valid, msg = validate_date_order(start, end)
        assert valid

    def test_same_date(self):
        d = datetime.date(2025, 6, 15)
        valid, msg = validate_date_order(d, d)
        assert valid

    def test_start_after_end(self):
        start = datetime.date(2026, 6, 1)
        end = datetime.date(2025, 1, 1)
        valid, msg = validate_date_order(start, end, "Manufacture Date", "Expiry Date")
        assert not valid
        assert "Manufacture Date" in msg

    def test_none_values_ok(self):
        valid, msg = validate_date_order(None, None)
        assert valid


# ─── collect_errors ───

class TestCollectErrors:
    def test_all_valid(self):
        valid, msg = collect_errors([
            (True, ""),
            (True, ""),
        ])
        assert valid
        assert msg == ""

    def test_single_error(self):
        valid, msg = collect_errors([
            (True, ""),
            (False, "Name is required."),
        ])
        assert not valid
        assert "Name is required" in msg

    def test_multiple_errors(self):
        valid, msg = collect_errors([
            (False, "Name is required."),
            (False, "Phone is invalid."),
        ])
        assert not valid
        assert "Name is required" in msg
        assert "Phone is invalid" in msg

    def test_empty_list(self):
        valid, msg = collect_errors([])
        assert valid
