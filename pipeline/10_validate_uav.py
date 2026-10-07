"""Validator cho kết quả Pha 2: tự tính lại chi phí từng UAV và tổng rủi ro phủ.

Không tin số liệu thuật toán tự báo; chỉ đọc `selected_packages`. Kiểm tra thêm:
không heuristic nào vượt đáp án ILP `optimal`.

Chạy: python pipeline/10_validate_uav.py [--tag g20_default]   (thoát mã 1 nếu có lỗi)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.rn.budgets import budgets_for_level
from pipeline.rn.store import list_instances, load_instance, tag_dir

TOL = 1e-6


def validate_uav_result(instance: dict, result: dict) -> list:
    n, owner = instance["n"], instance["route_uav"]
    selected = result["selected_packages"]
    bad = [j for j in selected if not (isinstance(j, int) and 0 <= j < n)]
    if bad:
        return [f"gói ngoài phạm vi [0, {n - 1}]: {bad}"]
    errors = []
    if len(set(selected)) != len(selected):
        errors.append("có gói bị chọn trùng")

    budgets = budgets_for_level(instance, result["budget_level"])
    if result["budget_values"] != budgets:
        errors.append(f"budget_values {result['budget_values']} khác tính lại {budgets}")

    spent = [0] * len(budgets)
    covered = set()
    for j in set(selected):
        spent[owner[j]] += instance["costs"][j]
        covered.update(instance["sets"][j])
    for u, (cost, budget) in enumerate(zip(spent, budgets)):
        if cost > budget:
            errors.append(f"UAV {u} vượt ngân sách: {cost} > {budget}")
    if "cost_per_uav" in result and result["cost_per_uav"] != spent:
        errors.append(f"cost_per_uav khai báo {result['cost_per_uav']} khác tính lại {spent}")

    weight = sum(instance["weights"][i] for i in covered)
    if abs(result["objective"] - weight) > TOL:
        errors.append(f"objective {result['objective']} khác tổng rủi ro tính lại {weight}")
    if "covered_cells" in result and result["covered_cells"] != len(covered):
        errors.append(f"covered_cells {result['covered_cells']} khác tính lại {len(covered)}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="g20_default")
    args = parser.parse_args()

    results, ilp_best = [], {}
    for path in sorted((tag_dir(args.tag) / "results").glob("*/*.json")):
        result = json.loads(path.read_text())
        results.append((path, result))
        if result["algorithm"] == "ilp_uav" and result["status"] == "optimal":
            ilp_best[(result["instance"], result["budget_level"])] = result["objective"]
    instances = {name: load_instance(args.tag, name) for name in list_instances(args.tag)}

    problems = []
    for path, result in results:
        tag = f"{path.parent.name}/{path.name}"
        for error in validate_uav_result(instances[result["instance"]], result):
            problems.append(f"{tag}: {error}")
        best = ilp_best.get((result["instance"], result["budget_level"]))
        if best is not None and result["objective"] > best + TOL:
            problems.append(f"{tag}: objective {result['objective']} VƯỢT tối ưu ILP {best}")

    print(f"đã kiểm tra {len(results)} file kết quả, {len(problems)} lỗi")
    for line in problems[:30]:
        print(" -", line)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
