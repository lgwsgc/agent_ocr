import argparse
import json
import os
import sys
import time
from pathlib import Path

from agents.license_agent import BusinessLicenseAgent
from tools.compact_output import build_compact_result
from tools.ocr_tool import run_paddleocr_vl
from tools.run_artifacts import copy_input_file, create_run_dir, mirror_final_result, save_run_artifacts


默认文本文件 = Path("samples/license_ocr_with_errors.txt")
默认图片文件 = Path("Snipaste_2026-06-04_15-12-26.jpg")
默认输出文件 = Path("outputs/license_agent_result.json")
默认图片输出文件 = Path("outputs/license_image_agent_result.json")
默认语义修复输出文件 = Path("outputs/license_llm_semantic_result.json")
默认OCR输出目录 = Path("outputs/paddleocr_vl")
默认运行输出目录 = Path("outputs/runs")

DEFAULT_TEXT = """统一社会信用代码 9111O1O2O8284I146L
名称 中华人民共和国财政部（报告审定专用）
类型 特种机构
法定代表人 李某某
注册资本 896 万元
成立日期 2013 年 11 月 O4 日
住所 北京市丰台区西四环南路 40 号院 1 号楼底商 20 层
经营范围 一般项目：工程造价咨询业务、工程管理服务、资产评估、价格鉴证评估等。
登记机关 北京市市场监督管理局
核准日期 2025 年 O2 月 27 日
"""


def main() -> None:
    """命令行入口：读取 OCR 文本或营业执照图片，并输出 Agent 结构化识别结果。"""
    started_at = time.perf_counter()
    prepare_llm_environment()
    parser = argparse.ArgumentParser(description="营业执照 OCR Agent 演示程序")
    parser.add_argument("--mode", choices=["image", "text"], default="image", help="运行模式：image 为图片识别，text 为 OCR 文本处理")
    parser.add_argument("--text", type=Path, default=默认文本文件, help="OCR 文本文件路径")
    parser.add_argument("--image", dest="mode", action="store_const", const="image", help="启用图片识别模式")
    parser.add_argument("--text-mode", dest="mode", action="store_const", const="text", help="启用文本处理模式")
    parser.add_argument("--image-path", type=Path, default=r"D:\OCR_Research\agent\data\58.jpg", help="营业执照图片路径")
    parser.add_argument("--out", type=Path, help="结果 JSON 输出路径；不传时根据运行模式自动选择")
    parser.add_argument("--ocr-out", type=Path, default=r"D:\OCR_Research\agent\output", help="图片 OCR 中间结果输出目录")
    parser.add_argument("--runs-root", type=Path, default=默认运行输出目录, help="每次运行的样本结果文件夹根目录")
    parser.add_argument("--use-llm-postprocess", dest="use_llm_postprocess", action="store_true", default=None, help="启用大模型语义后处理")
    parser.add_argument("--no-llm-postprocess", dest="use_llm_postprocess", action="store_false", help="关闭大模型语义后处理")
    args = parser.parse_args()

    if "--text" in sys.argv and "--mode" not in sys.argv and "--image" not in sys.argv and "--text-mode" not in sys.argv:
        args.mode = "text"

    output_path = choose_output_path(args)
    use_llm_postprocess = choose_llm_postprocess(args)

    ocr_meta = None
    if args.mode == "image":
        input_mode = "图片"
        input_path = args.image_path
        if not args.image_path.exists():
            raise FileNotFoundError(f"营业执照图片不存在：{args.image_path}")
        run_dir = create_run_dir(args.runs_root, input_path, args.mode)
        copy_input_file(input_path, run_dir)
        ocr_output_dir = run_dir / "ocr"
        ocr_meta = run_paddleocr_vl(args.image_path, ocr_output_dir)
        ocr_text = ocr_meta["text"]
    elif args.text.exists():
        input_mode = "OCR 文本"
        input_path = args.text
        run_dir = create_run_dir(args.runs_root, input_path, args.mode)
        copy_input_file(input_path, run_dir)
        ocr_text = args.text.read_text(encoding="utf-8")
    else:
        input_mode = "内置文本兜底"
        input_path = args.text
        run_dir = create_run_dir(args.runs_root, input_path, args.mode)
        ocr_text = DEFAULT_TEXT

    agent = BusinessLicenseAgent(use_llm_postprocess=use_llm_postprocess)
    result = agent.run(ocr_text)
    if ocr_meta:
        result["ocr_engine"] = ocr_meta

    total_elapsed_seconds = round(time.perf_counter() - started_at, 3)
    result["run_info"].update(
        {
            "输入类型": input_mode,
            "输入路径": str(input_path),
            "输出路径": str((run_dir / "final_result.json").resolve()),
            "运行文件夹": str(run_dir.resolve()),
            "程序总耗时秒": total_elapsed_seconds,
            "大模型跳过原因": get_llm_skip_reason(use_llm_postprocess),
        }
    )

    compact_result = build_compact_result(result, find_ocr_json(run_dir / "ocr", input_path) if ocr_meta else None)
    save_run_artifacts(run_dir, result, compact_result, ocr_text, input_path, args.mode, ocr_meta)
    if output_path:
        mirror_final_result(compact_result, output_path)
    print_run_summary(result)


def print_run_summary(result: dict) -> None:
    """打印适合现场演示查看的运行摘要。"""
    info = result.get("run_info", {})
    ocr_engine = result.get("ocr_engine", {})
    print("\n========== 运行摘要 ==========")
    print(f"输入类型：{info.get('输入类型', '')}")
    print(f"输入路径：{info.get('输入路径', '')}")
    if ocr_engine:
        print(f"OCR 模型：{ocr_engine.get('engine', '')}")
        print(f"OCR 耗时：{ocr_engine.get('elapsed_seconds', 0)} 秒")
    if info.get("大模型") and info.get("大模型") != "未调用":
        print(f"调用模型：{info.get('大模型')}")
        print(f"大模型耗时：{info.get('大模型耗时秒', 0)} 秒")
    if info.get("大模型接口"):
        print(f"模型接口：{info.get('大模型接口')}")
    print(f"程序总耗时：{info.get('程序总耗时秒', 0)} 秒")
    print(f"结果已保存：{info.get('输出路径', '')}")
    if info.get("运行文件夹"):
        print(f"运行文件夹：{info.get('运行文件夹')}")
    print("==============================")


def choose_output_path(args: argparse.Namespace) -> Path:
    """根据运行模式选择默认输出路径，减少演示时需要输入的参数。"""
    if args.out:
        return args.out
    if args.mode == "image":
        return 默认图片输出文件
    if choose_llm_postprocess(args):
        return 默认语义修复输出文件
    return 默认输出文件


def find_ocr_json(output_dir: Path, input_path: Path) -> Path | None:
    """Find the PaddleOCR JSON result that carries block coordinates."""
    output_dir = Path(output_dir)
    input_path = Path(input_path)
    candidates = [
        output_dir / f"{input_path.stem}_res.json",
        output_dir / f"{input_path.stem}.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = sorted(output_dir.glob("*_res.json"))
    return matches[0] if matches else None


def choose_llm_postprocess(args: argparse.Namespace) -> bool:
    """决定是否启用大模型语义后处理；默认在检测到 API key 时自动启用。"""
    if args.use_llm_postprocess is not None:
        return args.use_llm_postprocess
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def prepare_llm_environment() -> None:
    """补齐大模型调用所需环境变量，优先使用当前进程，其次读取 Windows 用户环境变量。"""
    for name in ["ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "SSL_CERT_FILE"]:
        if os.getenv(name):
            continue
        value = read_windows_user_env(name)
        if value:
            os.environ[name] = value
    os.environ.setdefault("ANTHROPIC_BASE_URL", "https://crs.hexai.cn/api")
    cert_path = Path(r"D:\conda_envs\company_tool\lib\site-packages\certifi\cacert.pem")
    if not os.getenv("SSL_CERT_FILE") and cert_path.exists():
        os.environ["SSL_CERT_FILE"] = str(cert_path)


def read_windows_user_env(name: str) -> str:
    """读取 Windows 用户环境变量，解决 setx 后当前终端未刷新的问题。"""
    if os.name != "nt":
        return ""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except OSError:
        return ""


def get_llm_skip_reason(use_llm_postprocess: bool) -> str:
    """给 JSON 结果记录大模型未调用原因，终端摘要保持简洁。"""
    if use_llm_postprocess:
        return ""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return "未检测到 ANTHROPIC_API_KEY"
    return "运行参数关闭了大模型语义后处理"


if __name__ == "__main__":
    main()
