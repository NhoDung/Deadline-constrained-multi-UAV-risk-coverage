"""Genetic Algorithm có sửa nghiệm (repair) cho Budgeted Max Coverage (có trọng số).

GA trạng thái ổn định (steady-state): mỗi thế hệ sinh một con bằng lai ghép
giữ gói chung của hai cha mẹ + đột biến xóa-rồi-lấp; mọi cá thể luôn được sửa
về hợp lệ (chi phí ≤ B) nên tỉ lệ khả thi là 100%.
Xem thiết kế đầy đủ ở docs/genetic-thiet-ke.md.

Chạy: python pipeline/08_genetic.py --instances scpa1,scp61 --budget-levels 75,50,25 --seeds 20
"""

import argparse
import importlib
import json
import math
import random
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.opt_reference import OPT_REFERENCE

_greedy_ls = importlib.import_module("pipeline.06_greedy_ls")
prepare = _greedy_ls.prepare
lazy_ratio_greedy = _greedy_ls.lazy_ratio_greedy
_weight = _greedy_ls._weight

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results" / "genetic"

DEFAULT_SEEDS = 20
DEFAULT_POP_SIZE = 30
DEFAULT_GENERATIONS = 1000
DEFAULT_STALL = 300
DEFAULT_MUTATION_RATE = 0.3
DEFAULT_TIME_LIMIT = 10.0


def load_instance(name: str) -> dict:
    path = PROCESSED_DIR / f"{name}.json"
    return json.loads(path.read_text())


def _or_masks(prep: dict, selected) -> int:
    covered = 0
    for j in selected:
        covered |= prep["masks"][j]
    return covered


def _fitness(prep: dict, selected) -> tuple:
    """Phủ nhiều trọng số hơn là tốt hơn; hòa thì rẻ hơn là tốt hơn."""
    return (_weight(_or_masks(prep, selected), prep["weights"]), -sum(prep["costs"][j] for j in selected))


def repair(prep: dict, budget: int, chosen, protected=(), banned=()) -> list:
    """Sửa một tập gói bất kỳ thành lời giải hợp lệ rồi lấp ngân sách còn dư.

    Khi vượt ngân sách: bỏ dần gói có tỉ lệ (trọng số chỉ mình nó phủ / chi phí)
    nhỏ nhất, ưu tiên bỏ gói không thuộc `protected` trước. Sau đó lấp phần
    ngân sách còn dư bằng ratio greedy (CELF), không dùng gói trong `banned`.
    """
    costs, masks, weights = prep["costs"], prep["masks"], prep["weights"]
    protected = set(protected)
    kept = sorted(set(chosen))
    spent = sum(costs[j] for j in kept)

    while spent > budget:
        worst, worst_key = None, None
        for idx, j in enumerate(kept):
            others = _or_masks(prep, kept[:idx]) | _or_masks(prep, kept[idx + 1:])
            unique = _weight(masks[j] & ~others, weights)
            ratio = math.inf if costs[j] == 0 else unique / costs[j]
            key = (j in protected, ratio, -costs[j], -j)
            if worst_key is None or key < worst_key:
                worst, worst_key = j, key
        kept.remove(worst)
        spent -= costs[worst]

    selected, _, _ = lazy_ratio_greedy(prep, budget, start=kept, banned=banned)
    return selected


def crossover(prep: dict, budget: int, a, b, rng: random.Random) -> list:
    """Lai ghép: giữ mọi gói chung của hai cha mẹ, mỗi gói chỉ có ở một bên được
    lấy với xác suất 1/2, rồi sửa nghiệm (ưu tiên giữ gói chung)."""
    common = set(a) & set(b)
    child = set(common)
    for j in sorted(set(a) ^ set(b)):
        if rng.random() < 0.5:
            child.add(j)
    return repair(prep, budget, child, protected=common)


def mutate(prep: dict, budget: int, parent, rng: random.Random) -> list:
    """Đột biến: xóa ngẫu nhiên 1..max(1, 20%) gói, có thể chèn một gói ngẫu nhiên
    vừa ngân sách, rồi sửa nghiệm; gói vừa xóa bị cấm khi lấp lại."""
    current = list(parent)
    removed = []
    if current:
        k = rng.randint(1, max(1, len(current) // 5))
        removed = rng.sample(current, k)
        current = [j for j in current if j not in removed]
    if rng.random() < 0.5:
        affordable = [j for j in range(prep["n"]) if prep["costs"][j] <= budget and j not in removed]
        if affordable:
            inserted = rng.choice(affordable)
            if inserted not in current:
                current.append(inserted)
            return repair(prep, budget, current, protected=(inserted,), banned=removed)
    return repair(prep, budget, current, banned=removed)


def _initial_population(prep: dict, budget: int, pop_size: int, rng: random.Random) -> list:
    """Cá thể 0 = ratio greedy từ tập rỗng; các cá thể còn lại bắt đầu từ 1–3
    gói ngẫu nhiên vừa ngân sách rồi sửa + lấp, để quần thể đủ đa dạng."""
    affordable = [j for j in range(prep["n"]) if prep["costs"][j] <= budget]
    population = [lazy_ratio_greedy(prep, budget)[0]]
    attempts = 0
    while len(population) < pop_size and affordable and attempts < 5 * pop_size:
        attempts += 1
        start = rng.sample(affordable, min(len(affordable), rng.randint(1, 3)))
        population.append(repair(prep, budget, start, protected=start))
    return population


def solve(
    instance: dict,
    budget: int,
    seed: int,
    pop_size: int = DEFAULT_POP_SIZE,
    generations: int = DEFAULT_GENERATIONS,
    stall: int = DEFAULT_STALL,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    time_limit: float = DEFAULT_TIME_LIMIT,
) -> dict:
    """GA steady-state.

    Mỗi thế hệ: chọn hai cha mẹ bằng tournament nhị phân, lai ghép, đột biến với
    xác suất `mutation_rate`. Con thay cá thể tệ nhất nếu tốt hơn nó và chưa có
    trong quần thể. Dừng khi hết `generations`, khi `stall` thế hệ liên tiếp
    không cải thiện cá thể tốt nhất, hoặc khi chạy quá `time_limit` giây.
    """
    prep = prepare(instance)
    rng = random.Random(seed)
    start_time = time.time()

    population = []
    seen = set()
    for individual in _initial_population(prep, budget, pop_size, rng):
        key = frozenset(individual)
        if key not in seen:
            seen.add(key)
            population.append((_fitness(prep, individual), individual))

    best = max(population, key=lambda p: p[0])
    since_improved = 0
    generation = 0
    while generation < generations and since_improved < stall and len(population) > 1:
        if time.time() - start_time > time_limit:
            break
        generation += 1

        def tournament():
            x, y = rng.sample(population, 2)
            return x if x[0] >= y[0] else y

        parent_a, parent_b = tournament(), tournament()
        child = crossover(prep, budget, parent_a[1], parent_b[1], rng)
        if rng.random() < mutation_rate:
            child = mutate(prep, budget, child, rng)

        key = frozenset(child)
        if key in seen:
            since_improved += 1
            continue
        fit = _fitness(prep, child)
        worst_idx = min(range(len(population)), key=lambda i: population[i][0])
        if fit > population[worst_idx][0]:
            seen.discard(frozenset(population[worst_idx][1]))
            seen.add(key)
            population[worst_idx] = (fit, child)
        if fit > best[0]:
            best = (fit, child)
            since_improved = 0
        else:
            since_improved += 1

    selected = best[1]
    covered = _or_masks(prep, selected)
    return {
        "selected_packages": selected,
        "covered_cells": covered.bit_count(),
        "covered_weight": best[0][0],
        "cost": -best[0][1],
        "generations": generation,
    }


def save_result(instance_name: str, level_label: str, budget: int, best: dict, runs: list, params: dict) -> Path:
    """Ghi một file cho mỗi (instance, mức ngân sách): lời giải của seed tốt nhất
    (để validator kiểm tra) kèm thống kê của mọi seed trong `per_seed`."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = RESULTS_DIR / f"{instance_name}_budgeted_{level_label.rstrip('%')}.json"
    objectives = [r["objective"] for r in runs]
    times = [r["solve_time_seconds"] for r in runs]
    payload = {
        "instance": instance_name,
        "algorithm": "genetic",
        "mode": "budgeted",
        "budget_level": level_label,
        "budget_value": budget,
        "status": "heuristic",
        "objective": best["covered_cells"],
        "covered_weight": best["covered_weight"],
        "cost": best["cost"],
        "selected_packages": best["selected_packages"],
        "seed": best["seed"],
        "solve_time_seconds": best["solve_time_seconds"],
        "solve_time_mean_seconds": round(statistics.mean(times), 3),
        "objective_mean": round(statistics.mean(objectives), 3),
        "objective_std": round(statistics.pstdev(objectives), 3),
        "objective_min": min(objectives),
        "objective_max": max(objectives),
        "per_seed": runs,
        "params": params,
    }
    dest.write_text(json.dumps(payload, indent=2))
    return dest


def _run_one(task: tuple) -> dict:
    name, budget, seed, params = task
    instance = load_instance(name)
    start = time.time()
    result = solve(
        instance,
        budget,
        seed=seed,
        pop_size=params["pop_size"],
        generations=params["generations"],
        stall=params["stall"],
        mutation_rate=params["mutation_rate"],
        time_limit=params["time_limit"],
    )
    return {**result, "seed": seed, "solve_time_seconds": round(time.time() - start, 3)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", default=None, help="Danh sách tên instance, cách nhau bởi dấu phẩy. Mặc định: tất cả trong data/processed/.")
    parser.add_argument("--budget-levels", default="75,50,25", help="Các mức %% OPT dùng cho ngân sách (mặc định 75,50,25).")
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS, help=f"Số seed ngẫu nhiên, chạy seed 0..N-1 (mặc định {DEFAULT_SEEDS}).")
    parser.add_argument("--pop-size", type=int, default=DEFAULT_POP_SIZE)
    parser.add_argument("--generations", type=int, default=DEFAULT_GENERATIONS)
    parser.add_argument("--stall", type=int, default=DEFAULT_STALL, help="Dừng sớm sau N thế hệ không cải thiện.")
    parser.add_argument("--mutation-rate", type=float, default=DEFAULT_MUTATION_RATE)
    parser.add_argument("--time-limit", type=float, default=DEFAULT_TIME_LIMIT, help="Giới hạn thời gian mỗi lần chạy (giây).")
    parser.add_argument("--workers", type=int, default=1, help="Số tiến trình chạy song song các seed.")
    args = parser.parse_args()

    budget_levels = [int(x) for x in args.budget_levels.split(",")]
    params = {
        "seeds": args.seeds,
        "pop_size": args.pop_size,
        "generations": args.generations,
        "stall": args.stall,
        "mutation_rate": args.mutation_rate,
        "time_limit": args.time_limit,
    }

    if args.instances:
        instance_names = args.instances.split(",")
    else:
        instance_names = sorted(p.stem for p in PROCESSED_DIR.glob("*.json"))

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for name in instance_names:
            ref_opt = OPT_REFERENCE.get(name)
            if ref_opt is None:
                print(f"[{name}] bỏ qua: không có OPT tham khảo cho instance này.")
                continue

            m = load_instance(name)["m"]
            for level in budget_levels:
                budget = math.floor(level / 100 * ref_opt)
                tasks = [(name, budget, seed, params) for seed in range(args.seeds)]
                results = list(pool.map(_run_one, tasks))
                runs = [
                    {
                        "seed": r["seed"],
                        "objective": r["covered_cells"],
                        "cost": r["cost"],
                        "generations": r["generations"],
                        "solve_time_seconds": r["solve_time_seconds"],
                    }
                    for r in results
                ]
                best = max(results, key=lambda r: (r["covered_weight"], -r["cost"], -r["seed"]))
                save_result(name, f"{level}%", budget, best, runs, params)
                objectives = [r["objective"] for r in runs]
                print(
                    f"[{name}] genetic B={budget} ({level}% của OPT={ref_opt}) "
                    f"-> best={best['covered_cells']}/{m} mean={statistics.mean(objectives):.1f} "
                    f"std={statistics.pstdev(objectives):.2f} "
                    f"time_mean={statistics.mean(r['solve_time_seconds'] for r in runs):.2f}s"
                )


if __name__ == "__main__":
    main()
