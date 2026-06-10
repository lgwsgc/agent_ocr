import re


FIELD_ALIASES = {
    "统一社会信用代码": ["统一社会信用代码", "统一信用代码", "社会信用代码"],
    "名称": ["名称", "企业名称"],
    "类型": ["类型"],
    "法定代表人": ["法定代表人", "负责人", "经营者", "执行事务合伙人"],
    "注册资本": ["注册资本", "出资额"],
    "成立日期": ["成立日期"],
    "营业期限": ["营业期限"],
    "住所": ["住所", "经营场所", "主要经营场所"],
    "经营范围": ["经营范围"],
    "登记机关": ["登记机关"],
    "核准日期": ["核准日期"],
}


def extract_business_license_fields(text: str) -> dict:
    """从 OCR 全文中按标签别名抽取营业执照字段。"""
    lines = [normalize_space(line) for line in text.splitlines() if normalize_space(line)]
    fields = {}

    for key, aliases in FIELD_ALIASES.items():
        fields[key] = extract_by_alias(lines, aliases, allow_next_value=(key != "登记机关"))

    if not fields["核准日期"]:
        dates = [line for line in lines if re.search(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", line)]
        if dates:
            fields["核准日期"] = dates[-1]

    return fields


def extract_by_alias(lines: list[str], aliases: list[str], allow_next_value: bool = True) -> str:
    """根据字段标签或标签别名，从多行 OCR 文本中寻找字段值。"""
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
    """把连续空白压缩成单个空格，降低 OCR 空格噪声影响。"""
    return re.sub(r"\s+", " ", value.strip())


def compact_label(value: str) -> str:
    """移除中英文空格，用于匹配被 OCR 拆开的字段标签。"""
    return re.sub(r"[\s　]+", "", value)


def value_after_alias(line: str, alias: str) -> str:
    """从同一行中截取字段标签后面的内容。"""
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
    """判断一行是否像其他字段标签，避免把标签误当成字段值。"""
    compact = compact_label(line)
    all_aliases = [compact_label(alias) for aliases in FIELD_ALIASES.values() for alias in aliases]
    return compact in all_aliases and compact not in current_aliases


def find_next_value(lines: list[str], start: int, current_aliases: list[str]) -> str:
    """当标签独占一行时，向后寻找最近的有效字段值。"""
    for line in lines[start : start + 6]:
        if is_noise_line(line) or looks_like_label(line, current_aliases):
            continue
        return line.strip(" ：:，,")
    return ""


def is_noise_line(line: str) -> bool:
    """过滤 Markdown、HTML 图片标签和版面分类等非字段文本。"""
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith("<"):
        return True
    compact = compact_label(stripped)
    if compact in {"text", "doc_title", "seal", "image", "vision_footnote", "header_image", "footer"}:
        return True
    return False
