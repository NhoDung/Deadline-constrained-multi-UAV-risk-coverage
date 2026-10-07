"""Tổng hợp kết quả Pha 2: gap so với ILP, kiểm định Wilcoxon cặp, xuất summary.csv.

Chạy: python pipeline/11_summarize_rn.py [--tag g20_default]

Ghi chú diễn giải (docs/phase2-rescuenet-thiet-ke.md mục 6):
- Tỉ lệ = objective / objective của ILP. Với ca ILP chỉ `best-known` (chưa chứng minh
  tối ưu), tỉ lệ là so với nghiệm tốt nhất ILP tìm được và có thể > 1; bảng tách riêng
  hai nhóm `optimal` và `best-known`.
- Cả hai thuật toán đều deterministic nên Wilcoxon ghép cặp theo instance (n = số instance,
  không phải số seed).
"""

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.rn.store import tag_dir

TOL = 1e-9


def ratios_to_ilp(records: list, ilp_status: str = None) -> dict:
    """{(thuật toán, mức): [tỉ lệ objective/ILP theo instance, sắp theo tên instance]}.

    Bỏ instance thiếu ILP hoặc có tối ưu ILP = 0. `ilp_status` (tùy chọn) chỉ giữ ca ILP có
    đúng trạng thái đó ("optimal" hoặc "best-known").
    """
    ilp = {(r["instance"], r["budget_level"]): r for r in records if r["algorithm"] == "ilp_uav"}
    out = {}
    for r in sorted(records, key=lambda r: r["instance"]):
        if r["algorithm"] == "ilp_uav":
            continue
        ref = ilp.get((r["instance"], r["budget_level"]))
        if ref is None or not ref["objective"]:
            continue
        if ilp_status is not None and ref.get("status") != ilp_status:
            continue
        out.setdefault((r["algorithm"], r["budget_level"]), []).append(r["objective"] / ref["objective"])
    return out


def paired_wilcoxon(a: list, b: list) -> float:
    """p-value hai phía của kiểm định Wilcoxon ghép cặp; 1.0 nếu mọi cặp bằng nhau."""
    if all(abs(x - y) <= TOL for x, y in zip(a, b)):
        return 1.0
    return float(wilcoxon(a, b).pvalue)


def win_tie_loss(a: list, b: list) -> tuple:
    """Số cặp a > b, a ≈ b, a < b (dung sai TOL)."""
    wins = sum(x - y > TOL for x, y in zip(a, b))
    losses = sum(y - x > TOL for x, y in zip(a, b))
    return wins, len(a) - wins - losses, losses


def _print_table(title: str, ratios: dict) -> None:
    print(f"\n{title}\nthuật toán | mức | n | trung bình | nhỏ nhất | lớn nhất")
    for (algorithm, level), values in sorted(ratios.items()):
        print(f"{algorithm} | {level}% | {len(values)} | {statistics.mean(values):.4f} | "
              f"{min(values):.4f} | {max(values):.4f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="g20_default")
    args = parser.parse_args()
    records = [json.loads(p.read_text()) for p in sorted((tag_dir(args.tag) / "results").glob("*/*.json"))]

    csv_path = tag_dir(args.tag) / "summary.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["instance", "algorithm", "budget_level", "seed", "covered_cells",
                         "covered_weight", "cost", "time_seconds"])
        for r in records:
            writer.writerow([r["instance"], r["algorithm"], r["budget_level"], "-", r["covered_cells"],
                             r["objective"], sum(r["cost_per_uav"]), r["solve_time_seconds"]])
    print(f"đã ghi {csv_path}")

    _print_table("Tỉ lệ objective/ILP, mọi ca", ratios_to_ilp(records))
    _print_table("Chỉ ca ILP `optimal`", ratios_to_ilp(records, "optimal"))
    _print_table("Chỉ ca ILP `best-known` (tỉ lệ so với nghiệm tốt nhất, có thể > 1)", ratios_to_ilp(records, "best-known"))

    ratios = ratios_to_ilp(records)
    print("\nSo cặp proposed vs naive theo instance (thắng/hòa/thua của proposed) và Wilcoxon hai phía")
    for level in sorted({lv for _, lv in ratios}):
        a, b = ratios.get(("proposed", level)), ratios.get(("naive", level))
        if a and b and len(a) == len(b) and len(a) >= 2:
            w, t, l = win_tie_loss(a, b)
            print(f"{level}%: {w}/{t}/{l}  p = {paired_wilcoxon(a, b):.4g}  (n={len(a)})")

    ablations = sorted({alg for alg, _ in ratios if alg.startswith("abl_")})
    if ablations:
        print("\nAblation: proposed đầy đủ so với bản bỏ bớt thành phần (thắng/hòa/thua của proposed, Wilcoxon)")
        for alg in ablations:
            for level in sorted({lv for a_, lv in ratios if a_ == alg}):
                full, part = ratios.get(("proposed", level)), ratios.get((alg, level))
                if full and part and len(full) == len(part) and len(full) >= 2:
                    w, t, l = win_tie_loss(full, part)
                    print(f"{alg} @{level}%: {w}/{t}/{l}  p = {paired_wilcoxon(full, part):.4g}  (n={len(full)})")


if __name__ == "__main__":
    main()
