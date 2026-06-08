from tools.langchain_tools import build_business_license_langchain_tools
from tools.validators import validate_fields


class BusinessLicenseAgent:
    """Small orchestration layer for the sharing demo."""

    def run(self, ocr_text: str) -> dict:
        langchain_tools = build_business_license_langchain_tools()
        tool_trace = [
            {
                "step": 1,
                "tool": "ocr_or_text_input",
                "purpose": "读取营业执照图片或 OCR 文本",
                "observation": "获得可供字段抽取的全文文本",
            }
        ]
        extracted = langchain_tools["extract_business_license_fields"].invoke({"ocr_text": ocr_text})
        tool_trace.append(
            {
                "step": 2,
                "tool": "LangChain StructuredTool: extract_business_license_fields",
                "purpose": "从全文文本中抽取营业执照标准字段",
                "observation": f"抽取到 {sum(bool(v) for v in extracted.values())} 个非空字段",
            }
        )
        first_pass = langchain_tools["validate_business_license_fields"].invoke({"fields": extracted})
        tool_trace.append(
            {
                "step": 3,
                "tool": "LangChain StructuredTool: validate_business_license_fields",
                "purpose": "校验统一社会信用代码、日期、出资额/注册资本等字段",
                "observation": self._validation_observation(first_pass),
            }
        )
        repaired = langchain_tools["repair_business_license_fields"].invoke(
            {"fields": extracted, "validation": first_pass}
        )
        tool_trace.append(
            {
                "step": 4,
                "tool": "LangChain StructuredTool: repair_business_license_fields",
                "purpose": "根据校验失败原因修复 O/0、I/1、日期等 OCR 常见错误",
                "observation": f"自动修复 {len(repaired['actions'])} 个字段",
            }
        )
        final_validation = langchain_tools["validate_business_license_fields"].invoke({"fields": repaired["fields"]})
        tool_trace.append(
            {
                "step": 5,
                "tool": "LangChain StructuredTool: validate_business_license_fields",
                "purpose": "再次校验修复后的结构化结果",
                "observation": self._validation_observation(final_validation),
            }
        )

        return {
            "task": "business_license_ocr",
            "framework": "LangChain Core StructuredTool",
            "agent_loop": ["read", "extract", "validate", "repair", "explain"],
            "tool_use_pattern": {
                "source": "智能体设计模式(google).pdf 第 5 章：工具使用（函数调用）",
                "mapping": [
                    "工具定义：LangChain StructuredTool 封装字段抽取器、校验器、修复器",
                    "工具执行：PaddleOCR-VL 推理与 LangChain 工具调用",
                    "观察结果：OCR 文本、字段 JSON、校验失败原因",
                    "下一步处理：自动修复或标记人工复核",
                ],
            },
            "tool_trace": tool_trace,
            "raw_ocr_text": ocr_text,
            "extracted_fields": extracted,
            "validation_before_repair": first_pass,
            "repair_actions": repaired["actions"],
            "final_fields": repaired["fields"],
            "validation_after_repair": final_validation,
            "summary": self._summarize(final_validation, repaired["actions"]),
        }

    @staticmethod
    def _summarize(validation: dict, actions: list[dict]) -> dict:
        failed = [name for name, item in validation.items() if not item["valid"]]
        return {
            "status": "pass" if not failed else "needs_review",
            "auto_repair_count": len(actions),
            "remaining_issue_fields": failed,
        }

    @staticmethod
    def _validation_observation(validation: dict) -> str:
        failed = [name for name, item in validation.items() if not item["valid"]]
        if not failed:
            return "关键字段全部通过校验"
        return "待修复或复核字段：" + "、".join(failed)
