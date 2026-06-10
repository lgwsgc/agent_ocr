import json
import os
import re
import time
from pathlib import Path

import certifi
from langchain_anthropic import ChatAnthropic


FIELD_KEYS = [
    "统一社会信用代码",
    "名称",
    "类型",
    "法定代表人",
    "注册资本",
    "成立日期",
    "营业期限",
    "住所",
    "经营范围",
    "登记机关",
    "核准日期",
]


def llm_semantic_repair_fields(ocr_text: str, fields: dict) -> dict:
    """使用大模型做语义后处理，修复规则难以覆盖的 OCR 错字和字段粘连。"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {
            "fields": fields,
            "actions": [],
            "status": "已跳过",
            "reason": "当前环境未设置 ANTHROPIC_API_KEY",
        }

    ensure_ssl_cert_file()
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://crs.hexai.cn/api")
    model = ChatAnthropic(
        model_name=model_name,
        base_url=base_url,
        temperature=0,
        max_tokens_to_sample=1600,
    )
    prompt = build_prompt(ocr_text, fields)
    started_at = time.perf_counter()
    response = model.invoke(prompt)
    elapsed_seconds = round(time.perf_counter() - started_at, 3)
    content = response.content
    if isinstance(content, list):
        content = "\n".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in content)

    parsed = parse_json_object(str(content))
    repaired_fields = sanitize_fields(parsed.get("fields", fields), fields)
    actions = sanitize_actions(parsed.get("actions", []), fields, repaired_fields)
    return {
        "fields": repaired_fields,
        "actions": actions,
        "status": "完成",
        "model": model_name,
        "base_url": base_url,
        "elapsed_seconds": elapsed_seconds,
        "raw_response": str(content),
    }


def ensure_ssl_cert_file() -> None:
    """确保 SSL 证书路径有效，避免中转服务请求时因证书路径失效而失败。"""
    ssl_cert_file = os.getenv("SSL_CERT_FILE")
    if ssl_cert_file and Path(ssl_cert_file).exists():
        return
    os.environ["SSL_CERT_FILE"] = certifi.where()


def build_prompt(ocr_text: str, fields: dict) -> str:
    """构造约束严格的大模型提示词，要求只输出 JSON 修复结果。"""
    return f"""
你是营业执照 OCR 后处理工具。请根据 OCR 全文和当前字段 JSON，修复明显的 OCR 语义错误。

严格规则：
1. 只能修复 OCR 明显错字、字段粘连、标签混入、常见字符混淆。
2. 不要编造 OCR 全文中没有依据的信息。
3. 统一社会信用代码、日期、金额如果没有把握，不要修改。
4. 经营范围可以根据营业执照常见语义修复明显错字，例如“工程浩价”更正为“工程造价”，但必须保守。
5. 只输出 JSON，不要输出解释性文字。
6. JSON 字符串内部不要使用英文双引号，如需引用错字请使用中文引号“”。

字段键只能使用：
{json.dumps(FIELD_KEYS, ensure_ascii=False)}

输出格式：
{{
  "fields": {{
    "统一社会信用代码": "...",
    "名称": "...",
    "类型": "...",
    "法定代表人": "...",
    "注册资本": "...",
    "成立日期": "...",
    "营业期限": "...",
    "住所": "...",
    "经营范围": "...",
    "登记机关": "...",
    "核准日期": "..."
  }},
  "actions": [
    {{
      "field": "经营范围",
      "original": "...",
      "corrected": "...",
      "reason": "根据上下文修复明显 OCR 错字",
      "confidence": 0.82
    }}
  ]
}}

OCR 全文：
{ocr_text}

当前字段 JSON：
{json.dumps(fields, ensure_ascii=False, indent=2)}
""".strip()


def parse_json_object(text: str) -> dict:
    """从大模型输出中解析 JSON 对象，兼容模型偶尔包裹额外文本的情况。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def sanitize_fields(candidate: dict, fallback: dict) -> dict:
    """清洗大模型返回字段，只接受预定义的中文营业执照字段。"""
    result = dict(fallback)
    if not isinstance(candidate, dict):
        return result
    for key in FIELD_KEYS:
        value = candidate.get(key)
        if isinstance(value, str):
            result[key] = value.strip()
    return result


def sanitize_actions(actions: list, before: dict, after: dict) -> list[dict]:
    """清洗大模型修复动作，丢弃无效字段和没有实际变化的修复建议。"""
    clean = []
    if not isinstance(actions, list):
        return clean
    for action in actions:
        if not isinstance(action, dict):
            continue
        field = action.get("field")
        if field not in FIELD_KEYS:
            continue
        original = str(action.get("original", before.get(field, ""))).strip()
        corrected = str(action.get("corrected", after.get(field, ""))).strip()
        if original == corrected:
            continue
        clean.append(
            {
                "field": field,
                "original": original,
                "corrected": corrected,
                "reason": str(action.get("reason", "LLM 根据 OCR 上下文进行语义修复")).strip(),
                "confidence": float(action.get("confidence", 0.7)),
            }
        )
    return clean
