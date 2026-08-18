import re
from datetime import date


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^[0-9+().\-\s]{7,30}$")


def validate_contact(payload):
    if not isinstance(payload, dict):
        return None, {"form": "The request body must be a JSON object."}

    first_name = str(payload.get("first_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()
    company = str(payload.get("company", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    birthday_value = str(payload.get("birthday", "")).strip()
    raw_emails = payload.get("emails", [])
    errors = {}

    if not first_name:
        errors["first_name"] = "First name is required."
    elif len(first_name) > 80:
        errors["first_name"] = "First name must be 80 characters or fewer."

    if not last_name:
        errors["last_name"] = "Last name is required."
    elif len(last_name) > 80:
        errors["last_name"] = "Last name must be 80 characters or fewer."

    if len(company) > 120:
        errors["company"] = "Company must be 120 characters or fewer."

    if phone and not PHONE_PATTERN.fullmatch(phone):
        errors["phone"] = "Enter a valid phone number."

    birthday = None
    if birthday_value:
        try:
            birthday = date.fromisoformat(birthday_value)
        except ValueError:
            errors["birthday"] = "Enter a valid birthday."
        else:
            if birthday > date.today():
                errors["birthday"] = "Birthday cannot be in the future."

    if not isinstance(raw_emails, list):
        errors["emails"] = "Emails must be provided as a list."
        raw_emails = []

    # Lowercasing makes duplicate detection case-insensitive.
    emails = []
    seen = set()
    for index, value in enumerate(raw_emails):
        address = str(value).strip().lower()
        if not address:
            continue
        if len(address) > 254 or not EMAIL_PATTERN.fullmatch(address):
            errors.setdefault("email_fields", {})[str(index)] = (
                "Enter a valid email address."
            )
            continue
        if address in seen:
            errors.setdefault("email_fields", {})[str(index)] = (
                "This email is already listed."
            )
            continue
        seen.add(address)
        emails.append(address)

    if errors:
        return None, errors

    return {
        "first_name": first_name,
        "last_name": last_name,
        "company": company or None,
        "phone": phone or None,
        "birthday": birthday,
        "emails": emails,
    }, None
