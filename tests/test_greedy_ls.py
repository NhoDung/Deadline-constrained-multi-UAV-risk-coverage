from pipeline.greedy_ls import lazy_ratio_greedy, prepare, solve


def _run_greedy(instance, budget, start=()):
    prep = prepare(instance)
    return lazy_ratio_greedy(prep, budget, start=start)


def test_ratio_greedy_prefers_cheap_efficient_packages():
    # Pure greedy would take P0 (3 cells, cost 10) and stop. Ratio greedy takes
    # P1 (2 cells/1) and P2 (1 cell/1) and covers all 4 cells.
    instance = {"m": 4, "n": 3, "costs": [10, 1, 1], "sets": [[0, 1, 2], [0, 1], [3]]}

    selected, covered_weight, cost = _run_greedy(instance, budget=10)

    assert selected == [1, 2]
    assert covered_weight == 3
    assert cost == 2


def test_greedy_skips_unaffordable_package_and_continues():
    # After P0, P1 has the best ratio but no longer fits (cost 4 > 3 left);
    # the greedy must skip it and still add P2 instead of stopping.
    instance = {"m": 9, "n": 3, "costs": [2, 4, 1], "sets": [[0, 1, 2, 3], [4, 5, 6, 7], [8]]}

    selected, covered_weight, cost = _run_greedy(instance, budget=5)

    assert selected == [0, 2]
    assert covered_weight == 5
    assert cost == 3


def test_greedy_ties_broken_by_lowest_index():
    instance = {"m": 4, "n": 2, "costs": [2, 2], "sets": [[0, 1], [2, 3]]}

    selected, _, _ = _run_greedy(instance, budget=4)

    assert selected == [0, 1]


def test_greedy_respects_seed_set():
    instance = {"m": 3, "n": 3, "costs": [1, 1, 5], "sets": [[0], [1], [0, 1, 2]]}

    selected, covered_weight, cost = _run_greedy(instance, budget=6, start=[2])

    assert selected[0] == 2
    assert covered_weight == 3
    assert cost <= 6


def test_weights_change_the_choice():
    # Same costs and sizes; cell 2 carries high risk so P1 must be preferred.
    instance = {
        "m": 4,
        "n": 2,
        "costs": [1, 1],
        "sets": [[0, 1], [2, 3]],
        "weights": [1.0, 1.0, 10.0, 0.0],
    }

    selected, covered_weight, _ = _run_greedy(instance, budget=1)

    assert selected == [1]
    assert covered_weight == 10.0


def test_solve_beats_ratio_greedy_when_best_singleton_wins():
    # Classic bad case for ratio greedy: a tiny cheap package with a great
    # ratio blocks the one big package. Best-singleton candidate fixes it.
    instance = {
        "m": 11,
        "n": 2,
        "costs": [1, 10],
        "sets": [[0], list(range(1, 11))],
    }

    result = solve(instance, budget=10)

    assert result["selected_packages"] == [1]
    assert result["covered_cells"] == 10


def test_local_search_improves_greedy_solution():
    # Ratio greedy takes P2 (4 cells / 2) first, then P0 adds only cell 2 -> 5 cells.
    # Optimal is P0 + P1 (6 cells). Dropping P2 and refilling must find it.
    instance = {
        "m": 6,
        "n": 3,
        "costs": [2, 2, 2],
        "sets": [[0, 1, 2], [3, 4, 5], [0, 1, 3, 4]],
    }

    assert _run_greedy(instance, budget=4)[1] == 5
    result = solve(instance, budget=4, n_seeds=0)

    assert sorted(result["selected_packages"]) == [0, 1]
    assert result["covered_cells"] == 6
    assert result["cost"] <= 4


def test_solve_never_exceeds_budget_and_reports_consistent_numbers():
    instance = {
        "m": 6,
        "n": 5,
        "costs": [3, 2, 2, 4, 1],
        "sets": [[0, 1, 2], [2, 3], [4], [0, 3, 4, 5], [5]],
    }

    for budget in range(0, 13):
        result = solve(instance, budget=budget)
        chosen = result["selected_packages"]
        assert len(set(chosen)) == len(chosen)
        assert result["cost"] == sum(instance["costs"][j] for j in chosen) <= budget
        covered = set().union(*(instance["sets"][j] for j in chosen)) if chosen else set()
        assert result["covered_cells"] == len(covered)


def test_zero_budget_returns_empty_solution():
    instance = {"m": 2, "n": 1, "costs": [1], "sets": [[0, 1]]}

    result = solve(instance, budget=0)

    assert result["selected_packages"] == []
    assert result["covered_cells"] == 0
    assert result["cost"] == 0
