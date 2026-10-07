"""Đường dẫn và đọc/ghi file cho dữ liệu Pha 2 (data/rescuenet/<tag>/...)."""

import json
from pathlib import Path

RN_DIR = Path(__file__).resolve().parents[2] / "data" / "rescuenet"


def tag_dir(tag: str) -> Path:
    return RN_DIR / tag


def list_instances(tag: str) -> list:
    return sorted(p.stem for p in (tag_dir(tag) / "instances").glob("*.json"))


def load_instance(tag: str, name: str) -> dict:
    return json.loads((tag_dir(tag) / "instances" / f"{name}.json").read_text())


def save_result(tag: str, algorithm: str, instance_name: str, level: int, payload: dict) -> Path:
    dest = tag_dir(tag) / "results" / algorithm / f"{instance_name}_{level}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2))
    return dest
