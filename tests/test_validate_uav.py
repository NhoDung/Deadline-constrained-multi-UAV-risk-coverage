from pipeline.validate_uav import validate_uav_result

INSTANCE = {
    "n": 4, "m": 3, "weights": [5.0, 1.0, 1.0],
    "costs": [3, 2, 2, 1], "sets": [[0], [1], [1, 2], [2]],
    "route_uav": [0, 0, 1, 1],
    "reference_cost": 8, "uav_share": [0.5, 0.5],
}


def good(**overrides):
    result = {"budget_level": 100, "budget_values": [4, 4], "selected_packages": [0, 2],
              "cost_per_uav": [3, 2], "objective": 7.0, "covered_cells": 3}
    result.update(overrides)
    return result


def test_valid_result_has_no_errors():
    assert validate_uav_result(INSTANCE, good()) == []


def test_flags_uav_over_own_budget_even_if_total_is_fine():
    # j0 (3) + j1 (2) = 5 trên UAV0 > 4, trong khi tổng ngân sách 8 chưa hết.
    errors = validate_uav_result(INSTANCE, good(selected_packages=[0, 1], cost_per_uav=[5, 0],
                                                objective=6.0, covered_cells=2))
    assert any("UAV 0 vượt ngân sách" in e for e in errors)


def test_flags_wrong_declared_objective():
    assert any("objective" in e for e in validate_uav_result(INSTANCE, good(objective=9.0)))


def test_flags_duplicate_and_out_of_range_packages():
    assert any("trùng" in e for e in validate_uav_result(INSTANCE, good(selected_packages=[0, 0, 2])))
    assert any("ngoài phạm vi" in e for e in validate_uav_result(INSTANCE, good(selected_packages=[0, 9])))


def test_flags_wrong_budget_values():
    assert any("budget_values" in e for e in validate_uav_result(INSTANCE, good(budget_values=[5, 5])))
