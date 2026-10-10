"""Đo thời gian chạy của thuật toán Pha 2 (docs/phase2-thoi-gian-chay.md).

`solve_time_seconds` trong file kết quả đã có thời gian một lần chạy của từng thuật toán.
Script này đo thêm những thứ pipeline không ghi sẵn:
  lazy   so ratio greedy lazy (CELF) với bản duyệt lại toàn bộ: số lần đánh giá, thời gian
  runs   số lần chạy ratio greedy trong một lần `solve_uav` (gốc + seed + local search)
  seeds  thời gian và chất lượng (tỉ lệ so với ILP) theo số seed
  scale  thời gian theo n (số route) và m (số ô) trên instance ngẫu nhiên tổng hợp

Chạy: python pipeline/12_timing_rn.py lazy|runs|seeds|scale [--tag g20_default]
Mỗi lệnh in tóm tắt và ghi CSV vào data/rescuenet/<tag>/timing_<lệnh>.csv
(riêng `scale`: data/rescuenet/timing_scale.csv). Thời gian là giá trị nhỏ nhất của --repeats lần đo.
"""

import argparse
import csv
import importlib.util
import json
import math
import statistics
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.rn.budgets import budgets_for_level
from pipeline.rn.routes import build_instance
from pipeline.rn.store import RN_DIR, list_instances, load_instance, tag_dir


def _greedy_uav_module():
    """Nạp 09_greedy_uav.py (tên file có số đầu nên không import thường được)."""
    cached = sys.modules.get("pipeline.greedy_uav")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("pipeline.greedy_uav", Path(__file__).with_name("09_greedy_uav.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["pipeline.greedy_uav"] = module
    spec.loader.exec_module(module)
    return module


gu = _greedy_uav_module()


def prep_of(instance: dict) -> dict:
    return {**gu.prepare(instance), "route_uav": instance["route_uav"]}


def greedy_plain(prep: dict, budgets: list) -> tuple:
    """Ratio greedy KHÔNG lazy: mỗi bước tính lại giá trị mới của mọi route còn vừa pin.

    Cùng tiêu chí và cùng cách phá hòa (chỉ số nhỏ nhất) với `lazy_ratio_greedy_uav`.
    Trả về (selected, số lần đánh giá giá trị mới).
    """
    costs, masks, weights, owner = prep["costs"], prep["masks"], prep["weights"], prep["route_uav"]
    remaining = list(budgets)
    chosen, selected, covered, evaluations = set(), [], 0, 0
    while True:
        best_j, best_ratio = None, 0
        for j in range(prep["n"]):
            if j in chosen or costs[j] > remaining[owner[j]]:
                continue
            gain = gu._weight(masks[j] & ~covered, weights)
            evaluations += 1
            if gain > 0:
                ratio = gu._ratio(gain, costs[j])
                if ratio > best_ratio:
                    best_j, best_ratio = j, ratio
        if best_j is None:
            return selected, evaluations
        selected.append(best_j)
        chosen.add(best_j)
        covered |= masks[best_j]
        remaining[owner[best_j]] -= costs[best_j]


def count_lazy_evals(prep: dict, budgets: list) -> tuple:
    """Chạy `lazy_ratio_greedy_uav` và đếm số lần đánh giá giá trị mới.

    Trả về (kết quả (selected, weight, cost), số lần đánh giá). Không tính lần cuối cùng
    hàm tự cộng tổng giá trị đã phủ.
    """
    original, counter = gu._weight, [0]

    def counting(mask, weights):
        counter[0] += 1
        return original(mask, weights)

    gu._weight = counting
    try:
        result = gu.lazy_ratio_greedy_uav(prep, budgets)
    finally:
        gu._weight = original
    return result, counter[0] - 1


def count_greedy_runs(instance: dict, budgets: list, n_seeds: int = 20, ls_rounds: int = 50) -> int:
    """Số lần `lazy_ratio_greedy_uav` được gọi trong một lần `solve_uav`."""
    original, counter = gu.lazy_ratio_greedy_uav, [0]

    def counting(*args, **kwargs):
        counter[0] += 1
        return original(*args, **kwargs)

    gu.lazy_ratio_greedy_uav = counting
    try:
        gu.solve_uav(instance, budgets, n_seeds, ls_rounds)
    finally:
        gu.lazy_ratio_greedy_uav = original
    return counter[0]


def synth_instance(grid: int, routes_per_uav: int, seed: int = 0) -> dict:
    """Instance ngẫu nhiên tổng hợp (mọi ô điểm > 0, K = 4 UAV) chỉ để xem xu hướng thời gian."""
    risk = np.random.default_rng(seed).random((grid, grid)) + 0.05
    return build_instance(risk, 4, routes_per_uav, 40, seed)


def fit_loglog_exponent(xs: list, ys: list) -> float:
    """Hệ số mũ a của đường thẳng log y = a log x + b (thời gian ∝ x^a)."""
    return float(np.polyfit(np.log(xs), np.log(ys), 1)[0])


def best_time(function, repeats: int) -> tuple:
    """(thời gian nhỏ nhất của `repeats` lần, kết quả lần cuối)."""
    best, result = math.inf, None
    for _ in range(repeats):
        start = time.perf_counter()
        result = function()
        best = min(best, time.perf_counter() - start)
    return best, result


def _write_csv(path: Path, header: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    print(f"đã ghi {path}")


def _levels(args) -> list:
    return [int(x) for x in args.levels.split(",")]


def cmd_lazy(args) -> None:
    rows = []
    for name in list_instances(args.tag):
        instance = load_instance(args.tag, name)
        prep = prep_of(instance)
        for level in _levels(args):
            budgets = budgets_for_level(instance, level)
            t_lazy, (lazy, lazy_evals) = best_time(lambda: count_lazy_evals(prep, budgets), args.repeats)
            t_plain, (plain, plain_evals) = best_time(lambda: greedy_plain(prep, budgets), args.repeats)
            rows.append([name, level, instance["n"], len(plain), lazy_evals, plain_evals,
                         f"{t_lazy:.6f}", f"{t_plain:.6f}", int(lazy[0] == plain)])
    _write_csv(tag_dir(args.tag) / "timing_lazy.csv",
               ["instance", "level", "n", "k", "evals_lazy", "evals_plain", "time_lazy", "time_plain", "same_solution"], rows)
    print(f"cùng lời giải: {sum(r[-1] for r in rows)}/{len(rows)} lần")
    for level in _levels(args):
        r = [x for x in rows if x[1] == level]
        mean = lambda i: statistics.mean(float(x[i]) for x in r)
        print(f"@{level}%: n TB {mean(2):.0f}, k TB {mean(3):.1f}; số lần đánh giá lazy {mean(4):.0f} / không lazy {mean(5):.0f} "
              f"(giảm {mean(5) / mean(4):.1f}x); thời gian {mean(6) * 1000:.2f} ms / {mean(7) * 1000:.2f} ms "
              f"(nhanh {mean(7) / mean(6):.1f}x)")


def cmd_runs(args) -> None:
    rows = []
    for name in list_instances(args.tag):
        instance = load_instance(args.tag, name)
        for level in _levels(args):
            budgets = budgets_for_level(instance, level)
            solution = gu.solve_uav(instance, budgets)
            rows.append([name, level, count_greedy_runs(instance, budgets), len(solution["selected_packages"])])
    _write_csv(tag_dir(args.tag) / "timing_runs.csv", ["instance", "level", "greedy_runs", "k"], rows)
    runs = [r[2] for r in rows]
    print(f"số lần chạy greedy mỗi lần giải: TB {statistics.mean(runs):.1f}, nhỏ nhất {min(runs)}, lớn nhất {max(runs)}; "
          f"k TB {statistics.mean(r[3] for r in rows):.1f}")


def cmd_seeds(args) -> None:
    seed_values = [int(x) for x in args.seed_values.split(",")]
    rows = []
    for name in list_instances(args.tag):
        instance = load_instance(args.tag, name)
        for level in _levels(args):
            reference = json.loads((tag_dir(args.tag) / "results" / "ilp" / f"{name}_{level}.json").read_text())["objective"]
            if not reference:
                continue  # tối ưu ILP bằng 0: tỉ lệ không xác định
            budgets = budgets_for_level(instance, level)
            for n_seeds in seed_values:
                seconds, result = best_time(lambda: gu.solve_uav(instance, budgets, n_seeds, args.ls_rounds), args.repeats)
                rows.append([name, level, n_seeds, f"{seconds:.6f}", f"{result['covered_weight'] / reference:.6f}"])
    _write_csv(tag_dir(args.tag) / "timing_seeds.csv", ["instance", "level", "n_seeds", "time", "ratio_to_ilp"], rows)
    print("số seed | thời gian TB (ms) | tỉ lệ TB so với ILP theo mức " + "/".join(f"{lv}%" for lv in _levels(args)))
    for n_seeds in seed_values:
        r = [x for x in rows if x[2] == n_seeds]
        ratios = [statistics.mean(float(x[4]) for x in r if x[1] == lv) for lv in _levels(args)]
        print(f"{n_seeds:7d} | {statistics.mean(float(x[3]) for x in r) * 1000:8.1f}          | " + "  ".join(f"{v:.4f}" for v in ratios))


def cmd_scale(args) -> None:
    budgets = [60] * 4
    rows = []

    def measure(sweep, parameter, instance):
        seconds, result = best_time(lambda: gu.solve_uav(instance, budgets), args.repeats)
        rows.append([sweep, parameter, instance["n"], instance["m"], len(result["selected_packages"]), f"{seconds:.6f}"])

    for routes in (50, 100, 200, 400, 800, 1600, 3200, 6400):
        measure("n", routes, synth_instance(20, routes))
    for grid in (10, 14, 20, 28, 40, 56):
        measure("m", grid, synth_instance(grid, 400))
    _write_csv(RN_DIR / "timing_scale.csv", ["sweep", "parameter", "n", "m", "k", "time"], rows)
    for sweep, x_index, label in (("n", 2, "n"), ("m", 3, "m")):
        r = [x for x in rows if x[0] == sweep]
        for x in r:
            print(f"  [{sweep}] tham số={x[1]:>5} n={x[2]:>6} m={x[3]:>5} k={x[4]:>2} thời gian={float(x[5]) * 1000:8.1f} ms")
        exponent = fit_loglog_exponent([x[x_index] for x in r], [float(x[5]) for x in r])
        print(f"  hệ số mũ log-log (thời gian ~ {label}^a): a = {exponent:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in (("lazy", cmd_lazy), ("runs", cmd_runs), ("seeds", cmd_seeds), ("scale", cmd_scale)):
        p = sub.add_parser(name)
        p.add_argument("--tag", default="g20_default")
        p.add_argument("--repeats", type=int, default=3, help="số lần đo, lấy nhỏ nhất (mặc định 3)")
        p.add_argument("--levels", default="50,100" if name in ("lazy", "runs") else "25,50,75,100")
        if name == "seeds":
            p.add_argument("--seed-values", default="0,5,10,20,40,80")
            p.add_argument("--ls-rounds", type=int, default=50)
        p.set_defaults(func=func)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
