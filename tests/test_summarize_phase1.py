from pipeline.summarize_phase1 import (
    aggregate_rows,
    check_budget_values,
    ilp_objective_map,
)

# OPT tham chiếu dùng cho test check_budget_values (thay bằng OPT thật của scpa1).
import pipeline.summarize_phase1 as mod


def make_rows():
    ilp = [
        {"instance": "scpa1", "budget_level": "75%", "budget_value": 100,
         "objective": 40, "mode": "budgeted", "solve_time_seconds": 1.0},
        {"instance": "scpa1", "budget_level": "50%", "budget_value": 50,
         "objective": 30, "mode": "budgeted", "solve_time_seconds": 1.0},
    ]
    greedy = [
        {"instance": "scpa1", "budget_level": "75%", "budget_value": 100,
         "objective": 20, "cost": 100, "solve_time_seconds": 0.01},
        {"instance": "scpa1", "budget_level": "50%", "budget_value": 50,
         "objective": 30, "cost": 50, "solve_time_seconds": 0.01},
    ]
    return {"ilp": ilp, "greedy": greedy, "greedy_ls": []}


def test_ilp_objective_map_skips_setcover_mode():
    rows = make_rows()["ilp"] + [
        {"instance": "scpa1", "budget_level": "-", "mode": "setcover",
         "objective": 253, "budget_value": None, "solve_time_seconds": 2.0},
    ]
    m = ilp_objective_map(rows)
    assert m == {("scpa1", "75%"): 40, ("scpa1", "50%"): 30}


def test_aggregate_rows_computes_gap_and_coverage():
    rows_by_algorithm = make_rows()
    ilp_map = ilp_objective_map(rows_by_algorithm["ilp"])
    out = aggregate_rows(rows_by_algorithm, ilp_map, {"scpa1": 253})

    by_key = {(r["algorithm"], r["budget_level"]): r for r in out}
    assert set(by_key) == {("ilp", "75%"), ("ilp", "50%"),
                           ("greedy", "75%"), ("greedy", "50%")}
    # greedy đạt 20/40 => gap 0.5; coverage = 100 * 20 / 253
    assert by_key[("greedy", "75%")]["gap_vs_ilp"] == 0.5
    assert by_key[("greedy", "75%")]["coverage_pct"] == 100.0 * 20 / 253
    # dòng ILP có gap 0
    assert by_key[("ilp", "75%")]["gap_vs_ilp"] == 0


def test_aggregate_rows_skips_zero_or_missing_ilp():
    rows_by_algorithm = make_rows()
    ilp_map = {}  # không có ILP -> không ghép được dòng nào
    assert aggregate_rows(rows_by_algorithm, ilp_map, {"scpa1": 253}) == []


def test_check_budget_values_flags_mismatch(monkeypatch):
    monkeypatch.setitem(mod.OPT_REFERENCE, "scpa1", 253)
    rows_by_algorithm = make_rows()
    ilp_map = ilp_objective_map(rows_by_algorithm["ilp"])
    rows = aggregate_rows(rows_by_algorithm, ilp_map, {"scpa1": 253})

    # Sửa budget_value dòng 75% thành giá trị sai (75% x 253 = floor(189.75) = 189)
    for r in rows:
        if r["algorithm"] == "ilp" and r["budget_level"] == "75%":
            r["budget_value"] = 999
    warnings = check_budget_values(rows)
    assert any("999" in w and "75%" in w for w in warnings)
