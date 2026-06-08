import json
import threading
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, TOP, Button, Frame, Label, Text, Tk
from tkinter import messagebox

from agents.license_agent import BusinessLicenseAgent


ROOT = Path(__file__).resolve().parent
SAMPLE_TEXT = ROOT / "samples" / "license_ocr_with_errors.txt"
IMAGE_PATH = ROOT / "Snipaste_2026-06-04_15-12-26.jpg"
REAL_OCR_TEXT = ROOT / "samples" / "license_real_ocr.md"
TEXT_DEMO_OUT = ROOT / "outputs" / "gui_langchain_text_demo.json"
REAL_DEMO_OUT = ROOT / "outputs" / "gui_real_ocr_demo.json"


class BusinessLicenseDemo:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("营业执照 OCR Agent Demo - LangChain Tool Use")
        self.root.geometry("1180x760")
        self.root.minsize(980, 620)

        self.image_ref = None
        self._build_ui()
        self._render_intro()

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        header = Frame(self.root, padx=14, pady=10)
        header.pack(side=TOP, fill="x")
        Label(
            header,
            text="营业执照字段识别 Agent：PaddleOCR-VL + LangChain 工具调用 + 自动纠错",
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(anchor="w")
        Label(
            header,
            text="演示链路：OCR 文本/图片结果 -> 字段抽取 -> 合规校验 -> OCR 错误修复 -> 结构化输出",
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        toolbar = Frame(self.root, padx=14, pady=8)
        toolbar.pack(side=TOP, fill="x")
        Button(
            toolbar,
            text="1. 运行文本兜底 Demo",
            command=lambda: self._run_async(self._run_text_demo),
            width=22,
        ).pack(side=LEFT, padx=(0, 8))
        Button(
            toolbar,
            text="2. 加载真实图片 OCR 结果",
            command=lambda: self._run_async(self._run_real_ocr_demo),
            width=24,
        ).pack(side=LEFT, padx=(0, 8))
        Button(toolbar, text="清空输出", command=self._render_intro, width=12).pack(side=LEFT)

        body = Frame(self.root, padx=14, pady=10)
        body.pack(side=TOP, fill=BOTH, expand=True)

        left = Frame(body)
        left.pack(side=LEFT, fill=BOTH, expand=False)
        Label(left, text="识别对象", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        self.image_label = Label(left, width=430, height=330, bg="#f4f4f4", relief="solid", borderwidth=1)
        self.image_label.pack(side=TOP, pady=(8, 12))
        self._load_image_preview()

        knowledge = (
            "营业执照知识点：\n"
            "1. 统一社会信用代码是企业身份标识，常见 OCR 错误是 O/0、I/1、S/5。\n"
            "2. 名称、类型、住所、经营范围、登记机关、核准日期是抽取重点。\n"
            "3. Agent 的价值不是只识别文字，而是把识别结果交给工具校验和修复。"
        )
        Label(left, text=knowledge, justify=LEFT, wraplength=420, font=("Microsoft YaHei UI", 10)).pack(anchor="w")

        right = Frame(body)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=(16, 0))
        Label(right, text="Agent 运行结果", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        self.output = Text(right, wrap="word", font=("Consolas", 10), padx=10, pady=10)
        self.output.pack(side=TOP, fill=BOTH, expand=True, pady=(8, 0))

    def _load_image_preview(self) -> None:
        try:
            from PIL import Image, ImageOps, ImageTk

            img = Image.open(IMAGE_PATH)
            img = ImageOps.contain(img, (420, 300))
            canvas = Image.new("RGB", (430, 330), "#f4f4f4")
            offset = ((430 - img.width) // 2, (330 - img.height) // 2)
            canvas.paste(img, offset)
            canvas = ImageOps.expand(canvas, border=1, fill="#c9c9c9")
            self.image_ref = ImageTk.PhotoImage(canvas)
            self.image_label.configure(image=self.image_ref, text="")
        except Exception:
            self.image_label.configure(text=f"图片文件：\n{IMAGE_PATH}")

    def _render_intro(self) -> None:
        self._set_output(
            "准备就绪。\n\n"
            "建议现场演示顺序：\n"
            "1. 点击“运行文本兜底 Demo”，快速展示 LangChain StructuredTool 工具调用和自动纠错。\n"
            "2. 点击“加载真实图片 OCR 结果”，展示同一套 Agent 如何处理 PaddleOCR-VL 已识别出的真实图片文本。\n\n"
            "说明：真实图片 OCR 在 CPU 上可能较慢，所以现场优先读取已经生成好的 OCR 结果，保证分享节奏稳定。"
        )

    def _run_async(self, task) -> None:
        self._set_output("Agent 正在运行，请稍等...\n")
        threading.Thread(target=task, daemon=True).start()

    def _run_text_demo(self) -> None:
        try:
            text = SAMPLE_TEXT.read_text(encoding="utf-8")
            result = BusinessLicenseAgent().run(text)
            self._save_and_show(result, TEXT_DEMO_OUT)
        except Exception as exc:
            self._show_error(exc)

    def _run_real_ocr_demo(self) -> None:
        try:
            if not REAL_OCR_TEXT.exists():
                raise FileNotFoundError(f"未找到真实 OCR 文本：{REAL_OCR_TEXT}")
            text = REAL_OCR_TEXT.read_text(encoding="utf-8")
            result = BusinessLicenseAgent().run(text)
            result["ocr_source"] = str(REAL_OCR_TEXT)
            self._save_and_show(result, REAL_DEMO_OUT)
        except Exception as exc:
            self._show_error(exc)

    def _save_and_show(self, result: dict, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        self._set_output(self._format_result(result, output_path))

    def _format_result(self, result: dict, output_path: Path) -> str:
        lines = [
            f"任务：{result['task']}",
            f"框架：{result['framework']}",
            f"状态：{result['summary']['status']}",
            f"自动修复字段数：{result['summary']['auto_repair_count']}",
            f"保存位置：{output_path}",
            "",
            "工具调用轨迹：",
        ]
        for item in result["tool_trace"]:
            lines.append(f"  {item['step']}. {item['tool']}")
            lines.append(f"     目的：{item['purpose']}")
            lines.append(f"     观察：{item['observation']}")

        lines.extend(["", "自动修复动作："])
        if result["repair_actions"]:
            for action in result["repair_actions"]:
                lines.append(
                    f"  - {action['field']}: {action['original']} -> {action['corrected']} "
                    f"({action['reason']})"
                )
        else:
            lines.append("  - 无需自动修复")

        lines.extend(["", "最终字段："])
        for key, value in result["final_fields"].items():
            lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def _set_output(self, text: str) -> None:
        self.output.after(0, lambda: self._replace_output(text))

    def _replace_output(self, text: str) -> None:
        self.output.delete("1.0", END)
        self.output.insert(END, text)

    def _show_error(self, exc: Exception) -> None:
        self._set_output(f"运行失败：{exc}")
        self.root.after(0, lambda: messagebox.showerror("Demo 运行失败", str(exc)))


if __name__ == "__main__":
    BusinessLicenseDemo().run()
