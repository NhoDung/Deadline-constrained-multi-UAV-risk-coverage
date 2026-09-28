"""Greedy thuần cho Budgeted Max Coverage.

Xem thiết kế đầy đủ ở docs/greedy-thuan-thiet-ke.md.

Chạy: python baseline/greedy_pure.py --instances scpa1,scp61 --budget-levels 75,50,25
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.opt_reference import OPT_REFERENCE

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results" / "greedy"


def load_instance(name: str) -> dict:
    path = PROCESSED_DIR / f"{name}.json"
    return json.loads(path.read_text())


def greedy_budgeted(instance: dict, budget: int) -> dict:
    """Chọn lần lượt gói phủ được nhiều ô mới nhất, miễn còn vừa ngân sách.

    Không xét chi phí khi so sánh các gói (đây là điểm khác với greedy tỉ lệ) —
    chi phí chỉ dùng để lọc gói nào còn vừa ngân sách còn lại. Hòa số ô mới
    phủ được thì chọn gói có chỉ số nhỏ nhất.
    """
    costs = instance["costs"]
    sets = instance["sets"]
    n = instance["n"]

    covered = set()
    selected = []
    remaining_budget = budget
    total_cost = 0
    available = set(range(n))

    while True:
        best_j = None
        best_new_cells = 0
        for j in available:
            if costs[j] > remaining_budget:
                continue
            new_cells = len(set(sets[j]) - covered)
            if new_cells > best_new_cells:
                best_new_cells = new_cells
                best_j = j

        if best_j is None:
            break

        selected.append(best_j)
        covered |= set(sets[best_j])
        remaining_budget -= costs[best_j]
        total_cost += costs[best_j]
        available.discard(best_j)

    return {
        "selected_packages": selected,
        "covered_cells": len(covered),
        "cost": total_cost,
    }


def save_result(instance_name: str, level_label: str, budget: int, result: dict, solve_time: float) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = RESULTS_DIR / f"{instance_name}_budgeted_{level_label.rstrip('%')}.json"
    payload = {
        "instance": instance_name,
        "algorithm": "greedy_pure",
        "mode": "budgeted",
        "budget_level": level_label,
        "budget_value": budget,
        "status": "greedy",
        "objective": result["covered_cells"],
        "cost": result["cost"],
        "selected_packages": result["selected_packages"],
        "solve_time_seconds": round(solve_time, 3),
    }
    dest.write_text(json.dumps(payload, indent=2))
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", default=None, help="Danh sách tên instance, cách nhau bởi dấu phẩy. Mặc định: tất cả trong data/processed/.")
    parser.add_argument("--budget-levels", default="75,50,25", help="Các mức %% OPT dùng cho ngân sách (mặc định 75,50,25).")
    args = parser.parse_args()

    budget_levels = [int(x) for x in args.budget_levels.split(",")]

    if args.instances:
        instance_names = args.instances.split(",")
    else:
        instance_names = sorted(p.stem for p in PROCESSED_DIR.glob("*.json"))

    for name in instance_names:
        ref_opt = OPT_REFERENCE.get(name)
        if ref_opt is None:
            print(f"[{name}] bỏ qua: không có OPT tham khảo cho instance này.")
            continue

        instance = load_instance(name)
        for level in budget_levels:
            budget = math.floor(level / 100 * ref_opt)
            start = time.time()
            result = greedy_budgeted(instance, budget)
            solve_time = time.time() - start
            print(
                f"[{name}] greedy B={budget} ({level}% của OPT={ref_opt}) "
                f"-> objective(số ô phủ)={result['covered_cells']}/{instance['m']} "
                f"cost={result['cost']} time={round(solve_time, 3)}s"
            )
            save_result(name, f"{level}%", budget, result, solve_time)


if __name__ == "__main__":
    main()
