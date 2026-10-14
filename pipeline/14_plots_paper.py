"""Vẽ các hình cho paper IEEE (xuất PDF + PNG vào paper/figures/).

Các hình (spec chi tiết ở report/ke-hoach-bo-sung-paper.md mục B1):
  h1  Sơ đồ pipeline hai pha.
  h2  Minh họa một thực thể RescueNet: bản đồ rủi ro 20x20 + route 4 UAV.
      (Ảnh gốc RescueNet không có trong git — khi có dữ liệu ở
      data/RescueNet/segmentation-validationset/val-org-img/ thì chèn panel
      ảnh gốc bên trái bằng tay hoặc chạy lại script có --org-img-dir.)
  h3  Kết quả chính 350 ảnh: tỉ lệ so với ILP của proposed/naive theo mức.
  h4  Chất lượng - thời gian theo số seed (2 panel xếp dọc, chung trục x).
  h5  Pha 1 OR-Library: tỉ lệ so với ILP của greedy thuần và greedy_ls
      (cần chạy 13_summarize_phase1.py trước).
  h6  Thời gian chạy theo quy mô thực thể (timing_scale.csv).

Chạy: python pipeline/14_plots_paper.py --figs h1,h2,h3,h4,h5,h6
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
# Console Windows có thể dùng mã página không hỗ trợ tiếng Việt (cp1252).
for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding="utf-8", errors="replace")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG_DIR = ROOT / "paper" / "figures"

# Bảng màu đã kiểm tra phân biệt được (dataviz): proposed/greedy_ls = blue,
# baseline (naive/greedy thuần) = orange; thứ tự cố định theo thực thể.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
# Dãy bậc ordinal cho 4 mức ngân sách (25/50/75/100%): một sắc màu, nhạt -> đậm.
LEVEL_COLORS = ("#86b6ef", "#3987e5", "#1c5cab", "#0d366b")
UAV_COLORS = (BLUE, ORANGE, AQUA, YELLOW)
UAV_MARKERS = ("o", "s", "^", "D")

LEVELS = ("25%", "50%", "75%", "100%")
LEVELS_P1 = ("75%", "50%", "25%")


def style_axes(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=INK_MUTED, labelcolor=INK_2)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png"):
        fig.savefig(FIG_DIR / f"{name}.{suffix}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Đã ghi {FIG_DIR / name}.pdf và .png")


def _norm_level(raw: str) -> str:
    """Chuẩn hóa tên mức: '25' / '25%' -> '25%' (summary.csv ghi không có %)."""
    return str(raw).strip().rstrip("%") + "%"


def ratios_from_summary(summary_csv: Path) -> dict:
    """Tỉ lệ covered_weight từng thuật toán so với ilp_uav, theo (thuật toán, mức).

    Trả về {algorithm: {level: [ratio, ...]}}; bỏ ca ILP objective = 0.
    """
    per = defaultdict(lambda: defaultdict(list))
    ilp = {}
    with summary_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (str(row["instance"]), _norm_level(row["budget_level"]))
            if row["algorithm"] == "ilp_uav":
                ilp[key] = float(row["covered_weight"])
    with summary_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            algorithm = row["algorithm"]
            if algorithm == "ilp_uav":
                continue
            key = (str(row["instance"]), _norm_level(row["budget_level"]))
            ref = ilp.get(key)
            if not ref:
                continue
            per[algorithm][_norm_level(row["budget_level"])].append(
                float(row["covered_weight"]) / ref
            )
    return per


def fig_main(summary_csv: Path) -> None:
    """H3: dot plot tỉ lệ trung bình (khoảng min-max) theo mức, 350 ảnh.

    Dot plot thay cho bar vì tỉ lệ dao động hẹp quanh 0,9-1,0 — bar phải bắt
    từ 0 sẽ che hết khác biệt.
    """
    per = ratios_from_summary(summary_csv)
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    style_axes(ax)
    series = (("proposed", BLUE, "o"), ("naive", ORANGE, "s"))
    offsets = (-0.12, 0.12)
    ax.axhline(1.0, color=INK_MUTED, linewidth=0.9, linestyle=(0, (4, 3)))
    ax.text(3.42, 1.004, "ILP", color=INK_MUTED, fontsize=7, ha="right")
    for (algorithm, color, marker), dx in zip(series, offsets):
        for i, level in enumerate(LEVELS):
            vals = sorted(per[algorithm][level])
            mean = sum(vals) / len(vals)
            ax.errorbar(
                i + dx, mean,
                yerr=[[mean - vals[0]], [vals[-1] - mean]],
                marker=marker, markersize=4.5, color=color,
                linewidth=1.4, capsize=2.5, markeredgewidth=0,
            )
            ax.annotate(f"{mean:.3f}".replace(".", ","),
                        (i + dx, mean), textcoords="offset points",
                        xytext=(0, 6 if algorithm == "proposed" else -12),
                        ha="center", fontsize=6.5, color=INK_2)
    ax.set_xticks(range(len(LEVELS)), LEVELS)
    ax.set_xlabel("Mức ngân sách (so với chi phí tham chiếu R)")
    ax.set_ylabel("Tỉ lệ so với ILP")
    ax.set_xlim(-0.5, 3.5)
    ax.legend([plt.Line2D([], [], marker=m, color=c, linewidth=1.4)
               for _, c, m in series],
              [a for a, _, _ in series], frameon=False, loc="lower right",
              fontsize=7, labelcolor=INK_2)
    fig.tight_layout()
    _save(fig, "h3_main_results")


def fig_phase1(summary_csv: Path) -> None:
    """H5: dot plot tỉ lệ trung bình Pha 1 (greedy thuần vs greedy_ls)."""
    per = defaultdict(lambda: defaultdict(list))
    with summary_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["algorithm"] == "ilp":
                continue
            # gap_vs_ilp = (ILP - heuristic) / ILP nên tỉ lệ = 1 - gap.
            per[row["algorithm"]][row["budget_level"]].append(
                1.0 - float(row["gap_vs_ilp"])
            )
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    style_axes(ax)
    series = (("greedy_ls", BLUE, "o"), ("greedy", ORANGE, "s"))
    offsets = (-0.12, 0.12)
    for (algorithm, color, marker), dx in zip(series, offsets):
        for i, level in enumerate(LEVELS_P1):
            vals = sorted(per[algorithm][level])
            mean = sum(vals) / len(vals)
            ax.errorbar(
                i + dx, mean,
                yerr=[[mean - vals[0]], [vals[-1] - mean]],
                marker=marker, markersize=4.5, color=color,
                linewidth=1.4, capsize=2.5, markeredgewidth=0,
            )
            ax.annotate(f"{100 * mean:.1f}".replace(".", ",") + "%",
                        (i + dx, mean), textcoords="offset points",
                        xytext=(0, 6 if algorithm == "greedy_ls" else -12),
                        ha="center", fontsize=6.5, color=INK_2)
    ax.set_xticks(range(len(LEVELS_P1)), LEVELS_P1)
    ax.set_xlabel("Mức ngân sách (so với OPT phủ trọn)")
    ax.set_ylabel("Tỉ lệ so với ILP")
    ax.set_ylim(0, 1.08)
    ax.set_xlim(-0.5, 2.5)
    ax.legend([plt.Line2D([], [], marker=m, color=c, linewidth=1.4)
               for _, c, m in series],
              ["greedy tỉ lệ + seed + LS", "greedy thuần"],
              frameon=False, loc="lower center", fontsize=7, labelcolor=INK_2)
    fig.tight_layout()
    _save(fig, "h5_phase1_results")


def fig_example(instance_path: Path, solution_path: Path | None = None,
                level: str = "100") -> None:
    """H2: bản đồ rủi ro 20x20 (một sắc màu nhạt->đậm) + route 4 UAV.

    Chỉ vẽ các route được thuật toán `proposed` chọn ở mức ngân sách `level`
    (đọc từ file kết quả) — vẽ toàn bộ route ứng viên sẽ rối không đọc được.
    """
    instance = json.loads(instance_path.read_text())
    g = instance["grid"]
    risk = [[0.0] * g for _ in range(g)]
    for (r, c), w in zip(instance["cell_rc"], instance["weights"]):
        risk[r][c] = w

    selected = None
    if solution_path is None:
        candidate = instance_path.parent.parent / "results" / "proposed" / (
            f"{instance_path.stem}_{level}.json"
        )
        if candidate.exists():
            solution_path = candidate
    if solution_path is not None:
        selected = set(json.loads(solution_path.read_text())["selected_packages"])

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.9))
    ax = axes[0]
    im = ax.imshow(risk, cmap="Oranges", origin="upper")
    ax.set_xticks([0, g - 1], ["1", str(g)])
    ax.set_yticks([0, g - 1], ["1", str(g)])
    ax.set_xlabel("cột")
    ax.set_ylabel("hàng")
    ax.set_title(f"Bản đồ rủi ro {g}×{g} (ảnh {instance['image_id']}, tầng {instance['tier']})",
                 fontsize=8, color=INK)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.ax.tick_params(labelsize=6, colors=INK_MUTED)
    cbar.outline.set_edgecolor(GRID)
    cbar.set_label("điểm rủi ro", fontsize=7, color=INK_2)

    ax = axes[1]
    ax.imshow(risk, cmap="Oranges", origin="upper", alpha=0.55)
    for u, color in enumerate(UAV_COLORS):
        first = True
        for route_idx, uav in enumerate(instance["route_uav"]):
            if uav != u:
                continue
            if selected is not None and route_idx not in selected:
                continue
            cells = instance["paths"][route_idx]
            rows = [c[0] for c in cells]
            cols = [c[1] for c in cells]
            label = f"UAV {u + 1}" if first else None
            ax.plot(cols, rows, color=color, linewidth=1.8, alpha=0.9,
                    solid_capstyle="round", label=label)
            first = False
    for u, (r, c) in enumerate(instance["uav_starts"]):
        ax.plot(c, r, marker="*", markersize=11, color=UAV_COLORS[u],
                markeredgecolor=INK, markeredgewidth=0.6, linestyle="none")
    ax.set_xticks([0, g - 1], ["1", str(g)])
    ax.set_yticks([0, g - 1], ["1", str(g)])
    ax.set_xlabel("cột")
    ax.set_ylabel("hàng")
    subtitle = ("route proposed chọn ở mức " + level + "%"
                if selected is not None else "toàn bộ route ứng viên")
    ax.set_title(f"Route của K = {len(instance['uav_starts'])} UAV (★: xuất phát, {subtitle})",
                 fontsize=8, color=INK)
    ax.legend(frameon=False, fontsize=6.5, loc="upper center",
              ncols=4, bbox_to_anchor=(0.5, -0.22), labelcolor=INK_2)
    fig.tight_layout()
    _save(fig, "h2_example_instance")


def fig_seeds(timing_csv: Path) -> None:
    """H4: 2 panel xếp dọc, chung trục x = số seed (không dùng trục kép)."""
    per = defaultdict(list)  # (level, n_seeds) -> [(time, ratio)]
    with timing_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            per[(row["level"], int(row["n_seeds"]))].append(
                (float(row["time"]), float(row["ratio_to_ilp"]))
            )
    seeds = sorted({k[1] for k in per})
    levels = sorted({k[0] for k in per}, key=lambda lv: int(lv.rstrip("%")))
    fig, (ax_t, ax_q) = plt.subplots(
        2, 1, figsize=(3.5, 3.4), sharex=True,
        gridspec_kw={"hspace": 0.12},
    )
    for ax in (ax_t, ax_q):
        style_axes(ax)
    for i, level in enumerate(levels):
        color = LEVEL_COLORS[i]
        label = level.rstrip("%") + " %"
        times, ratios = [], []
        for s in seeds:
            vals = per.get((level, s), [])
            if not vals:
                continue
            times.append(sum(t for t, _ in vals) / len(vals))
            ratios.append(sum(r for _, r in vals) / len(vals))
        ax_t.plot(seeds, times, color=color, linewidth=1.6, marker="o",
                  markersize=3, label=label)
        ax_q.plot(seeds, ratios, color=color, linewidth=1.6, marker="o",
                  markersize=3)
    ax_t.set_ylabel("Thời gian (s)")
    ax_q.set_ylabel("Tỉ lệ so với ILP")
    ax_q.set_xlabel("Số seed")
    ax_t.legend(frameon=False, fontsize=6.5, ncols=2, labelcolor=INK_2)
    fig.tight_layout()
    _save(fig, "h4_seeds_quality_time")


def fig_scale(timing_csv: Path) -> None:
    """H6: thời gian theo quy mô (đổi m với n cố định, đổi n với m cố định), thang log."""
    series = defaultdict(list)  # sweep -> (size, time)
    with timing_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            size = int(row["m"]) if row["sweep"] == "m" else int(row["n"])
            series[row["sweep"]].append((size, float(row["time"])))
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    style_axes(ax)
    specs = (("m", BLUE, "o", "đổi m ($n$ cố định)"),
             ("n", ORANGE, "s", "đổi $n$ ($m$ cố định)"))
    for sweep, color, marker, label in specs:
        pts = sorted(series[sweep])
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color,
                marker=marker, markersize=4, linewidth=1.6, label=label)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Quy mô (số ô $m$ / số route $n$)")
    ax.set_ylabel("Thời gian một lần giải (s)")
    ax.legend(frameon=False, fontsize=7, labelcolor=INK_2, loc="lower right")
    fig.tight_layout()
    _save(fig, "h6_scale")


def _box(ax, xy, w, h, text, face) -> None:
    ax.add_patch(FancyBboxPatch(
        xy, w, h, boxstyle="round,pad=0.02,rounding_size=0.02",
        facecolor=face, edgecolor=GRID, linewidth=0.8))
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center",
            fontsize=6.8, color=INK, wrap=True)


def _arrow(ax, start, end) -> None:
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=8,
        color=INK_MUTED, linewidth=1.0, shrinkA=2, shrinkB=2))


def fig_pipeline() -> None:
    """H1: sơ đồ pipeline hai pha (vẽ bằng matplotlib, không cần dữ liệu)."""
    fig, ax = plt.subplots(figsize=(7.16, 2.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    blue_bg = "#cde2fb"
    orange_bg = "#f7d4c3"
    gray_bg = "#f0efec"
    # Pha 1 (hàng trên)
    _box(ax, (0.02, 0.58), 0.15, 0.24, "OR-Library\n45 thực thể\nSet Covering", gray_bg)
    _box(ax, (0.21, 0.58), 0.15, 0.24, "Chuyển đổi\n(02)\ngói → ô", gray_bg)
    _box(ax, (0.40, 0.58), 0.15, 0.24, "ILP tối ưu\n(03)\nchế độ A + B", blue_bg)
    _box(ax, (0.59, 0.58), 0.15, 0.24, "Greedy thuần (04)\ngreedy + seed\n+ LS (06)", orange_bg)
    _box(ax, (0.78, 0.58), 0.20, 0.24, "Validator (05)\ntự tính lại,\nHệ quả 1", gray_bg)
    _arrow(ax, (0.17, 0.70), (0.21, 0.70))
    _arrow(ax, (0.36, 0.70), (0.40, 0.70))
    _arrow(ax, (0.55, 0.70), (0.59, 0.70))
    _arrow(ax, (0.74, 0.70), (0.78, 0.70))
    # Pha 2 (hàng dưới)
    _box(ax, (0.02, 0.12), 0.15, 0.24, "RescueNet\nmask 11 lớp\n(ảnh thật)", gray_bg)
    _box(ax, (0.21, 0.12), 0.15, 0.24, "risk map\n(07)\nlưới G×G", gray_bg)
    _box(ax, (0.40, 0.12), 0.15, 0.24, "Route + pin\nK = 4 UAV\n(07)", gray_bg)
    _box(ax, (0.59, 0.12), 0.15, 0.24, "ILP (08) —\nproposed (09)\nnaive (09)", blue_bg)
    _box(ax, (0.78, 0.12), 0.20, 0.24, "Validator (10)\n+ tổng hợp (11)\n+ thời gian (12)", gray_bg)
    _arrow(ax, (0.17, 0.24), (0.21, 0.24))
    _arrow(ax, (0.36, 0.24), (0.40, 0.24))
    _arrow(ax, (0.55, 0.24), (0.59, 0.24))
    _arrow(ax, (0.74, 0.24), (0.78, 0.24))
    # Nhãn pha
    ax.text(0.01, 0.88, "Pha 1 — một ngân sách", fontsize=7.5, color=INK_2, style="italic")
    ax.text(0.01, 0.42, "Pha 2 — nhiều ngân sách (per-UAV)", fontsize=7.5, color=INK_2, style="italic")
    # greedy_ls chuyển từ Pha 1 sang Pha 2
    _arrow(ax, (0.665, 0.58), (0.665, 0.36))
    ax.text(0.675, 0.47, "dùng lại\n(09)", fontsize=6.2, color=INK_MUTED, va="center")
    fig.tight_layout()
    _save(fig, "h1_pipeline")


def main(argv: list[str] | None = None) -> int:
    global FIG_DIR
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--figs",
        default="h1,h2,h3,h4,h5,h6",
        help="Danh sách hình cần vẽ, ví dụ: h1,h3 (mặc định: tất cả)",
    )
    parser.add_argument(
        "--summary-full",
        type=Path,
        default=DATA / "rescuenet" / "full_g20_default" / "summary.csv",
        help="summary.csv của lần chạy 350 ảnh (cho h3)",
    )
    parser.add_argument(
        "--summary-phase1",
        type=Path,
        default=DATA / "results" / "summary_phase1.csv",
        help="summary_phase1.csv từ 13_summarize_phase1.py (cho h5)",
    )
    parser.add_argument(
        "--timing-seeds",
        type=Path,
        default=DATA / "rescuenet" / "g20_default" / "timing_seeds.csv",
        help="timing_seeds.csv (cho h4)",
    )
    parser.add_argument(
        "--timing-scale",
        type=Path,
        default=DATA / "rescuenet" / "timing_scale.csv",
        help="timing_scale.csv (cho h6)",
    )
    parser.add_argument(
        "--instance",
        type=Path,
        default=None,
        help="File instance JSON để vẽ h2 (mặc định: ảnh tầng 'high' đầu tiên của g20_default)",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=FIG_DIR,
        help="Thư mục xuất hình (mặc định: paper/figures/)",
    )
    args = parser.parse_args(argv)
    FIG_DIR = args.outdir

    wanted = {f.strip().lower() for f in args.figs.split(",") if f.strip()}
    jobs = {
        "h1": lambda: fig_pipeline(),
        "h2": lambda: fig_example(
            args.instance or sorted(
                (DATA / "rescuenet" / "g20_default" / "instances").glob("*.json"),
                key=lambda p: json.loads(p.read_text())["tier"] != "high",
            )[0]
        ),
        "h3": lambda: fig_main(args.summary_full),
        "h4": lambda: fig_seeds(args.timing_seeds),
        "h5": lambda: fig_phase1(args.summary_phase1),
        "h6": lambda: fig_scale(args.timing_scale),
    }
    if "h5" in wanted and not args.summary_phase1.exists():
        print("Thiếu data/results/summary_phase1.csv — chạy trước:\n"
              "  python pipeline/13_summarize_phase1.py", file=sys.stderr)
        return 1
    for name in sorted(wanted):
        if name not in jobs:
            print(f"Không biết hình '{name}' (hợp lệ: {', '.join(sorted(jobs))})",
                  file=sys.stderr)
            return 1
        jobs[name]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
