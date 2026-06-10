from langchain_core.tools import StructuredTool

from tools.field_extractor import extract_business_license_fields
from tools.llm_postprocessor import llm_semantic_repair_fields
from tools.repair import repair_fields
from tools.validators import validate_fields


def extract_business_license_fields_tool(ocr_text: str) -> dict:
    """从 OCR 全文中抽取营业执照中文字段。"""
    return extract_business_license_fields(ocr_text)


def validate_business_license_fields_tool(fields: dict) -> dict:
    """使用确定性规则校验营业执照字段。"""
    return validate_fields(fields)


def repair_business_license_fields_tool(fields: dict, validation: dict) -> dict:
    """根据校验失败原因修复常见 OCR 字符错误。"""
    return repair_fields(fields, validation)


def llm_semantic_repair_business_license_fields_tool(ocr_text: str, fields: dict) -> dict:
    """使用兼容 Anthropic 协议的大模型修复语义型 OCR 错误。"""
    return llm_semantic_repair_fields(ocr_text, fields)


def build_business_license_langchain_tools() -> dict:
    """构建营业执照 Agent 可调用的 LangChain 工具集合。"""
    tools = [
        StructuredTool.from_function(
            func=extract_business_license_fields_tool,
            name="extract_business_license_fields",
            description="从 OCR 全文中抽取统一社会信用代码、名称、类型、注册资本、成立日期、住所、经营范围等中文字段。",
        ),
        StructuredTool.from_function(
            func=validate_business_license_fields_tool,
            name="validate_business_license_fields",
            description="使用统一社会信用代码校验位、日期格式、注册资本格式等确定性规则校验字段。",
        ),
        StructuredTool.from_function(
            func=repair_business_license_fields_tool,
            name="repair_business_license_fields",
            description="根据校验反馈修复 O/0、I/1、日期字符等常见 OCR 混淆错误。",
        ),
        StructuredTool.from_function(
            func=llm_semantic_repair_business_license_fields_tool,
            name="llm_semantic_repair_business_license_fields",
            description="使用兼容 Anthropic 协议的大模型，保守修复语义型 OCR 错误和字段边界错误。",
        ),
    ]
    return {tool.name: tool for tool in tools}
