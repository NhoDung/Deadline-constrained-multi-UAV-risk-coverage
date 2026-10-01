# Thiết kế: Seeded Lazy Ratio Greedy + Local Search (`greedy_ls`)

> Script: `pipeline/06_greedy_ls.py`. Thuật toán heuristic **dùng chung cho cả hai phương án**: OR-Library (mọi ô trọng số 1) và instance RescueNet (ô có trọng số rủi ro). Không phải thuật toán giải chính xác; đáp án chính xác để so sánh lấy từ ILP (`pipeline/03_solve_ilp.py`).

## 1. Bài toán

Budgeted Maximum Coverage có trọng số:

- Universe gồm `m` ô, ô `i` có trọng số rủi ro `w_i ≥ 0` (OR-Library: `w_i = 1`).
- `n` gói (trong Pha 2 là các route UAV ứng viên), gói `j` có chi phí `c_j` và phủ tập ô `S_j`.
- Tìm tập gói `X` sao cho `Σ_{j∈X} c_j ≤ B` và tối đa `f(X) = Σ_{i ∈ ∪_{j∈X} S_j} w_i`.

`f` là hàm **đơn điệu và submodular**. Đây là cơ sở cho cận xấp xỉ ở mục 4.

## 2. Thuật toán

Gồm 4 bước. Mỗi bước chỉ thay lời giải hiện tại khi lời giải mới tốt hơn: phủ nhiều trọng số hơn, hoặc phủ bằng nhưng rẻ hơn.

1. **Ratio greedy (bản Khuller–Moss–Naor).** Mỗi bước chọn gói có tỉ lệ `trọng số ô mới / chi phí` lớn nhất trong các gói còn vừa ngân sách. Gói không vừa thì **bỏ qua và xét gói tiếp theo** chứ không dừng. Hòa tỉ lệ thì chọn chỉ số nhỏ nhất.
2. **Gói đơn tốt nhất.** Gói đơn vừa ngân sách và phủ nhiều trọng số nhất. Bước này xử lý trường hợp xấu của greedy tỉ lệ: một gói rẻ có tỉ lệ cao chặn mất một gói lớn.
3. **Đa khởi tạo (seed).** Chạy lại bước 1 với mỗi tập bắt đầu `{j}`, trong đó `j` thuộc `K` gói phủ nhiều nhất hoặc `K` gói có tỉ lệ tốt nhất. Mặc định `K = 20`, tức tối đa 40 lần chạy.
4. **Local search drop-and-refill.** Với lời giải tốt nhất `X`, lần lượt thử bỏ một gói `i ∈ X`, rồi lấp lại ngân sách còn dư bằng bước 1. Gói `i` bị cấm trong lần lấp đó để lời giải buộc phải đổi. Nhận cải thiện đầu tiên tìm được, lặp tới khi không còn cải thiện hoặc hết `--ls-rounds` vòng (mặc định 50).

Thuật toán **deterministic**: chạy một lần cho mỗi instance và mức ngân sách, không cần nhiều seed ngẫu nhiên. Ở đây "seed" nghĩa là gói khởi tạo, không phải seed của bộ sinh số ngẫu nhiên.

### Kỹ thuật cài đặt

- **Bitmask:** mỗi gói lưu thành một số nguyên Python, bit `i` bật nếu gói phủ ô `i`. Độ phủ mới tính bằng `mask & ~covered`, rồi `int.bit_count()` khi không có trọng số.
- **Lazy evaluation (CELF):** heap lưu tỉ lệ tính ở vòng trước. Do `f` submodular, tỉ lệ cũ luôn là cận trên của tỉ lệ hiện tại, nên chỉ cần tính lại cho phần tử đang ở đầu heap.

## 3. Độ phức tạp

- Một lần ratio greedy: `O(n · m/64)` để dựng heap, cộng thêm số lần đánh giá lại (thực tế nhỏ nhờ CELF).
- Tổng số lần chạy greedy: `1 + 2K + (số lần thử trong local search)`.
- Thực nghiệm trên 45 instance OR-Library (n ≤ 4000, m ≤ 400): trung bình 0.04 giây, chậm nhất 0.15 giây mỗi lần. ILP mất tới khoảng 14 giây mỗi lần.

## 4. Bảo đảm xấp xỉ

Gọi `G` là kết quả ratio greedy ở bước 1 và `s*` là gói đơn tốt nhất ở bước 2. Khuller, Moss và Naor (1999) chứng minh:

```
max(f(G), f({s*})) ≥ ½ (1 − 1/e) · OPT ≈ 0.316 · OPT
```

Bước 3 và 4 chỉ thay lời giải khi `f` tăng, nên kết quả cuối **giữ nguyên cận này**. Cận `(1 − 1/e)` đầy đủ đòi hỏi duyệt mọi tập seed gồm 3 gói (Sviridenko 2004), tức `O(n³)` lần chạy greedy, quá chậm với `n = 4000`. Seed một gói là phiên bản rút gọn của ý tưởng đó.

*Cần người phụ trách mô hình & lý thuyết (người 1) xác nhận lại cách phát biểu cận khi viết báo cáo.*

## 5. Kết quả trên OR-Library (45 instance × 3 mức ngân sách)

Tỉ lệ = số ô phủ / số ô phủ tối ưu (ILP, tất cả `optimal`). Mỗi ô ghi trung bình, trong ngoặc là giá trị thấp nhất.

| Cấu hình | 75% OPT | 50% OPT | 25% OPT | Số lần = ILP (/135) | Thời gian tối đa |
|---|---|---|---|---|---|
| Greedy thuần (baseline, `04`) | 0.435 (0.093) | 0.410 (0.191) | 0.408 (0.201) | – | 0.014s |
| Chỉ ratio greedy | 0.985 (0.974) | 0.987 (0.971) | 0.990 (0.971) | 2 | 0.01s |
| Ratio + seed | 0.987 (0.979) | 0.990 (0.977) | 0.995 (0.986) | 13 | 0.15s |
| Ratio + local search | 0.993 (0.979) | 0.993 (0.977) | 0.995 (0.978) | 25 | 0.07s |
| **Đầy đủ (mặc định, K=20)** | **0.994 (0.989)** | **0.994 (0.985)** | **0.997 (0.986)** | **35** | 0.17s |
| Đầy đủ, K=100 | 0.996 (0.990) | 0.997 (0.988) | 0.998 (0.991) | 56 | 0.67s |

Nhận xét:

- Greedy tỉ lệ đã tốt hơn hẳn greedy thuần, vì greedy thuần bỏ qua chi phí (xem `docs/greedy-thuan-thiet-ke.md` mục 2).
- Seed và local search bổ sung cho nhau: kết hợp cả hai thì số lần đạt tối ưu tăng từ 2 lên 35 (lên 56 nếu K=100), và trường hợp xấu nhất tăng từ 97.1% lên 98.5%.
- Kết quả **đơn điệu theo ngân sách** ở cả 45/45 instance. Greedy thuần thì không đơn điệu ở 21/45.
- Thực nghiệm thường cao hơn nhiều so với cận lý thuyết 0.316. Cận này chỉ là bảo đảm cho trường hợp xấu nhất.

## 6. Dùng cho Pha 2 (RescueNet)

- Instance cần cùng format với `data/processed/` (`m, n, costs, sets`), cộng thêm trường tùy chọn `weights` (độ dài `m`) chứa trọng số rủi ro từng ô. Không có `weights` thì mọi ô có trọng số 1.
- Trong kết quả, `objective` vẫn là **số ô** phủ được, để validator hiện tại kiểm tra được. Trường `covered_weight` là tổng trọng số rủi ro phủ được, tức hàm mục tiêu thật của Pha 2.
- **Giới hạn:** mô hình hiện tại dùng **một ngân sách chung**. Nếu Pha 2 chốt ngân sách hoặc deadline riêng cho từng UAV, mỗi UAV chọn một route, thì bài toán có thêm ràng buộc partition matroid. Khi đó bước 1 cần lọc thêm điều kiện "UAV này còn slot / còn pin". Việc này chờ người 1 và người 4 chốt format.
- Validator chưa kiểm tra `covered_weight`. Cần bổ sung khi có instance RescueNet.

## 7. Định dạng kết quả

`data/results/greedy_ls/<instance>_budgeted_<level>.json`, cùng các trường như baseline (`docs/huong-dan-chay.md`), thêm:

| Trường | Ý nghĩa |
|---|---|
| `algorithm` | `"greedy_ls"` |
| `status` | luôn là `"heuristic"` |
| `covered_weight` | tổng trọng số rủi ro phủ được (bằng `objective` với OR-Library) |
| `params` | `{"seeds": K, "ls_rounds": ...}` đã dùng khi chạy |

## 8. Chạy và kiểm thử

```bash
python pipeline/06_greedy_ls.py                                  # 45 instance × 75/50/25%
python pipeline/06_greedy_ls.py --instances scpa1 --seeds 100 --ls-rounds 50
python pipeline/05_validate_solution.py --results-dir data/results/greedy_ls
python -m pytest tests/test_greedy_ls.py
```

`tests/test_greedy_ls.py` kiểm tra các hành vi chính trên instance nhỏ tự tạo:

- Greedy tỉ lệ ưu tiên gói rẻ mà hiệu quả.
- Bỏ qua gói không vừa ngân sách nhưng vẫn chạy tiếp.
- Hòa tỉ lệ thì chọn chỉ số nhỏ nhất.
- Giữ đúng tập seed ban đầu.
- Trọng số rủi ro làm thay đổi lựa chọn gói.
- Gói đơn tốt nhất thắng greedy tỉ lệ khi cần.
- Local search sửa được lời giải sai của greedy.
- Không bao giờ vượt ngân sách.
- Ngân sách bằng 0 trả về lời giải rỗng.

## 9. Tài liệu tham khảo

- S. Khuller, A. Moss, J. Naor. *The budgeted maximum coverage problem*. Information Processing Letters 70(1), 1999.
- M. Sviridenko. *A note on maximizing a submodular set function subject to a knapsack constraint*. Operations Research Letters 32(1), 2004.
- J. Leskovec et al. *Cost-effective outbreak detection in networks* (CELF). KDD 2007.
- G. Nemhauser, L. Wolsey, M. Fisher. *An analysis of approximations for maximizing submodular set functions*. Mathematical Programming 14, 1978.
