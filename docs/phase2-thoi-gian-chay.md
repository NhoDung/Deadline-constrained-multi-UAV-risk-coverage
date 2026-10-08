# Pha 2: phân tích thời gian chạy (lý thuyết Big-O và đo thực tế)

> Soạn 07/10/2026. Bổ sung cho `docs/phase2-ket-qua.md` (chất lượng lời giải). Nguồn số liệu: thời gian ghi sẵn trong file kết quả (`solve_time_seconds`, do `08` và `09` đo khi chạy) và script **`pipeline/12_timing_rn.py`** (các lệnh `lazy`, `runs`, `seeds`, `scale`, ghi CSV vào `data/rescuenet/`). Mục 3.1 và 3.7 tính từ file kết quả; mục 3.2 đến 3.6 tái lập được bằng script (xem mục 7). Xem mục 6 về hạn chế.

## 1. Ký hiệu

| Ký hiệu | Ý nghĩa | Giá trị trong thực nghiệm |
|---|---|---|
| `m` | số ô cần phủ (universe) | 68 đến 304 (cấu hình chính) |
| `n` | số route (gói) của cả K UAV | 403 đến 1027 |
| `K` | số UAV | 4 |
| `L` | số ô tối đa của một route | 40 |
| `c̄` | số ô trung bình một route phủ (`c̄ ≤ L`) | từ 1 đến 40, trung bình 14,8 (đo trên 30 instance chính) |
| `W = ⌈m/64⌉` | số "từ" 64-bit của một mask bit (Python dùng số nguyên lớn) | 2 đến 5 |
| `k` | số route được chọn trong lời giải | 3,5 (mức 25%) đến 11,6 (mức 100%) |
| `S` | số lần chạy "seed" (tối đa `2 × n_seeds`) | tối đa 40 (`n_seeds = 20`) |
| `r` | số vòng local search tối đa | 50 |
| `P` | số pixel của ảnh | 12 triệu (4000×3000) |

## 2. Độ phức tạp lý thuyết

### 2.1. Các phép tính nền

- **Đánh giá giá trị mới của một route** (`_weight(mask & ~covered, weights)`): các phép `&`, `~` mất `O(W)`; sau đó duyệt từng bit của phần ô mới (mỗi bit: `mask & -mask`, `bit_length`, `mask ^= low`, mỗi phép `O(W)`). Tổng **`O(g · W)`** với `g ≤ c̄ ≤ L` là số ô mới. Vì `W ≤ 5` và `L ≤ 40`, coi như hằng số nhỏ.
- **Dựng mask** (`prepare`): `O(n · c̄ · W)`.

### 2.2. Từng thành phần

| Thành phần | Thời gian (trường hợp xấu nhất) | Ghi chú |
|---|---|---|
| Risk map (`cell_risk`) | `O(P)` | tra bảng điểm rồi lấy trung bình theo khối, vector hóa bằng numpy; bộ nhớ `O(P)` (khoảng 96 MB cho ảnh 12 triệu pixel vì mảng `float64`) |
| Sinh route (`build_instance`) | `O(K · T · L + n log n)` | `T` = số route sinh mỗi UAV (300); dedupe bằng `frozenset`, sắp xếp để cố định thứ tự |
| Chi phí tham chiếu `R` | NP-khó (ILP set cover) | thực tế khoảng 4 giây mỗi instance |
| **Ratio greedy không lazy** | `O(n · k · L · W)` | mỗi bước duyệt lại mọi route còn lại |
| **Ratio greedy lazy (CELF)**, một lần chạy `G` | khởi tạo `O(n · L · W)` + heap; mỗi lần tính lại `O(L · W + log n)`; xấu nhất `O(n · k · (L · W + log n))` | bằng không lazy ở xấu nhất; thực tế chỉ khoảng `1,1 n` đến `2,2 n` lần đánh giá (mục 3.3) |
| Route đơn tốt nhất | `O(n · L · W)` | cộng sắp xếp `O(n log n)` để chọn seed |
| Seed | `O(S · G)` | `S ≤ 40` lần chạy greedy, mỗi lần bắt đầu từ một route cho trước |
| Local search drop-and-refill | `O(r · k · G)` xấu nhất | mỗi vòng thử bỏ lần lượt `k` route, mỗi lần là một lần greedy |
| **`proposed` tổng** | **`O((1 + S + r·k) · G)`**, với `G = O(n·L·W)` thường gặp | thực tế khoảng 54 lần chạy greedy mỗi lần giải (mục 3.2) |
| `naive` | cùng dạng `O((1 + S + r·k') · G)` với `k'` là số route của lời giải ngân sách chung, cộng sửa `O(k log k)` và một lần lấp lại | `k'` lớn hơn nên chậm hơn khoảng 1,6 lần |
| ILP (CBC) | **NP-khó**, nhánh-cận tệ nhất `O(2^n)`; nới lỏng LP có `n + m` biến, `K + m` ràng buộc, `O(n·c̄)` số khác 0 | nới lỏng LP giải được trong thời gian đa thức trong thực tế, nhưng tìm nghiệm nguyên tối ưu không có chặn đa thức |
| Validator | `O(Σ_{j ∈ chọn} \|S_j\| + K)` | không đáng kể |
| Wilcoxon | `O(N log N)` với `N = 30` | không đáng kể |

**Bài toán là NP-khó** vì chứa Budgeted Max Coverage (và knapsack khi chỉ có một UAV, một ô mỗi route), nên ILP không có thuật toán đa thức nào được biết. Heuristic greedy đổi tính tối ưu lấy thời gian gần tuyến tính trong `n`.

### 2.3. Tóm tắt dạng công thức

Với tham số mặc định (`S ≤ 40`, `r = 50`, `W ≤ 5`, `L ≤ 40`), thời gian của `proposed` được dự đoán là **tuyến tính theo `n`** và **gần như không phụ thuộc `m`** (vì `m` chỉ vào qua `W`, rất nhỏ), và **tuyến tính theo số seed**. Mục 3 kiểm chứng ba dự đoán này.

## 3. Đo thực tế

Máy: Intel Core i5-12450HX (12 luồng), Python 3.12, một luồng, lấy giá trị nhỏ nhất của 2 đến 3 lần chạy. Có vài ứng dụng khác chạy nền (trình duyệt, một job khác) nên số tuyệt đối có thể dao động một chút.

### 3.1. Thời gian trên 30 instance thật (cấu hình chính `g20_default`)

Thời gian đo lại sạch (nhỏ nhất của 3 lần), trung bình / lớn nhất trên 120 lần giải (30 instance × 4 mức):

| Thuật toán | Trung bình | Lớn nhất |
|---|---|---|
| `abl_ratio_only` (chỉ ratio greedy per-UAV + route đơn) | 2,6 ms | 8,2 ms |
| `abl_no_seed` (có local search, không seed) | 5,2 ms | 27,2 ms |
| `abl_no_ls` (có seed, không local search) | 34,7 ms | 149,8 ms |
| **`proposed`** | **36,7 ms** | **163,4 ms** |
| `naive` | 58,1 ms | 189,4 ms |

Theo mức ngân sách, `proposed`: 10,8 ms (25%), 32,0 ms (50%), 47,0 ms (75%), 57,0 ms (100%) trung bình, với số route chọn `k` trung bình 3,5 / 6,1 / 8,9 / 11,6. Thời gian tăng theo `k`, khớp với dự đoán (nhiều bước greedy hơn và nhiều route để thử bỏ hơn).

Các giá trị `solve_time_seconds` ghi sẵn trong file kết quả khớp số đo lại này (ví dụ `proposed` 11 / 31 / 47 / 58 ms ở 4 mức).

**Phân rã chi phí:** bản chỉ có ratio greedy một lần (`abl_ratio_only`) chỉ khoảng 2,6 ms; **seed chiếm gần hết thời gian** (`abl_no_ls` 34,7 ms so với `proposed` 36,7 ms); local search chỉ thêm khoảng 2 ms.

### 3.2. Số lần chạy greedy mỗi lần giải

Đếm trên 60 lượt giải (30 instance × mức 50% và 100%): trung bình **54,2** lần chạy ratio greedy mỗi `solve_uav` (nhỏ nhất 24, lớn nhất 116), gồm 1 lần gốc, tối đa 40 lần seed và phần còn lại là local search (khoảng một lượt `k` lần thử bỏ route).

### 3.3. Lazy evaluation (CELF) có tác dụng không?

So ratio greedy lazy với bản duyệt lại toàn bộ (cài riêng để so), trên 60 lượt (30 instance × 2 mức). **Cả hai cho cùng lời giải, cùng thứ tự chọn, ở 60/60 lượt.**

| Mức | `n` TB | `k` TB | Số lần đánh giá, lazy | Số lần đánh giá, không lazy | Giảm | Thời gian lazy | Không lazy | Nhanh hơn |
|---|---|---|---|---|---|---|---|---|
| 50% | 678 | 6,5 | 752 | 2192 | 2,9× | 1,29 ms | 2,68 ms | 2,1× |
| 100% | 678 | 12,0 | 1472 | 5884 | 4,0× | 2,26 ms | 4,87 ms | 2,2× |

Số lần đánh giá lazy chỉ khoảng `1,1 n` (mức 50%) đến `2,2 n` (mức 100%), trong khi không lazy là `3,2 n` đến `8,7 n` và tăng theo `k`. Lợi ích thật nhưng **khiêm tốn** (khoảng 2 lần về thời gian), vì `k` chỉ khoảng 6 đến 12 và bước khởi tạo (`n` lần đánh giá) chiếm phần lớn.

### 3.4. Thời gian theo số seed

Thời gian (ms) của `solve_uav` khi đổi số seed `n_seeds` (local search 50 vòng), mức 100%, ba instance cỡ nhỏ / vừa / lớn (trích từ `timing_seeds.csv`):

| Instance | `n`, `m` | 0 | 5 | 10 | 20 | 40 | 80 |
|---|---|---|---|---|---|---|---|
| 15699 | 403, 68 | 1,3 | 2,2 | 2,8 | 4,5 | 7,5 | 13,3 |
| 14881 | 647, 166 | 7,2 | 19,4 | 28,4 | 48,5 | 85,0 | 170,2 |
| 12078 | 1027, 285 | 15,4 | 50,2 | 78,2 | 125,2 | 222,1 | 417,1 |

Thời gian tăng **gần tuyến tính theo số seed** (ví dụ instance 12078: 20 → 40 → 80 seed là 125,2 → 222,1 → 417,1 ms, mỗi lần gấp đôi seed thì thời gian tăng khoảng 1,8 lần), đúng với `O(S · G)`. Phần local search rẻ: ở mục 3.1, `abl_no_ls` (34,7 ms) và `proposed` (36,7 ms) chỉ chênh khoảng 2 ms.

### 3.5. Đường cong thời gian so với chất lượng (số seed)

Tỉ lệ trung bình so với ILP trên 30 instance (local search 50 vòng), và thời gian trung bình của một lần giải:

| Số seed | Thời gian TB | 25% | 50% | 75% | 100% |
|---|---|---|---|---|---|
| 0 | 5,0 ms | 0,9722 | 0,9330 | 0,9389 | 0,9607 |
| 5 | 13,2 ms | 0,9838 | 0,9648 | 0,9628 | 0,9721 |
| 10 | 20,7 ms | 0,9849 | 0,9689 | 0,9672 | 0,9779 |
| **20 (mặc định)** | **35,2 ms** | **0,9872** | **0,9744** | **0,9689** | **0,9796** |
| 40 | 64,5 ms | 0,9900 | 0,9765 | 0,9714 | 0,9821 |
| 80 | 122,4 ms | 0,9898 | 0,9773 | 0,9736 | 0,9835 |

**Lợi ích giảm dần rõ rệt:** 5 seed đã cho phần lớn cải thiện (ở mức 50%: từ 0,9330 lên 0,9648, tức +3,2 điểm với +8 ms); từ 20 lên 80 seed (thêm 87 ms) chỉ thêm khoảng 0,3 đến 0,5 điểm. Giá trị mặc định 20 là điểm thỏa hiệp hợp lý, nhưng **chưa phải đã được tối ưu hóa**; 10 seed cho thời gian thấp hơn khoảng 41% và mất 0,2 đến 0,6 điểm.

### 3.6. Tăng quy mô instance (instance ngẫu nhiên tổng hợp)

Instance tổng hợp: bản đồ rủi ro ngẫu nhiên, K = 4, ngân sách mỗi UAV cố định 60 để giữ `k` gần hằng số (8 đến 12), `proposed` mặc định.

**Đổi `n`** (lưới 20×20, `m = 400`, tăng số route sinh mỗi UAV):

| `n` | 194 | 386 | 738 | 1381 | 2682 | 5184 | 9858 | 18841 |
|---|---|---|---|---|---|---|---|---|
| Thời gian (ms) | 19,0 | 41,1 | 70,3 | 117,1 | 294,9 | 595,7 | 1196,9 | 2310,8 |

Hệ số mũ log-log **`a = 1,06`** (thời gian ∝ `n^1,06`): gần tuyến tính, đúng dự đoán `O(n)` cho `k` gần hằng số. 18.841 route (lớn hơn khoảng 18 lần instance thật lớn nhất) vẫn chỉ mất 2,3 giây.

**Đổi `m`** (cố định 400 route mỗi UAV, `n ≈ 1380` đến `1420`, tăng lưới):

| `m` | 100 | 196 | 400 | 784 | 1600 | 3136 |
|---|---|---|---|---|---|---|
| Thời gian (ms) | 181,1 | 148,2 | 115,2 | 159,4 | 202,8 | 248,0 |

Hệ số mũ **`a = 0,12`**: gần như không phụ thuộc `m` (khi `n` và `k` gần như không đổi), đúng dự đoán vì `m` chỉ vào qua `W`. Dãy không đơn điệu (đầu dãy cao hơn) do `k` dao động (8 đến 12) và nhiễu đo, nên chỉ nên đọc là "phụ thuộc yếu".

### 3.7. ILP so với heuristic

Cấu hình chính, thời gian ILP là của lần chạy **cuối** (giới hạn 120 giây, hoặc 600 giây với 23 ca chạy lại):

| Mức | ILP trung bình | ILP trung vị | ILP lớn nhất | `proposed` trung bình | ILP / `proposed` (tỉ lệ trung bình) | Ca ILP hết giờ (`best-known`) |
|---|---|---|---|---|---|---|
| 25% | 0,3 giây | 0,08 giây | 2 giây | 10,8 ms | 29× | 0/30 |
| 50% | 100,8 giây | 0,61 giây | 601 giây | 31,5 ms | 3.202× | 5/30 |
| 75% | 177,2 giây | 15,7 giây | 601 giây | 47,2 ms | 3.751× | 8/30 |
| 100% | 170,7 giây | 17,7 giây | 601 giây | 58,0 ms | 2.942× | 7/30 |

Tổng cộng: ILP **3,74 giờ CPU**, `proposed` **4,4 giây** cho 120 lần giải; tỉ lệ khoảng **3.000×**. Đây là **cận dưới** của độ chênh, vì ILP bị cắt bởi giới hạn thời gian (20 ca vẫn chưa chứng minh được tối ưu).

**Thời gian ILP phụ thuộc mạnh vào kích thước và mức ngân sách:**
- Hệ số tương quan hạng Spearman giữa thời gian ILP và `m`: 0,91 (50%), 0,88 (75%), 0,92 (100%); với `n`: 0,77 ở cả ba mức; với `R`: 0,84 đến 0,93.
- Ca ILP chỉ đạt `best-known` có `m` trung bình **245** và `n` trung bình **920**, so với **131** và **629** ở ca `optimal`.
- Mức 25% giải rất nhanh vì pin quá nhỏ (nhiều UAV không bay được), nên nhánh-cận cắt gần hết.

**So với Phase 1** (OR-Library, `n` 1000 đến 4000, `m` 200 đến 400): ILP trung bình 0,89 giây, lớn nhất 14,3 giây; `greedy_ls` trung bình 41 ms, lớn nhất 147 ms. ILP của Phase 2 khó hơn nhiều dù `n` nhỏ hơn: ràng buộc pin riêng từng UAV (nhiều knapsack) và trọng số làm nới lỏng LP yếu đi.

### 3.8. Chi phí chuẩn bị (không tính vào thời gian "giải")

- Risk map: khoảng 0,14 giây cho một ảnh (đọc mask và `cell_risk`, đo ở bước đầu).
- Sinh route (4 UAV, 300 route mỗi UAV): khoảng 0,03 giây cho một instance.
- Chi phí tham chiếu `R` (ILP set cover): bước `build` cho 30 instance mất khoảng 2 phút (khoảng 4 giây mỗi instance), gần như toàn bộ là ILP này; riêng cấu hình `tree1` (nhiều ô hơn) mất khoảng 20 phút.

## 4. Diễn giải

1. **Thời gian heuristic gần tuyến tính theo `n`** (`a = 1,06`) và gần như độc lập với `m` (`a = 0,12`), đúng như phân tích lý thuyết `O((1 + S + r·k)·n·L·W)`. Nên mở rộng sang bài toán lớn hơn rất khả thi: 18.841 route vẫn dưới 2,5 giây.
2. **Thời gian bị chi phối bởi seed**, không phải local search hay lazy evaluation. Đây là chỗ cần chỉnh nếu muốn nhanh hơn: giảm từ 20 xuống 10 seed tiết kiệm khoảng 40% thời gian với mức mất chất lượng nhỏ.
3. **Lazy evaluation (CELF) giúp khoảng 2 lần**, ít hơn kỳ vọng "nhanh hơn rất nhiều", vì `k` nhỏ và phần khởi tạo `n` lần đánh giá là chi phí chính.
4. **Đánh đổi chất lượng và thời gian:** `proposed` đạt 0,969 đến 0,987 so với ILP trong khoảng 11 đến 58 ms, trong khi ILP mất hàng chục đến hàng trăm giây (khoảng 3.000 lần) và có ca không chứng minh được tối ưu. Với tình huống cứu hộ cần ra quyết định nhanh (đã nêu trong brief), đánh đổi này hợp lý. Tuy vậy vẫn còn khoảng 1 đến 3 điểm phần trăm so với tối ưu.
5. **`naive` chậm hơn `proposed` khoảng 1,6 lần** (58,1 ms so với 36,7 ms) dù đơn giản về ý tưởng, vì ngân sách chung cho lời giải nhiều route hơn nên greedy và local search chạy nhiều bước hơn.

## 5. Những điều không nên khẳng định

- **Không khẳng định độ chênh 3.000× là cố định**: chỉ là cận dưới trên 30 instance này và phụ thuộc giới hạn thời gian, mức ngân sách, và việc ILP ở đây giải mô hình khá yếu (chưa có bước tiền xử lý như loại route bị trội).
- **Không so sánh công bằng tuyệt đối giữa hai ngôn ngữ/cài đặt**: heuristic là Python thuần (số nguyên lớn làm mask bit), ILP là CBC (C++) cùng chi phí tạo mô hình PuLP và ghi/đọc file trung gian (có thể vài chục ms, thấy rõ ở mức 25% với trung vị 0,08 giây).
- **Không rút ra "độ phức tạp thực nghiệm" từ chỉ ba bộ số đo**: hệ số mũ 1,06 và 0,12 là hệ số hồi quy trên 6 đến 8 điểm của instance ngẫu nhiên, không phải chứng minh.

## 6. Hạn chế của các số đo

1. Đo trên một máy, một luồng, có tải nền nhẹ; chỉ lấy giá trị nhỏ nhất của 3 lần (`--repeats`), chưa có khoảng tin cậy. Chạy lại script cho kết quả sai khác ở mức nhiễu đo (ví dụ hệ số mũ 1,05 và 1,06 giữa hai lần chạy).
2. Instance tổng hợp ở mục 3.6 dùng bản đồ rủi ro ngẫu nhiên và ngân sách cố định (60 mỗi UAV), chỉ để xem xu hướng.
3. Không đo bộ nhớ, và chưa đo `n` vượt 18.841 hoặc `K` khác 4.
4. Thời gian ILP của cấu hình chính gồm hai lượt giới hạn khác nhau (120 và 600 giây); thời gian ILP của các cấu hình sensitivity chỉ 120 giây.
5. Chưa phân tích bộ nhớ lý thuyết ngoài vài ghi chú (`O(n·W)` cho các mask, `O(P)` cho risk map).
6. Số đo ILP (mục 3.7) là thời gian một lần chạy được ghi lúc giải, không lặp lại nhiều lần.

## 7. Tái lập

```bash
python pipeline/12_timing_rn.py lazy      # mục 3.3  -> data/rescuenet/g20_default/timing_lazy.csv
python pipeline/12_timing_rn.py runs      # mục 3.2  -> timing_runs.csv
python pipeline/12_timing_rn.py seeds     # mục 3.4, 3.5 -> timing_seeds.csv
python pipeline/12_timing_rn.py scale     # mục 3.6  -> data/rescuenet/timing_scale.csv
```

Mục 3.1 (thời gian từng thuật toán) và 3.7 (ILP so với heuristic) tính từ `solve_time_seconds` trong `data/rescuenet/g20_default/results/*/*.json` (cũng có trong cột `time_seconds` của `summary.csv`). Riêng bảng đo lại 3.1 (nhỏ nhất của 3 lần) do một script tạm; số ghi sẵn trong file kết quả khớp với nó (ví dụ `proposed` 11 / 31 / 47 / 58 ms theo mức).

## 8. Thời gian trên lần chạy đầy đủ 350 ảnh (`full_g20_default`, 1400 lần giải mỗi thuật toán)

Lấy từ `solve_time_seconds` trong file kết quả (một lần chạy, không lặp; `proposed`, `naive` và ablation chạy song song 5 tiến trình trên máy nhiều nhân nên có thể nhiễu hơn bảng đo ở mục 3.1):

| Thuật toán | Trung bình | Lớn nhất |
|---|---|---|
| `abl_ratio_only` | 3,2 ms | 11 ms |
| `abl_no_seed` | 7,4 ms | 60 ms |
| `abl_no_ls` | 43,9 ms | 226 ms |
| **`proposed`** | **46,4 ms** | **245 ms** |
| `naive` | 66,5 ms | 294 ms |

ILP (giới hạn 120 giây, không chạy lại): trung bình 3,2 / 42,2 / 60,0 / 66,2 giây và trung vị 0,13 / 3,15 / 51,1 / 69,3 giây ở mức 25 / 50 / 75 / 100%; lớn nhất đều chạm 120 giây. Tổng **16,7 giờ CPU** (chia 10 tiến trình, khoảng 2 giờ thực) so với **65 giây** của `proposed`: tỉ lệ khoảng **924 lần**.

Tỉ lệ 924 lần **thấp hơn** con số khoảng 3000 lần ở mục 3.7 một phần vì lần chạy đầy đủ chỉ dùng giới hạn 120 giây, còn lần 30 ảnh có 23 ca được chạy lại 600 giây (tập instance cũng khác nhau, chưa tách riêng được từng nguyên nhân). Cả hai đều chỉ là **cận dưới** của độ chênh (ILP bị cắt bởi giới hạn thời gian; 393/1400 ca chưa chứng minh được tối ưu). Thời gian `proposed` trung bình 46,4 ms (so với 36,7 ms ở mục 3.1) có thể do `n` trung bình lớn hơn một chút (719 so với 678) và do các thuật toán chạy song song nên nhiễu hơn; chưa tách riêng hai nguyên nhân.

