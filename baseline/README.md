# Baseline: Greedy thuần

Thuật toán #2 trong `project-brief.md` mục 7, cho bài toán **Budgeted Max Coverage** trên 45 instance OR-Library. Ở mỗi bước, chọn gói phủ được **nhiều ô mới nhất** trong số các gói còn vừa ngân sách; **không xét chi phí** khi so sánh (khác greedy theo tỉ lệ). Hòa thì chọn chỉ số gói nhỏ nhất. Thuật toán deterministic nên chỉ cần chạy 1 lần, không cần nhiều seed.

Thiết kế đầy đủ (thuật toán, độ phức tạp, format kết quả): `docs/greedy-thuan-thiet-ke.md`.

## Chạy

```bash
# từ thư mục gốc của repo
python baseline/greedy_pure.py                                        # tất cả 45 instance, B = 75/50/25% OPT
python baseline/greedy_pure.py --instances scpa1,scp61 --budget-levels 75,50,25
```

Kết quả ghi ra `data/results/greedy/<instance>_budgeted_<mức>.json`. Mức 100% OPT không cần chạy vì luôn phủ 100% (Mệnh đề chính, mục 5 của brief).

## Kiểm tra kết quả

```bash
python -m pytest tests/test_greedy_pure.py                     # 4 test hành vi của thuật toán
python scripts/validate_solution.py --results-dir data/results/greedy
```

Validator tự tính lại chi phí và số ô phủ từ `selected_packages` và báo lỗi nếu chi phí vượt `B`, `budget_value` sai, hoặc số liệu khai báo lệch (xem `docs/ilp-solver-thiet-ke.md` mục 6). Lần chạy hiện tại: 135/135 file hợp lệ.

## Kết quả so với ILP tối ưu (45 instance)

Tỉ lệ = số ô phủ của greedy / số ô phủ tối ưu của ILP (đều `optimal`), lấy trung bình trên 45 instance:

| Mức ngân sách | Độ phủ TB của greedy | Độ phủ TB của ILP tối ưu | Tỉ lệ greedy/ILP TB (thấp nhất – cao nhất) |
|---|---|---|---|
| 75% OPT | 41.7% | 96.0% | 0.435 (0.093 – 0.707) |
| 50% OPT | 35.9% | 87.5% | 0.410 (0.191 – 0.678) |
| 25% OPT | 28.3% | 69.3% | 0.408 (0.201 – 0.669) |

Thời gian chạy của greedy tối đa 14ms/lần; ILP mỗi lần giải tối đa ~14 giây.

**Lưu ý khi đọc kết quả:** greedy thuần yếu vì bỏ qua chi phí, nên hay chọn một gói đắt phủ nhiều ô rồi cạn ngân sách. Hệ quả là kết quả **không đơn điệu theo ngân sách** ở 21/45 instance (ngân sách cao hơn lại phủ ít hơn), ví dụ `scpd5`: B=45 → 36 ô, B=30 → 144 ô, B=15 → 148 ô. Đây là điểm cần nêu trong phần Discussion của báo cáo, và là lý do cần các thuật toán tốt hơn (greedy theo tỉ lệ, Khuller–Moss–Naor, ...). Không có bảo đảm xấp xỉ nào cho thuật toán này (brief mục 6).

## Thêm thuật toán baseline mới

1. Đặt code trong thư mục này, đọc instance từ `data/processed/<tên>.json` (`m, n, costs, sets`, 0-indexed).
2. Dùng bảng OPT chung `scripts/opt_reference.py` để tính `B = floor(mức% × OPT)`.
3. Ghi kết quả JSON cùng format với greedy/ILP vào `data/results/<tên thuật toán>/` (các trường `instance, algorithm, mode, budget_level, budget_value, status, objective, cost, selected_packages, solve_time_seconds`).
4. Viết test trước (TDD), rồi chạy `python scripts/validate_solution.py` để chắc kết quả hợp lệ. Không chỉnh heuristic cho khớp đáp án ILP (brief mục 7).
