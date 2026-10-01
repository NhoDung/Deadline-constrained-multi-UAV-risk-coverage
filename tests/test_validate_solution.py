from pipeline.validate_solution import validate_solution, validate_results_dir

# 4 ô, 3 gói. OPT thật của instance này là 3 (gói 0 + gói 1 phủ hết 4 ô).
INSTANCE = {
    "m": 4,
    "n": 3,
    "costs": [2, 1, 5],
    "sets": [[0, 1], [2, 3], [0, 1, 2]],
}
OPT = 3


def budgeted(selected, objective, cost=None, budget_value=3, level="100%"):
    solution = {
        "instance": "toy",
        "mode": "budgeted",
        "budget_level": level,
        "budget_value": budget_value,
        "objective": objective,
        "selected_packages": selected,
    }
    if cost is not None:
        solution["cost"] = cost
    return solution


def test_valid_budgeted_solution_has_no_errors():
    solution = budgeted([0], objective=2, cost=2, budget_value=3, level="100%")

    assert validate_solution(INSTANCE, solution, opt=OPT) == []


def test_reports_cost_over_budget():
    solution = budgeted([2], objective=3, budget_value=3, level="100%")

    errors = validate_solution(INSTANCE, solution, opt=OPT)

    assert any("vượt ngân sách" in e for e in errors)


def test_reports_objective_mismatch():
    solution = budgeted([0], objective=4, budget_value=3, level="100%")

    errors = validate_solution(INSTANCE, solution, opt=OPT)

    assert any("số ô phủ" in e for e in errors)


def test_reports_reported_cost_mismatch():
    solution = budgeted([0], objective=2, cost=1, budget_value=3, level="100%")

    errors = validate_solution(INSTANCE, solution, opt=OPT)

    assert any("chi phí" in e for e in errors)


def test_reports_full_coverage_when_budget_below_opt():
    # Instance giả: nghiệm phủ 4/4 ô với chi phí 3 nhưng B khai báo là 2 < OPT.
    # Nếu code báo "phủ 100%" thì vi phạm Hệ quả 1 dù chi phí có hợp lệ hay không.
    solution = budgeted([0, 1], objective=4, budget_value=2, level="75%")

    errors = validate_solution(INSTANCE, solution, opt=OPT)

    assert any("Hệ quả 1" in e for e in errors)


def test_reports_budget_value_inconsistent_with_level():
    # 75% của OPT=3 phải là floor(2.25)=2, không phải 3.
    solution = budgeted([0], objective=2, budget_value=3, level="75%")

    errors = validate_solution(INSTANCE, solution, opt=OPT)

    assert any("budget_value" in e for e in errors)


def test_reports_out_of_range_and_duplicate_packages():
    solution = budgeted([0, 0, 7], objective=2, budget_value=3, level="100%")

    errors = validate_solution(INSTANCE, solution, opt=OPT)

    assert any("ngoài phạm vi" in e for e in errors)
    assert any("trùng" in e for e in errors)


def test_valid_setcover_solution_matches_opt():
    solution = {
        "instance": "toy",
        "mode": "setcover",
        "budget_level": None,
        "budget_value": None,
        "objective": 3,
        "selected_packages": [0, 1],
    }

    assert validate_solution(INSTANCE, solution, opt=OPT) == []


def test_reports_setcover_that_leaves_cells_uncovered():
    solution = {
        "instance": "toy",
        "mode": "setcover",
        "budget_level": None,
        "budget_value": None,
        "objective": 2,
        "selected_packages": [0],
    }

    errors = validate_solution(INSTANCE, solution, opt=OPT)

    assert any("chưa phủ hết" in e for e in errors)


def test_reports_setcover_cheaper_than_opt():
    # Chi phí 2 < OPT=3 mà lại phủ hết: mâu thuẫn định nghĩa OPT (hoặc bảng OPT sai).
    instance = {"m": 2, "n": 1, "costs": [2], "sets": [[0, 1]]}
    solution = {
        "instance": "toy",
        "mode": "setcover",
        "budget_level": None,
        "budget_value": None,
        "objective": 2,
        "selected_packages": [0],
    }

    errors = validate_solution(instance, solution, opt=3)

    assert any("nhỏ hơn OPT" in e for e in errors)


def test_validate_results_dir_collects_errors_per_file(tmp_path):
    import json

    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "toy.json").write_text(json.dumps(INSTANCE))
    results = tmp_path / "results" / "greedy"
    results.mkdir(parents=True)
    good = budgeted([0], objective=2, cost=2, budget_value=2, level="75%")
    bad = budgeted([2], objective=3, budget_value=2, level="75%")
    (results / "toy_good.json").write_text(json.dumps(good))
    (results / "toy_bad.json").write_text(json.dumps(bad))

    report = validate_results_dir(tmp_path / "results", processed, opt_table={"toy": OPT})

    assert report["checked"] == 2
    assert list(report["errors"]) == [str(results / "toy_bad.json")]
