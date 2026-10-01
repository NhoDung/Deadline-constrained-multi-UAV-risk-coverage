"""Seeded Lazy Ratio Greedy + Local Search cho Budgeted Max Coverage (có trọng số).

Thuật toán dùng chung cho cả OR-Library (trọng số ô = 1) và instance
RescueNet (trọng số rủi ro theo ô, trường `weights` tùy chọn trong instance).
Xem thiết kế đầy đủ ở docs/greedy-ls-thiet-ke.md.

Chạy: python pipeline/06_greedy_ls.py --instances scpa1,scp61 --budget-levels 75,50,25
"""

import argparse
import heapq
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.opt_reference import OPT_REFERENCE

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results" / "greedy_ls"

DEFAULT_SEEDS = 20
DEFAULT_LS_ROUNDS = 50


def load_instance(name: str) -> dict:
    path = PROCESSED_DIR / f"{name}.json"
    return json.loads(path.read_text())


def prepare(instance: dict) -> dict:
    """Chuyển mỗi gói thành bitmask ô (int Python) để tính độ phủ mới nhanh.

    `weights` (tùy chọn) = trọng số rủi ro từng ô; thiếu thì mọi ô có trọng số 1
    và độ phủ mới được tính bằng popcount.
    """
    masks = []
    for cells in instance["sets"]:
        mask = 0
        for i in cells:
            mask |= 1 << i
        masks.append(mask)
    return {
        "n": instance["n"],
        "costs": instance["costs"],
        "masks": masks,
        "weights": instance.get("weights"),
    }


def _weight(mask: int, weights) -> float:
    if weights is None:
        return mask.bit_count()
    total = 0
    while mask:
        low = mask & -mask
        total += weights[low.bit_length() - 1]
        mask ^= low
    return total


def _ratio(gain, cost) -> float:
    return math.inf if cost == 0 else gain / cost


def lazy_ratio_greedy(prep: dict, budget: int, start=(), banned=()) -> tuple:
    """Greedy theo tỉ lệ (giá trị phủ mới / chi phí), đánh giá lười kiểu CELF.

    Bắt đầu từ tập `start` (giữ nguyên thứ tự), không bao giờ chọn gói trong
    `banned`. Gói không còn vừa ngân sách thì bỏ qua và xét tiếp (không dừng),
    theo bản sửa đổi của Khuller–Moss–Naor. Hòa tỉ lệ thì chọn chỉ số nhỏ nhất.

    Trả về (selected, covered_weight, cost).
    """
    costs, masks, weights = prep["costs"], prep["masks"], prep["weights"]
    selected = list(start)
    covered = 0
    spent = 0
    for j in selected:
        covered |= masks[j]
        spent += costs[j]

    excluded = set(selected) | set(banned)
    # Phần tử heap: (-tỉ lệ, chỉ số gói, vòng đánh giá). Tỉ lệ tính ở vòng cũ
    # là cận trên của tỉ lệ hiện tại (tính submodular), nên chỉ cần tính lại
    # khi phần tử đứng đầu heap đã cũ.
    heap = []
    for j in range(prep["n"]):
        if j in excluded or costs[j] > budget - spent:
            continue
        gain = _weight(masks[j] & ~covered, weights)
        if gain > 0:
            heap.append((-_ratio(gain, costs[j]), j, 0))
    heapq.heapify(heap)

    round_no = 0
    while heap:
        neg_ratio, j, evaluated_at = heapq.heappop(heap)
        if costs[j] > budget - spent:
            continue  # ngân sách chỉ giảm dần nên gói này sẽ không bao giờ vừa nữa
        if evaluated_at != round_no:
            gain = _weight(masks[j] & ~covered, weights)
            if gain > 0:
                heapq.heappush(heap, (-_ratio(gain, costs[j]), j, round_no))
            continue
        selected.append(j)
        covered |= masks[j]
        spent += costs[j]
        round_no += 1

    return selected, _weight(covered, weights), spent


def _evaluate(prep: dict, selected) -> tuple:
    covered = 0
    for j in selected:
        covered |= prep["masks"][j]
    return _weight(covered, prep["weights"]), sum(prep["costs"][j] for j in selected)


def _better(a: tuple, b: tuple) -> bool:
    """So sánh hai lời giải (selected, weight, cost): phủ nhiều hơn, hòa thì rẻ hơn."""
    return a[1] > b[1] or (a[1] == b[1] and a[2] < b[2])


def drop_and_refill(prep: dict, budget: int, solution: tuple, max_rounds: int) -> tuple:
    """Local search: bỏ một gói đã chọn rồi lấp lại ngân sách bằng ratio greedy.

    Gói vừa bỏ bị cấm trong lần lấp lại đó để buộc lời giải đổi hướng. Nhận
    bước cải thiện đầu tiên tìm được (first improvement), lặp tới khi không
    còn cải thiện hoặc hết `max_rounds` vòng.
    """
    best = solution
    for _ in range(max_rounds):
        improved = False
        for i in best[0]:
            kept = [j for j in best[0] if j != i]
            candidate = lazy_ratio_greedy(prep, budget, start=kept, banned=(i,))
            if _better(candidate, best):
                best = candidate
                improved = True
                break
        if not improved:
            break
    return best


def solve(instance: dict, budget: int, n_seeds: int = DEFAULT_SEEDS, ls_rounds: int = DEFAULT_LS_ROUNDS) -> dict:
    """Seeded lazy ratio greedy + local search.

    1. Ratio greedy từ tập rỗng.
    2. Gói đơn tốt nhất vừa ngân sách (kết hợp với bước 1 cho cận ½(1−1/e)).
    3. Ratio greedy bắt đầu từ mỗi gói seed: `n_seeds` gói phủ nhiều nhất và
       `n_seeds` gói có tỉ lệ tốt nhất (trong số gói vừa ngân sách).
    4. Drop-and-refill trên lời giải tốt nhất.
    """
    prep = prepare(instance)
    costs, masks, weights = prep["costs"], prep["masks"], prep["weights"]

    affordable = [j for j in range(prep["n"]) if costs[j] <= budget]
    single_gain = {j: _weight(masks[j], weights) for j in affordable}

    best = lazy_ratio_greedy(prep, budget)
    candidates_tried = 1

    if affordable:
        top_single = max(affordable, key=lambda j: (single_gain[j], -costs[j], -j))
        single = ([top_single], single_gain[top_single], costs[top_single])
        if _better(single, best):
            best = single

    seeds = set()
    if n_seeds > 0:
        by_gain = sorted(affordable, key=lambda j: (-single_gain[j], costs[j], j))
        by_ratio = sorted(affordable, key=lambda j: (-_ratio(single_gain[j], costs[j]), j))
        seeds.update(by_gain[:n_seeds])
        seeds.update(by_ratio[:n_seeds])
    for j in sorted(seeds):
        candidate = lazy_ratio_greedy(prep, budget, start=[j])
        candidates_tried += 1
        if _better(candidate, best):
            best = candidate

    if ls_rounds > 0 and best[0]:
        best = drop_and_refill(prep, budget, best, ls_rounds)

    selected = best[0]
    covered_weight, cost = _evaluate(prep, selected)
    covered_cells = _evaluate({**prep, "weights": None}, selected)[0]
    return {
        "selected_packages": selected,
        "covered_cells": covered_cells,
        "covered_weight": covered_weight,
        "cost": cost,
        "candidates_tried": candidates_tried,
    }


def save_result(instance_name: str, level_label: str, budget: int, result: dict, solve_time: float, params: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = RESULTS_DIR / f"{instance_name}_budgeted_{level_label.rstrip('%')}.json"
    payload = {
        "instance": instance_name,
        "algorithm": "greedy_ls",
        "mode": "budgeted",
        "budget_level": level_label,
        "budget_value": budget,
        "status": "heuristic",
        "objective": result["covered_cells"],
        "covered_weight": result["covered_weight"],
        "cost": result["cost"],
        "selected_packages": result["selected_packages"],
        "solve_time_seconds": round(solve_time, 3),
        "params": params,
    }
    dest.write_text(json.dumps(payload, indent=2))
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", default=None, help="Danh sách tên instance, cách nhau bởi dấu phẩy. Mặc định: tất cả trong data/processed/.")
    parser.add_argument("--budget-levels", default="75,50,25", help="Các mức %% OPT dùng cho ngân sách (mặc định 75,50,25).")
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS, help=f"Số gói seed mỗi tiêu chí (mặc định {DEFAULT_SEEDS}; 0 = tắt).")
    parser.add_argument("--ls-rounds", type=int, default=DEFAULT_LS_ROUNDS, help=f"Số vòng local search tối đa (mặc định {DEFAULT_LS_ROUNDS}; 0 = tắt).")
    args = parser.parse_args()

    budget_levels = [int(x) for x in args.budget_levels.split(",")]
    params = {"seeds": args.seeds, "ls_rounds": args.ls_rounds}

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
            result = solve(instance, budget, n_seeds=args.seeds, ls_rounds=args.ls_rounds)
            solve_time = time.time() - start
            print(
                f"[{name}] greedy_ls B={budget} ({level}% của OPT={ref_opt}) "
                f"-> objective(số ô phủ)={result['covered_cells']}/{instance['m']} "
                f"cost={result['cost']} time={round(solve_time, 3)}s"
            )
            save_result(name, f"{level}%", budget, result, solve_time, params)


if __name__ == "__main__":
    main()
