import re


USCC_CHARS = "0123456789ABCDEFGHJKLMNPQRTUWXY"
USCC_WEIGHTS = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]


def validate_fields(fields: dict) -> dict:
    return {
        "unified_social_credit_code": validate_uscc(fields.get("unified_social_credit_code", "")),
        "company_name": required_text(fields.get("company_name", "")),
        "company_type": required_text(fields.get("company_type", "")),
        "registered_capital": validate_capital(fields.get("registered_capital", "")),
        "establishment_date": validate_cn_date(fields.get("establishment_date", "")),
        "approval_date": validate_cn_date(fields.get("approval_date", "")),
    }


def required_text(value: str) -> dict:
    return {"valid": bool(value.strip()), "reason": "required field" if not value.strip() else "ok"}


def validate_capital(value: str) -> dict:
    if not value.strip():
        return {"valid": False, "reason": "missing registered capital"}
    valid = bool(re.search(r"\d+(\.\d+)?\s*(万|万元|人民币|美元)", value))
    return {"valid": valid, "reason": "ok" if valid else "capital format is suspicious"}


def validate_cn_date(value: str) -> dict:
    if not value.strip():
        return {"valid": False, "reason": "missing date"}
    valid = bool(re.search(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", value))
    return {"valid": valid, "reason": "ok" if valid else "date format is suspicious"}


def validate_uscc(value: str) -> dict:
    code = re.sub(r"\s+", "", value.upper())
    if len(code) != 18:
        return {"valid": False, "reason": f"USCC length should be 18, got {len(code)}"}
    invalid_chars = [c for c in code if c not in USCC_CHARS]
    if invalid_chars:
        return {"valid": False, "reason": f"invalid USCC chars: {''.join(sorted(set(invalid_chars)))}"}

    total = sum(USCC_CHARS.index(code[i]) * USCC_WEIGHTS[i] for i in range(17))
    expected = USCC_CHARS[(31 - total % 31) % 31]
    if code[-1] != expected:
        return {"valid": False, "reason": f"checksum mismatch, expected {expected}"}
    return {"valid": True, "reason": "ok"}

