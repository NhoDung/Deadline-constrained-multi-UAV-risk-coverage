"""ILP chính xác (PuLP/CBC) cho Budgeted Max Coverage có trọng số rủi ro và
ngân sách riêng từng UAV. Đáp án tham chiếu của Pha 2
(docs/phase2-rescuenet-thiet-ke.md mục 6).

Chạy: python pipeline/08_ilp_uav.py [--tag g20_default] [--levels 100,75,50,25] [--time-limit 120]
      [--instances 11690,12016]   (chạy một phần, để song song nhiều tiến trình)
"""

import argparse
import sys
import time
from pathlib import Path

import pulp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.rn.budgets import budgets_for_level
from pipeline.rn.store import list_instances, load_instance, save_result


def status_label(prob) -> str:
    """`LpStatus` vẫn báo "Optimal" khi CBC hết giờ mà có nghiệm khả thi; chỉ
    `sol_status == 1` mới là nghiệm đã được chứng minh tối ưu."""
    return "optimal" if prob.sol_status == pulp.LpSolutionOptimal else "best-known"


def solve_uav_ilp(instance: dict, budgets: list, time_limit: int) -> dict:
    """max Σ w_i y_i  với  y_i ≤ Σ_{j phủ i} x_j  và  Σ_{j của UAV u} c_j x_j ≤ B_u.

    `y` để liên tục trong [0, 1]: vì trọng số ≥ 0 nên tối ưu tự đẩy y về 0/1.
    """
    n, m = instance["n"], instance["m"]
    costs, owner, weights = instance["costs"], instance["route_uav"], instance["weights"]
    covering = [[] for _ in range(m)]
    for j, cells in enumerate(instance["sets"]):
        for i in cells:
            covering[i].append(j)

    prob = pulp.LpProblem("uav_budgeted_coverage", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(n)]
    y = [pulp.LpVariable(f"y_{i}", lowBound=0, upBound=1) for i in range(m)]
    prob += pulp.lpSum(weights[i] * y[i] for i in range(m))
    for u, budget in enumerate(budgets):
        prob += pulp.lpSum(costs[j] * x[j] for j in range(n) if owner[j] == u) <= budget, f"budget_uav_{u}"
    for i, routes in enumerate(covering):
        prob += y[i] <= pulp.lpSum(x[j] for j in routes), f"link_{i}"

    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    selected = [j for j in range(n) if x[j].value() is not None and x[j].value() > 0.5]
    covered = {i for j in selected for i in instance["sets"][j]}
    return {
        "status": status_label(prob),
        "objective": float(sum(weights[i] for i in covered)),
        "selected_packages": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="g20_default")
    parser.add_argument("--levels", default="100,75,50,25")
    parser.add_argument("--time-limit", type=int, default=120)
    parser.add_argument("--instances", default=None, help="Danh sách instance cách nhau bởi dấu phẩy (mặc định: tất cả).")
    args = parser.parse_args()
    levels = [int(x) for x in args.levels.split(",")]

    names = args.instances.split(",") if args.instances else list_instances(args.tag)
    for name in names:
        instance = load_instance(args.tag, name)
        for level in levels:
            budgets = budgets_for_level(instance, level)
            start = time.time()
            res = solve_uav_ilp(instance, budgets, args.time_limit)
            elapsed = time.time() - start
            cells = {i for j in res["selected_packages"] for i in instance["sets"][j]}
            cost_per_uav = [sum(instance["costs"][j] for j in res["selected_packages"] if instance["route_uav"][j] == u)
                            for u in range(len(budgets))]
            save_result(args.tag, "ilp", name, level, {
                "instance": name, "algorithm": "ilp_uav", "mode": "budgeted_uav",
                "budget_level": level, "budget_values": budgets, "status": res["status"],
                "objective": res["objective"], "covered_cells": len(cells),
                "cost_per_uav": cost_per_uav, "selected_packages": res["selected_packages"],
                "solve_time_seconds": round(elapsed, 3), "time_limit_seconds": args.time_limit,
            })
            print(f"[{name}] ILP {level}% B={budgets} -> {res['objective']:.2f} ({res['status']}, {elapsed:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
