import json
import re
import shutil
from datetime import datetime
from pathlib import Path


def create_run_dir(runs_root: Path, sample_path: Path, mode: str) -> Path:
    sample_name = safe_name(Path(sample_path).stem or mode)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(runs_root) / f"{sample_name}_{timestamp}"
    suffix = 1
    while run_dir.exists():
        run_dir = Path(runs_root) / f"{sample_name}_{timestamp}_{suffix}"
        suffix += 1
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_run_artifacts(
    run_dir: Path,
    result: dict,
    compact_result: dict,
    ocr_text: str,
    input_path: Path,
    mode: str,
    ocr_meta: dict | None = None,
) -> dict[str, Path]:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "final_result": run_dir / "final_result.json",
        "agent_full": run_dir / "agent_full.json",
        "ocr_text": run_dir / "ocr" / "ocr_text.txt",
        "fields_before_llm": run_dir / "llm" / "fields_before_llm.json",
        "fields_after_llm": run_dir / "llm" / "fields_after_llm.json",
        "llm_postprocess": run_dir / "llm" / "llm_postprocess.json",
        "llm_changes": run_dir / "llm" / "llm_changes.json",
        "run_manifest": run_dir / "run_manifest.json",
    }

    paths["ocr_text"].parent.mkdir(parents=True, exist_ok=True)
    paths["fields_before_llm"].parent.mkdir(parents=True, exist_ok=True)

    write_json(paths["final_result"], compact_result)
    write_json(paths["agent_full"], result)
    paths["ocr_text"].write_text(ocr_text, encoding="utf-8")

    if ocr_meta:
        paths["ocr_engine"] = run_dir / "ocr" / "ocr_engine.json"
        write_json(paths["ocr_engine"], ocr_meta)

    llm_postprocess = result.get("llm_postprocess", {})
    fields_before_llm = result.get("fields_before_llm", result.get("extracted_fields", {}))
    fields_after_llm = result.get("final_fields", {})
    write_json(paths["fields_before_llm"], fields_before_llm)
    write_json(paths["fields_after_llm"], fields_after_llm)
    write_json(paths["llm_postprocess"], llm_postprocess)
    write_json(paths["llm_changes"], build_llm_changes(fields_before_llm, fields_after_llm, llm_postprocess))

    manifest = {
        "mode": mode,
        "input_path": str(Path(input_path)),
        "run_dir": str(run_dir.resolve()),
        "files": {name: str(path.resolve()) for name, path in paths.items()},
    }
    write_json(paths["run_manifest"], manifest)
    return paths


def mirror_final_result(compact_result: dict, output_path: Path | None) -> None:
    if not output_path:
        return
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, compact_result)


def copy_input_file(input_path: Path, run_dir: Path) -> Path | None:
    input_path = Path(input_path)
    if not input_path.exists() or not input_path.is_file():
        return None
    target = Path(run_dir) / "input" / input_path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, target)
    return target


def build_llm_changes(before: dict, after: dict, llm_postprocess: dict) -> dict:
    changed_fields = []
    for key in sorted(set(before) | set(after)):
        before_value = before.get(key, "")
        after_value = after.get(key, "")
        if before_value != after_value:
            changed_fields.append({"field": key, "before": before_value, "after": after_value})
    return {
        "status": llm_postprocess.get("status", "未启用"),
        "model": llm_postprocess.get("model", "未调用"),
        "base_url": llm_postprocess.get("base_url", ""),
        "elapsed_seconds": llm_postprocess.get("elapsed_seconds", 0),
        "actions": llm_postprocess.get("actions", []),
        "changed_fields": changed_fields,
        "raw_response": llm_postprocess.get("raw_response", ""),
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_name(value: str) -> str:
    value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._")
    return value or "sample"
