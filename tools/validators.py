import re


USCC_CHARS = "0123456789ABCDEFGHJKLMNPQRTUWXY"
USCC_WEIGHTS = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]


def validate_fields(fields: dict) -> dict:
    """对关键营业执照字段执行规则校验。"""
    return {
        "统一社会信用代码": validate_uscc(fields.get("统一社会信用代码", "")),
        "名称": required_text(fields.get("名称", "")),
        "类型": required_text(fields.get("类型", "")),
        "注册资本": validate_capital(fields.get("注册资本", "")),
        "成立日期": validate_cn_date(fields.get("成立日期", "")),
        "核准日期": validate_cn_date(fields.get("核准日期", "")),
    }


def required_text(value: str) -> dict:
    """校验必填文本字段是否为空。"""
    return {"valid": bool(value.strip()), "reason": "必填字段为空" if not value.strip() else "通过"}


def validate_capital(value: str) -> dict:
    """校验注册资本或出资额是否包含金额和币种/单位。"""
    if not value.strip():
        return {"valid": False, "reason": "缺少注册资本或出资额"}
    valid = bool(re.search(r"\d+(\.\d+)?\s*(万|万元|人民币|美元)", value))
    return {"valid": valid, "reason": "通过" if valid else "注册资本或出资额格式可疑"}


def validate_cn_date(value: str) -> dict:
    """校验中文日期是否符合“YYYY年MM月DD日”格式。"""
    if not value.strip():
        return {"valid": False, "reason": "缺少日期"}
    valid = bool(re.search(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", value))
    return {"valid": valid, "reason": "通过" if valid else "日期格式可疑"}


def validate_uscc(value: str) -> dict:
    """校验统一社会信用代码长度、字符集和校验位。"""
    code = re.sub(r"\s+", "", value.upper())
    if len(code) != 18:
        return {"valid": False, "reason": f"统一社会信用代码应为 18 位，当前为 {len(code)} 位"}
    invalid_chars = [c for c in code if c not in USCC_CHARS]
    if invalid_chars:
        return {"valid": False, "reason": f"统一社会信用代码包含非法字符：{''.join(sorted(set(invalid_chars)))}"}

    total = sum(USCC_CHARS.index(code[i]) * USCC_WEIGHTS[i] for i in range(17))
    expected = USCC_CHARS[(31 - total % 31) % 31]
    if code[-1] != expected:
        return {"valid": False, "reason": f"统一社会信用代码校验位不匹配，期望为 {expected}"}
    return {"valid": True, "reason": "通过"}
