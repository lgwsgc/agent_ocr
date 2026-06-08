from langchain_core.tools import StructuredTool

from tools.field_extractor import extract_business_license_fields
from tools.repair import repair_fields
from tools.validators import validate_fields


def extract_business_license_fields_tool(ocr_text: str) -> dict:
    """Extract canonical Chinese business license fields from OCR text."""
    return extract_business_license_fields(ocr_text)


def validate_business_license_fields_tool(fields: dict) -> dict:
    """Validate extracted business license fields with deterministic rules."""
    return validate_fields(fields)


def repair_business_license_fields_tool(fields: dict, validation: dict) -> dict:
    """Repair common OCR errors using validation feedback."""
    return repair_fields(fields, validation)


def build_business_license_langchain_tools() -> dict:
    tools = [
        StructuredTool.from_function(
            func=extract_business_license_fields_tool,
            name="extract_business_license_fields",
            description="Extract fields such as unified social credit code, name, type, capital, dates, address and business scope from OCR text.",
        ),
        StructuredTool.from_function(
            func=validate_business_license_fields_tool,
            name="validate_business_license_fields",
            description="Validate business license fields using deterministic rules such as USCC checksum and date/capital format checks.",
        ),
        StructuredTool.from_function(
            func=repair_business_license_fields_tool,
            name="repair_business_license_fields",
            description="Repair common OCR confusions such as O/0, I/1 and suspicious date characters based on validation feedback.",
        ),
    ]
    return {tool.name: tool for tool in tools}

