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
    """根据规则校验结果修复可确定的 OCR 字符混淆。"""
    repaired = dict(fields)
    actions = []

    uscc_result = validation.get("统一社会信用代码", {})
    if not uscc_result.get("valid"):
        candidate, action = repair_uscc(fields.get("统一社会信用代码", ""))
        if action:
            repaired["统一社会信用代码"] = candidate
            actions.append(action)

    for key in ["成立日期", "核准日期"]:
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
    """修复统一社会信用代码中的 O/0、I/1 等常见混淆字符。"""
    original = re.sub(r"\s+", "", value)
    candidate = "".join(OCR_CONFUSIONS.get(c, c) for c in original).upper()
    before = validate_uscc(original)
    after = validate_uscc(candidate)

    if original != candidate and (after["valid"] or before["reason"] != after["reason"]):
        return candidate, {
            "field": "统一社会信用代码",
            "original": original,
            "corrected": candidate,
            "reason": "统一社会信用代码存在常见 OCR 混淆字符，按 O/0、I/1 等规则生成修复候选",
            "validation_before": before,
            "validation_after": after,
            "confidence": 0.9 if after["valid"] else 0.62,
        }
    return value, None


def repair_date(value: str) -> tuple[str, bool]:
    """修复日期字段中把数字 0 识别成字母 O 的问题。"""
    fixed = value.replace("O", "0").replace("o", "0")
    return fixed, fixed != value
