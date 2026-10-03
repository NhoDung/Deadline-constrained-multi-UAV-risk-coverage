# Thiết kế: LP Relaxation + Randomized Rounding (`lp_rounding`)

> Script: `pipeline/07_lp_rounding.py`. Thuật toán heuristic dùng chung cho OR-Library (mọi ô trọng số 1) và instance RescueNet (trường `weights`). Đáp án chính xác để so sánh lấy từ ILP (`pipeline/03_solve_ilp.py`).

## 1. Bài toán

Giống `docs/greedy-ls-thiet-ke.md` mục 1: Budgeted Maximum Coverage có trọng số. Có `m` ô (ô `i` có trọng số `w_i`) và `n` gói (gói `j` có chi phí `c_j` và phủ tập ô `S_j`). Cần chọn tập gói `X` với `Σ_{j∈X} c_j ≤ B` sao cho tổng trọng số ô được phủ là lớn nhất.

Mô hình ILP (giống `03_solve_ilp.py`):

```
max   Σ_i w_i · y_i
s.t.  Σ_j c_j · x_j ≤ B
      y_i ≤ Σ_{j : i ∈ S_j} x_j      với mọi ô i
      x_j, y_i ∈ {0, 1}
```

## 2. Ý tưởng

Thay ràng buộc `x_j, y_i ∈ {0, 1}` bằng `0 ≤ x_j, y_i ≤ 1` để được bài toán **quy hoạch tuyến tính (LP)**. LP giải được trong thời gian đa thức. Nghiệm phân số `x*` cho biết mức độ "nên chọn" từng gói, và giá trị LP là **cận trên** của OPT.

Thuật toán này thuộc họ khác với greedy và local search của `greedy_ls` (`06`): nó dựa trên **lời giải tối ưu toàn cục của bài toán nới lỏng**, thay vì xây lời giải từng bước theo tiêu chí cục bộ.

## 3. Thuật toán

1. **Giải LP một lần** cho mỗi cặp (instance, ngân sách) bằng PuLP/CBC, thu được `x*` và `lp_bound`. Tất cả seed dùng chung nghiệm LP này.
2. **Làm tròn tất định:** giữ các gói có `x*_j = 1`, rồi sửa và lấp (bước 4).
3. **Làm tròn ngẫu nhiên** `samples` lần (mặc định 200). Mỗi lần chọn gói `j` độc lập với xác suất `x*_j`, rồi sửa và lấp (bước 4). Giữ lời giải tốt nhất: phủ nhiều trọng số hơn, hoặc phủ bằng nhưng rẻ hơn.
4. **Sửa và lấp (`repair_and_fill`):**
   - **Sửa:** khi tập gói vượt ngân sách, bỏ dần gói có tỉ lệ `trọng số chỉ mình nó phủ / chi phí` nhỏ nhất. Hòa thì bỏ gói đắt hơn trước.
   - **Lấp:** dùng phần ngân sách còn dư để chạy ratio greedy (CELF) bắt đầu từ các gói còn lại. Hàm này lấy lại từ `06_greedy_ls.py`, nên cách tính độ phủ thống nhất với `greedy_ls`.

Kỳ vọng chi phí của một lần làm tròn ngẫu nhiên là `Σ c_j x*_j ≤ B`. Vì vậy phần lớn các lần làm tròn chỉ cần bỏ vài gói là vừa ngân sách.

**Seed:** mỗi seed là một bộ sinh số ngẫu nhiên khác nhau cho bước 3. Script chạy seed 0..19 theo yêu cầu của README (20–30 seed).

## 4. Độ phức tạp

- **Giải LP:** có `n + m` biến và `m + 1` ràng buộc. Simplex (CBC) không có cận đa thức chặt, nhưng thực tế giải nhanh: dưới 1 giây với n ≤ 4000 và m ≤ 400.
- **Một lần làm tròn:**
  - Lấy mẫu: `O(n)`.
  - Sửa: `O(d · k² · m/64)`, với `k` là số gói được chọn và `d` là số gói phải bỏ (thường nhỏ).
  - Lấp: chi phí của một lần ratio greedy CELF, khoảng `O(n · m/64)`.
- **Tổng một seed:** `O(samples · (n · m/64 + d · k² · m/64))`, cộng một lần giải LP dùng chung cho mọi seed.

## 5. Bảo đảm và cận trên

- **Cận trên:** `lp_bound ≥ OPT`. Vì vậy `objective / lp_bound` là **cận dưới của tỉ lệ so với tối ưu**, tính được ngay cả khi không có ILP. Điều này hữu ích cho instance RescueNet lớn, nơi ILP có thể không giải xong.
- **Cận xấp xỉ:** với Maximum Coverage có ràng buộc số lượng gói, pipage rounding hoặc dependent rounding đạt `(1 − 1/e)` (Ageev & Sviridenko 2004). Phiên bản ở đây làm tròn **độc lập** rồi sửa nghiệm, nên **không mang cận đó**; nó là một heuristic. Bảo đảm duy nhất là kết quả luôn hợp lệ và không tệ hơn chính lần làm tròn tất định.

*Cần người phụ trách lý thuyết (người 1) xem lại nếu muốn đưa cận của pipage rounding vào báo cáo.*

## 6. Kết quả trên OR-Library (45 instance × 3 mức ngân sách, 20 seed)

Tỉ lệ = số ô phủ / số ô phủ tối ưu (ILP, tất cả `optimal`). Mỗi ô ghi trung bình trên 45 instance, trong ngoặc là giá trị thấp nhất.

**So với các thuật toán khác:**

| Thuật toán | 75% OPT | 50% OPT | 25% OPT | Số lần = ILP | Thời gian / lần chạy |
|---|---|---|---|---|---|
| Greedy thuần (`04`) | 0.435 (0.093) | 0.410 (0.191) | 0.408 (0.201) | 0/135 | 0.003s |
| `greedy_ls` (`06`, tất định) | 0.994 (0.989) | 0.994 (0.985) | 0.997 (0.986) | 35/135 | TB 0.04s, max 0.15s |
| **`lp_rounding`, trung bình 20 seed** | **0.994 (0.983)** | **0.997 (0.986)** | **0.999 (0.988)** | **58.7% số lần chạy** | **TB 0.42s, max 1.82s** |
| `lp_rounding`, tốt nhất trong 20 seed | 0.997 (0.987) | 0.998 (0.989) | 0.9995 (0.993) | 94/135 | – |

- **Thời gian:** đã gồm giải LP (trung bình 0.25s, lâu nhất 1.43s). ILP mất tới khoảng 14s mỗi lần.
- **Độ lệch chuẩn giữa các seed:** trung bình 0.33 / 0.24 / 0.10 ô ở các mức 75 / 50 / 25%. Thuật toán rất ổn định.
- **Tỉ lệ khả thi:** 100%. Validator báo 0 lỗi.

**Cận trên LP so với tối ưu:**

| Mức ngân sách | `lp_bound / ILP` trung bình | Lớn nhất | Số instance LP = ILP |
|---|---|---|---|
| 75% | 1.006 | 1.017 | 1/45 |
| 50% | 1.008 | 1.027 | 1/45 |
| 25% | 1.008 | 1.048 | 13/45 |

**Nhận xét:**

- **So với `greedy_ls` theo từng lần chạy** (2700 lần): tốt hơn ở 42.6%, kém hơn ở 22.4%, bằng ở phần còn lại.
- **So với `greedy_ls` theo kết quả tốt nhất của 20 seed:** tốt hơn ở 75/135, kém ở 14/135.
- **Lý do LP làm tròn tốt:** LP nới lỏng của bộ OR-Library rất chặt, chỉ lệch tối đa 4.8% so với OPT. Nghiệm phân số vì vậy là "bản đồ" tốt để làm tròn.
- **Giá phải trả:** chậm hơn `greedy_ls` khoảng 10 lần, và phụ thuộc bộ giải LP (CBC).
- **Instance khó nhất:** họ `c` và `d` (n = 4000, mật độ cao), trung bình 0.995–0.996. Ở hai họ này LP nới lỏng lỏng hơn.
- **Lợi ích riêng:** `lp_bound` cho cận dưới của tỉ lệ so với tối ưu **mà không cần chạy ILP**. Điều này hữu ích khi instance RescueNet lớn tới mức ILP không giải xong.

## 7. Định dạng kết quả

`data/results/lp_rounding/<instance>_budgeted_<level>.json`. Có các trường như `greedy_ls`, cộng thêm:

| Trường | Ý nghĩa |
|---|---|
| `algorithm` | `"lp_rounding"` |
| `selected_packages`, `objective`, `cost` | lời giải của **seed tốt nhất**, là lời giải được validator kiểm tra |
| `seed` | seed cho lời giải tốt nhất |
| `lp_bound` | giá trị LP nới lỏng (cận trên của OPT theo trọng số) |
| `lp_time_seconds` | thời gian giải LP |
| `objective_mean/std/min/max` | thống kê số ô phủ qua mọi seed |
| `per_seed` | `[{seed, objective, cost, solve_time_seconds}]` của từng seed |
| `params` | `{"seeds", "samples"}` |

`solve_time_seconds` của mỗi seed **đã bao gồm** thời gian giải LP.

## 8. Chạy và kiểm thử

```bash
python pipeline/07_lp_rounding.py
python pipeline/05_validate_solution.py --results-dir data/results/lp_rounding
python -m pytest tests/test_lp_rounding.py
```

`tests/test_lp_rounding.py` kiểm tra các hành vi sau:

- LP cho nghiệm phân số và là cận trên của OPT.
- LP có tính đến trọng số ô.
- Bước sửa bỏ đúng gói có đóng góp kém nhất.
- Bước lấp dùng hết ngân sách còn dư.
- Không bao giờ vượt ngân sách, và số liệu khai báo khớp số tính lại.
- Đạt tối ưu ở trường hợp ratio greedy bị kẹt.
- Cùng seed cho cùng kết quả.
- Ngân sách bằng 0 trả về lời giải rỗng.

## 9. Tài liệu tham khảo

- P. Raghavan, C. Thompson. *Randomized rounding: a technique for provably good algorithms and algorithmic proofs*. Combinatorica 7(4), 1987.
- A. Ageev, M. Sviridenko. *Pipage rounding: a new method of constructing algorithms with proven performance guarantee*. Journal of Combinatorial Optimization 8(3), 2004.
- S. Khuller, A. Moss, J. Naor. *The budgeted maximum coverage problem*. Information Processing Letters 70(1), 1999.
