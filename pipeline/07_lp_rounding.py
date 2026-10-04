"""LP Relaxation + Randomized Rounding cho Budgeted Max Coverage (có trọng số).

Giải bài toán nới lỏng tuyến tính (LP) một lần, rồi làm tròn ngẫu nhiên nghiệm
phân số nhiều lần; mỗi lần làm tròn được sửa cho vừa ngân sách và lấp phần ngân
sách còn dư bằng ratio greedy. Giá trị LP là cận trên của OPT.
Xem thiết kế đầy đủ ở docs/lp-rounding-thiet-ke.md.

Chạy: python pipeline/07_lp_rounding.py --instances scpa1,scp61 --budget-levels 75,50,25 --seeds 20
"""

import argparse
import importlib
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

import pulp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.opt_reference import OPT_REFERENCE

_greedy_ls = importlib.import_module("pipeline.06_greedy_ls")
prepare = _greedy_ls.prepare
lazy_ratio_greedy = _greedy_ls.lazy_ratio_greedy
_weight = _greedy_ls._weight
_better = _greedy_ls._better

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results" / "lp_rounding"

DEFAULT_SEEDS = 20
DEFAULT_SAMPLES = 200


def load_instance(name: str) -> dict:
    path = PROCESSED_DIR / f"{name}.json"
    return json.loads(path.read_text())


def solve_lp_relaxation(instance: dict, budget: int) -> tuple:
    """Giải LP nới lỏng của mô hình ILP (03_solve_ilp.py) với 0 ≤ x, y ≤ 1.

    Trả về (x, lp_bound): x[j] ∈ [0, 1] là nghiệm phân số của gói j, lp_bound là
    giá trị mục tiêu LP (cận trên của OPT).
    """
    m, n = instance["m"], instance["n"]
    costs = instance["costs"]
    weights = instance.get("weights") or [1] * m

    covering = [[] for _ in range(m)]
    for j, cells in enumerate(instance["sets"]):
        for i in cells:
            covering[i].append(j)

    prob = pulp.LpProblem("budgeted_max_coverage_lp", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x_{j}", lowBound=0, upBound=1) for j in range(n)]
    y = [pulp.LpVariable(f"y_{i}", lowBound=0, upBound=1) for i in range(m)]

    prob += pulp.lpSum(weights[i] * y[i] for i in range(m))
    prob += pulp.lpSum(costs[j] * x[j] for j in range(n)) <= budget, "budget"
    for i, packages in enumerate(covering):
        prob += y[i] <= pulp.lpSum(x[j] for j in packages), f"cover_link_{i}"

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    values = [min(1.0, max(0.0, v.value() or 0.0)) for v in x]
    return values, pulp.value(prob.objective) or 0.0


def repair_and_fill(prep: dict, budget: int, chosen) -> list:
    """Sửa một tập gói bất kỳ thành lời giải hợp lệ rồi lấp ngân sách còn dư.

    Khi vượt ngân sách: bỏ dần gói có tỉ lệ (trọng số chỉ mình nó phủ / chi phí)
    nhỏ nhất; hòa thì bỏ gói đắt hơn, rồi gói chỉ số lớn hơn. Sau đó chạy ratio
    greedy (CELF) bắt đầu từ các gói còn lại.
    """
    costs, masks, weights = prep["costs"], prep["masks"], prep["weights"]
    kept = sorted(set(chosen))
    spent = sum(costs[j] for j in kept)

    while spent > budget:
        worst = None
        worst_key = None
        for j in kept:
            others = 0
            for k in kept:
                if k != j:
                    others |= masks[k]
            unique = _weight(masks[j] & ~others, weights)
            ratio = math.inf if costs[j] == 0 else unique / costs[j]
            key = (ratio, -costs[j], -j)
            if worst_key is None or key < worst_key:
                worst, worst_key = j, key
        kept.remove(worst)
        spent -= costs[worst]

    selected, _, _ = lazy_ratio_greedy(prep, budget, start=kept)
    return selected


def solve(instance: dict, budget: int, seed: int, samples: int = DEFAULT_SAMPLES, lp=None) -> dict:
    """LP relaxation + randomized rounding.

    1. Giải LP (hoặc dùng `lp` = (x, lp_bound) đã tính sẵn để chạy nhiều seed).
    2. Làm tròn tất định: giữ các gói có x_j = 1, rồi sửa + lấp.
    3. `samples` lần làm tròn ngẫu nhiên: chọn gói j với xác suất x_j, rồi sửa + lấp.
    Trả về lời giải tốt nhất (phủ nhiều trọng số hơn, hòa thì rẻ hơn).
    """
    prep = prepare(instance)
    x, lp_bound = lp if lp is not None else solve_lp_relaxation(instance, budget)
    rng = random.Random(seed)

    def evaluate(selected):
        covered = _or_masks(prep, selected)
        return selected, _weight(covered, prep["weights"]), sum(prep["costs"][j] for j in selected)

    integral = [j for j in range(prep["n"]) if x[j] > 1 - 1e-6]
    best = evaluate(repair_and_fill(prep, budget, integral))

    fractional = [j for j in range(prep["n"]) if x[j] > 1e-6]
    for _ in range(samples):
        chosen = [j for j in fractional if rng.random() < x[j]]
        candidate = evaluate(repair_and_fill(prep, budget, chosen))
        if _better(candidate, best):
            best = candidate

    selected = best[0]
    covered_cells = _or_masks(prep, selected).bit_count()
    return {
        "selected_packages": selected,
        "covered_cells": covered_cells,
        "covered_weight": best[1],
        "cost": best[2],
        "lp_bound": lp_bound,
    }


def _or_masks(prep: dict, selected) -> int:
    covered = 0
    for j in selected:
        covered |= prep["masks"][j]
    return covered


def save_result(instance_name: str, level_label: str, budget: int, best: dict, runs: list, lp_time: float, params: dict) -> Path:
    """Ghi một file cho mỗi (instance, mức ngân sách): lời giải của seed tốt nhất
    (để validator kiểm tra) kèm thống kê của mọi seed trong `per_seed`."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = RESULTS_DIR / f"{instance_name}_budgeted_{level_label.rstrip('%')}.json"
    objectives = [r["objective"] for r in runs]
    payload = {
        "instance": instance_name,
        "algorithm": "lp_rounding",
        "mode": "budgeted",
        "budget_level": level_label,
        "budget_value": budget,
        "status": "heuristic",
        "objective": best["covered_cells"],
        "covered_weight": best["covered_weight"],
        "cost": best["cost"],
        "selected_packages": best["selected_packages"],
        "seed": best["seed"],
        "lp_bound": round(best["lp_bound"], 6),
        "lp_time_seconds": round(lp_time, 3),
        "solve_time_seconds": round(best["solve_time"], 3),
        "objective_mean": round(statistics.mean(objectives), 3),
        "objective_std": round(statistics.pstdev(objectives), 3),
        "objective_min": min(objectives),
        "objective_max": max(objectives),
        "per_seed": runs,
        "params": params,
    }
    dest.write_text(json.dumps(payload, indent=2))
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", default=None, help="Danh sách tên instance, cách nhau bởi dấu phẩy. Mặc định: tất cả trong data/processed/.")
    parser.add_argument("--budget-levels", default="75,50,25", help="Các mức %% OPT dùng cho ngân sách (mặc định 75,50,25).")
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS, help=f"Số seed ngẫu nhiên, chạy seed 0..N-1 (mặc định {DEFAULT_SEEDS}).")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES, help=f"Số lần làm tròn ngẫu nhiên mỗi seed (mặc định {DEFAULT_SAMPLES}).")
    args = parser.parse_args()

    budget_levels = [int(x) for x in args.budget_levels.split(",")]
    params = {"seeds": args.seeds, "samples": args.samples}

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
            lp = solve_lp_relaxation(instance, budget)
            lp_time = time.time() - start

            runs, best = [], None
            for seed in range(args.seeds):
                start = time.time()
                result = solve(instance, budget, seed=seed, samples=args.samples, lp=lp)
                solve_time = lp_time + time.time() - start
                runs.append({"seed": seed, "objective": result["covered_cells"], "cost": result["cost"], "solve_time_seconds": round(solve_time, 3)})
                if best is None or (result["covered_weight"], -result["cost"]) > (best["covered_weight"], -best["cost"]):
                    best = {**result, "seed": seed, "solve_time": solve_time}

            save_result(name, f"{level}%", budget, best, runs, lp_time, params)
            objectives = [r["objective"] for r in runs]
            print(
                f"[{name}] lp_rounding B={budget} ({level}% của OPT={ref_opt}) "
                f"-> best={best['covered_cells']}/{instance['m']} mean={statistics.mean(objectives):.1f} "
                f"LP<={lp[1]:.1f} lp_time={lp_time:.2f}s"
            )


if __name__ == "__main__":
    main()
