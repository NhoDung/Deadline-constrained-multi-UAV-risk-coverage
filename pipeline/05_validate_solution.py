"""Validator chung: tự tính lại chi phí và độ phủ của mọi file lời giải.

Dùng được cho kết quả của ILP lẫn mọi heuristic (miễn đúng format JSON
trong docs/ilp-solver-thiet-ke.md mục 3). Không tin số liệu do thuật toán tự
báo cáo — chỉ đọc `selected_packages` rồi tính lại từ instance gốc.

Chạy (kiểm tra toàn bộ data/results/):
    python pipeline/05_validate_solution.py
    python pipeline/05_validate_solution.py --results-dir data/results/greedy
Thoát với mã 1 nếu có bất kỳ lỗi nào.
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.opt_reference import OPT_REFERENCE

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
RESULTS_DIR = ROOT / "data" / "results"


def validate_solution(instance: dict, solution: dict, opt: int) -> list:
    """Trả về danh sách lỗi (rỗng nếu lời giải hợp lệ)."""
    errors = []
    n, m = instance["n"], instance["m"]
    selected = solution["selected_packages"]

    out_of_range = [j for j in selected if not 0 <= j < n]
    if out_of_range:
        errors.append(f"gói ngoài phạm vi [0, {n - 1}]: {out_of_range}")
    if len(set(selected)) != len(selected):
        errors.append("có gói bị chọn trùng")

    valid = [j for j in set(selected) if 0 <= j < n]
    cost = sum(instance["costs"][j] for j in valid)
    covered = set()
    for j in valid:
        covered.update(instance["sets"][j])
    coverage = len(covered)

    reported_cost = solution.get("cost")
    if reported_cost is not None and reported_cost != cost:
        errors.append(f"chi phí khai báo {reported_cost} khác chi phí tính lại {cost}")

    if solution["mode"] == "setcover":
        if coverage != m:
            errors.append(f"chưa phủ hết ô: {coverage}/{m}")
        if solution["objective"] != cost:
            errors.append(f"objective {solution['objective']} khác chi phí tính lại {cost}")
        if coverage == m and cost < opt:
            errors.append(f"chi phí {cost} nhỏ hơn OPT={opt} nhưng phủ hết ô (mâu thuẫn định nghĩa OPT)")
        return errors

    budget = solution["budget_value"]
    level = solution["budget_level"]
    expected_budget = math.floor(int(level.rstrip("%")) / 100 * opt)
    if budget != expected_budget:
        errors.append(f"budget_value={budget} không khớp floor({level} × OPT={opt}) = {expected_budget}")
    if cost > budget:
        errors.append(f"chi phí {cost} vượt ngân sách {budget}")
    if solution["objective"] != coverage:
        errors.append(f"số ô phủ khai báo {solution['objective']} khác số ô tính lại {coverage}")
    if coverage == m and budget < opt:
        errors.append(f"phủ 100% ô với B={budget} < OPT={opt} (vi phạm Hệ quả 1, mục 5 project-brief.md)")
    return errors


def validate_results_dir(results_dir: Path, processed_dir: Path, opt_table: dict) -> dict:
    """Kiểm tra mọi *.json (đệ quy) trong results_dir. Trả về {"checked": n, "errors": {path: [lỗi]}}."""
    checked = 0
    errors = {}
    for path in sorted(Path(results_dir).rglob("*.json")):
        checked += 1
        solution = json.loads(path.read_text())
        name = solution.get("instance")
        instance_path = Path(processed_dir) / f"{name}.json"
        if name not in opt_table or not instance_path.exists():
            errors[str(path)] = [f"không tìm thấy instance/OPT tham khảo cho '{name}'"]
            continue
        instance = json.loads(instance_path.read_text())
        file_errors = validate_solution(instance, solution, opt_table[name])
        if file_errors:
            errors[str(path)] = file_errors
    return {"checked": checked, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default=str(RESULTS_DIR), help="Thư mục chứa file kết quả (mặc định: data/results/, quét đệ quy).")
    parser.add_argument("--processed-dir", default=str(PROCESSED_DIR))
    args = parser.parse_args()

    report = validate_results_dir(Path(args.results_dir), Path(args.processed_dir), OPT_REFERENCE)
    for path, file_errors in report["errors"].items():
        for e in file_errors:
            print(f"LỖI {path}: {e}")
    print(f"Đã kiểm tra {report['checked']} file, {len(report['errors'])} file có lỗi.")
    sys.exit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
