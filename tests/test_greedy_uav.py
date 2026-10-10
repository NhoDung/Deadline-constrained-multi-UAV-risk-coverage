import numpy as np

from pipeline.greedy_uav import lazy_ratio_greedy_uav, solve_naive_shared, solve_uav
from pipeline.greedy_ls import prepare
from pipeline.ilp_uav import solve_uav_ilp
from pipeline.rn.budgets import budgets_for_level, reference_cost
from pipeline.rn.routes import build_instance

TINY = {
    "n": 4, "m": 3, "weights": [5.0, 1.0, 1.0],
    "costs": [3, 2, 2, 1], "sets": [[0], [1], [1, 2], [2]],
    "route_uav": [0, 0, 1, 1],
}


def _prep(instance):
    return {**prepare(instance), "route_uav": instance["route_uav"]}


def test_greedy_skips_route_of_exhausted_uav_and_continues():
    inst = {"n": 3, "m": 4, "weights": [1.0] * 4, "costs": [2, 2, 1],
            "sets": [[0, 1], [2], [3]], "route_uav": [0, 0, 1]}
    selected, weight, cost = lazy_ratio_greedy_uav(_prep(inst), budgets=[2, 1])
    assert selected == [0, 2] and weight == 3.0 and cost == 3


def test_solve_uav_finds_optimum_on_tiny_instance():
    res = solve_uav(TINY, budgets=[3, 2])
    assert res["covered_weight"] == 7.0 and sorted(res["selected_packages"]) == [0, 2]


def test_uav_with_budget_below_every_route_gets_nothing():
    res = solve_uav(TINY, budgets=[0, 0])
    assert res["selected_packages"] == [] and res["covered_weight"] == 0.0


def test_naive_shared_result_respects_each_uav_budget_after_repair():
    # Ngân sách chung 5 cho phép j0 (UAV0, c3) + j2 (UAV1, c2); với [2, 3] thì j0 vi phạm.
    res = solve_naive_shared(TINY, budgets=[2, 3])
    assert all(c <= b for c, b in zip(res["cost_per_uav"], [2, 3]))


def test_heuristics_are_feasible_and_never_beat_ilp_on_generated_instance():
    risk = np.random.default_rng(0).random((6, 6)) + 0.05
    inst = build_instance(risk, k=2, routes_per_uav=30, max_cells=8, seed=3)
    inst["reference_cost"] = reference_cost(inst)
    budgets = budgets_for_level(inst, 50)
    optimum = solve_uav_ilp(inst, budgets, time_limit=60)["objective"]
    for solver in (solve_uav, solve_naive_shared):
        res = solver(inst, budgets)
        assert all(c <= b for c, b in zip(res["cost_per_uav"], budgets))
        assert res["covered_weight"] <= optimum + 1e-6


def test_naive_refills_leftover_budget_after_repair():
    # Ngân sách chung 4: greedy chung chọn j0 (UAV0, c3, giá trị 5), vi phạm pin UAV0 = 2.
    # Sau khi bỏ j0, pin còn dư phải được lấp lại bằng j1 (UAV0, c2) và j2 (UAV1, c2).
    inst = {"n": 3, "m": 3, "weights": [5.0, 3.0, 1.0], "costs": [3, 2, 2],
            "sets": [[0], [1], [2]], "route_uav": [0, 0, 1]}
    res = solve_naive_shared(inst, budgets=[2, 2])
    assert sorted(res["selected_packages"]) == [1, 2]
    assert res["covered_weight"] == 4.0
