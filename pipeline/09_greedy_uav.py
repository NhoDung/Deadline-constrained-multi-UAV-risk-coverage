"""Greedy cho Budgeted Max Coverage có trọng số rủi ro và ngân sách riêng từng UAV.

- `proposed`: lazy ratio greedy + gói đơn tốt nhất + seed + drop-and-refill,
  mọi bước kiểm tra pin của UAV sở hữu route (phát triển từ 06_greedy_ls.py).
- `naive`: greedy_ls với ngân sách chung ΣB_u, bỏ route của UAV vượt pin, rồi
  lấp lại pin còn dư bằng ratio greedy (để baseline không bị thiệt vì sửa lỗi thô).

Chạy: python pipeline/09_greedy_uav.py --algorithm proposed [--tag g20_default]
      [--levels 100,75,50,25] [--seeds 20] [--ls-rounds 50] [--name proposed]
"""

import argparse
import heapq
import importlib.util
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.rn.budgets import budgets_for_level
from pipeline.rn.store import list_instances, load_instance, save_result


def _load_greedy_ls():
    """Nạp 06_greedy_ls.py (tên file có số đầu nên không import thường được)."""
    cached = sys.modules.get("pipeline.greedy_ls")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("pipeline.greedy_ls", Path(__file__).with_name("06_greedy_ls.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["pipeline.greedy_ls"] = module
    spec.loader.exec_module(module)
    return module


_ls = _load_greedy_ls()
_better, _ratio, _weight, prepare = _ls._better, _ls._ratio, _ls._weight, _ls.prepare
solve_shared_budget = _ls.solve


def lazy_ratio_greedy_uav(prep: dict, budgets: list, start=(), banned=()) -> tuple:
    """Như `lazy_ratio_greedy` của 06, nhưng route j chỉ chọn được khi còn đủ pin của UAV sở hữu nó."""
    costs, masks, weights, owner = prep["costs"], prep["masks"], prep["weights"], prep["route_uav"]
    remaining = list(budgets)
    selected = list(start)
    covered = 0
    for j in selected:
        covered |= masks[j]
        remaining[owner[j]] -= costs[j]

    excluded = set(selected) | set(banned)
    heap = []
    for j in range(prep["n"]):
        if j in excluded or costs[j] > remaining[owner[j]]:
            continue
        gain = _weight(masks[j] & ~covered, weights)
        if gain > 0:
            heap.append((-_ratio(gain, costs[j]), j, 0))
    heapq.heapify(heap)

    round_no = 0
    while heap:
        _, j, evaluated_at = heapq.heappop(heap)
        if costs[j] > remaining[owner[j]]:
            continue  # pin của UAV này chỉ giảm dần nên route sẽ không bao giờ vừa nữa
        if evaluated_at != round_no:
            gain = _weight(masks[j] & ~covered, weights)
            if gain > 0:
                heapq.heappush(heap, (-_ratio(gain, costs[j]), j, round_no))
            continue
        selected.append(j)
        covered |= masks[j]
        remaining[owner[j]] -= costs[j]
        round_no += 1

    return selected, _weight(covered, weights), sum(costs[j] for j in selected)


def _drop_and_refill(prep: dict, budgets: list, solution: tuple, max_rounds: int) -> tuple:
    best = solution
    for _ in range(max_rounds):
        improved = False
        for i in best[0]:
            kept = [j for j in best[0] if j != i]
            candidate = lazy_ratio_greedy_uav(prep, budgets, start=kept, banned=(i,))
            if _better(candidate, best):
                best, improved = candidate, True
                break
        if not improved:
            break
    return best


def _describe(instance: dict, prep: dict, selected: list, k: int) -> dict:
    covered = 0
    for j in selected:
        covered |= prep["masks"][j]
    cost_per_uav = [0] * k
    for j in selected:
        cost_per_uav[instance["route_uav"][j]] += instance["costs"][j]
    return {
        "selected_packages": list(selected),
        "covered_weight": float(_weight(covered, instance["weights"])),
        "covered_cells": int(_weight(covered, None)),
        "cost_per_uav": cost_per_uav,
        "cost": sum(cost_per_uav),
    }


def solve_uav(instance: dict, budgets: list, n_seeds: int = 20, ls_rounds: int = 50) -> dict:
    prep = {**prepare(instance), "route_uav": instance["route_uav"]}
    costs, masks, weights, owner = prep["costs"], prep["masks"], prep["weights"], prep["route_uav"]
    affordable = [j for j in range(prep["n"]) if costs[j] <= budgets[owner[j]]]
    single_gain = {j: _weight(masks[j], weights) for j in affordable}

    best = lazy_ratio_greedy_uav(prep, budgets)
    if affordable:
        top = max(affordable, key=lambda j: (single_gain[j], -costs[j], -j))
        single = ([top], single_gain[top], costs[top])
        if _better(single, best):
            best = single

    seeds = set()
    if n_seeds > 0:
        by_gain = sorted(affordable, key=lambda j: (-single_gain[j], costs[j], j))
        by_ratio = sorted(affordable, key=lambda j: (-_ratio(single_gain[j], costs[j]), j))
        seeds.update(by_gain[:n_seeds])
        seeds.update(by_ratio[:n_seeds])
    for j in sorted(seeds):
        candidate = lazy_ratio_greedy_uav(prep, budgets, start=[j])
        if _better(candidate, best):
            best = candidate

    if ls_rounds > 0 and best[0]:
        best = _drop_and_refill(prep, budgets, best, ls_rounds)
    return _describe(instance, prep, best[0], len(budgets))


def solve_naive_shared(instance: dict, budgets: list, n_seeds: int = 20, ls_rounds: int = 50) -> dict:
    """Baseline: bỏ qua ranh giới UAV khi chọn (ngân sách chung), sửa cho hợp lệ, rồi lấp lại pin dư.

    Bước lấp lại dùng cùng ratio greedy như `proposed` nhưng không có seed và local
    search, nên sự khác biệt còn lại giữa hai thuật toán là cách xét ngân sách riêng
    từng UAV ngay lúc chọn, không phải chất lượng bước sửa lỗi.
    """
    prep = {**prepare(instance), "route_uav": instance["route_uav"]}
    pooled = solve_shared_budget(instance, sum(budgets), n_seeds=n_seeds, ls_rounds=ls_rounds)
    selected = list(pooled["selected_packages"])
    costs, owner, weights = instance["costs"], instance["route_uav"], instance["weights"]
    for u, budget in enumerate(budgets):
        mine = [j for j in selected if owner[j] == u]
        mine.sort(key=lambda j: (_weight(prep["masks"][j], weights) / costs[j], -j))  # tỉ lệ thấp nhất bị bỏ trước
        while sum(costs[j] for j in mine) > budget:
            drop = mine.pop(0)
            selected.remove(drop)
    selected, _, _ = lazy_ratio_greedy_uav(prep, budgets, start=selected)
    return _describe(instance, prep, selected, len(budgets))


ALGORITHMS = {"proposed": solve_uav, "naive": solve_naive_shared}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", choices=sorted(ALGORITHMS), default="proposed")
    parser.add_argument("--name", default=None, help="Tên thư mục kết quả (mặc định = tên thuật toán); dùng cho ablation.")
    parser.add_argument("--tag", default="g20_default")
    parser.add_argument("--levels", default="100,75,50,25")
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--ls-rounds", type=int, default=50)
    args = parser.parse_args()
    name_out = args.name or args.algorithm
    levels = [int(x) for x in args.levels.split(",")]
    solver = ALGORITHMS[args.algorithm]

    for name in list_instances(args.tag):
        instance = load_instance(args.tag, name)
        for level in levels:
            budgets = budgets_for_level(instance, level)
            start = time.time()
            res = solver(instance, budgets, n_seeds=args.seeds, ls_rounds=args.ls_rounds)
            elapsed = time.time() - start
            save_result(args.tag, name_out, name, level, {
                "instance": name, "algorithm": name_out, "mode": "budgeted_uav",
                "budget_level": level, "budget_values": budgets, "status": "heuristic",
                "objective": res["covered_weight"], "covered_cells": res["covered_cells"],
                "cost_per_uav": res["cost_per_uav"], "selected_packages": res["selected_packages"],
                "solve_time_seconds": round(elapsed, 3),
                "params": {"seeds": args.seeds, "ls_rounds": args.ls_rounds},
            })
            print(f"[{name}] {name_out} {level}% -> {res['covered_weight']:.2f} ({elapsed:.2f}s)")


if __name__ == "__main__":
    main()
