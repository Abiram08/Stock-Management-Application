"""
Centralized input validation utilities for all form dialogs.
Each validator returns a tuple: (is_valid: bool, error_message: str)
For numeric validators, returns: (is_valid: bool, error_message: str, parsed_value: float|None)
"""
import re


def validate_required(value, field_name):
    """Check that a field is not empty after stripping whitespace."""
    if not value or not value.strip():
        return False, f"{field_name} is required."
    return True, ""


def validate_gst(value):
    """
    Validate Indian GST Number format (optional field).
    Format: 2-digit state code + 10-char PAN + 1 entity code + 'Z' + 1 checksum
    Example: 33AAAAA0000A1Z5
    """
    if not value or not value.strip():
        return True, ""  # Optional field

    value = value.strip().upper()
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    if not re.match(pattern, value):
        return False, (
            "Invalid GST Number format.\n"
            "Expected: 15 characters (e.g., 33AAAAA0000A1Z5)\n"
            "Format: [2-digit state][5 letters][4 digits][1 letter][1 alphanumeric]Z[1 alphanumeric]"
        )
    return True, ""


def validate_phone(value):
    """
    Validate Indian phone number (optional field).
    Accepts: 10 digits starting with 6-9, with optional +91 prefix.
    """
    if not value or not value.strip():
        return True, ""  # Optional field

    cleaned = value.strip().replace(" ", "").replace("-", "")

    # Remove +91 prefix if present
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]

    # Remove leading 0 if present
    if cleaned.startswith("0"):
        cleaned = cleaned[1:]

    if not re.match(r'^[6-9]\d{9}$', cleaned):
        return False, (
            "Invalid phone number.\n"
            "Expected: 10-digit Indian mobile number starting with 6-9.\n"
            "Optionally prefixed with +91 (e.g., +91 9876543210 or 9876543210)"
        )
    return True, ""


def validate_phone_required(value, field_name="Phone"):
    """Validate phone number and also ensure it's not empty."""
    valid, msg = validate_required(value, field_name)
    if not valid:
        return False, msg
    return validate_phone(value)


def validate_email(value):
    """
    Validate email format (optional field).
    """
    if not value or not value.strip():
        return True, ""  # Optional field

    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value.strip()):
        return False, "Invalid email address format (e.g., user@example.com)."
    return True, ""


def validate_positive_float(value, field_name, allow_zero=True):
    """
    Validate that value is a valid non-negative number.
    Returns (is_valid, error_message, parsed_value).
    """
    if not value or not value.strip():
        return True, "", 0.0  # Default to 0 if empty

    try:
        parsed = float(value.strip())
    except ValueError:
        return False, f"{field_name} must be a valid number.", None

    if parsed < 0:
        return False, f"{field_name} cannot be negative.", None

    if not allow_zero and parsed == 0:
        return False, f"{field_name} must be greater than zero.", None

    return True, "", parsed


def validate_percentage(value, field_name):
    """
    Validate that a value is a valid percentage (0-100).
    Returns (is_valid, error_message, parsed_value).
    """
    valid, msg, parsed = validate_positive_float(value, field_name)
    if not valid:
        return valid, msg, parsed

    if parsed is not None and parsed > 100:
        return False, f"{field_name} must be between 0 and 100.", None

    return True, "", parsed


def validate_batch_id(value):
    """
    Validate batch ID: required, alphanumeric + hyphens + underscores only.
    """
    if not value or not value.strip():
        return False, "Batch ID is required."

    pattern = r'^[A-Za-z0-9\-_]+$'
    if not re.match(pattern, value.strip()):
        return False, "Batch ID can only contain letters, numbers, hyphens, and underscores."

    return True, ""


def validate_password(value, field_name="Password"):
    """
    Validate password strength: required, minimum 4 characters.
    """
    if not value:
        return False, f"{field_name} is required."
    if len(value) < 4:
        return False, f"{field_name} must be at least 4 characters."
    return True, ""


def validate_username(value):
    """
    Validate username: required, min 3 chars, alphanumeric + underscores only.
    """
    if not value or not value.strip():
        return False, "Username is required."

    value = value.strip()
    if len(value) < 3:
        return False, "Username must be at least 3 characters."

    pattern = r'^[A-Za-z0-9_]+$'
    if not re.match(pattern, value):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""


def validate_temp_range(min_val, max_val):
    """
    Validate that min temperature is less than or equal to max temperature.
    Returns (is_valid, error_message).
    """
    if min_val is not None and max_val is not None and min_val > max_val:
        return False, f"Storage Min Temp ({min_val}°C) cannot be greater than Max Temp ({max_val}°C)."
    return True, ""


def validate_date_order(start_date, end_date, start_name="Start Date", end_name="End Date"):
    """
    Validate that start_date is on or before end_date.
    Returns (is_valid, error_message).
    """
    if start_date and end_date and start_date > end_date:
        return False, f"{start_name} cannot be after {end_name}."
    return True, ""


def collect_errors(validations):
    """
    Collect all validation errors from a list of (is_valid, error_msg) tuples.
    Returns (all_valid: bool, combined_error_message: str).
    """
    errors = []
    for valid, msg in validations:
        if not valid:
            errors.append(f"• {msg}")

    if errors:
        return False, "\n".join(errors)
    return True, ""
