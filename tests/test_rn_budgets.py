from pipeline.rn.budgets import budgets_for_level, reference_cost


def test_reference_cost_is_min_cost_cover():
    inst = {"n": 3, "costs": [2, 3, 4], "sets": [[0, 1], [1, 2], [0, 1, 2]]}
    assert reference_cost(inst) == 4  # một route 4 rẻ hơn 2+3


def test_reference_cost_ignores_cells_no_route_can_cover():
    # ô 2 không route nào phủ: vẫn phải giải được, chi phí = 1 + 2.
    inst = {"n": 2, "costs": [1, 2], "sets": [[0], [1]]}
    assert reference_cost(inst) == 3


def test_budgets_split_by_share_and_floor():
    inst = {"reference_cost": 8, "uav_share": [0.5, 0.5]}
    assert budgets_for_level(inst, 100) == [4, 4]
    assert budgets_for_level(inst, 75) == [3, 3]
    assert budgets_for_level(inst, 50) == [2, 2]
    assert budgets_for_level(inst, 25) == [1, 1]
