import numpy as np
import pytest

from pipeline.greedy_uav import lazy_ratio_greedy_uav
from pipeline.timing_rn import (count_greedy_runs, count_lazy_evals, fit_loglog_exponent,
                                greedy_plain, prep_of, synth_instance)

TINY = {
    "n": 4, "m": 3, "weights": [5.0, 1.0, 1.0],
    "costs": [3, 2, 2, 1], "sets": [[0], [1], [1, 2], [2]],
    "route_uav": [0, 0, 1, 1],
}


def test_fit_loglog_exponent_recovers_power_laws():
    xs = [1, 2, 4, 8, 16]
    assert fit_loglog_exponent(xs, [x for x in xs]) == pytest.approx(1.0)
    assert fit_loglog_exponent(xs, [3 * x**2 for x in xs]) == pytest.approx(2.0)


def test_synth_instance_has_one_cell_per_grid_square_and_is_deterministic():
    a = synth_instance(grid=8, routes_per_uav=20, seed=3)
    assert a["m"] == 64 and len(a["uav_share"]) == 4
    assert a == synth_instance(grid=8, routes_per_uav=20, seed=3)


def test_plain_greedy_matches_lazy_greedy_on_tiny_instance():
    prep = prep_of(TINY)
    for budgets in ([3, 2], [2, 3], [0, 0], [10, 10]):
        plain, _ = greedy_plain(prep, budgets)
        assert plain == lazy_ratio_greedy_uav(prep, budgets)[0]


def test_plain_greedy_matches_lazy_greedy_on_generated_instances():
    for seed in range(4):
        inst = synth_instance(grid=10, routes_per_uav=60, seed=seed)
        prep = prep_of(inst)
        budgets = [40, 40, 40, 40]
        plain, _ = greedy_plain(prep, budgets)
        assert plain == lazy_ratio_greedy_uav(prep, budgets)[0]


def test_lazy_needs_no_more_evaluations_than_plain():
    inst = synth_instance(grid=10, routes_per_uav=80, seed=1)
    prep, budgets = prep_of(inst), [60, 60, 60, 60]
    plain_selected, plain_evals = greedy_plain(prep, budgets)
    (lazy_selected, _, _), lazy_evals = count_lazy_evals(prep, budgets)
    assert lazy_selected == plain_selected
    assert 0 < lazy_evals <= plain_evals


def test_count_greedy_runs_counts_base_seed_and_local_search_runs():
    inst = synth_instance(grid=10, routes_per_uav=60, seed=2)
    budgets = [50, 50, 50, 50]
    runs_without_extras = count_greedy_runs(inst, budgets, n_seeds=0, ls_rounds=0)
    assert runs_without_extras == 1
    assert count_greedy_runs(inst, budgets, n_seeds=3, ls_rounds=0) > runs_without_extras
