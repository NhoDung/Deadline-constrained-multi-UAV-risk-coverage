from pipeline.lp_rounding import repair_and_fill, prepare, solve, solve_lp_relaxation


def test_lp_relaxation_is_an_upper_bound_and_fractional():
    # Two packages of cost 2 sharing nothing, budget 3: the integer optimum
    # takes one package (2 cells); the LP may take 1.5 packages (3 cells).
    instance = {"m": 4, "n": 2, "costs": [2, 2], "sets": [[0, 1], [2, 3]]}

    x, bound = solve_lp_relaxation(instance, budget=3)

    assert abs(bound - 3.0) < 1e-6
    assert abs(sum(2 * v for v in x) - 3.0) < 1e-6


def test_lp_relaxation_uses_weights():
    instance = {"m": 2, "n": 2, "costs": [1, 1], "sets": [[0], [1]], "weights": [1.0, 5.0]}

    x, bound = solve_lp_relaxation(instance, budget=1)

    assert abs(bound - 5.0) < 1e-6
    assert x[1] > 0.99


def test_repair_drops_worst_ratio_package_until_within_budget():
    # P0 and P1 overlap fully, so P0 contributes nothing on top of P1 and
    # must be dropped first; then the remaining set fits.
    instance = {"m": 3, "n": 3, "costs": [3, 2, 2], "sets": [[0, 1], [0, 1], [2]]}
    prep = prepare(instance)

    selected = repair_and_fill(prep, budget=4, chosen=[0, 1, 2])

    assert sorted(selected) == [1, 2]


def test_repair_fills_leftover_budget_greedily():
    instance = {"m": 3, "n": 3, "costs": [1, 1, 1], "sets": [[0], [1], [2]]}
    prep = prepare(instance)

    selected = repair_and_fill(prep, budget=3, chosen=[0])

    assert sorted(selected) == [0, 1, 2]


def test_solve_never_exceeds_budget_and_reports_consistent_numbers():
    instance = {
        "m": 6,
        "n": 5,
        "costs": [3, 2, 2, 4, 1],
        "sets": [[0, 1, 2], [2, 3], [4], [0, 3, 4, 5], [5]],
    }

    for budget in range(0, 13):
        result = solve(instance, budget=budget, seed=0, samples=20)
        chosen = result["selected_packages"]
        assert len(set(chosen)) == len(chosen)
        assert result["cost"] == sum(instance["costs"][j] for j in chosen) <= budget
        covered = set().union(*(instance["sets"][j] for j in chosen)) if chosen else set()
        assert result["covered_cells"] == len(covered)
        assert result["covered_weight"] <= result["lp_bound"] + 1e-6


def test_solve_reaches_optimum_on_small_instance():
    # Optimal is P0 + P1 (6 cells); ratio greedy alone gets stuck at 5.
    instance = {"m": 6, "n": 3, "costs": [2, 2, 2], "sets": [[0, 1, 2], [3, 4, 5], [0, 1, 3, 4]]}

    result = solve(instance, budget=4, seed=0, samples=50)

    assert result["covered_cells"] == 6


def test_same_seed_gives_same_result():
    instance = {
        "m": 6,
        "n": 5,
        "costs": [3, 2, 2, 4, 1],
        "sets": [[0, 1, 2], [2, 3], [4], [0, 3, 4, 5], [5]],
    }

    a = solve(instance, budget=6, seed=7, samples=30)
    b = solve(instance, budget=6, seed=7, samples=30)

    assert a["selected_packages"] == b["selected_packages"]


def test_zero_budget_returns_empty_solution():
    instance = {"m": 2, "n": 1, "costs": [1], "sets": [[0, 1]]}

    result = solve(instance, budget=0, seed=0)

    assert result["selected_packages"] == []
    assert result["covered_cells"] == 0
