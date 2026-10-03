from pipeline.genetic import crossover, mutate, prepare, repair, solve

import random

INSTANCE = {
    "m": 6,
    "n": 5,
    "costs": [3, 2, 2, 4, 1],
    "sets": [[0, 1, 2], [2, 3], [4], [0, 3, 4, 5], [5]],
}


def _cost(selected):
    return sum(INSTANCE["costs"][j] for j in selected)


def test_repair_makes_any_set_feasible():
    prep = prepare(INSTANCE)

    selected = repair(prep, budget=5, chosen=[0, 1, 2, 3, 4])

    assert _cost(selected) <= 5
    assert len(set(selected)) == len(selected)


def test_repair_keeps_packages_shared_by_both_parents_when_possible():
    # Crossover child = union of parents; packages present in both parents
    # are kept, the rest compete for the remaining budget.
    prep = prepare(INSTANCE)
    rng = random.Random(0)

    child = crossover(prep, budget=6, a=[0, 4], b=[0, 2], rng=rng)

    assert 0 in child
    assert _cost(child) <= 6


def test_mutation_changes_solution_but_stays_feasible():
    prep = prepare(INSTANCE)
    rng = random.Random(1)
    parent = [3, 1]

    children = [mutate(prep, budget=6, parent=parent, rng=rng) for _ in range(20)]

    assert all(_cost(c) <= 6 for c in children)
    assert any(sorted(c) != sorted(parent) for c in children)


def test_solve_never_exceeds_budget_and_reports_consistent_numbers():
    for budget in range(0, 13):
        result = solve(INSTANCE, budget=budget, seed=0, pop_size=10, generations=30)
        chosen = result["selected_packages"]
        assert len(set(chosen)) == len(chosen)
        assert result["cost"] == _cost(chosen) <= budget
        covered = set().union(*(INSTANCE["sets"][j] for j in chosen)) if chosen else set()
        assert result["covered_cells"] == len(covered)


def test_solve_escapes_ratio_greedy_trap():
    # Ratio greedy takes P2 (4 cells / 2) and ends with 5 cells; optimum is 6.
    instance = {"m": 6, "n": 3, "costs": [2, 2, 2], "sets": [[0, 1, 2], [3, 4, 5], [0, 1, 3, 4]]}

    result = solve(instance, budget=4, seed=0, pop_size=10, generations=30)

    assert result["covered_cells"] == 6


def test_weights_drive_the_objective():
    instance = {"m": 4, "n": 2, "costs": [1, 1], "sets": [[0, 1], [2, 3]], "weights": [1.0, 1.0, 10.0, 0.0]}

    result = solve(instance, budget=1, seed=0, pop_size=6, generations=10)

    assert result["selected_packages"] == [1]
    assert result["covered_weight"] == 10.0


def test_same_seed_gives_same_result():
    a = solve(INSTANCE, budget=6, seed=3, pop_size=10, generations=20)
    b = solve(INSTANCE, budget=6, seed=3, pop_size=10, generations=20)

    assert a["selected_packages"] == b["selected_packages"]


def test_zero_budget_returns_empty_solution():
    result = solve({"m": 2, "n": 1, "costs": [1], "sets": [[0, 1]]}, budget=0, seed=0)

    assert result["selected_packages"] == []
    assert result["covered_cells"] == 0
