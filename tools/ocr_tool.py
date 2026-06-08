import json
import subprocess
import sys
from pathlib import Path


def run_paddleocr_vl(image_path: Path, output_dir: Path) -> dict:
    """Run local PaddleOCR-VL through the PaddleOCR CLI.

    The CLI writes rich document parsing artifacts. For the agent demo we collect
    readable text from generated Markdown/TXT/JSON files and pass it downstream.
    """
    image_path = image_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    paddleocr_cli = find_paddleocr_cli()
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
            "paddleocr CLI not found. Install it with `python -m pip install -U \"paddleocr[doc-parser]\"`."
        ) from exc

    text = collect_ocr_text(output_dir)
    if not text.strip():
        text = proc.stdout.strip()

    return {
        "engine": "PaddleOCR-VL-1.6",
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "output_dir": str(output_dir),
        "text": text,
    }


def find_paddleocr_cli() -> Path | str:
    scripts_dir = Path(sys.executable).resolve().parent / "Scripts"
    exe = scripts_dir / "paddleocr.exe"
    if exe.exists():
        return exe
    return "paddleocr"


def collect_ocr_text(output_dir: Path) -> str:
    chunks = []
    for path in sorted(output_dir.rglob("*")):
        if path.suffix.lower() in {".md", ".txt"}:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        elif path.suffix.lower() == ".json":
            chunks.extend(extract_json_text(path))
    return "\n".join(chunk for chunk in chunks if chunk.strip())


def extract_json_text(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return []
    values = []
    walk_json(data, values)
    return values


def walk_json(value, values: list[str]) -> None:
    if isinstance(value, str):
        if value.strip():
            values.append(value.strip())
    elif isinstance(value, list):
        for item in value:
            walk_json(item, values)
    elif isinstance(value, dict):
        for item in value.values():
            walk_json(item, values)
