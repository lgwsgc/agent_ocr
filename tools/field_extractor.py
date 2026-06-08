import re


FIELD_ALIASES = {
    "unified_social_credit_code": ["统一社会信用代码", "统一信用代码", "社会信用代码"],
    "company_name": ["名称", "企业名称"],
    "company_type": ["类型"],
    "legal_representative": ["法定代表人", "负责人", "经营者", "执行事务合伙人"],
    "registered_capital": ["注册资本", "出资额"],
    "establishment_date": ["成立日期"],
    "business_period": ["营业期限"],
    "address": ["住所", "经营场所", "主要经营场所"],
    "business_scope": ["经营范围"],
    "registration_authority": ["登记机关"],
    "approval_date": ["核准日期"],
}


def extract_business_license_fields(text: str) -> dict:
    lines = [normalize_space(line) for line in text.splitlines() if normalize_space(line)]
    fields = {}

    for key, aliases in FIELD_ALIASES.items():
        fields[key] = extract_by_alias(lines, aliases, allow_next_value=(key != "registration_authority"))

    if not fields["approval_date"]:
        dates = [line for line in lines if re.search(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", line)]
        if dates:
            fields["approval_date"] = dates[-1]

    return fields


def extract_by_alias(lines: list[str], aliases: list[str], allow_next_value: bool = True) -> str:
    normalized_aliases = [compact_label(alias) for alias in aliases]
    for index, line in enumerate(lines):
        compact_line = compact_label(line)
        for alias in aliases:
            compact_alias = compact_label(alias)
            if compact_alias in compact_line:
                value = value_after_alias(line, alias)
                if value:
                    return value
                if allow_next_value:
                    next_value = find_next_value(lines, index + 1, normalized_aliases)
                    if next_value:
                        return next_value
    return ""


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def compact_label(value: str) -> str:
    return re.sub(r"[\s　]+", "", value)


def value_after_alias(line: str, alias: str) -> str:
    compact_alias = compact_label(alias)
    chars = list(line)
    compact_positions = []
    compact = []
    for pos, char in enumerate(chars):
        if not char.isspace() and char != "　":
            compact_positions.append(pos)
            compact.append(char)
    compact_text = "".join(compact)
    start = compact_text.find(compact_alias)
    if start < 0:
        return ""
    end = start + len(compact_alias)
    if end >= len(compact_positions):
        return ""
    original_end = compact_positions[end - 1] + 1
    return line[original_end:].strip(" ：:，,")


def looks_like_label(line: str, current_aliases: list[str]) -> bool:
    compact = compact_label(line)
    all_aliases = [compact_label(alias) for aliases in FIELD_ALIASES.values() for alias in aliases]
    return compact in all_aliases and compact not in current_aliases


def find_next_value(lines: list[str], start: int, current_aliases: list[str]) -> str:
    for line in lines[start : start + 6]:
        if is_noise_line(line) or looks_like_label(line, current_aliases):
            continue
        return line.strip(" ：:，,")
    return ""


def is_noise_line(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith("<"):
        return True
    compact = compact_label(stripped)
    if compact in {"text", "doc_title", "seal", "image", "vision_footnote", "header_image", "footer"}:
        return True
    return False
