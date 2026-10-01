# Hướng dẫn chạy: thứ tự, input, output

Mọi lệnh chạy **từ thư mục gốc của repo**. Các script trong `pipeline/` được đánh số theo thứ tự chạy; output của bước trước là input của bước sau.

```
01 download → 02 convert → 03 ILP ─┐
                          ├ 04 greedy ─┤
                          └ 06 greedy_ls ┴→ 05 validate
```

Cài đặt một lần:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt        # pytest + PuLP
```

Dữ liệu raw, processed và kết quả đều đã có sẵn trong repo, nên chỉ cần chạy lại khi muốn tái lập từ đầu.

## Tổng quan

| Bước | Script | Input | Output |
|---|---|---|---|
| 01 | `pipeline/01_download_orlib.py` | Internet (OR-Library) | `data/raw/OR-Library/*.txt` (45 file) |
| 02 | `pipeline/02_convert_to_input.py` | `data/raw/OR-Library/*.txt` | `data/processed/*.json` (45 file) |
| 03 | `pipeline/03_solve_ilp.py` | `data/processed/*.json` | `data/results/ilp/*.json` (180 file) |
| 04 | `pipeline/04_greedy_pure.py` | `data/processed/*.json` | `data/results/greedy/*.json` (135 file) |
| 06 | `pipeline/06_greedy_ls.py` | `data/processed/*.json` | `data/results/greedy_ls/*.json` (135 file) |
| 05 | `pipeline/05_validate_solution.py` | `data/processed/` + `data/results/**` | báo cáo trên terminal, mã thoát 0/1 |

`pipeline/opt_reference.py` là bảng OPT dùng chung (giá trị tối ưu set cover của 45 instance), do các bước 03, 04, 05 import. Không chạy trực tiếp.

Bước 03 và 04 độc lập với nhau, chạy thứ tự nào cũng được, nhưng cả hai phải chạy sau 02.

## Bước 01: tải dữ liệu

```bash
python pipeline/01_download_orlib.py
```

- **Input:** không có (tải từ OR-Library qua HTTP). File đã tồn tại thì bỏ qua (`[skip]`).
- **Output:** 45 file `.txt` trong `data/raw/OR-Library/` (bộ 4, 5, 6, A–D), ví dụ `scp41.txt`.
- **Ý nghĩa:** file gốc của bài toán Set Covering, theo chiều ô→gói, đánh chỉ số từ 1. Chưa dùng trực tiếp được.

## Bước 02: chuyển đổi

```bash
python pipeline/02_convert_to_input.py
```

- **Input:** `data/raw/OR-Library/*.txt`.
- **Output:** `data/processed/<instance>.json`, ví dụ `scp41.json`.
- **Ý nghĩa các trường:**

| Trường | Ý nghĩa |
|---|---|
| `instance` | tên instance |
| `m` | số ô cần phủ (universe), ví dụ scp41: 200 |
| `n` | số gói, ví dụ scp41: 1000 |
| `costs` | `costs[j]` = chi phí của gói `j` |
| `sets` | `sets[j]` = danh sách ô mà gói `j` phủ |

Tất cả chỉ số đã chuyển về **0-indexed** và theo chiều gói→ô. Giải thích chi tiết: `docs/mo-hinh-du-lieu.md`.

## Bước 03: ILP chính xác

```bash
python pipeline/03_solve_ilp.py --time-limit 600                     # cả 45 instance
python pipeline/03_solve_ilp.py --instances scpa1,scp61 --modes budgeted --time-limit 120
```

Tham số: `--instances` (mặc định tất cả), `--modes setcover,budgeted`, `--time-limit` giây (mặc định 120), `--budget-levels` (mặc định `75,50,25`).

- **Input:** `data/processed/*.json`, bảng OPT trong `opt_reference.py`.
- **Output:** `data/results/ilp/<instance>_setcover.json` và `<instance>_budgeted_<75|50|25>.json`, mỗi instance 4 file.
- **Hai chế độ:**
  - `setcover`: phủ toàn bộ ô với chi phí tối thiểu. Kết quả phải khớp bảng OPT, dùng để xác nhận dữ liệu đúng.
  - `budgeted`: tối đa số ô phủ với ngân sách `B = floor(mức% × OPT)`. Đây là đáp án tối ưu để so sánh với heuristic.
- **Các trường:**

| Trường | Ý nghĩa |
|---|---|
| `mode` | `setcover` hoặc `budgeted` |
| `budget_level`, `budget_value` | mức ngân sách (`"50%"`) và giá trị `B` thực tế; `null` ở chế độ setcover |
| `status` | `optimal` nếu solver chứng minh tối ưu; trạng thái khác nghĩa là hết time limit hoặc không giải được |
| `objective` | setcover: tổng chi phí tối thiểu; budgeted: số ô phủ tối đa |
| `selected_packages` | các gói được chọn (0-indexed) |
| `solve_time_seconds`, `time_limit_seconds` | thời gian giải thực tế và giới hạn đã đặt |

Thiết kế và công thức: `docs/ilp-solver-thiet-ke.md`.

## Bước 04: greedy thuần (baseline)

```bash
python pipeline/04_greedy_pure.py                                       # 45 instance x 75/50/25%
python pipeline/04_greedy_pure.py --instances scpa1,scp61 --budget-levels 75,50,25
```

- **Input:** `data/processed/*.json`, bảng OPT (để tính `B`).
- **Output:** `data/results/greedy/<instance>_budgeted_<75|50|25>.json`. Mức 100% không cần chạy vì luôn phủ 100%.
- **Thuật toán:** mỗi bước chọn gói phủ nhiều ô mới nhất trong số gói còn vừa ngân sách, không xét chi phí. Deterministic nên chạy một lần, không cần nhiều seed.
- **Các trường:** giống ILP, thêm `algorithm` (`"greedy_pure"`) và `cost` (tổng chi phí thực tế, luôn ≤ `budget_value`). `status` luôn là `"greedy"` vì đây là heuristic, không có khái niệm tối ưu. `selected_packages` theo đúng thứ tự chọn.

Thiết kế và kết quả so với ILP: `docs/greedy-thuan-thiet-ke.md`.

## Bước 06: Seeded Lazy Ratio Greedy + Local Search

```bash
python pipeline/06_greedy_ls.py                                         # 45 instance x 75/50/25%
python pipeline/06_greedy_ls.py --instances scpa1 --seeds 100 --ls-rounds 50
```

- **Input:** `data/processed/*.json` (có thể có thêm trường `weights` cho trọng số rủi ro), bảng OPT.
- **Output:** `data/results/greedy_ls/<instance>_budgeted_<75|50|25>.json`. Các trường giống greedy thuần, thêm `covered_weight` và `params`; `status` là `"heuristic"`.
- **Thuật toán:** greedy theo tỉ lệ ô mới/chi phí, kết hợp gói đơn tốt nhất, khởi tạo từ nhiều gói seed, rồi local search drop-and-refill. Deterministic.

Thiết kế, cận xấp xỉ và kết quả: `docs/greedy-ls-thiet-ke.md`.

## Bước 05: kiểm tra kết quả

```bash
python pipeline/05_validate_solution.py                                  # quét đệ quy data/results/
python pipeline/05_validate_solution.py --results-dir data/results/greedy
```

- **Input:** các file kết quả và `data/processed/`.
- **Output:** danh sách lỗi (nếu có) và dòng tổng kết, ví dụ `Đã kiểm tra 315 file, 0 file có lỗi.` Thoát mã 1 nếu có lỗi.
- **Cách hoạt động:** bỏ qua số liệu thuật toán tự báo, tự tính lại chi phí và số ô phủ từ `selected_packages`. Báo lỗi khi: chi phí vượt `B`; `budget_value` khác `floor(mức% × OPT)`; `objective`/`cost` khai báo lệch số tính lại; gói ngoài phạm vi hoặc trùng; phủ 100% ô khi `B < OPT` (Hệ quả 1).
- Chạy validator trước khi nộp hoặc báo cáo kết quả của **bất kỳ** thuật toán nào.

## Chạy test

```bash
python -m pytest tests/
```

## Cách đọc kết quả

Đọc `objective` của greedy chia cho `objective` của ILP cùng instance và cùng mức ngân sách, để ra tỉ lệ độ phủ so với tối ưu (số liệu tổng hợp ở `docs/greedy-thuan-thiet-ke.md` mục 9). Với mức ngân sách nhỏ hơn 100% OPT, độ phủ chưa bao giờ đạt 100%.

## Thêm thuật toán mới

1. Đặt code trong `pipeline/` (đánh số tiếp theo, ví dụ `07_...py`) hoặc `proposed-algorithm/`, đọc instance từ `data/processed/<tên>.json`.
2. Dùng `pipeline/opt_reference.py` để tính `B = floor(mức% × OPT)`.
3. Ghi kết quả JSON cùng format vào `data/results/<tên thuật toán>/`, với các trường `instance, algorithm, mode, budget_level, budget_value, status, objective, cost, selected_packages, solve_time_seconds`. Nếu có yếu tố ngẫu nhiên, chạy 20–30 seed và ghi thêm `seed`.
4. Viết test trước (TDD), rồi chạy bước 05 để chắc kết quả hợp lệ. Không chỉnh heuristic cho khớp đáp án ILP.
