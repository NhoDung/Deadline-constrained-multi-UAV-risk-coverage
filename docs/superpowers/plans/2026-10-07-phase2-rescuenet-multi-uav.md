# Phase 2 RescueNet multi-UAV: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sinh instance multi-UAV từ nhãn RescueNet, giải bằng ILP có trọng số + ngân sách riêng từng UAV, cài thuật toán đề xuất và baseline, rồi so sánh để có số liệu cho báo cáo (hạn nộp: hết ngày 11/10/2026).

**Architecture:** Thư viện nhỏ `pipeline/rn/` (risk map, chọn ảnh, sinh route, ngân sách, lưu trữ) + các script đánh số tiếp nối `pipeline/` (07 chuẩn bị, 08 ILP, 09 greedy per-UAV, 10 validator, 11 tổng hợp). Mỗi route thuộc đúng một UAV; chọn nhiều route cho một UAV miễn tổng chi phí ≤ pin của UAV đó. Thuật toán đề xuất tái dùng ý tưởng `pipeline/06_greedy_ls.py` (lazy ratio greedy + seed + drop-and-refill) nhưng kiểm tra ngân sách theo từng UAV.

**Tech Stack:** Python (venv `.venv`), numpy, Pillow, scipy, PuLP==3.3.2 (CBC), pytest.

**Spec:** `docs/phase2-rescuenet-thiet-ke.md` (đã duyệt tạm 07/10/2026). Đọc spec này trước khi làm bất kỳ task nào.

## Global Constraints

- Mọi lệnh chạy từ thư mục gốc repo, với venv đã kích hoạt (`source .venv/bin/activate`).
- **Không sửa** script Pha 1 (`pipeline/01`–`06`, `opt_reference.py`) và **không sửa** `data/results/**`. `audit_results.py` glob `data/results/*/*.json`, nên mọi kết quả Pha 2 nằm ở `data/rescuenet/<tag>/...`, không bao giờ nằm trong `data/results/`.
- Tag mặc định `g20_default` = lưới 20×20 + bảng điểm `default`. Layout: `data/rescuenet/<tag>/instances/*.json`, `data/rescuenet/<tag>/results/<algorithm>/<instance>_<level>.json`.
- Bảng điểm `default` = `[0,1,1,2,3,3,1,1,3,0,1]` (chỉ số = nhãn 0..10; Background = 0, Tree = 0). Ô có điểm 0 bị loại khỏi universe.
- Route: chi phí = `takeoff_cost(2) + cell_cost(1) × số ô đi qua`. K = 4 UAV, `routes_per_uav = 300`, `max_cells = 40` (mặc định, chỉnh được bằng CLI).
- Ngân sách: `B_u(level) = floor(level × R × share_u / 100)` với `R` = chi phí nhỏ nhất để phủ mọi ô **có route phủ được** (ILP set cover trên toàn bộ route, bỏ qua phân chia UAV), `share_u ∝ 1 + ε_u`, `ε_u ∈ [−0.2, 0.2]` sinh theo seed. Mức mặc định: 100, 75, 50, 25.
- Mục tiêu = **tổng điểm rủi ro** của ô được phủ. Trường kết quả `objective` = tổng điểm rủi ro (khác Pha 1, nơi `objective` là số ô).
- Docstring/comment bằng tiếng Việt, như code hiện có. Tên hàm/biến tiếng Anh.
- **Không chỉnh heuristic để khớp ILP**; báo cáo gap trung thực (project-brief mục 7).
- Mọi con số trong báo cáo lấy từ file kết quả/`summary.csv`, **không để AI tự viết số**.
- Chỉ commit khi người dùng đồng ý. Làm trên nhánh `phase2-rescuenet`. Commit message kết thúc bằng dòng `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Review Focus

Các tình huống spec ngầm đòi hỏi nhưng dễ bị bỏ sót (mỗi dòng có test trong task chủ):

1. Ảnh có kích thước lẻ (4056×3040, không chia hết cho lưới) → `cell_risk` cắt phần dư, không lỗi (Task 1).
2. Ảnh gần như không có ô điểm > 0 → `build_instance` báo `ValueError` rõ ràng; `select` loại sẵn bằng ngưỡng `min_cells` (Task 2, 3).
3. Hai route của cùng một UAV phủ cùng tập ô nhưng khác chi phí → chỉ giữ route rẻ nhất (Task 3).
4. Ô không route nào phủ được → `reference_cost` chỉ tính ô phủ được, không bị infeasible (Task 4).
5. UAV có ngân sách nhỏ hơn mọi route của nó (mức 25%) → lời giải rỗng hợp lệ cho UAV đó, không crash, ở cả ILP và greedy (Task 5, 6).
6. Tổng ngân sách đủ nhưng một UAV vượt pin riêng → validator bắt lỗi dù tổng chi phí hợp lệ (Task 7).

---

## Cách tiếp tục ở session mới (ĐỌC TRƯỚC)

1. Đọc spec `docs/phase2-rescuenet-thiet-ke.md` và file này.
2. Chạy `git status`, `git branch --show-current`, `python -m pytest -q`.
3. Xem bảng **Tiến độ** bên dưới, tìm task đầu tiên chưa xong, rồi tìm checkbox `- [ ]` đầu tiên của task đó. Nếu test đang đỏ do task dở dang, sửa cho xanh trước.
4. Sau mỗi task: tick checkbox trong file này, cập nhật bảng Tiến độ và Nhật ký session, rồi mới chuyển task.
5. Bộ nhớ dự án (ngoài repo) cũng có con trỏ tới file này.

### Tiến độ

| Task | Nội dung | Hạn mục tiêu | Trạng thái |
|---|---|---|---|
| 0 | Nhánh, phụ thuộc, `.gitignore` | 07/10 | ✅ đã commit |
| 1 | Risk map từ mask (`rn/risk.py`) | 07/10 | ✅ đã commit |
| 2 | Chọn ảnh phân tầng (`rn/select.py`) | 07/10 | ✅ đã commit |
| 3 | Sinh route/instance (`rn/routes.py`) | 08/10 | ✅ đã commit |
| 4 | Chi phí tham chiếu, ngân sách, CLI chuẩn bị `07` | 08/10 | ✅ đã commit |
| 5 | ILP có trọng số + per-UAV (`08`) | 08/10 | ✅ đã commit (20/120 best-known) |
| 6 | Greedy per-UAV: đề xuất + naive (`09`) | 09/10 | ✅ đã commit |
| 7 | Validator per-UAV (`10`) | 09/10 | ✅ (chưa commit) |
| 8 | Chạy toàn bộ + tổng hợp + Wilcoxon (`11`) | 10/10 | ⬜ |
| 9 | Sensitivity + ablation + cập nhật docs | 10/10 | ⬜ |

### Nhật ký session

- 07/10/2026: audit Pha 1 xong (0 lỗi/450 file), xác nhận dữ liệu RescueNet (validation set 449 ảnh), duyệt spec, viết kế hoạch này.
- 07/10/2026 (session 1, tiếp): chọn cách thực thi Native. Xong Task 0 (nhánh `phase2-rescuenet`, ghim numpy==2.5.3, pillow==12.3.0, scipy==1.18.1) và Task 1 (`pipeline/rn/risk.py`, 6 test mới, toàn bộ 33 test xanh). Thử trên mask thật 14238: lưới 20x20, 155 ô điểm > 0, 0.14s. Chưa commit gì (chờ người dùng đồng ý). Đã commit Task 0 và 1 (be14bc9, 739d9ca).
- 07/10/2026: xong Task 2 (`pipeline/rn/select.py`, 4 test, tổng 37 test xanh), đã commit 98a58ed.
- 07/10/2026: xong Task 3 (`pipeline/rn/routes.py`, 8 test, tổng 45 test xanh), chưa commit. Thử trên mask 14238 (k=4, 300 route/UAV, max 40 ô): m=155, n=755, đủ 155/155 ô phủ được, 0.03s; số route mỗi UAV lệch (271/212/43/229) vì dedupe theo tập ô. Đã commit d8c639c.
- 07/10/2026: xong Task 4 (`rn/budgets.py`, `rn/store.py`, `07_rn_prepare.py`, 4 test, tổng 49 test xanh), chưa commit. Chạy thật: `select` (33s): 449 ảnh, 350 đủ điều kiện (min_cells=60), chọn 30 (10/tầng; tầng low có damage_frac 0–0.0023, mid 0.042–0.090, high 0.098–0.283). `build` (2 phút): 30 instance trong `data/rescuenet/g20_default/instances/` (5.4MB), m=68–304, n=403–1027, R=109–598. Phát hiện: (a) instance 12078 có 1 ô không route nào phủ được (đã được `reference_cost` xử lý); (b) trên 120 cặp (instance, UAV), số UAV có ngân sách < route rẻ nhất của chính nó: 28 ở mức 25%, 9 ở 50%, 3 ở 75%, 1 ở 100% (tức mức 25% khá khắc nghiệt: ~23% UAV không bay được route nào). Task kế tiếp: Task 5 (ILP có trọng số + per-UAV, `08`).

---

### Task 0: Nhánh, phụ thuộc

**Files:**
- Modify: `requirements.txt`
- (`.gitignore` đã có dòng `data/RescueNet/`.)

- [ ] **Step 1: Tạo nhánh**

```bash
git checkout -b phase2-rescuenet
```

- [ ] **Step 2: Cài phụ thuộc vào venv của repo**

```bash
source .venv/bin/activate
pip install numpy Pillow scipy
pip freeze | grep -i -E '^(numpy|pillow|scipy)=='
```

- [ ] **Step 3: Ghim đúng các phiên bản vừa in ra vào `requirements.txt`** (mỗi dòng dạng `numpy==X.Y.Z`, `pillow==X.Y.Z`, `scipy==X.Y.Z`, giữ nguyên dòng `PuLP==3.3.2`).

- [ ] **Step 4: Xác nhận test cũ vẫn xanh**

Run: `python -m pytest -q`
Expected: `27 passed`

- [ ] **Step 5: Commit (khi người dùng đồng ý)**

```bash
git add .gitignore requirements.txt docs/phase2-rescuenet-thiet-ke.md docs/superpowers/plans/2026-10-07-phase2-rescuenet-multi-uav.md
git commit -m "docs: phase 2 spec and plan; add numpy/pillow/scipy"
```

---

### Task 1: Risk map từ mask

**Files:**
- Create: `pipeline/rn/__init__.py` (rỗng)
- Create: `pipeline/rn/risk.py`
- Test: `tests/test_rn_risk.py`

**Interfaces:**
- Produces: `SCORE_TABLES: dict[str, list[float]]`; `cell_risk(mask: np.ndarray, grid: int, table: list) -> np.ndarray` (shape `(grid, grid)`, điểm trung bình pixel mỗi ô, cắt phần dư); `damage_fraction(mask) -> float` (tỉ lệ pixel nhãn 3, 4, 5, 8); `load_mask(path) -> np.ndarray`.

- [ ] **Step 1: Viết test (thất bại)**

```python
# tests/test_rn_risk.py
import numpy as np
import pytest
from PIL import Image

from pipeline.rn.risk import SCORE_TABLES, cell_risk, damage_fraction, load_mask

TABLE = SCORE_TABLES["default"]


def test_cell_risk_averages_pixel_scores_per_cell():
    mask = np.array([[5, 0, 0, 0], [5, 0, 0, 0], [0, 0, 4, 4], [0, 0, 4, 4]])
    out = cell_risk(mask, grid=2, table=TABLE)
    assert out.tolist() == [[1.5, 0.0], [0.0, 3.0]]


def test_cell_risk_crops_remainder_pixels():
    # Ảnh 5x5 không chia hết cho lưới 2x2: phải cắt phần dư thay vì báo lỗi.
    out = cell_risk(np.zeros((5, 5), dtype=int), grid=2, table=TABLE)
    assert out.shape == (2, 2)


def test_cell_risk_rejects_labels_outside_table():
    with pytest.raises(ValueError):
        cell_risk(np.array([[11]]), grid=1, table=TABLE)


def test_tree_scores_zero_in_default_and_one_in_tree1():
    mask = np.full((2, 2), 9)
    assert cell_risk(mask, 1, SCORE_TABLES["default"]).item() == 0.0
    assert cell_risk(mask, 1, SCORE_TABLES["tree1"]).item() == 1.0


def test_damage_fraction_counts_labels_3_4_5_8():
    assert damage_fraction(np.array([[3, 4], [0, 9]])) == 0.5


def test_load_mask_reads_grayscale_png(tmp_path):
    path = tmp_path / "x_lab.png"
    Image.fromarray(np.array([[0, 5], [8, 10]], dtype=np.uint8)).save(path)
    assert load_mask(path).tolist() == [[0, 5], [8, 10]]
```

- [ ] **Step 2: Chạy, xác nhận thất bại**

Run: `python -m pytest tests/test_rn_risk.py -q`
Expected: FAIL (`ModuleNotFoundError: pipeline.rn.risk`)

- [ ] **Step 3: Cài đặt**

```python
# pipeline/rn/risk.py
"""Bản đồ rủi ro từ mask RescueNet (xem docs/phase2-rescuenet-thiet-ke.md mục 2, 3)."""

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# Chỉ số = nhãn 0..10 (Background, Water, Bld-No, Bld-Minor, Bld-Major,
# Bld-Total, Vehicle, Road-Clear, Road-Blocked, Tree, Pool).
SCORE_TABLES = {
    "default": [0, 1, 1, 2, 3, 3, 1, 1, 3, 0, 1],
    "tree1": [0, 1, 1, 2, 3, 3, 1, 1, 3, 1, 1],
    "convex": [0, 1, 1, 4, 9, 9, 1, 1, 9, 0, 1],
    "damage_only": [0, 0, 0, 2, 3, 3, 0, 0, 3, 0, 0],
}

DAMAGE_LABELS = (3, 4, 5, 8)


def load_mask(path) -> np.ndarray:
    return np.array(Image.open(path))


def cell_risk(mask: np.ndarray, grid: int, table: list) -> np.ndarray:
    """Điểm rủi ro trung bình của pixel trong mỗi ô lưới `grid` x `grid`.

    Phần pixel dư ở mép (khi kích thước ảnh không chia hết cho `grid`) bị cắt.
    """
    if mask.max() >= len(table):
        raise ValueError(f"mask có nhãn {int(mask.max())} nhưng bảng điểm chỉ có {len(table)} lớp")
    pixel_score = np.asarray(table, dtype=float)[mask]
    cell_h, cell_w = pixel_score.shape[0] // grid, pixel_score.shape[1] // grid
    cropped = pixel_score[: cell_h * grid, : cell_w * grid]
    return cropped.reshape(grid, cell_h, grid, cell_w).mean(axis=(1, 3))


def damage_fraction(mask: np.ndarray) -> float:
    """Tỉ lệ pixel thuộc nhãn hư hại (3, 4, 5, 8); dùng để chia tầng ảnh."""
    return float(np.isin(mask, DAMAGE_LABELS).mean())
```

- [ ] **Step 4: Chạy, xác nhận qua**

Run: `python -m pytest tests/test_rn_risk.py -q`
Expected: `6 passed`

- [ ] **Step 5: Commit (khi người dùng đồng ý)** `git add pipeline/rn tests/test_rn_risk.py && git commit -m "feat: rescuenet risk map from masks"`

---

### Task 2: Chọn ảnh phân tầng

**Files:**
- Create: `pipeline/rn/select.py`
- Test: `tests/test_rn_select.py`

**Interfaces:**
- Consumes: không.
- Produces: `select_images(stats: list[dict], n_per_tier: int, min_cells: int, seed: int) -> list[dict]`. Mỗi phần tử `stats` có `id` (str), `damage_frac` (float), `nonzero_cells` (int). Trả về các phần tử đã chọn kèm trường `tier` ∈ {`"low"`, `"mid"`, `"high"`}, sắp theo tầng rồi theo `id`.

- [ ] **Step 1: Viết test (thất bại)**

```python
# tests/test_rn_select.py
from pipeline.rn.select import select_images


def make(i, damage, cells=100):
    return {"id": f"{i:05d}", "damage_frac": damage, "nonzero_cells": cells}


def test_filters_images_with_too_few_nonzero_cells():
    stats = [make(i, i / 100, 100 if i % 2 else 10) for i in range(30)]
    out = select_images(stats, n_per_tier=2, min_cells=60, seed=1)
    assert out and all(s["nonzero_cells"] >= 60 for s in out)


def test_stratifies_into_three_equal_tiers_ordered_by_damage():
    stats = [make(i, i / 100) for i in range(60)]
    out = select_images(stats, n_per_tier=5, min_cells=60, seed=1)
    by_tier = {t: [s["damage_frac"] for s in out if s["tier"] == t] for t in ("low", "mid", "high")}
    assert [len(v) for v in by_tier.values()] == [5, 5, 5]
    assert max(by_tier["low"]) < min(by_tier["mid"]) <= max(by_tier["mid"]) < min(by_tier["high"])


def test_same_seed_same_selection_different_seed_differs():
    stats = [make(i, i / 100) for i in range(60)]
    a = select_images(stats, 5, 60, seed=1)
    assert a == select_images(stats, 5, 60, seed=1)
    assert a != select_images(stats, 5, 60, seed=2)


def test_returns_fewer_when_tier_is_small():
    stats = [make(i, i / 100) for i in range(6)]
    out = select_images(stats, n_per_tier=10, min_cells=60, seed=1)
    assert len(out) == 6
```

- [ ] **Step 2: Chạy, xác nhận thất bại** — `python -m pytest tests/test_rn_select.py -q` → FAIL (import).

- [ ] **Step 3: Cài đặt**

```python
# pipeline/rn/select.py
"""Chọn ảnh RescueNet phân tầng theo mức hư hại (docs/phase2-rescuenet-thiet-ke.md mục 4)."""

import random

TIERS = ("low", "mid", "high")


def select_images(stats: list, n_per_tier: int, min_cells: int, seed: int) -> list:
    """Lọc ảnh đủ ô điểm > 0, chia 3 tầng theo tỉ lệ hư hại, bốc ngẫu nhiên có seed.

    Tầng chia theo tam phân vị của `damage_frac` trong số ảnh đủ điều kiện
    (tập validation không có nhãn phân loại ảnh 0/1/2 chính thức).
    """
    eligible = [s for s in stats if s["nonzero_cells"] >= min_cells]
    eligible.sort(key=lambda s: (s["damage_frac"], s["id"]))
    third = len(eligible) // 3
    tiers = [eligible[:third], eligible[third : 2 * third], eligible[2 * third :]]
    rng = random.Random(seed)
    chosen = []
    for name, tier in zip(TIERS, tiers):
        picked = rng.sample(tier, min(n_per_tier, len(tier)))
        chosen += [{**s, "tier": name} for s in sorted(picked, key=lambda s: s["id"])]
    return chosen
```

- [ ] **Step 4: Chạy, xác nhận qua** — `python -m pytest tests/test_rn_select.py -q` → `4 passed`.

  Lưu ý test 4: 6 ảnh → mỗi tầng 2 ảnh (`third = 2`; tầng cuối nhận phần dư), tổng 6. Nếu `high` nhận dư ảnh thì vẫn tổng 6.

- [ ] **Step 5: Commit (khi người dùng đồng ý)** `git add pipeline/rn/select.py tests/test_rn_select.py && git commit -m "feat: stratified rescuenet image selection"`

---

### Task 3: Sinh route và instance

**Files:**
- Create: `pipeline/rn/routes.py`
- Test: `tests/test_rn_routes.py`

**Interfaces:**
- Produces: `start_cells(k, grid) -> list[tuple[int,int]]`; `random_route(start, risk, max_cells, rng) -> list[tuple[int,int]]`; `build_instance(risk, k, routes_per_uav, max_cells, seed, takeoff_cost=2, cell_cost=1) -> dict` với các khóa: `grid, m, n, costs, sets, weights, route_uav, paths, uav_starts, uav_share, cell_rc, reference_cost (None)`. `sets[j]` là danh sách chỉ số ô (0-based, trong universe đã lọc ô điểm 0) mà route `j` phủ; `route_uav[j]` ∈ [0, k).

- [ ] **Step 1: Viết test (thất bại)**

```python
# tests/test_rn_routes.py
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
```

- [ ] **Step 2: Chạy, xác nhận thất bại** — `python -m pytest tests/test_rn_routes.py -q` → FAIL (import).

- [ ] **Step 3: Cài đặt**

```python
# pipeline/rn/routes.py
"""Sinh instance multi-UAV từ bản đồ rủi ro (docs/phase2-rescuenet-thiet-ke.md mục 5).

Route = đường đi tự tránh (không đi lại ô) liền mạch trên lưới 4 hướng, xuất
phát từ điểm của một UAV, ưu tiên bước vào ô có rủi ro cao. Route phủ các ô
có điểm > 0 nằm trên đường đi; ô điểm 0 chỉ là đường đi, không thuộc universe.
"""

import random

_MOVES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def start_cells(k: int, grid: int) -> list:
    """K điểm xuất phát cố định: 4 góc rồi 4 trung điểm cạnh."""
    last, mid = grid - 1, grid // 2
    pool = [(0, 0), (0, last), (last, 0), (last, last), (0, mid), (mid, 0), (last, mid), (mid, last)]
    if not 1 <= k <= len(pool):
        raise ValueError(f"k phải trong [1, {len(pool)}], nhận {k}")
    return pool[:k]


def random_route(start: tuple, risk, max_cells: int, rng: random.Random) -> list:
    """Đường đi tự tránh dài tối đa `max_cells` ô, lệch về ô rủi ro cao."""
    grid = risk.shape[0]
    path = [start]
    seen = {start}
    target = rng.randint(2, max_cells)
    while len(path) < target:
        r, c = path[-1]
        neighbours = [
            (r + dr, c + dc)
            for dr, dc in _MOVES
            if 0 <= r + dr < grid and 0 <= c + dc < grid and (r + dr, c + dc) not in seen
        ]
        if not neighbours:
            break
        weights = [float(risk[n]) + 0.1 for n in neighbours]
        nxt = rng.choices(neighbours, weights=weights)[0]
        path.append(nxt)
        seen.add(nxt)
    return path


def build_instance(risk, k: int, routes_per_uav: int, max_cells: int, seed: int,
                   takeoff_cost: int = 2, cell_cost: int = 1) -> dict:
    grid = risk.shape[0]
    cells = [(r, c) for r in range(grid) for c in range(grid) if risk[r, c] > 0]
    if not cells:
        raise ValueError("bản đồ rủi ro không có ô nào điểm > 0")
    index = {rc: i for i, rc in enumerate(cells)}
    starts = start_cells(k, grid)
    rng = random.Random(seed)

    costs, sets, owners, paths = [], [], [], []
    for u, start in enumerate(starts):
        best = {}  # tập ô phủ -> (chi phí, đường đi): giữ route rẻ nhất cho mỗi tập ô
        for _ in range(routes_per_uav):
            path = random_route(start, risk, max_cells, rng)
            covered = frozenset(index[p] for p in path if p in index)
            if not covered:
                continue
            cost = takeoff_cost + cell_cost * len(path)
            if covered not in best or cost < best[covered][0]:
                best[covered] = (cost, path)
        for covered, (cost, path) in sorted(best.items(), key=lambda kv: (kv[1][0], sorted(kv[0]))):
            costs.append(cost)
            sets.append(sorted(covered))
            owners.append(u)
            paths.append([list(p) for p in path])

    share_rng = random.Random(seed + 1)
    raw = [1 + share_rng.uniform(-0.2, 0.2) for _ in range(k)]
    return {
        "grid": grid,
        "m": len(cells),
        "n": len(costs),
        "costs": costs,
        "sets": sets,
        "weights": [float(risk[rc]) for rc in cells],
        "route_uav": owners,
        "paths": paths,
        "uav_starts": [list(s) for s in starts],
        "uav_share": [x / sum(raw) for x in raw],
        "cell_rc": [list(rc) for rc in cells],
        "reference_cost": None,
    }
```

- [ ] **Step 4: Chạy, xác nhận qua** — `python -m pytest tests/test_rn_routes.py -q` → `8 passed`. Nếu `test_duplicate_cover_keeps_cheapest...` thất bại vì seed không sinh được đường ngắn nhất, tăng `routes_per_uav` trong test (không đổi code).

- [ ] **Step 5: Commit (khi người dùng đồng ý)** `git add pipeline/rn/routes.py tests/test_rn_routes.py && git commit -m "feat: multi-UAV route and instance generation"`

---

### Task 4: Chi phí tham chiếu, ngân sách, CLI chuẩn bị

**Files:**
- Create: `pipeline/rn/budgets.py`
- Create: `pipeline/rn/store.py`
- Create: `pipeline/07_rn_prepare.py`
- Modify: `tests/conftest.py` (thêm alias `"pipeline.rn_prepare": "07_rn_prepare.py"`)
- Test: `tests/test_rn_budgets.py`, `tests/test_rn_prepare.py`

**Interfaces:**
- Consumes: `build_instance`, `cell_risk`, `SCORE_TABLES`, `select_images`.
- Produces:
  - `reference_cost(instance, time_limit=120) -> int` (ILP set cover trên các ô phủ được).
  - `budgets_for_level(instance, level: int) -> list[int]` (đọc `instance["reference_cost"]`, `instance["uav_share"]`).
  - `store.tag_dir(tag) -> Path`, `store.list_instances(tag) -> list[str]`, `store.load_instance(tag, name) -> dict`, `store.save_result(tag, algorithm, instance_name, level, payload) -> Path`.
  - `07_rn_prepare.build_from_mask(mask, grid, table_name, k, routes_per_uav, max_cells, seed) -> dict` (instance đã có `reference_cost`).

- [ ] **Step 1: Viết test ngân sách (thất bại)**

```python
# tests/test_rn_budgets.py
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
```

- [ ] **Step 2: Chạy, xác nhận thất bại** — `python -m pytest tests/test_rn_budgets.py -q` → FAIL.

- [ ] **Step 3: Cài đặt `budgets.py` và `store.py`**

```python
# pipeline/rn/budgets.py
"""Chi phí tham chiếu R và ngân sách riêng từng UAV (spec mục 5)."""

import math

import pulp


def reference_cost(instance: dict, time_limit: int = 120) -> int:
    """Chi phí nhỏ nhất để phủ mọi ô mà ít nhất một route phủ được (bỏ qua phân chia UAV)."""
    n, costs = instance["n"], instance["costs"]
    covering = {}
    for j, cells in enumerate(instance["sets"]):
        for i in cells:
            covering.setdefault(i, []).append(j)
    if not covering:
        return 0
    prob = pulp.LpProblem("reference_cover", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(n)]
    prob += pulp.lpSum(costs[j] * x[j] for j in range(n))
    for i, routes in covering.items():
        prob += pulp.lpSum(x[j] for j in routes) >= 1, f"cover_{i}"
    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    if pulp.LpStatus[prob.status] != "Optimal":
        raise RuntimeError(f"không giải tối ưu được chi phí tham chiếu (status={pulp.LpStatus[prob.status]})")
    return round(sum(costs[j] for j in range(n) if x[j].value() > 0.5))


def budgets_for_level(instance: dict, level: int) -> list:
    """B_u = floor(level% x R x share_u)."""
    r = instance["reference_cost"]
    return [math.floor(level * r * s / 100) for s in instance["uav_share"]]
```

```python
# pipeline/rn/store.py
"""Đường dẫn và đọc/ghi file cho dữ liệu Pha 2 (data/rescuenet/<tag>/...)."""

import json
from pathlib import Path

RN_DIR = Path(__file__).resolve().parents[2] / "data" / "rescuenet"


def tag_dir(tag: str) -> Path:
    return RN_DIR / tag


def list_instances(tag: str) -> list:
    return sorted(p.stem for p in (tag_dir(tag) / "instances").glob("*.json"))


def load_instance(tag: str, name: str) -> dict:
    return json.loads((tag_dir(tag) / "instances" / f"{name}.json").read_text())


def save_result(tag: str, algorithm: str, instance_name: str, level: int, payload: dict) -> Path:
    dest = tag_dir(tag) / "results" / algorithm / f"{instance_name}_{level}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2))
    return dest
```

- [ ] **Step 4: Chạy test ngân sách** — `python -m pytest tests/test_rn_budgets.py -q` → `3 passed`.

- [ ] **Step 5: Viết test CLI chuẩn bị (thất bại)**

```python
# tests/test_rn_prepare.py
import numpy as np

from pipeline.rn_prepare import build_from_mask


def test_build_from_mask_sets_reference_cost_and_is_deterministic():
    mask = np.zeros((40, 40), dtype=int)
    mask[:20, :20] = 5   # góc trên-trái: hư hại nặng
    mask[20:, 20:] = 3   # góc dưới-phải: hư hại vừa
    a = build_from_mask(mask, grid=4, table_name="default", k=2, routes_per_uav=60, max_cells=6, seed=1)
    b = build_from_mask(mask, grid=4, table_name="default", k=2, routes_per_uav=60, max_cells=6, seed=1)
    assert a == b
    assert a["m"] == 8  # 4 ô trái-trên + 4 ô phải-dưới có điểm > 0
    assert isinstance(a["reference_cost"], int) and a["reference_cost"] > 0
```

- [ ] **Step 6: Thêm alias vào `tests/conftest.py`** (trong dict `ALIASES`): `"pipeline.rn_prepare": "07_rn_prepare.py",`. Chạy test: FAIL (thiếu file).

- [ ] **Step 7: Cài đặt `pipeline/07_rn_prepare.py`**

```python
"""Chuẩn bị instance RescueNet cho Pha 2 (docs/phase2-rescuenet-thiet-ke.md).

Hai bước:
  python pipeline/07_rn_prepare.py select
      -> data/rescuenet/image_stats.json (thống kê mọi mask)
         data/rescuenet/selection.json   (ảnh được chọn, phân tầng, có seed)
  python pipeline/07_rn_prepare.py build [--grid 20] [--table default]
      -> data/rescuenet/<tag>/instances/<id>.json  (tag = g<grid>_<table>)
Sensitivity: chạy `build` với --grid/--table khác, vẫn dùng chung selection.json.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.rn.budgets import reference_cost
from pipeline.rn.risk import SCORE_TABLES, cell_risk, damage_fraction, load_mask
from pipeline.rn.routes import build_instance
from pipeline.rn.select import select_images
from pipeline.rn.store import RN_DIR, tag_dir

MASK_DIR = Path(__file__).resolve().parent.parent / "data" / "RescueNet" / "segmentation-validationset" / "val-label-img"
SELECT_GRID, SELECT_TABLE = 20, "default"


def build_from_mask(mask: np.ndarray, grid: int, table_name: str, k: int,
                    routes_per_uav: int, max_cells: int, seed: int) -> dict:
    risk = cell_risk(mask, grid, SCORE_TABLES[table_name])
    instance = build_instance(risk, k, routes_per_uav, max_cells, seed)
    instance["reference_cost"] = reference_cost(instance)
    return instance


def image_id(path: Path) -> str:
    return path.name.removesuffix("_lab.png")


def cmd_select(args) -> None:
    stats = []
    for path in sorted(MASK_DIR.glob("*_lab.png")):
        mask = load_mask(path)
        risk = cell_risk(mask, SELECT_GRID, SCORE_TABLES[SELECT_TABLE])
        stats.append({"id": image_id(path), "damage_frac": damage_fraction(mask),
                      "nonzero_cells": int((risk > 0).sum())})
    RN_DIR.mkdir(parents=True, exist_ok=True)
    (RN_DIR / "image_stats.json").write_text(json.dumps(stats, indent=1))
    chosen = select_images(stats, args.per_tier, args.min_cells, args.seed)
    payload = {"seed": args.seed, "per_tier": args.per_tier, "min_cells": args.min_cells,
               "grid": SELECT_GRID, "table": SELECT_TABLE, "images": chosen}
    (RN_DIR / "selection.json").write_text(json.dumps(payload, indent=1))
    print(f"{len(stats)} ảnh, {sum(s['nonzero_cells'] >= args.min_cells for s in stats)} đủ điều kiện, chọn {len(chosen)}")


def cmd_build(args) -> None:
    selection = json.loads((RN_DIR / "selection.json").read_text())
    out_dir = tag_dir(f"g{args.grid}_{args.table}") / "instances"
    out_dir.mkdir(parents=True, exist_ok=True)
    for entry in selection["images"]:
        mask = load_mask(MASK_DIR / f"{entry['id']}_lab.png")
        instance = build_from_mask(mask, args.grid, args.table, args.k, args.routes_per_uav,
                                   args.max_cells, seed=int(entry["id"]))
        instance.update({"image_id": entry["id"], "tier": entry["tier"], "table": args.table})
        (out_dir / f"{entry['id']}.json").write_text(json.dumps(instance))
        print(f"[{entry['id']}] m={instance['m']} n={instance['n']} R={instance['reference_cost']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("select")
    s.add_argument("--per-tier", type=int, default=10)
    s.add_argument("--min-cells", type=int, default=60)
    s.add_argument("--seed", type=int, default=2026)
    s.set_defaults(func=cmd_select)
    b = sub.add_parser("build")
    b.add_argument("--grid", type=int, default=20)
    b.add_argument("--table", default="default", choices=sorted(SCORE_TABLES))
    b.add_argument("--k", type=int, default=4)
    b.add_argument("--routes-per-uav", type=int, default=300)
    b.add_argument("--max-cells", type=int, default=40)
    b.set_defaults(func=cmd_build)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Chạy test** — `python -m pytest tests/test_rn_prepare.py -q` → `1 passed`; rồi `python -m pytest -q` toàn bộ xanh.

- [ ] **Step 9: Chạy thật trên dữ liệu (thủ công, mất vài phút)**

```bash
python pipeline/07_rn_prepare.py select
python pipeline/07_rn_prepare.py build
```
Expected: `selection.json` chứa 30 ảnh (10/tầng); `data/rescuenet/g20_default/instances/` có 30 file. Xem in ra `m`, `n`, `R` của vài instance; nếu `n` quá lớn/nhỏ hoặc `R` bất thường (ví dụ 0), dừng và báo người dùng. Nếu số ảnh đủ điều kiện < 30 thì hạ `--min-cells` và ghi ngưỡng cuối vào spec mục 4.

- [ ] **Step 10: Commit (khi người dùng đồng ý)**, gồm `data/rescuenet/` (file nhỏ) nhưng **không** gồm `data/RescueNet/`.

---

### Task 5: ILP có trọng số + ngân sách từng UAV

**Files:**
- Create: `pipeline/08_ilp_uav.py`
- Modify: `tests/conftest.py` (alias `"pipeline.ilp_uav": "08_ilp_uav.py"`)
- Test: `tests/test_ilp_uav.py`

**Interfaces:**
- Consumes: `store.*`, `budgets_for_level`.
- Produces: `solve_uav_ilp(instance, budgets, time_limit) -> dict` với `status` (`"optimal"`/`"best-known"`), `objective` (float, tổng điểm rủi ro), `selected_packages` (list[int]). Kết quả ghi bằng `save_result(tag, "ilp", ...)` theo schema ở Task 7.

- [ ] **Step 1: Viết test (thất bại)**

```python
# tests/test_ilp_uav.py
from pipeline.ilp_uav import solve_uav_ilp

# 3 ô trọng số [5, 1, 1]. Route: j0 (UAV0, c3, ô0), j1 (UAV0, c2, ô1),
# j2 (UAV1, c2, ô1+ô2), j3 (UAV1, c1, ô2).
INSTANCE = {
    "n": 4, "m": 3, "weights": [5.0, 1.0, 1.0],
    "costs": [3, 2, 2, 1], "sets": [[0], [1], [1, 2], [2]],
    "route_uav": [0, 0, 1, 1],
}


def test_optimum_with_per_uav_budgets():
    res = solve_uav_ilp(INSTANCE, budgets=[3, 2], time_limit=30)
    assert res["status"] == "optimal"
    assert abs(res["objective"] - 7.0) < 1e-9
    assert sorted(res["selected_packages"]) == [0, 2]


def test_budget_is_per_uav_not_pooled():
    # Tổng 5 đủ cho j0 (3) + j2 (2), nhưng UAV0 chỉ có 2 nên j0 bị cấm.
    res = solve_uav_ilp(INSTANCE, budgets=[2, 3], time_limit=30)
    assert abs(res["objective"] - 2.0) < 1e-9


def test_uav_with_budget_below_every_route_selects_nothing():
    res = solve_uav_ilp(INSTANCE, budgets=[0, 0], time_limit=30)
    assert res["selected_packages"] == [] and res["objective"] == 0.0
```

- [ ] **Step 2: Thêm alias, chạy, xác nhận thất bại** (`FileNotFoundError` khi nạp alias hoặc import lỗi).

- [ ] **Step 3: Cài đặt**

```python
# pipeline/08_ilp_uav.py
"""ILP chính xác (PuLP/CBC) cho Budgeted Max Coverage có trọng số rủi ro và
ngân sách riêng từng UAV. Đáp án tham chiếu của Pha 2 (spec mục 6).

Chạy: python pipeline/08_ilp_uav.py [--tag g20_default] [--levels 100,75,50,25] [--time-limit 120]
"""

import argparse
import sys
import time
from pathlib import Path

import pulp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.rn.budgets import budgets_for_level
from pipeline.rn.store import list_instances, load_instance, save_result


def solve_uav_ilp(instance: dict, budgets: list, time_limit: int) -> dict:
    """max Σ w_i y_i  với  y_i ≤ Σ_{j phủ i} x_j  và  Σ_{j của UAV u} c_j x_j ≤ B_u.

    `y` để liên tục trong [0, 1]: vì trọng số ≥ 0 nên tối ưu tự đẩy y về 0/1.
    """
    n, m = instance["n"], instance["m"]
    costs, owner, weights = instance["costs"], instance["route_uav"], instance["weights"]
    covering = [[] for _ in range(m)]
    for j, cells in enumerate(instance["sets"]):
        for i in cells:
            covering[i].append(j)

    prob = pulp.LpProblem("uav_budgeted_coverage", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(n)]
    y = [pulp.LpVariable(f"y_{i}", lowBound=0, upBound=1) for i in range(m)]
    prob += pulp.lpSum(weights[i] * y[i] for i in range(m))
    for u, budget in enumerate(budgets):
        prob += pulp.lpSum(costs[j] * x[j] for j in range(n) if owner[j] == u) <= budget, f"budget_uav_{u}"
    for i, routes in enumerate(covering):
        prob += y[i] <= pulp.lpSum(x[j] for j in routes), f"link_{i}"

    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    selected = [j for j in range(n) if x[j].value() is not None and x[j].value() > 0.5]
    covered = {i for j in selected for i in instance["sets"][j]}
    return {
        "status": "optimal" if pulp.LpStatus[prob.status] == "Optimal" else "best-known",
        "objective": float(sum(weights[i] for i in covered)),
        "selected_packages": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="g20_default")
    parser.add_argument("--levels", default="100,75,50,25")
    parser.add_argument("--time-limit", type=int, default=120)
    args = parser.parse_args()
    levels = [int(x) for x in args.levels.split(",")]

    for name in list_instances(args.tag):
        instance = load_instance(args.tag, name)
        for level in levels:
            budgets = budgets_for_level(instance, level)
            start = time.time()
            res = solve_uav_ilp(instance, budgets, args.time_limit)
            elapsed = time.time() - start
            cells = {i for j in res["selected_packages"] for i in instance["sets"][j]}
            cost_per_uav = [sum(instance["costs"][j] for j in res["selected_packages"] if instance["route_uav"][j] == u)
                            for u in range(len(budgets))]
            save_result(args.tag, "ilp", name, level, {
                "instance": name, "algorithm": "ilp_uav", "mode": "budgeted_uav",
                "budget_level": level, "budget_values": budgets, "status": res["status"],
                "objective": res["objective"], "covered_cells": len(cells),
                "cost_per_uav": cost_per_uav, "selected_packages": res["selected_packages"],
                "solve_time_seconds": round(elapsed, 3), "time_limit_seconds": args.time_limit,
            })
            print(f"[{name}] ILP {level}% B={budgets} -> {res['objective']:.2f} ({res['status']}, {elapsed:.1f}s)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Chạy test** — `python -m pytest tests/test_ilp_uav.py -q` → `3 passed`.

- [ ] **Step 5: Chạy thật** — `python pipeline/08_ilp_uav.py`. Ghi lại thời gian lớn nhất và số `best-known` (nếu có) vào Nhật ký session. Nếu ILP quá chậm (> 2 phút/instance), giảm `--routes-per-uav` rồi build lại (báo người dùng).

- [ ] **Step 6: Commit (khi người dùng đồng ý).**

---

### Task 6: Greedy per-UAV: thuật toán đề xuất + baseline naive

**Files:**
- Create: `pipeline/09_greedy_uav.py`
- Modify: `tests/conftest.py` (alias `"pipeline.greedy_uav": "09_greedy_uav.py"`, đặt **sau** dòng `pipeline.greedy_ls`)
- Test: `tests/test_greedy_uav.py`

**Interfaces:**
- Consumes: `pipeline.greedy_ls` (`prepare`, `_weight`, `_ratio`, `_better`, `solve`), `budgets_for_level`.
- Produces:
  - `lazy_ratio_greedy_uav(prep, budgets, start=(), banned=()) -> (selected, covered_weight, cost)` (`prep` = `prepare(instance)` + khóa `route_uav`).
  - `solve_uav(instance, budgets, n_seeds=20, ls_rounds=50) -> dict` (thuật toán đề xuất).
  - `solve_naive_shared(instance, budgets, n_seeds=20, ls_rounds=50) -> dict` (greedy_ls với ngân sách chung `ΣB_u`, sau đó sửa bằng cách bỏ route tỉ lệ giá trị/chi phí thấp nhất của UAV vượt pin).
  - Cả hai trả dict: `selected_packages`, `covered_weight`, `covered_cells`, `cost_per_uav`, `cost`.

- [ ] **Step 1: Viết test (thất bại)**

```python
# tests/test_greedy_uav.py
import numpy as np

from pipeline.greedy_uav import lazy_ratio_greedy_uav, solve_naive_shared, solve_uav
from pipeline.greedy_ls import prepare
from pipeline.ilp_uav import solve_uav_ilp
from pipeline.rn.budgets import budgets_for_level, reference_cost
from pipeline.rn.routes import build_instance

TINY = {
    "n": 4, "m": 3, "weights": [5.0, 1.0, 1.0],
    "costs": [3, 2, 2, 1], "sets": [[0], [1], [1, 2], [2]],
    "route_uav": [0, 0, 1, 1],
}


def _prep(instance):
    return {**prepare(instance), "route_uav": instance["route_uav"]}


def test_greedy_skips_route_of_exhausted_uav_and_continues():
    inst = {"n": 3, "m": 4, "weights": [1.0] * 4, "costs": [2, 2, 1],
            "sets": [[0, 1], [2], [3]], "route_uav": [0, 0, 1]}
    selected, weight, cost = lazy_ratio_greedy_uav(_prep(inst), budgets=[2, 1])
    assert selected == [0, 2] and weight == 3.0 and cost == 3


def test_solve_uav_finds_optimum_on_tiny_instance():
    res = solve_uav(TINY, budgets=[3, 2])
    assert res["covered_weight"] == 7.0 and sorted(res["selected_packages"]) == [0, 2]


def test_uav_with_budget_below_every_route_gets_nothing():
    res = solve_uav(TINY, budgets=[0, 0])
    assert res["selected_packages"] == [] and res["covered_weight"] == 0.0


def test_naive_shared_result_respects_each_uav_budget_after_repair():
    # Ngân sách chung 5 cho phép j0 (UAV0, c3) + j2 (UAV1, c2); với [2, 3] thì j0 vi phạm.
    res = solve_naive_shared(TINY, budgets=[2, 3])
    assert all(c <= b for c, b in zip(res["cost_per_uav"], [2, 3]))


def test_heuristics_are_feasible_and_never_beat_ilp_on_generated_instance():
    risk = np.random.default_rng(0).random((6, 6)) + 0.05
    inst = build_instance(risk, k=2, routes_per_uav=30, max_cells=8, seed=3)
    inst["reference_cost"] = reference_cost(inst)
    budgets = budgets_for_level(inst, 50)
    optimum = solve_uav_ilp(inst, budgets, time_limit=60)["objective"]
    for solver in (solve_uav, solve_naive_shared):
        res = solver(inst, budgets)
        assert all(c <= b for c, b in zip(res["cost_per_uav"], budgets))
        assert res["covered_weight"] <= optimum + 1e-6
```

- [ ] **Step 2: Thêm alias, chạy, xác nhận thất bại.**

- [ ] **Step 3: Cài đặt**

```python
# pipeline/09_greedy_uav.py
"""Greedy cho Budgeted Max Coverage có trọng số rủi ro và ngân sách riêng từng UAV.

- `proposed`: lazy ratio greedy + gói đơn tốt nhất + seed + drop-and-refill,
  mọi bước kiểm tra pin của UAV sở hữu route (phát triển từ 06_greedy_ls.py).
- `naive`: greedy_ls với ngân sách chung ΣB_u rồi sửa lời giải cho hợp lệ.

Chạy: python pipeline/09_greedy_uav.py --algorithm proposed [--tag g20_default]
      [--levels 100,75,50,25] [--seeds 20] [--ls-rounds 50] [--name proposed]
"""

import argparse
import heapq
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.greedy_ls import _better, _ratio, _weight, prepare, solve as solve_shared_budget
from pipeline.rn.budgets import budgets_for_level
from pipeline.rn.store import list_instances, load_instance, save_result


def lazy_ratio_greedy_uav(prep: dict, budgets: list, start=(), banned=()) -> tuple:
    """Như `lazy_ratio_greedy` của 06, nhưng route j chỉ chọn được khi còn đủ pin của UAV sở hữu nó."""
    costs, masks, weights, owner = prep["costs"], prep["masks"], prep["weights"], prep["route_uav"]
    remaining = list(budgets)
    selected = list(start)
    covered = 0
    for j in selected:
        covered |= masks[j]
        remaining[owner[j]] -= costs[j]

    excluded = set(selected) | set(banned)
    heap = []
    for j in range(prep["n"]):
        if j in excluded or costs[j] > remaining[owner[j]]:
            continue
        gain = _weight(masks[j] & ~covered, weights)
        if gain > 0:
            heap.append((-_ratio(gain, costs[j]), j, 0))
    heapq.heapify(heap)

    round_no = 0
    while heap:
        _, j, evaluated_at = heapq.heappop(heap)
        if costs[j] > remaining[owner[j]]:
            continue  # pin của UAV này chỉ giảm dần nên route sẽ không bao giờ vừa nữa
        if evaluated_at != round_no:
            gain = _weight(masks[j] & ~covered, weights)
            if gain > 0:
                heapq.heappush(heap, (-_ratio(gain, costs[j]), j, round_no))
            continue
        selected.append(j)
        covered |= masks[j]
        remaining[owner[j]] -= costs[j]
        round_no += 1

    return selected, _weight(covered, weights), sum(costs[j] for j in selected)


def _drop_and_refill(prep: dict, budgets: list, solution: tuple, max_rounds: int) -> tuple:
    best = solution
    for _ in range(max_rounds):
        improved = False
        for i in best[0]:
            kept = [j for j in best[0] if j != i]
            candidate = lazy_ratio_greedy_uav(prep, budgets, start=kept, banned=(i,))
            if _better(candidate, best):
                best, improved = candidate, True
                break
        if not improved:
            break
    return best


def _describe(instance: dict, prep: dict, selected: list, k: int) -> dict:
    covered = 0
    for j in selected:
        covered |= prep["masks"][j]
    cost_per_uav = [0] * k
    for j in selected:
        cost_per_uav[instance["route_uav"][j]] += instance["costs"][j]
    return {
        "selected_packages": list(selected),
        "covered_weight": float(_weight(covered, instance["weights"])),
        "covered_cells": int(_weight(covered, None)),
        "cost_per_uav": cost_per_uav,
        "cost": sum(cost_per_uav),
    }


def solve_uav(instance: dict, budgets: list, n_seeds: int = 20, ls_rounds: int = 50) -> dict:
    prep = {**prepare(instance), "route_uav": instance["route_uav"]}
    costs, masks, weights, owner = prep["costs"], prep["masks"], prep["weights"], prep["route_uav"]
    affordable = [j for j in range(prep["n"]) if costs[j] <= budgets[owner[j]]]
    single_gain = {j: _weight(masks[j], weights) for j in affordable}

    best = lazy_ratio_greedy_uav(prep, budgets)
    if affordable:
        top = max(affordable, key=lambda j: (single_gain[j], -costs[j], -j))
        single = ([top], single_gain[top], costs[top])
        if _better(single, best):
            best = single

    seeds = set()
    if n_seeds > 0:
        by_gain = sorted(affordable, key=lambda j: (-single_gain[j], costs[j], j))
        by_ratio = sorted(affordable, key=lambda j: (-_ratio(single_gain[j], costs[j]), j))
        seeds.update(by_gain[:n_seeds])
        seeds.update(by_ratio[:n_seeds])
    for j in sorted(seeds):
        candidate = lazy_ratio_greedy_uav(prep, budgets, start=[j])
        if _better(candidate, best):
            best = candidate

    if ls_rounds > 0 and best[0]:
        best = _drop_and_refill(prep, budgets, best, ls_rounds)
    return _describe(instance, prep, best[0], len(budgets))


def solve_naive_shared(instance: dict, budgets: list, n_seeds: int = 20, ls_rounds: int = 50) -> dict:
    """Baseline: bỏ qua ranh giới UAV khi chọn (ngân sách chung), rồi sửa cho hợp lệ."""
    prep = {**prepare(instance), "route_uav": instance["route_uav"]}
    pooled = solve_shared_budget(instance, sum(budgets), n_seeds=n_seeds, ls_rounds=ls_rounds)
    selected = list(pooled["selected_packages"])
    costs, owner, weights = instance["costs"], instance["route_uav"], instance["weights"]
    for u, budget in enumerate(budgets):
        mine = [j for j in selected if owner[j] == u]
        mine.sort(key=lambda j: (_weight(prep["masks"][j], weights) / costs[j], -j))  # tỉ lệ thấp nhất bị bỏ trước
        while sum(costs[j] for j in mine) > budget:
            drop = mine.pop(0)
            selected.remove(drop)
    return _describe(instance, prep, selected, len(budgets))


ALGORITHMS = {"proposed": solve_uav, "naive": solve_naive_shared}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", choices=sorted(ALGORITHMS), default="proposed")
    parser.add_argument("--name", default=None, help="Tên thư mục kết quả (mặc định = tên thuật toán); dùng cho ablation.")
    parser.add_argument("--tag", default="g20_default")
    parser.add_argument("--levels", default="100,75,50,25")
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--ls-rounds", type=int, default=50)
    args = parser.parse_args()
    name_out = args.name or args.algorithm
    levels = [int(x) for x in args.levels.split(",")]
    solver = ALGORITHMS[args.algorithm]

    for name in list_instances(args.tag):
        instance = load_instance(args.tag, name)
        for level in levels:
            budgets = budgets_for_level(instance, level)
            start = time.time()
            res = solver(instance, budgets, n_seeds=args.seeds, ls_rounds=args.ls_rounds)
            elapsed = time.time() - start
            save_result(args.tag, name_out, name, level, {
                "instance": name, "algorithm": name_out, "mode": "budgeted_uav",
                "budget_level": level, "budget_values": budgets, "status": "heuristic",
                "objective": res["covered_weight"], "covered_cells": res["covered_cells"],
                "cost_per_uav": res["cost_per_uav"], "selected_packages": res["selected_packages"],
                "solve_time_seconds": round(elapsed, 3),
                "params": {"seeds": args.seeds, "ls_rounds": args.ls_rounds},
            })
            print(f"[{name}] {name_out} {level}% -> {res['covered_weight']:.2f} ({elapsed:.2f}s)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Chạy test** — `python -m pytest tests/test_greedy_uav.py -q` → `5 passed`. Nếu `test_naive_shared...` hoặc test seed 3 thất bại, **sửa code, không nới điều kiện test** (đây là bất biến: hợp lệ + không vượt ILP).

- [ ] **Step 5: Chạy thật** — `python pipeline/09_greedy_uav.py --algorithm proposed` và `python pipeline/09_greedy_uav.py --algorithm naive`.

- [ ] **Step 6: Commit (khi người dùng đồng ý).**

---

### Task 7: Validator per-UAV

**Files:**
- Create: `pipeline/10_validate_uav.py`
- Modify: `tests/conftest.py` (alias `"pipeline.validate_uav": "10_validate_uav.py"`)
- Test: `tests/test_validate_uav.py`

**Interfaces:**
- Consumes: `budgets_for_level`, `store.*`.
- Produces: `validate_uav_result(instance, result) -> list[str]` (rỗng nếu hợp lệ). Schema kết quả (bắt buộc): `instance, algorithm, mode="budgeted_uav", budget_level (int), budget_values (list[int]), status, objective (float = tổng rủi ro), covered_cells, cost_per_uav, selected_packages, solve_time_seconds`.

- [ ] **Step 1: Viết test (thất bại)**

```python
# tests/test_validate_uav.py
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
```

- [ ] **Step 2: Thêm alias, chạy, xác nhận thất bại.**

- [ ] **Step 3: Cài đặt**

```python
# pipeline/10_validate_uav.py
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

    problems, checked, ilp_best = [], 0, {}
    results = []
    for path in sorted((tag_dir(args.tag) / "results").glob("*/*.json")):
        result = json.loads(path.read_text())
        results.append((path, result))
        if result["algorithm"] == "ilp_uav" and result["status"] == "optimal":
            ilp_best[(result["instance"], result["budget_level"])] = result["objective"]
    instances = {name: load_instance(args.tag, name) for name in list_instances(args.tag)}

    for path, result in results:
        checked += 1
        tag = f"{path.parent.name}/{path.name}"
        for error in validate_uav_result(instances[result["instance"]], result):
            problems.append(f"{tag}: {error}")
        best = ilp_best.get((result["instance"], result["budget_level"]))
        if best is not None and result["objective"] > best + TOL:
            problems.append(f"{tag}: objective {result['objective']} VƯỢT tối ưu ILP {best}")

    print(f"đã kiểm tra {checked} file kết quả, {len(problems)} lỗi")
    for line in problems[:30]:
        print(" -", line)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Chạy test** — `python -m pytest tests/test_validate_uav.py -q` → `5 passed`.

- [ ] **Step 5: Chạy thật** — `python pipeline/10_validate_uav.py`. Expected: `0 lỗi`. Có lỗi thì **dừng và điều tra** (dùng `superpowers:systematic-debugging`), không sửa heuristic cho khớp ILP.

- [ ] **Step 6: Commit (khi người dùng đồng ý).**

---

### Task 8: Tổng hợp, Wilcoxon, CSV

**Files:**
- Create: `pipeline/11_summarize_rn.py`
- Modify: `tests/conftest.py` (alias `"pipeline.summarize_rn": "11_summarize_rn.py"`)
- Test: `tests/test_summarize_rn.py`

**Interfaces:**
- Consumes: file kết quả (schema Task 7).
- Produces: `ratios_to_ilp(records) -> dict[(algorithm, level) -> list[float]]` (tỉ lệ `objective / ILP optimum` theo instance, sắp theo tên instance; bỏ instance thiếu ILP hoặc ILP = 0); `paired_wilcoxon(a, b) -> float` (p-value hai phía; trả `1.0` nếu mọi hiệu bằng 0). Ghi `data/rescuenet/<tag>/summary.csv` với cột: `instance, algorithm, budget_level, seed, covered_cells, covered_weight, cost, time_seconds` (`seed` = `-` cho thuật toán deterministic).

- [ ] **Step 1: Viết test (thất bại)**

```python
# tests/test_summarize_rn.py
from pipeline.summarize_rn import paired_wilcoxon, ratios_to_ilp


def rec(instance, algorithm, level, objective):
    return {"instance": instance, "algorithm": algorithm, "budget_level": level, "objective": objective}


def test_ratios_to_ilp_pairs_by_instance_and_skips_missing_ilp():
    records = [rec("a", "ilp_uav", 50, 10.0), rec("b", "ilp_uav", 50, 20.0),
               rec("a", "proposed", 50, 9.0), rec("b", "proposed", 50, 20.0),
               rec("c", "proposed", 50, 5.0)]
    assert ratios_to_ilp(records)[("proposed", 50)] == [0.9, 1.0]


def test_ratios_skip_zero_optimum():
    records = [rec("a", "ilp_uav", 25, 0.0), rec("a", "proposed", 25, 0.0)]
    assert ratios_to_ilp(records).get(("proposed", 25), []) == []


def test_wilcoxon_identical_samples_gives_p_one():
    assert paired_wilcoxon([0.9, 0.8, 1.0], [0.9, 0.8, 1.0]) == 1.0


def test_wilcoxon_consistent_improvement_gives_small_p():
    a = [0.99 - 0.001 * i for i in range(12)]
    b = [x - 0.05 - 0.001 * i for i, x in enumerate(a)]
    assert paired_wilcoxon(a, b) < 0.01
```

- [ ] **Step 2: Thêm alias, chạy, xác nhận thất bại.**

- [ ] **Step 3: Cài đặt**

```python
# pipeline/11_summarize_rn.py
"""Tổng hợp kết quả Pha 2: gap so với ILP, kiểm định Wilcoxon cặp, xuất summary.csv.

Chạy: python pipeline/11_summarize_rn.py [--tag g20_default]
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


def ratios_to_ilp(records: list) -> dict:
    ilp = {(r["instance"], r["budget_level"]): r["objective"] for r in records if r["algorithm"] == "ilp_uav"}
    out = {}
    for r in sorted(records, key=lambda r: r["instance"]):
        if r["algorithm"] == "ilp_uav":
            continue
        best = ilp.get((r["instance"], r["budget_level"]))
        if not best:  # thiếu ILP hoặc tối ưu = 0 (instance tầm thường)
            continue
        out.setdefault((r["algorithm"], r["budget_level"]), []).append(r["objective"] / best)
    return out


def paired_wilcoxon(a: list, b: list) -> float:
    if all(x == y for x, y in zip(a, b)):
        return 1.0
    return float(wilcoxon(a, b).pvalue)


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

    ratios = ratios_to_ilp(records)
    print("\nalgorithm | level | n | mean | min | (tỉ lệ objective / ILP)")
    for (algorithm, level), values in sorted(ratios.items()):
        print(f"{algorithm} | {level}% | {len(values)} | {statistics.mean(values):.4f} | {min(values):.4f}")
    for level in sorted({lv for _, lv in ratios}):
        a, b = ratios.get(("proposed", level)), ratios.get(("naive", level))
        if a and b and len(a) == len(b) and len(a) >= 2:
            print(f"Wilcoxon proposed vs naive @{level}%: p = {paired_wilcoxon(a, b):.4g} (n={len(a)})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Chạy test** — `python -m pytest tests/test_summarize_rn.py -q` → `4 passed`; rồi `python -m pytest -q` toàn bộ xanh.

- [ ] **Step 5: Chạy thật** — `python pipeline/11_summarize_rn.py`. Dán bảng in ra vào Nhật ký session (ngày + số).

  Lưu ý: Wilcoxon cặp ở đây ghép theo instance (mỗi instance một cặp), vì cả hai thuật toán đều deterministic. Báo cáo phải nói rõ n = số instance, không phải số seed.

- [ ] **Step 6: Commit (khi người dùng đồng ý).**

---

### Task 9: Sensitivity, ablation, cập nhật docs

**Files:**
- Modify: `docs/huong-dan-chay.md` (thêm mục Pha 2: các bước 07–11, input/output)
- Modify: `docs/mo-hinh-du-lieu.md` (thêm định dạng instance Pha 2)
- Create: `docs/phase2-ket-qua.md` (bảng số liệu **dán từ output script**, kèm lệnh tái lập)
- Modify: `docs/phase2-rescuenet-thiet-ke.md` (ghi ngưỡng `min_cells` cuối cùng nếu đã đổi; đổi trạng thái "BẢN NHÁP" khi người dùng duyệt chính thức)

- [ ] **Step 1: Ablation** (trên tag mặc định)

```bash
python pipeline/09_greedy_uav.py --algorithm proposed --name abl_ratio_only --seeds 0 --ls-rounds 0
python pipeline/09_greedy_uav.py --algorithm proposed --name abl_no_ls --ls-rounds 0
python pipeline/09_greedy_uav.py --algorithm proposed --name abl_no_seed --seeds 0
python pipeline/11_summarize_rn.py
python pipeline/10_validate_uav.py
```
Expected: validator 0 lỗi. `11` thêm hàng cho `abl_*` (ratio dùng chung `ratios_to_ilp`).

- [ ] **Step 2: Sensitivity bảng điểm** (cùng 30 ảnh, tag khác)

```bash
for t in tree1 convex damage_only; do
  python pipeline/07_rn_prepare.py build --table $t
  python pipeline/08_ilp_uav.py --tag g20_$t
  python pipeline/09_greedy_uav.py --algorithm proposed --tag g20_$t
  python pipeline/09_greedy_uav.py --algorithm naive --tag g20_$t
  python pipeline/10_validate_uav.py --tag g20_$t
  python pipeline/11_summarize_rn.py --tag g20_$t
done
```
Lưu ý `damage_only` có thể sinh instance rất nhỏ hoặc `build_instance` báo `ValueError` cho ảnh không có ô điểm > 0. Khi đó **không sửa script lặng lẽ**: ghi số ảnh bị loại vào `docs/phase2-ket-qua.md` và báo người dùng.

- [ ] **Step 3: Sensitivity lưới**

```bash
python pipeline/07_rn_prepare.py build --grid 10
python pipeline/08_ilp_uav.py --tag g10_default
python pipeline/09_greedy_uav.py --algorithm proposed --tag g10_default
python pipeline/09_greedy_uav.py --algorithm naive --tag g10_default
python pipeline/10_validate_uav.py --tag g10_default
python pipeline/11_summarize_rn.py --tag g10_default
```
Lưới 40 chỉ làm trên vài instance nếu ILP kịp; không bắt buộc.

- [ ] **Step 4: Viết `docs/phase2-ket-qua.md`** với: lệnh tái lập, bảng gap (mean/min) theo thuật toán × mức ngân sách, p-value Wilcoxon, bảng ablation, bảng sensitivity (so sánh xếp hạng giữa các tag), **và nhận xét trung thực**, kể cả khi gap nhỏ hoặc naive ngang đề xuất. Mọi số lấy nguyên từ output script. Không viết số bằng tay.

- [ ] **Step 5: Cập nhật `docs/huong-dan-chay.md` và `docs/mo-hinh-du-lieu.md`** (mô tả file, lệnh, schema JSON instance/kết quả đúng như đã cài đặt).

- [ ] **Step 6: Chạy toàn bộ kiểm tra lần cuối**

```bash
python -m pytest -q
python pipeline/10_validate_uav.py
python audit_results.py        # Pha 1 không bị ảnh hưởng: vẫn 0 lỗi
git status                       # data/RescueNet/ không xuất hiện
```

- [ ] **Step 7: Cập nhật bảng Tiến độ + Nhật ký session; commit/PR (khi người dùng đồng ý).**

---

## Self-Review

**Spec coverage:** mục 2 (lưới 20, sensitivity 10/40) → Task 4, 9; mục 3 (bảng điểm, 3 bảng thay thế) → Task 1, 9; mục 4 (chọn ảnh, seed, lọc, phân tầng) → Task 2, 4; mục 5 (K UAV, route, nhiều route/UAV, ngân sách %, mục tiêu rủi ro) → Task 3, 4, 5; mục 6 (ILP, naive, đề xuất) → Task 5, 6; mục 7 (gitignore, plan, TDD, kiểm tra cận) → Task 0 và ghi chú. **Gap đã biết:** việc "mở bài gốc kiểm tra cận xấp xỉ nhiều knapsack" là việc đọc tài liệu, không phải code; phải làm trước khi viết Related Work (người dùng tự làm hoặc yêu cầu riêng). Mẫu "30 ảnh khác seed khác" trong spec mục 4: chạy lại `select --seed X` rồi `build`, chưa có task riêng; thêm nếu còn thời gian sau 10/10.

**Placeholder scan:** không có TBD/TODO; mọi bước code có code.

**Type consistency:** `build_instance` khóa `route_uav/uav_share/reference_cost/weights/costs/sets` được `budgets.py`, `08`, `09`, `10` dùng đúng tên; `budgets_for_level(instance, level)` trả `list[int]` khớp `budget_values`; `objective` = tổng rủi ro ở mọi kết quả; `algorithm` của ILP = `"ilp_uav"` khớp `10` và `11`; kết quả naive/proposed dùng `name_out` làm `algorithm` (nên `proposed`/`naive`/`abl_*` khớp `11`).

**Review Focus:** 6 mục đều có test: (1) Task 1 `crops_remainder`; (2) Task 3 `all_zero_risk_raises` + Task 2 filter; (3) Task 3 `duplicate_cover_keeps_cheapest`; (4) Task 4 `ignores_cells_no_route_can_cover`; (5) Task 5 `budget_below_every_route`, Task 6 `budget_below_every_route`; (6) Task 7 `flags_uav_over_own_budget`.
- 07/10/2026: xong Task 5 (`pipeline/08_ilp_uav.py`, 4 test, tổng 53 test xanh), chưa commit. Đã commit Task 4 (01c978a). **Lỗi bắt được:** `LpStatus` của PuLP vẫn báo "Optimal" khi CBC hết giờ; nhãn phải dựa vào `prob.sol_status == LpSolutionOptimal` (hàm `status_label`, có test). Kết quả ILP (120 lần, 30 instance × 4 mức), time limit 120s rồi chạy lại 23 ca best-known với 600s: 100 optimal, 20 best-known còn lại (mức 50%: 5, 75%: 8, 100%: 7; mức 25%: 30/30 optimal). 20 ca best-known tập trung ở instance lớn (11702, 11714, 12078, 12221, 12437, 13085, 13629, 14935). Tăng 5x thời gian chỉ giải thêm 3 ca. Báo cáo: gap ở các ca này là so với best-known, không phải tối ưu tuyệt đối; tỉ lệ heuristic/ILP có thể > 1. Task kế tiếp: Task 6 (greedy per-UAV `09`).
- 07/10/2026: quyết định giữ nguyên ILP hiện tại (không chạy lại), ghi nhận best-known trong spec; đã commit Task 5 (ee591e2). Xong Task 6 (`pipeline/09_greedy_uav.py`, 5 test, tổng 58 test xanh), chưa commit. `09` nạp `06_greedy_ls.py` bằng importlib (chạy trực tiếp được). Chạy thật 30 instance × 4 mức: proposed 4.6s, naive 6.9s tổng. Xem nhanh (chưa phải bảng chính thức, chưa qua validator) tỉ lệ objective/ILP: **proposed** trung bình 0.969–0.987 (min 0.890) ở mọi mức; **naive** rất thấp ở mức thấp (mean 0.15 ở 25%, 0.43 ở 50%, 0.64 ở 75%, 0.71 ở 100% với nhóm optimal). **Cảnh báo công bằng baseline:** `naive` chỉ bỏ route vi phạm mà KHÔNG lấp lại pin còn dư, nên gap lớn một phần do sửa lỗi thô; trước khi đưa vào báo cáo cần quyết định có thêm bước refill (xem Task 6 mở rộng bên dưới). Task kế tiếp: Task 7 (validator `10`).
- 07/10/2026: theo lựa chọn của người dùng, `naive` được sửa để **lấp lại pin còn dư** sau khi bỏ route vi phạm (thêm test `test_naive_refills_leftover_budget_after_repair`, tổng 59 test xanh); chạy lại `naive`. Xem nhanh tỉ lệ objective/ILP (chưa qua validator): proposed mean 0.969–0.987 (min 0.890); naive (có refill) mean 0.898–0.938 (min 0.718), nghĩa là chênh khoảng 5–8 điểm phần trăm thay vì chênh lớn như bản trước. So cặp theo instance: proposed > naive ở 19/25/29/28 trên 30 instance (mức 25/50/75/100%), bằng nhau 11/3/1/0, **proposed < naive ở 0/2/0/2** (không thống trị tuyệt đối). Không có ca nào vượt ILP. Task kế tiếp: Task 7 (validator `10`).
- 07/10/2026: đã commit Task 6 (68998e5). Xong Task 7 (`pipeline/10_validate_uav.py`, 5 test, tổng 64 test xanh), chưa commit. Chạy thật: 360 file kết quả (ilp, proposed, naive) → **0 lỗi**, không heuristic nào vượt ILP `optimal`. Đã thử cố ý làm hỏng một kết quả thật (thêm route vượt pin UAV 0; khai báo objective sai) và validator bắt được cả hai. Task kế tiếp: Task 8 (`11_summarize_rn.py`: bảng gap, Wilcoxon, CSV).
