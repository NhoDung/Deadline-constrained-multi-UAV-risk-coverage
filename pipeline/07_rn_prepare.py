"""Chuẩn bị instance RescueNet cho Pha 2 (docs/phase2-rescuenet-thiet-ke.md).

Hai bước:
  python pipeline/07_rn_prepare.py select [--all]
      -> data/rescuenet/image_stats.json (thống kê mọi mask)
         data/rescuenet/selection.json   (30 ảnh phân tầng, có seed)
         với --all: data/rescuenet/selection_all.json (MỌI ảnh đủ điều kiện --min-cells)
  python pipeline/07_rn_prepare.py build [--grid 20] [--table default]
        [--selection selection_all.json --tag full_g20_default] [--shard K/N]
      -> data/rescuenet/<tag>/instances/<id>.json  (tag mặc định = g<grid>_<table>)
Sensitivity: chạy `build` với --grid/--table khác, vẫn dùng chung selection.json.
`--shard K/N` (K từ 0): chỉ build phần K trong N phần, để chạy song song nhiều tiến trình.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.rn.budgets import reference_cost
from pipeline.rn.risk import SCORE_TABLES, cell_risk, damage_fraction, load_mask
from pipeline.rn.routes import build_instance
from pipeline.rn.select import select_images
from pipeline.rn.store import RN_DIR, tag_dir

MASK_DIR = Path(__file__).resolve().parent.parent / "data" / "RescueNet" / "segmentation-validationset" / "val-label-img"
SELECT_GRID, SELECT_TABLE = 20, "default"


def build_from_mask(mask: np.ndarray, grid: int, table_name: str, k: int,
                    routes_per_uav: int, max_cells: int, seed: int) -> dict:
    risk = cell_risk(mask, grid, SCORE_TABLES[table_name])
    instance = build_instance(risk, k, routes_per_uav, max_cells, seed)
    instance["reference_cost"] = reference_cost(instance)
    return instance


def shard_items(items: list, index: int, count: int) -> list:
    """Phần `index` (từ 0) trong `count` phần chia vòng tròn; các phần không giao nhau và hợp lại đủ."""
    return items[index::count]


def image_id(path: Path) -> str:
    return path.name.removesuffix("_lab.png")


def cmd_select(args) -> None:
    stats = []
    for path in sorted(MASK_DIR.glob("*_lab.png")):
        mask = load_mask(path)
        risk = cell_risk(mask, SELECT_GRID, SCORE_TABLES[SELECT_TABLE])
        stats.append({"id": image_id(path), "damage_frac": damage_fraction(mask),
                      "nonzero_cells": int((risk > 0).sum())})
    RN_DIR.mkdir(parents=True, exist_ok=True)
    (RN_DIR / "image_stats.json").write_text(json.dumps(stats, indent=1))
    chosen = select_images(stats, None if args.all else args.per_tier, args.min_cells, args.seed)
    payload = {"seed": args.seed, "per_tier": None if args.all else args.per_tier, "min_cells": args.min_cells,
               "grid": SELECT_GRID, "table": SELECT_TABLE, "images": chosen}
    (RN_DIR / ("selection_all.json" if args.all else "selection.json")).write_text(json.dumps(payload, indent=1))
    eligible = sum(s["nonzero_cells"] >= args.min_cells for s in stats)
    print(f"{len(stats)} ảnh, {eligible} đủ điều kiện, chọn {len(chosen)}")


def cmd_build(args) -> None:
    selection = json.loads((RN_DIR / args.selection).read_text())
    out_dir = tag_dir(args.tag or f"g{args.grid}_{args.table}") / "instances"
    out_dir.mkdir(parents=True, exist_ok=True)
    skipped = []
    images = selection["images"]
    skipped_name = "skipped.json"
    if args.shard:
        index, count = (int(x) for x in args.shard.split("/"))
        images = shard_items(images, index, count)
        skipped_name = f"skipped_{index}of{count}.json"
    for entry in images:
        mask = load_mask(MASK_DIR / f"{entry['id']}_lab.png")
        try:
            instance = build_from_mask(mask, args.grid, args.table, args.k, args.routes_per_uav,
                                       args.max_cells, seed=int(entry["id"]))
        except ValueError as error:  # ví dụ bảng damage_only: ảnh không có hư hại -> không có ô điểm > 0
            print(f"[{entry['id']}] BỎ QUA: {error}")
            skipped.append({"id": entry["id"], "tier": entry["tier"], "reason": str(error)})
            continue
        instance.update({"image_id": entry["id"], "tier": entry["tier"], "table": args.table})
        (out_dir / f"{entry['id']}.json").write_text(json.dumps(instance))
        print(f"[{entry['id']}] m={instance['m']} n={instance['n']} R={instance['reference_cost']}")
    (out_dir.parent / skipped_name).write_text(json.dumps(skipped, indent=1))
    print(f"đã bỏ qua {len(skipped)}/{len(images)} ảnh (xem {skipped_name})")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("select")
    s.add_argument("--per-tier", type=int, default=10)
    s.add_argument("--min-cells", type=int, default=60)
    s.add_argument("--seed", type=int, default=2026)
    s.add_argument("--all", action="store_true", help="chọn mọi ảnh đủ điều kiện, ghi selection_all.json")
    s.set_defaults(func=cmd_select)
    b = sub.add_parser("build")
    b.add_argument("--grid", type=int, default=20)
    b.add_argument("--table", default="default", choices=sorted(SCORE_TABLES))
    b.add_argument("--selection", default="selection.json", help="file danh sách ảnh trong data/rescuenet/")
    b.add_argument("--tag", default=None, help="tên thư mục đầu ra (mặc định g<grid>_<table>)")
    b.add_argument("--shard", default=None, help="K/N: chỉ build phần K (từ 0) trong N phần")
    b.add_argument("--k", type=int, default=4)
    b.add_argument("--routes-per-uav", type=int, default=300)
    b.add_argument("--max-cells", type=int, default=40)
    b.set_defaults(func=cmd_build)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
