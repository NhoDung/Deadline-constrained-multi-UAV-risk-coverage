# Thiết kế: Greedy thuần (baseline)

> Mục tiêu: script `pipeline/04_greedy_pure.py` — thuật toán greedy thuần của Pha 1 ("mỗi bước chọn gói phủ thêm được nhiều ô mới nhất"). Dùng làm baseline nhanh, so sánh với đáp án chính xác từ `pipeline/03_solve_ilp.py`.

## 1. Bài toán: Budgeted Max Coverage (chỉ chế độ budgeted)

Không cần chạy setcover — OPT đã có sẵn và đã xác nhận đúng bằng ILP (`data/results/ilp/*_setcover.json`; xem README, mục "Bài toán và khái niệm nền"). Greedy chỉ chạy ở 3 mức ngân sách `B = floor(75%/50%/25% × OPT)`.

## 2. Thuật toán

Vòng lặp, ở mỗi bước:

1. Xét các gói **chưa chọn** có `cost ≤ ngân sách còn lại`.
2. Trong số đó, chọn gói phủ được **nhiều ô mới nhất** (so với các ô đã phủ tích lũy). **Không** xét chi phí khi so sánh — đây là điểm phân biệt với "greedy tỉ lệ" (thuật toán #3, dùng `ô mới / chi phí`).
3. Hòa số ô mới phủ được → chọn **chỉ số gói nhỏ nhất**.
4. Nếu không còn gói nào vừa ngân sách còn lại **và** phủ thêm được ≥1 ô mới → dừng.
5. Ngược lại: chọn gói đó, cộng dồn chi phí, đánh dấu ô đã phủ, trừ ngân sách còn lại, quay lại bước 1.

Thuật toán **hoàn toàn deterministic** (không có yếu tố ngẫu nhiên) → chạy 1 lần/instance/mức ngân sách là đủ, không cần multi-seed (khác với random baseline hay GRASP).

### Vì sao không có bảo đảm xấp xỉ

Vì bước chọn bỏ qua chi phí, thuật toán có thể chọn một gói rất đắt (chiếm gần hết ngân sách) chỉ vì nó phủ được nhiều ô nhất tại bước đó, dù tỉ lệ ô/chi phí của nó tệ. Hệ quả thực nghiệm đã quan sát được: **kết quả không đơn điệu theo ngân sách**. Ví dụ `scpd5`:

| Mức ngân sách | B | Ô phủ được (/400) |
|---|---|---|
| 75% | 45 | 36 |
| 50% | 30 | 144 |
| 25% | 15 | 148 |

Ngân sách cao hơn (45) lại cho kết quả tệ hơn ngân sách thấp hơn (15/30) — vì ở B=45 thuật toán "khóa" vào một gói đắt, tốt ở bước đầu nhưng bóp nghẹt các bước sau; ở B=30/15 gói đó không vừa ngân sách nên thuật toán buộc phải chọn các gói rẻ, hiệu quả hơn. Đây là bằng chứng thực nghiệm khớp với nhận định (README, mục "Bài toán và khái niệm nền"): greedy theo tỉ lệ đơn thuần, không kết hợp gói đơn tốt nhất, không có bảo đảm xấp xỉ nào — greedy thuần còn yếu hơn thế vì không xét tỉ lệ. Cần nêu rõ phát hiện này trong báo cáo (Discussion) làm minh chứng cho lý do cần các thuật toán tốt hơn (greedy theo tỉ lệ, Khuller–Moss–Naor).

## 3. Độ phức tạp

- Mỗi bước: quét tối đa `n` gói chưa chọn, mỗi gói tính `|sets[j] - covered|` tốn tối đa `O(|sets[j]|)`.
- Số bước tối đa: `n` (chọn hết mọi gói) nhưng thực tế dừng sớm khi ngân sách cạn.
- Tổng: `O(k · n · s̄)` với `k` = số bước thực tế, `s̄` = kích thước trung bình một gói — trong thực nghiệm trên bộ dữ liệu này (n ≤ 4000, m ≤ 400) chạy dưới 15ms/instance/mức ngân sách (lần chạy chậm nhất đo được: 14ms; xem trường `solve_time_seconds` trong `data/results/greedy/`).
- Có thể tối ưu bằng lazy evaluation (CELF, thuật toán #5 trong roadmap) nếu cần chạy trên instance lớn hơn nhiều — không cần thiết ở quy mô hiện tại.

## 4. Cấu trúc file kết quả

`data/results/greedy/<instance>_budgeted_<level>.json`, cùng field với ILP (`data/results/ilp/`) để validator dùng chung về sau, cộng thêm `algorithm`:

| Trường | Ý nghĩa |
|---|---|
| `instance` | tên instance |
| `algorithm` | `"greedy_pure"` |
| `mode` | luôn `"budgeted"` |
| `budget_level` | `"75%"` / `"50%"` / `"25%"` |
| `budget_value` | giá trị `B` thực tế |
| `status` | luôn `"greedy"` (không có khái niệm optimal/best-known — đây là heuristic) |
| `objective` | số ô phủ được |
| `cost` | tổng chi phí các gói đã chọn (≤ `budget_value`) |
| `selected_packages` | danh sách chỉ số gói đã chọn, theo đúng thứ tự chọn (0-indexed) |
| `solve_time_seconds` | thời gian chạy thật |

## 5. Tham số dòng lệnh

```
python pipeline/04_greedy_pure.py --instances scpa1,scp61 --budget-levels 75,50,25
```

- `--instances`: mặc định tất cả 45 instance trong `data/processed/`.
- `--budget-levels`: mặc định `75,50,25` (mức 100% không chạy: đáp án tối ưu ở B = OPT chắc chắn phủ 100%, nên chỉ là mốc kiểm tra, xem README mục "Bài toán và khái niệm nền").
- Không có `--time-limit`: thuật toán không cần time limit vì luôn chạy nhanh và không lặp vô hạn.

## 6. Refactor liên quan

Bảng `OPT_REFERENCE` (trước đây hard-code trong `pipeline/03_solve_ilp.py`) đã được tách ra `pipeline/opt_reference.py` để dùng chung giữa ILP và mọi thuật toán baseline/heuristic khác — tránh lặp lại bảng số ở nhiều nơi và tránh lệch số liệu khi có người sửa một chỗ mà quên chỗ kia.

## 7. Kiểm thử

`tests/test_greedy_pure.py` (TDD, viết trước khi cài thuật toán) kiểm tra 4 hành vi cốt lõi trên instance nhỏ tự tạo tay:

1. Chọn gói phủ nhiều ô mới nhất bất kể chi phí, miễn còn vừa ngân sách.
2. Hòa số ô mới → chọn chỉ số gói nhỏ nhất.
3. Dừng đúng lúc khi không còn gói nào vừa ngân sách còn lại.
4. Bỏ qua gói không còn phủ ô mới nào (dù vẫn vừa ngân sách).

`tests/test_opt_reference.py` khoá lại vài giá trị tham chiếu sau khi tách bảng ra module riêng, đảm bảo refactor không làm lệch số liệu.

Chạy: `python -m pytest tests/`

## 8. Kiểm tra kết quả bằng validator

`python pipeline/05_validate_solution.py --results-dir data/results/greedy` tự tính lại chi phí và số ô phủ của 135 file kết quả greedy, và kiểm tra `cost ≤ B`, `budget_value` khớp mức % × OPT, Hệ quả 1. Xem `docs/ilp-solver-thiet-ke.md` mục 6.

## 9. Kết quả so với ILP tối ưu (45 instance)

Tỉ lệ = số ô phủ của greedy / số ô phủ tối ưu của ILP (đều `optimal`), lấy trung bình trên 45 instance:

| Mức ngân sách | Độ phủ TB của greedy | Độ phủ TB của ILP tối ưu | Tỉ lệ greedy/ILP TB (thấp nhất – cao nhất) |
|---|---|---|---|
| 75% OPT | 41.7% | 96.0% | 0.435 (0.093 – 0.707) |
| 50% OPT | 35.9% | 87.5% | 0.410 (0.191 – 0.678) |
| 25% OPT | 28.3% | 69.3% | 0.408 (0.201 – 0.669) |

Thời gian chạy của greedy tối đa 14ms/lần; ILP mỗi lần giải tối đa ~14 giây.

**Lưu ý khi đọc kết quả:** greedy thuần yếu vì bỏ qua chi phí, nên hay chọn một gói đắt phủ nhiều ô rồi cạn ngân sách. Hệ quả là kết quả **không đơn điệu theo ngân sách** ở 21/45 instance (ngân sách cao hơn lại phủ ít hơn), ví dụ `scpd5`: B=45 → 36 ô, B=30 → 144 ô, B=15 → 148 ô. Đây là điểm cần nêu trong phần Discussion của báo cáo, và là lý do cần các thuật toán tốt hơn (greedy theo tỉ lệ, Khuller–Moss–Naor, ...). Không có bảo đảm xấp xỉ nào cho thuật toán này (README, mục "Bài toán và khái niệm nền").
