"""Tổng hợp kết quả Pha 1 (OR-Library) thành một file CSV duy nhất.

Trước bước này, kết quả Pha 1 chỉ tồn tại dưới dạng 450 file JSON lẻ trong
data/results/{ilp,greedy,greedy_ls}/ — không có file tổng hợp nào để vẽ biểu đồ
hay lập bảng cho báo cáo. Script đọc cả ba thư mục, ghép theo cặp
(instance, budget_level) với nghiệm ILP, và ghi data/results/summary_phase1.csv.

Xem thiết kế ở report/ke-hoach-bo-sung-paper.md (việc C1).

Chạy: python pipeline/13_summarize_phase1.py
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.opt_reference import OPT_REFERENCE

ROOT = Path(__file__).resolve().parent.parent
# Console Windows có thể dùng mã página không hỗ trợ tiếng Việt (cp1252).
for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding="utf-8", errors="replace")
RESULTS_DIR = ROOT / "data" / "results"
PROCESSED_DIR = ROOT / "data" / "processed"
ALGORITHMS = ("ilp", "greedy", "greedy_ls")
BUDGET_LEVELS = ("75%", "50%", "25%")

CSV_COLUMNS = (
    "instance",
    "algorithm",
    "budget_level",
    "budget_value",
    "objective",
    "cost",
    "coverage_pct",
    "gap_vs_ilp",
    "solve_time_seconds",
)


def load_json_dir(directory: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))]


def ilp_objective_map(ilp_rows: list[dict]) -> dict[tuple[str, str], float]:
    return {
        (r["instance"], r["budget_level"]): r["objective"]
        for r in ilp_rows
        if r["mode"] == "budgeted"
    }


def aggregate_rows(
    rows_by_algorithm: dict[str, list[dict]],
    ilp_map: dict[tuple[str, str], float],
    m_by_instance: dict[str, int],
) -> list[dict]:
    """Ghép kết quả từng thuật toán với nghiệm ILP cùng (instance, mức).

    gap_vs_ilp = (objective ILP - objective thuật toán) / objective ILP.
    coverage_pct = 100 * objective / m (Pha 1 không có trọng số, objective là
    số ô phủ).
    """
    out = []
    for algorithm in ALGORITHMS:
        for r in rows_by_algorithm[algorithm]:
            key = (r["instance"], r["budget_level"])
            ilp_obj = ilp_map.get(key)
            if ilp_obj is None or ilp_obj <= 0:
                continue
            m = m_by_instance[r["instance"]]
            out.append(
                {
                    "instance": r["instance"],
                    "algorithm": algorithm,
                    "budget_level": r["budget_level"],
                    "budget_value": r["budget_value"],
                    "objective": r["objective"],
                    "cost": r.get("cost", ""),
                    "coverage_pct": 100.0 * r["objective"] / m,
                    "gap_vs_ilp": (ilp_obj - r["objective"]) / ilp_obj,
                    "solve_time_seconds": r["solve_time_seconds"],
                }
            )
    return out


def check_budget_values(rows: list[dict]) -> list[str]:
    """Cảnh báo nếu budget_value lệch floor(mức% × OPT) hoặc ILP không optimal."""
    warnings = []
    for r in rows:
        if r["algorithm"] != "ilp":
            continue
        name = r["instance"]
        if name not in OPT_REFERENCE:
            warnings.append(f"{name}: không có OPT tham chiếu")
            continue
        level_pct = int(r["budget_level"].rstrip("%"))
        expected = math.floor(level_pct / 100 * OPT_REFERENCE[name])
        if r["budget_value"] != expected:
            warnings.append(
                f"{name} mức {r['budget_level']}: budget_value={r['budget_value']}"
                f" khác floor({level_pct}% x OPT)={expected}"
            )
    return warnings


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=RESULTS_DIR / "summary_phase1.csv",
        help="Đường dẫn CSV xuất ra (mặc định: data/results/summary_phase1.csv)",
    )
    args = parser.parse_args(argv)

    m_by_instance = {
        d["instance"]: d["m"] for d in load_json_dir(PROCESSED_DIR)
    }
    rows_by_algorithm = {
        algorithm: load_json_dir(RESULTS_DIR / algorithm)
        for algorithm in ALGORITHMS
    }
    missing = [
        f"{algorithm}: {len(rows_by_algorithm[algorithm])} file"
        for algorithm in ALGORITHMS
    ]
    print("Đã đọc:", ", ".join(missing))

    ilp_map = ilp_objective_map(rows_by_algorithm["ilp"])
    rows = aggregate_rows(rows_by_algorithm, ilp_map, m_by_instance)

    warnings = check_budget_values(rows)
    for w in warnings:
        print(f"CẢNH BÁO: {w}", file=sys.stderr)
    if warnings:
        return 1

    write_csv(rows, args.out)
    print(f"Đã ghi {len(rows)} dòng vào {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
