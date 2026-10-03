# Thiết kế: Genetic Algorithm có repair (`genetic`)

> Script: `pipeline/08_genetic.py`. Thuật toán meta-heuristic (nhóm "nâng cao 1"), dùng chung cho OR-Library và instance RescueNet (trường `weights`). Đáp án chính xác để so sánh lấy từ ILP (`pipeline/03_solve_ilp.py`).

## 1. Bài toán

Giống `docs/greedy-ls-thiet-ke.md` mục 1: Budgeted Maximum Coverage có trọng số. Cần chọn tập gói `X` với `Σ_{j∈X} c_j ≤ B` sao cho tổng trọng số ô được phủ `f(X)` là lớn nhất.

## 2. Thiết kế

| Thành phần | Lựa chọn |
|---|---|
| **Mã hóa** | Mỗi cá thể là danh sách chỉ số gói được chọn (tương đương vector nhị phân độ dài `n`) |
| **Độ thích nghi** | `(f(X), −chi phí)`: so sánh theo trọng số phủ trước, hòa thì rẻ hơn tốt hơn |
| **Khởi tạo** | Cá thể 0 là ratio greedy từ tập rỗng. Các cá thể còn lại bắt đầu từ 1–3 gói ngẫu nhiên vừa ngân sách, rồi sửa và lấp. Kích thước quần thể mặc định 30 |
| **Chọn lọc** | Tournament nhị phân: chọn ngẫu nhiên 2 cá thể, lấy cá thể tốt hơn |
| **Lai ghép** | Giữ mọi gói **chung** của hai cha mẹ. Mỗi gói chỉ có ở một bên được lấy với xác suất ½. Sau đó sửa nghiệm, ưu tiên giữ gói chung |
| **Đột biến** (xác suất 0.3) | Xóa ngẫu nhiên từ 1 tới `max(1, 20%)` số gói. Với xác suất ½, chèn thêm một gói ngẫu nhiên vừa ngân sách. Sau đó sửa nghiệm; gói vừa xóa bị cấm khi lấp lại để buộc lời giải đổi hướng |
| **Sửa nghiệm** | Khi vượt ngân sách, bỏ dần gói có tỉ lệ `trọng số chỉ mình nó phủ / chi phí` nhỏ nhất (gói được bảo vệ bị bỏ sau cùng). Sau đó lấp ngân sách còn dư bằng ratio greedy CELF, hàm lấy lại từ `06_greedy_ls.py` |
| **Thay thế** | Steady-state: mỗi thế hệ sinh 1 con. Con thay cá thể tệ nhất nếu tốt hơn nó và chưa có trong quần thể. Việc loại cá thể trùng giúp giữ đa dạng |
| **Dừng** | Khi gặp điều kiện nào trước: đủ 1000 thế hệ, 300 thế hệ liên tiếp không cải thiện cá thể tốt nhất, hoặc chạy quá 10 giây |

Vì mọi cá thể đều đi qua bước sửa nghiệm, **tỉ lệ khả thi luôn là 100%**: không có lời giải nào vượt ngân sách.

Khác biệt với `greedy_ls`: `greedy_ls` là tìm kiếm tất định quanh một lời giải (drop-and-refill). GA duy trì **một quần thể** lời giải và kết hợp chúng qua lai ghép. Nhờ đó GA có thể ghép các phần tốt của những lời giải khác nhau, nhưng phải trả giá bằng thời gian chạy và tính ngẫu nhiên.

## 3. Độ phức tạp

Gọi `G` là số thế hệ (≤ 1000), `P` là kích thước quần thể, `k` là số gói trong một lời giải và `d` là số gói phải bỏ khi sửa.

- **Một thế hệ:**
  - Lai ghép và đột biến: `O(k)`.
  - Sửa: `O(d · k² · m/64)`.
  - Lấp: một lần ratio greedy CELF, khoảng `O(n · m/64)`.
  - Tìm cá thể tệ nhất: `O(P)`.
- **Khởi tạo:** `P` lần sửa và lấp.
- **Tổng:** `O((P + G) · (n · m/64 + d · k² · m/64))`. Thời gian bị chặn bởi `--time-limit`.

GA **không có bảo đảm xấp xỉ**. Tuy vậy, cá thể 0 là ratio greedy và cá thể tốt nhất không bao giờ bị thay bằng cá thể tệ hơn, nên kết quả **không bao giờ tệ hơn ratio greedy thuần** (bước 1 của `greedy_ls`).

## 4. Seed và cách báo cáo

- Thuật toán ngẫu nhiên nên chạy **20 seed** (0..19) cho mỗi cặp (instance, ngân sách), theo yêu cầu của README.
- File kết quả lưu lời giải của **seed tốt nhất** để validator kiểm tra. Kèm theo đó là `objective_mean/std/min/max` và `per_seed`.
- **Khi báo cáo, nên dùng trung bình ± độ lệch chuẩn qua các seed.** Kết quả "tốt nhất trong 20 seed" tương đương chạy thuật toán 20 lần, nên không công bằng khi so với thuật toán tất định.
- `--workers N` chạy các seed song song trên N tiến trình. Kết quả không phụ thuộc số worker.

## 5. Kết quả trên OR-Library (45 instance × 3 mức ngân sách, 20 seed)

Tỉ lệ = số ô phủ / số ô phủ tối ưu (ILP, tất cả `optimal`). Mỗi ô ghi trung bình trên 45 instance, trong ngoặc là giá trị thấp nhất.

| Thuật toán | 75% OPT | 50% OPT | 25% OPT | Số lần = ILP | Thời gian / lần chạy |
|---|---|---|---|---|---|
| Greedy thuần (`04`) | 0.435 (0.093) | 0.410 (0.191) | 0.408 (0.201) | 0/135 | 0.003s |
| `greedy_ls` (`06`, tất định) | 0.994 (0.989) | 0.994 (0.985) | 0.997 (0.986) | 35/135 | TB 0.04s, max 0.15s |
| `lp_rounding` (`07`), trung bình 20 seed | 0.994 (0.983) | 0.997 (0.986) | 0.999 (0.988) | 58.7% số lần chạy | TB 0.42s, max 1.82s |
| **`genetic`, trung bình 20 seed** | **0.992 (0.986)** | **0.995 (0.986)** | **0.997 (0.990)** | **28.5% số lần chạy** | **TB 0.79s, max 5.21s** |
| `genetic`, tốt nhất trong 20 seed | 0.996 (0.989) | 0.998 (0.992) | 0.9995 (0.993) | 84/135 | – |

- **Độ lệch chuẩn giữa các seed:** trung bình 0.59 / 0.52 / 0.29 ô ở các mức 75 / 50 / 25%.
- **Số thế hệ:** trung bình 454. Phần lớn lần chạy dừng do 300 thế hệ không cải thiện. Không lần nào chạm giới hạn 10 giây.
- **Tỉ lệ khả thi:** 100%. Validator báo 0 lỗi.

**Nhận xét:**

- **So với `greedy_ls` theo từng lần chạy** (2700 lần): tốt hơn ở 21.5%, **kém hơn ở 26.9%**. Tính trung bình, GA **ngang `greedy_ls` nhưng chậm hơn khoảng 20 lần**.
- **So theo kết quả tốt nhất của 20 seed:** GA tốt hơn `greedy_ls` ở 68/135 và kém ở 5/135. Tuy nhiên so sánh này không công bằng, vì tương đương chạy GA 20 lần.
- **So với `lp_rounding`:** GA kém hơn ở mọi mức ngân sách khi tính trung bình seed, và chậm hơn khoảng 2 lần.
- **Điểm mạnh:** GA tốt nhất ở họ `6`, `b` và `d` (0.9996 / 0.9993 / 0.9995 theo kết quả tốt nhất của 20 seed). Đây là các instance mật độ cao, nơi lai ghép ghép được nhiều phần tốt.
- **Hướng cải thiện** (chưa làm):
  - Thêm bước drop-and-refill của `greedy_ls` vào cá thể con (memetic algorithm).
  - Khởi tạo một phần quần thể từ `lp_rounding`.
  - Tăng kích thước quần thể với họ `c`/`d`.
  - Cần ghi rõ trong báo cáo rằng các tham số chưa được tinh chỉnh (dùng mặc định ở mục 2).

## 6. Định dạng kết quả

`data/results/genetic/<instance>_budgeted_<level>.json`. Có các trường như `greedy_ls`, cộng thêm `seed`, `solve_time_mean_seconds`, `objective_mean/std/min/max`, `per_seed` (`[{seed, objective, cost, generations, solve_time_seconds}]`) và `params` (`seeds, pop_size, generations, stall, mutation_rate, time_limit`).

## 7. Chạy và kiểm thử

```bash
python pipeline/08_genetic.py --workers 8
python pipeline/05_validate_solution.py --results-dir data/results/genetic
python -m pytest tests/test_genetic.py
```

`tests/test_genetic.py` kiểm tra các hành vi sau:

- Bước sửa luôn cho lời giải hợp lệ.
- Lai ghép giữ gói chung của hai cha mẹ.
- Đột biến thay đổi lời giải nhưng vẫn hợp lệ.
- Không bao giờ vượt ngân sách.
- Thoát được trường hợp ratio greedy bị kẹt.
- Trọng số ô quyết định hàm mục tiêu.
- Cùng seed cho cùng kết quả.
- Ngân sách bằng 0 trả về lời giải rỗng.

## 8. Tài liệu tham khảo

- J. E. Beasley, P. C. Chu. *A genetic algorithm for the set covering problem*. European Journal of Operational Research 94(2), 1996. (Ý tưởng mã hóa nhị phân + toán tử sửa nghiệm.)
- D. E. Goldberg. *Genetic Algorithms in Search, Optimization and Machine Learning*. Addison-Wesley, 1989.
- S. Khuller, A. Moss, J. Naor. *The budgeted maximum coverage problem*. Information Processing Letters 70(1), 1999.
