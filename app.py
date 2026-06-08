import argparse
import json
from pathlib import Path

from agents.license_agent import BusinessLicenseAgent
from tools.ocr_tool import run_paddleocr_vl


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
    parser = argparse.ArgumentParser(description="Business license OCR Agent demo")
    parser.add_argument("--text", type=Path, help="Path to OCR text file")
    parser.add_argument("--image", type=Path, help="Path to business license image")
    parser.add_argument("--out", type=Path, default=Path("outputs/license_agent_result.json"))
    parser.add_argument("--ocr-out", type=Path, default=Path("outputs/paddleocr_vl"))
    args = parser.parse_args()

    ocr_meta = None
    if args.image:
        ocr_meta = run_paddleocr_vl(args.image, args.ocr_out)
        ocr_text = ocr_meta["text"]
    elif args.text:
        ocr_text = args.text.read_text(encoding="utf-8")
    else:
        ocr_text = DEFAULT_TEXT

    agent = BusinessLicenseAgent()
    result = agent.run(ocr_text)
    if ocr_meta:
        result["ocr_engine"] = ocr_meta

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSaved: {args.out.resolve()}")


if __name__ == "__main__":
    main()
