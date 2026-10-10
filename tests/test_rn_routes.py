import numpy as np
import pytest

from pipeline.rn.routes import build_instance, start_cells


def full_risk():
    return np.random.default_rng(0).random((6, 6)) + 0.1


def test_start_cells_distinct_and_inside_grid():
    cells = start_cells(8, 20)
    assert len(set(cells)) == 8
    assert all(0 <= r < 20 and 0 <= c < 20 for r, c in cells)


def test_universe_excludes_zero_risk_cells():
    risk = np.zeros((4, 4))
    risk[0, 1], risk[1, 1] = 3.0, 1.0
    inst = build_instance(risk, k=1, routes_per_uav=50, max_cells=6, seed=0)
    assert inst["m"] == 2 and inst["weights"] == [3.0, 1.0]
    assert all(i in (0, 1) for cells in inst["sets"] for i in cells)


def test_all_zero_risk_raises():
    with pytest.raises(ValueError):
        build_instance(np.zeros((4, 4)), k=1, routes_per_uav=5, max_cells=4, seed=0)


def test_route_cost_is_takeoff_plus_cells_visited():
    inst = build_instance(full_risk(), k=2, routes_per_uav=30, max_cells=8, seed=0)
    assert inst["n"] > 0
    for j in range(inst["n"]):
        assert inst["costs"][j] == 2 + len(inst["paths"][j])


def test_routes_are_connected_paths_starting_at_their_uav():
    inst = build_instance(full_risk(), k=3, routes_per_uav=30, max_cells=8, seed=0)
    for j, path in enumerate(inst["paths"]):
        assert tuple(path[0]) == tuple(inst["uav_starts"][inst["route_uav"][j]])
        for a, b in zip(path, path[1:]):
            assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
        assert len(set(map(tuple, path))) == len(path)  # không đi lại ô cũ


def test_parallel_arrays_have_same_length():
    inst = build_instance(full_risk(), k=2, routes_per_uav=30, max_cells=8, seed=0)
    n = inst["n"]
    assert len(inst["costs"]) == len(inst["sets"]) == len(inst["route_uav"]) == len(inst["paths"]) == n


def test_duplicate_cover_keeps_cheapest_route_per_uav():
    risk = np.zeros((3, 3))
    risk[0, 1] = 1.0  # chỉ một ô giá trị, kề điểm xuất phát (0, 0)
    inst = build_instance(risk, k=1, routes_per_uav=200, max_cells=3, seed=0)
    assert inst["n"] == 1
    assert inst["costs"][0] == 2 + 2  # đường ngắn nhất (0,0) -> (0,1)


def test_deterministic_for_same_seed_and_shares_sum_to_one():
    a = build_instance(full_risk(), k=3, routes_per_uav=20, max_cells=8, seed=5)
    b = build_instance(full_risk(), k=3, routes_per_uav=20, max_cells=8, seed=5)
    assert a == b
    assert abs(sum(a["uav_share"]) - 1.0) < 1e-9
    assert all(0.2 < s < 0.35 for s in a["uav_share"])
