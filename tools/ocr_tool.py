import json
import subprocess
import sys
import time
from pathlib import Path


def run_paddleocr_vl(image_path: Path, output_dir: Path) -> dict:
    """调用本地 PaddleOCR-VL，把营业执照图片解析成可供 Agent 使用的 OCR 文本。"""
    image_path = image_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    paddleocr_cli = find_paddleocr_cli()
    started_at = time.perf_counter()
    cmd = [
        str(paddleocr_cli),
        "doc_parser",
        "-i",
        str(image_path),
        "--device",
        "cpu",
        "--pipeline_version",
        "v1.6",
        "--engine",
        "transformers",
        "--max_pixels",
        "802816",
        "--max_new_tokens",
        "512",
        "--save_path",
        str(output_dir),
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=image_path.parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "未找到 paddleocr 命令，请先执行：`python -m pip install -U \"paddleocr[doc-parser]\"`。"
        ) from exc
    elapsed_seconds = round(time.perf_counter() - started_at, 3)

    text = collect_ocr_text(output_dir)
    if not text.strip():
        text = proc.stdout.strip()

    return {
        "engine": "PaddleOCR-VL-1.6",
        "elapsed_seconds": elapsed_seconds,
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "output_dir": str(output_dir),
        "text": text,
    }


def find_paddleocr_cli() -> Path | str:
    """优先使用当前 Python 环境中的 paddleocr.exe，找不到时回退到 PATH。"""
    scripts_dir = Path(sys.executable).resolve().parent / "Scripts"
    exe = scripts_dir / "paddleocr.exe"
    if exe.exists():
        return exe
    return "paddleocr"


def collect_ocr_text(output_dir: Path) -> str:
    """从 PaddleOCR-VL 生成的 Markdown、文本和 JSON 文件中汇总可读文本。"""
    chunks = []
    for path in sorted(output_dir.rglob("*")):
        if path.suffix.lower() in {".md", ".txt"}:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        elif path.suffix.lower() == ".json":
            chunks.extend(extract_json_text(path))
    return "\n".join(chunk for chunk in chunks if chunk.strip())


def extract_json_text(path: Path) -> list[str]:
    """读取 OCR JSON 文件，并递归提取其中的字符串内容。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return []
    values = []
    walk_json(data, values)
    return values


def walk_json(value, values: list[str]) -> None:
    """递归遍历 JSON 对象，把所有非空字符串收集到列表中。"""
    if isinstance(value, str):
        if value.strip():
            values.append(value.strip())
    elif isinstance(value, list):
        for item in value:
            walk_json(item, values)
    elif isinstance(value, dict):
        for item in value.values():
            walk_json(item, values)
