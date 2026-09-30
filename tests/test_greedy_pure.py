from pipeline.greedy_pure import greedy_budgeted


def test_picks_package_covering_most_new_cells_within_budget():
    # P0 covers 3 cells but eats the whole budget; P1/P2 would fit together
    # but pure greedy must prefer raw coverage over cost.
    instance = {
        "m": 4,
        "n": 3,
        "costs": [10, 1, 1],
        "sets": [[0, 1, 2], [0, 1], [3]],
    }

    result = greedy_budgeted(instance, budget=10)

    assert result["selected_packages"] == [0]
    assert result["covered_cells"] == 3
    assert result["cost"] == 10


def test_ties_broken_by_lowest_package_index():
    instance = {
        "m": 4,
        "n": 2,
        "costs": [5, 5],
        "sets": [[0, 1], [2, 3]],  # both cover 2 new cells at each step
    }

    result = greedy_budgeted(instance, budget=10)

    assert result["selected_packages"] == [0, 1]
    assert result["covered_cells"] == 4
    assert result["cost"] == 10


def test_stops_when_no_affordable_package_remains():
    instance = {
        "m": 3,
        "n": 2,
        "costs": [100, 5],
        "sets": [[0, 1, 2], [0]],
    }

    result = greedy_budgeted(instance, budget=5)

    assert result["selected_packages"] == [1]
    assert result["covered_cells"] == 1
    assert result["cost"] == 5


def test_excludes_packages_with_zero_new_coverage():
    instance = {
        "m": 2,
        "n": 2,
        "costs": [1, 1],
        "sets": [[0, 1], [0]],  # P1 becomes useless once P0 is picked
    }

    result = greedy_budgeted(instance, budget=10)

    assert result["selected_packages"] == [0]
    assert result["covered_cells"] == 2
    assert result["cost"] == 1
