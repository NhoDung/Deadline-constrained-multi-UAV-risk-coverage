# Thiết kế: Greedy thuần (baseline)

> Mục tiêu: script `baseline/greedy_pure.py` — thuật toán #2 trong mục 7 project-brief.md ("Greedy thuần — mỗi bước chọn gói phủ thêm được nhiều ô mới nhất"). Dùng làm baseline nhanh, so sánh với đáp án chính xác từ `scripts/solve_ilp.py`.

## 1. Bài toán: Budgeted Max Coverage (chỉ chế độ budgeted)

Không cần chạy setcover — OPT đã có sẵn và đã xác nhận đúng bằng ILP (`data/results/ilp/*_setcover.json`, mục 3 project-brief.md). Greedy chỉ chạy ở 3 mức ngân sách `B = floor(75%/50%/25% × OPT)`.

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

Ngân sách cao hơn (45) lại cho kết quả tệ hơn ngân sách thấp hơn (15/30) — vì ở B=45 thuật toán "khóa" vào một gói đắt, tốt ở bước đầu nhưng bóp nghẹt các bước sau; ở B=30/15 gói đó không vừa ngân sách nên thuật toán buộc phải chọn các gói rẻ, hiệu quả hơn. Đây là bằng chứng thực nghiệm khớp với brief mục 6: "Greedy theo tỉ lệ... đơn thuần, không kết hợp gói đơn tốt nhất, KHÔNG có bảo đảm xấp xỉ nào cả" — greedy thuần còn yếu hơn thế vì không xét tỉ lệ. Cần nêu rõ phát hiện này trong báo cáo (Discussion) làm minh chứng cho lý do cần các thuật toán #3, #4 tốt hơn.

## 3. Độ phức tạp

- Mỗi bước: quét tối đa `n` gói chưa chọn, mỗi gói tính `|sets[j] - covered|` tốn tối đa `O(|sets[j]|)`.
- Số bước tối đa: `n` (chọn hết mọi gói) nhưng thực tế dừng sớm khi ngân sách cạn.
- Tổng: `O(k · n · s̄)` với `k` = số bước thực tế, `s̄` = kích thước trung bình một gói — trong thực nghiệm trên bộ dữ liệu này (n ≤ 4000, m ≤ 400) chạy dưới 10ms/instance/mức ngân sách (xem log chạy thực tế).
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
python baseline/greedy_pure.py --instances scpa1,scp61 --budget-levels 75,50,25
```

- `--instances`: mặc định tất cả 45 instance trong `data/processed/`.
- `--budget-levels`: mặc định `75,50,25` (mức 100% không cần chạy — coverage = 100% chắc chắn, đã chứng minh mục 5 project-brief.md).
- Không có `--time-limit`: thuật toán không cần time limit vì luôn chạy nhanh và không lặp vô hạn.

## 6. Refactor liên quan

Bảng `OPT_REFERENCE` (trước đây hard-code trong `scripts/solve_ilp.py`) đã được tách ra `scripts/opt_reference.py` để dùng chung giữa ILP và mọi thuật toán baseline/heuristic khác — tránh lặp lại bảng số ở nhiều nơi và tránh lệch số liệu khi có người sửa một chỗ mà quên chỗ kia.

## 7. Kiểm thử

`tests/test_greedy_pure.py` (TDD, viết trước khi cài thuật toán) kiểm tra 4 hành vi cốt lõi trên instance nhỏ tự tạo tay:

1. Chọn gói phủ nhiều ô mới nhất bất kể chi phí, miễn còn vừa ngân sách.
2. Hòa số ô mới → chọn chỉ số gói nhỏ nhất.
3. Dừng đúng lúc khi không còn gói nào vừa ngân sách còn lại.
4. Bỏ qua gói không còn phủ ô mới nào (dù vẫn vừa ngân sách).

`tests/test_opt_reference.py` khoá lại vài giá trị tham chiếu sau khi tách bảng ra module riêng, đảm bảo refactor không làm lệch số liệu.

Chạy: `python -m pytest tests/`
