import re

from tools.validators import validate_uscc


OCR_CONFUSIONS = {
    "O": "0",
    "o": "0",
    "I": "1",
    "l": "1",
    "|": "1",
    "S": "5",
}


def repair_fields(fields: dict, validation: dict) -> dict:
    repaired = dict(fields)
    actions = []

    uscc_result = validation.get("unified_social_credit_code", {})
    if not uscc_result.get("valid"):
        candidate, action = repair_uscc(fields.get("unified_social_credit_code", ""))
        if action:
            repaired["unified_social_credit_code"] = candidate
            actions.append(action)

    for key in ["establishment_date", "approval_date"]:
        fixed, changed = repair_date(repaired.get(key, ""))
        if changed:
            actions.append({
                "field": key,
                "original": repaired.get(key, ""),
                "corrected": fixed,
                "reason": "日期字段中 O/o 疑似为数字 0",
                "confidence": 0.86,
            })
            repaired[key] = fixed

    return {"fields": repaired, "actions": actions}


def repair_uscc(value: str) -> tuple[str, dict | None]:
    original = re.sub(r"\s+", "", value)
    candidate = "".join(OCR_CONFUSIONS.get(c, c) for c in original).upper()
    before = validate_uscc(original)
    after = validate_uscc(candidate)

    if original != candidate and (after["valid"] or before["reason"] != after["reason"]):
        return candidate, {
            "field": "unified_social_credit_code",
            "original": original,
            "corrected": candidate,
            "reason": "统一社会信用代码存在常见 OCR 混淆字符，按 O/0、I/1 等规则生成修复候选",
            "validation_before": before,
            "validation_after": after,
            "confidence": 0.9 if after["valid"] else 0.62,
        }
    return value, None


def repair_date(value: str) -> tuple[str, bool]:
    fixed = value.replace("O", "0").replace("o", "0")
    return fixed, fixed != value

