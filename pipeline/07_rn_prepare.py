"""Chuẩn bị instance RescueNet cho Pha 2 (docs/phase2-rescuenet-thiet-ke.md).

Hai bước:
  python pipeline/07_rn_prepare.py select
      -> data/rescuenet/image_stats.json (thống kê mọi mask)
         data/rescuenet/selection.json   (ảnh được chọn, phân tầng, có seed)
  python pipeline/07_rn_prepare.py build [--grid 20] [--table default]
      -> data/rescuenet/<tag>/instances/<id>.json  (tag = g<grid>_<table>)
Sensitivity: chạy `build` với --grid/--table khác, vẫn dùng chung selection.json.
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
    chosen = select_images(stats, args.per_tier, args.min_cells, args.seed)
    payload = {"seed": args.seed, "per_tier": args.per_tier, "min_cells": args.min_cells,
               "grid": SELECT_GRID, "table": SELECT_TABLE, "images": chosen}
    (RN_DIR / "selection.json").write_text(json.dumps(payload, indent=1))
    eligible = sum(s["nonzero_cells"] >= args.min_cells for s in stats)
    print(f"{len(stats)} ảnh, {eligible} đủ điều kiện, chọn {len(chosen)}")


def cmd_build(args) -> None:
    selection = json.loads((RN_DIR / "selection.json").read_text())
    out_dir = tag_dir(f"g{args.grid}_{args.table}") / "instances"
    out_dir.mkdir(parents=True, exist_ok=True)
    for entry in selection["images"]:
        mask = load_mask(MASK_DIR / f"{entry['id']}_lab.png")
        instance = build_from_mask(mask, args.grid, args.table, args.k, args.routes_per_uav,
                                   args.max_cells, seed=int(entry["id"]))
        instance.update({"image_id": entry["id"], "tier": entry["tier"], "table": args.table})
        (out_dir / f"{entry['id']}.json").write_text(json.dumps(instance))
        print(f"[{entry['id']}] m={instance['m']} n={instance['n']} R={instance['reference_cost']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("select")
    s.add_argument("--per-tier", type=int, default=10)
    s.add_argument("--min-cells", type=int, default=60)
    s.add_argument("--seed", type=int, default=2026)
    s.set_defaults(func=cmd_select)
    b = sub.add_parser("build")
    b.add_argument("--grid", type=int, default=20)
    b.add_argument("--table", default="default", choices=sorted(SCORE_TABLES))
    b.add_argument("--k", type=int, default=4)
    b.add_argument("--routes-per-uav", type=int, default=300)
    b.add_argument("--max-cells", type=int, default=40)
    b.set_defaults(func=cmd_build)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
