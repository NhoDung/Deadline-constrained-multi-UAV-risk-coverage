from pipeline.ilp_uav import solve_uav_ilp

# 3 ô trọng số [5, 1, 1]. Route: j0 (UAV0, c3, ô0), j1 (UAV0, c2, ô1),
# j2 (UAV1, c2, ô1+ô2), j3 (UAV1, c1, ô2).
INSTANCE = {
    "n": 4, "m": 3, "weights": [5.0, 1.0, 1.0],
    "costs": [3, 2, 2, 1], "sets": [[0], [1], [1, 2], [2]],
    "route_uav": [0, 0, 1, 1],
}


def test_optimum_with_per_uav_budgets():
    res = solve_uav_ilp(INSTANCE, budgets=[3, 2], time_limit=30)
    assert res["status"] == "optimal"
    assert abs(res["objective"] - 7.0) < 1e-9
    assert sorted(res["selected_packages"]) == [0, 2]


def test_budget_is_per_uav_not_pooled():
    # Tổng 5 đủ cho j0 (3) + j2 (2), nhưng UAV0 chỉ có 2 nên j0 bị cấm.
    res = solve_uav_ilp(INSTANCE, budgets=[2, 3], time_limit=30)
    assert abs(res["objective"] - 2.0) < 1e-9


def test_uav_with_budget_below_every_route_selects_nothing():
    res = solve_uav_ilp(INSTANCE, budgets=[0, 0], time_limit=30)
    assert res["selected_packages"] == [] and res["objective"] == 0.0


def test_status_label_uses_solution_status_not_lp_status():
    # CBC hết giờ vẫn có LpStatus "Optimal", chỉ sol_status (=2) cho biết chưa chứng minh tối ưu.
    from types import SimpleNamespace

    from pipeline.ilp_uav import status_label

    assert status_label(SimpleNamespace(sol_status=1)) == "optimal"
    assert status_label(SimpleNamespace(sol_status=2)) == "best-known"
