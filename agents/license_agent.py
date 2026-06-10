import time

from tools.langchain_tools import build_business_license_langchain_tools
from tools.validators import validate_fields


class BusinessLicenseAgent:
    """营业执照识别 Agent：编排字段抽取、规则校验、规则修复和可选的大模型语义后处理。"""

    def __init__(self, use_llm_postprocess: bool = False) -> None:
        """初始化 Agent。

        use_llm_postprocess 为 True 时，会在规则修复之后调用大模型做语义型 OCR 错误修复。
        """
        self.use_llm_postprocess = use_llm_postprocess

    def run(self, ocr_text: str) -> dict:
        """执行完整识别流程，并返回可解释的结构化结果。"""
        run_started_at = time.perf_counter()
        langchain_tools = build_business_license_langchain_tools()
        tool_trace = [
            {
                "step": 1,
                "tool": "ocr_or_text_input",
                "purpose": "读取营业执照图片或 OCR 文本",
                "observation": "获得可供字段抽取的全文文本",
                "耗时秒": 0,
            }
        ]
        step_started_at = time.perf_counter()
        extracted = langchain_tools["extract_business_license_fields"].invoke({"ocr_text": ocr_text})
        tool_trace.append(
            {
                "step": 2,
                "tool": "LangChain StructuredTool: extract_business_license_fields",
                "purpose": "从全文文本中抽取营业执照标准字段",
                "observation": f"抽取到 {sum(bool(v) for v in extracted.values())} 个非空字段",
                "耗时秒": round(time.perf_counter() - step_started_at, 3),
            }
        )
        step_started_at = time.perf_counter()
        first_pass = langchain_tools["validate_business_license_fields"].invoke({"fields": extracted})
        tool_trace.append(
            {
                "step": 3,
                "tool": "LangChain StructuredTool: validate_business_license_fields",
                "purpose": "校验统一社会信用代码、日期、出资额/注册资本等字段",
                "observation": self._validation_observation(first_pass),
                "耗时秒": round(time.perf_counter() - step_started_at, 3),
            }
        )
        step_started_at = time.perf_counter()
        repaired = langchain_tools["repair_business_license_fields"].invoke(
            {"fields": extracted, "validation": first_pass}
        )
        tool_trace.append(
            {
                "step": 4,
                "tool": "LangChain StructuredTool: repair_business_license_fields",
                "purpose": "根据校验失败原因修复 O/0、I/1、日期等 OCR 常见错误",
                "observation": f"自动修复 {len(repaired['actions'])} 个字段",
                "耗时秒": round(time.perf_counter() - step_started_at, 3),
            }
        )
        final_fields = repaired["fields"]
        fields_before_llm = dict(final_fields)
        repair_actions = list(repaired["actions"])

        llm_postprocess = {"status": "未启用", "actions": []}
        if self.use_llm_postprocess:
            step_started_at = time.perf_counter()
            llm_postprocess = langchain_tools["llm_semantic_repair_business_license_fields"].invoke(
                {"ocr_text": ocr_text, "fields": final_fields}
            )
            final_fields = llm_postprocess["fields"]
            repair_actions.extend(
                [{**action, "source": "llm_semantic_repair"} for action in llm_postprocess.get("actions", [])]
            )
            tool_trace.append(
                {
                    "step": 5,
                    "tool": "LangChain StructuredTool: llm_semantic_repair_business_license_fields",
                    "purpose": "根据 OCR 全文和字段上下文修复经营范围、地址、名称等语义型 OCR 错误",
                    "observation": f"LLM 后处理状态：{llm_postprocess.get('status')}，修复 {len(llm_postprocess.get('actions', []))} 个字段",
                    "耗时秒": round(time.perf_counter() - step_started_at, 3),
                    "模型": llm_postprocess.get("model", "未调用"),
                }
            )

        step_started_at = time.perf_counter()
        final_validation = langchain_tools["validate_business_license_fields"].invoke({"fields": final_fields})
        tool_trace.append(
            {
                "step": 6 if self.use_llm_postprocess else 5,
                "tool": "LangChain StructuredTool: validate_business_license_fields",
                "purpose": "再次校验修复后的结构化结果",
                "observation": self._validation_observation(final_validation),
                "耗时秒": round(time.perf_counter() - step_started_at, 3),
            }
        )
        total_elapsed_seconds = round(time.perf_counter() - run_started_at, 3)

        return {
            "task": "business_license_ocr",
            "framework": "LangChain Core StructuredTool + 可选大模型语义后处理",
            "agent_loop": ["读取", "抽取", "校验", "修复", "解释"],
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
            "repair_actions": repair_actions,
            "llm_postprocess": llm_postprocess,
            "fields_before_llm": fields_before_llm,
            "final_fields": final_fields,
            "validation_after_repair": final_validation,
            "summary": self._summarize(final_validation, repair_actions),
            "run_info": {
                "总耗时秒": total_elapsed_seconds,
                "是否启用大模型后处理": self.use_llm_postprocess,
                "大模型": llm_postprocess.get("model", "未调用"),
                "大模型接口": llm_postprocess.get("base_url", ""),
                "大模型耗时秒": llm_postprocess.get("elapsed_seconds", 0),
            },
        }

    @staticmethod
    def _summarize(validation: dict, actions: list[dict]) -> dict:
        """根据最终校验结果和修复动作生成摘要。"""
        failed = [name for name, item in validation.items() if not item["valid"]]
        return {
            "status": "通过" if not failed else "需复核",
            "auto_repair_count": len(actions),
            "remaining_issue_fields": failed,
        }

    @staticmethod
    def _validation_observation(validation: dict) -> str:
        """把字段校验结果转换为适合演示展示的观察文本。"""
        failed = [name for name, item in validation.items() if not item["valid"]]
        if not failed:
            return "关键字段全部通过校验"
        return "待修复或复核字段：" + "、".join(failed)
