import json
import re
from pathlib import Path


def build_compact_result(result: dict, ocr_json_path: Path | None = None) -> dict:
    fields = result.get("final_fields", {})
    ocr_blocks = load_ocr_blocks(ocr_json_path)
    items = []

    for field_name, value in fields.items():
        value = "" if value is None else str(value)
        if not value.strip():
            continue
        block = find_block_for_field(ocr_blocks, field_name, value)
        item = {
            "item": field_name,
            "itemcoord": bbox_to_itemcoord(block.get("block_bbox") if block else None),
            "itemstring": value,
            "raw_itemstring": value,
            "vertex": polygon_to_vertex(
                block.get("block_polygon_points") if block else None,
                block.get("block_bbox") if block else None,
            ),
        }
        items.append(item)

    return {
        "angle": 0,
        "errorcode": 0,
        "errormsg": "OK",
        "items": items,
    }


def load_ocr_blocks(ocr_json_path: Path | None) -> list[dict]:
    if not ocr_json_path or not ocr_json_path.exists():
        return []
    try:
        data = json.loads(ocr_json_path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return []
    blocks = data.get("parsing_res_list", [])
    return blocks if isinstance(blocks, list) else []


def find_block_for_field(blocks: list[dict], field_name: str, value: str) -> dict | None:
    compact_name = compact_text(field_name)
    compact_value = compact_text(value)
    for block in blocks:
        content = str(block.get("block_content", ""))
        compact_content = compact_text(content)
        if compact_value and compact_value in compact_content:
            return block
        if compact_name and compact_name in compact_content:
            return block
    return None


def bbox_to_itemcoord(bbox) -> dict:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    x1, y1, x2, y2 = [int(round(float(value))) for value in bbox]
    return {
        "x": x1,
        "y": y1,
        "width": max(0, x2 - x1),
        "height": max(0, y2 - y1),
    }


def polygon_to_vertex(points, fallback_bbox=None) -> dict:
    if not isinstance(points, list) or len(points) != 4:
        points = bbox_to_points(fallback_bbox)
    normalized = []
    for point in points[:4]:
        if isinstance(point, list) and len(point) >= 2:
            normalized.append((int(round(float(point[0]))), int(round(float(point[1])))))
    while len(normalized) < 4:
        normalized.append((0, 0))
    return {
        "x1": normalized[0][0],
        "x2": normalized[1][0],
        "x3": normalized[2][0],
        "x4": normalized[3][0],
        "y1": normalized[0][1],
        "y2": normalized[1][1],
        "y3": normalized[2][1],
        "y4": normalized[3][1],
    }


def bbox_to_points(bbox) -> list[list[int]]:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return [[0, 0], [0, 0], [0, 0], [0, 0]]
    x1, y1, x2, y2 = [int(round(float(value))) for value in bbox]
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


def compact_text(value: str) -> str:
    return re.sub(r"\s+", "", value or "")
