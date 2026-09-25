"""ILP solver chính xác (PuLP/CBC) cho Set Cover và Budgeted Max Coverage.

Xem thiết kế đầy đủ (công thức toán, sơ đồ) ở docs/ilp-solver-thiet-ke.md.

Chạy: python scripts/solve_ilp.py --instances scpa1,scp61 --time-limit 120
"""

import argparse
import json
import math
import time
from pathlib import Path

import pulp

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results" / "ilp"

# Bảng OPT tham khảo — mục 3 project-brief.md (Ohlsson, Peterson & Söderberg 1999, bảng C2).
# Chưa tự xác nhận lại bằng ILP; dùng tạm để tính mức ngân sách B cho chế độ budgeted.
OPT_REFERENCE = {}
_OPT_TABLE = {
    "scp4": [429, 512, 516, 494, 512, 560, 430, 492, 641, 514],
    "scp5": [253, 302, 226, 242, 211, 213, 293, 288, 279, 265],
    "scp6": [138, 146, 145, 131, 161],
    "scpa": [253, 252, 232, 234, 236],
    "scpb": [69, 76, 80, 79, 72],
    "scpc": [227, 219, 243, 219, 215],
    "scpd": [60, 66, 72, 62, 61],
}
for prefix, values in _OPT_TABLE.items():
    for idx, value in enumerate(values, start=1):
        OPT_REFERENCE[f"{prefix}{idx}"] = value


def load_instance(name: str) -> dict:
    path = PROCESSED_DIR / f"{name}.json"
    return json.loads(path.read_text())


def cells_covering(instance: dict) -> list:
    """Với mỗi ô i, trả về danh sách chỉ số gói phủ ô đó (đảo ngược instance['sets'])."""
    covering = [[] for _ in range(instance["m"])]
    for j, cells in enumerate(instance["sets"]):
        for i in cells:
            covering[i].append(j)
    return covering


def solve_setcover(instance: dict, time_limit: int) -> dict:
    n = instance["n"]
    costs = instance["costs"]
    covering = cells_covering(instance)

    prob = pulp.LpProblem("set_cover", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(n)]

    prob += pulp.lpSum(costs[j] * x[j] for j in range(n))
    for i, packages in enumerate(covering):
        prob += pulp.lpSum(x[j] for j in packages) >= 1, f"cover_cell_{i}"

    start = time.time()
    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    solve_time = time.time() - start

    selected = [j for j in range(n) if x[j].value() > 0.5]
    is_optimal = pulp.LpStatus[prob.status] == "Optimal"

    return {
        "mode": "setcover",
        "budget_level": None,
        "budget_value": None,
        "status": "optimal" if is_optimal else "best-known",
        "objective": sum(costs[j] for j in selected),
        "selected_packages": selected,
        "solve_time_seconds": round(solve_time, 3),
        "time_limit_seconds": time_limit,
    }


def solve_budgeted(instance: dict, budget: int, level_label: str, time_limit: int) -> dict:
    m, n = instance["m"], instance["n"]
    costs = instance["costs"]
    covering = cells_covering(instance)

    prob = pulp.LpProblem("budgeted_max_coverage", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(n)]
    y = [pulp.LpVariable(f"y_{i}", cat="Binary") for i in range(m)]

    prob += pulp.lpSum(y)
    prob += pulp.lpSum(costs[j] * x[j] for j in range(n)) <= budget, "budget"
    for i, packages in enumerate(covering):
        prob += y[i] <= pulp.lpSum(x[j] for j in packages), f"cover_link_{i}"

    start = time.time()
    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    solve_time = time.time() - start

    selected = [j for j in range(n) if x[j].value() > 0.5]
    covered = sum(1 for i in range(m) if y[i].value() > 0.5)
    is_optimal = pulp.LpStatus[prob.status] == "Optimal"

    return {
        "mode": "budgeted",
        "budget_level": level_label,
        "budget_value": budget,
        "status": "optimal" if is_optimal else "best-known",
        "objective": covered,
        "selected_packages": selected,
        "solve_time_seconds": round(solve_time, 3),
        "time_limit_seconds": time_limit,
    }


def save_result(instance_name: str, result: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = result["mode"]
    if result["budget_level"]:
        suffix += f"_{result['budget_level'].rstrip('%')}"
    dest = RESULTS_DIR / f"{instance_name}_{suffix}.json"
    payload = {"instance": instance_name, **result}
    dest.write_text(json.dumps(payload, indent=2))
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", default=None, help="Danh sách tên instance, cách nhau bởi dấu phẩy. Mặc định: tất cả trong data/processed/.")
    parser.add_argument("--modes", default="setcover,budgeted", help="setcover, budgeted, hoặc cả hai (mặc định).")
    parser.add_argument("--time-limit", type=int, default=120, help="Giây, time limit cho mỗi lần giải (mặc định 120s).")
    parser.add_argument("--budget-levels", default="75,50,25", help="Các mức % OPT dùng cho chế độ budgeted (mặc định 75,50,25 — mức 100% không cần solver).")
    args = parser.parse_args()

    modes = args.modes.split(",")
    budget_levels = [int(x) for x in args.budget_levels.split(",")]

    if args.instances:
        instance_names = args.instances.split(",")
    else:
        instance_names = sorted(p.stem for p in PROCESSED_DIR.glob("*.json"))

    for name in instance_names:
        instance = load_instance(name)

        if "setcover" in modes:
            print(f"[{name}] giải setcover (time_limit={args.time_limit}s)...")
            result = solve_setcover(instance, args.time_limit)
            ref_opt = OPT_REFERENCE.get(name)
            match_note = ""
            if ref_opt is not None:
                match_note = " (khớp bảng OPT tham khảo)" if result["objective"] == ref_opt else f" (LỆCH bảng OPT tham khảo={ref_opt})"
            print(f"  -> status={result['status']} objective={result['objective']}{match_note} time={result['solve_time_seconds']}s")
            save_result(name, result)

        if "budgeted" in modes:
            ref_opt = OPT_REFERENCE.get(name)
            if ref_opt is None:
                print(f"[{name}] bỏ qua budgeted: không có OPT tham khảo cho instance này.")
                continue
            for level in budget_levels:
                budget = math.floor(level / 100 * ref_opt)
                print(f"[{name}] giải budgeted B={budget} ({level}% của OPT={ref_opt}, time_limit={args.time_limit}s)...")
                result = solve_budgeted(instance, budget, f"{level}%", args.time_limit)
                print(f"  -> status={result['status']} objective(số ô phủ)={result['objective']}/{instance['m']} time={result['solve_time_seconds']}s")
                save_result(name, result)


if __name__ == "__main__":
    main()
