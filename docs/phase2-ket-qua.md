# Pha 2: kết quả thực nghiệm RescueNet multi-UAV

> Số liệu dán **nguyên từ output** của `pipeline/11_summarize_rn.py` (chạy 07 và 08/10/2026). Không số nào viết tay. Thiết kế và lý do các lựa chọn: `docs/phase2-rescuenet-thiet-ke.md`; cách chạy: `docs/huong-dan-chay.md`; định dạng dữ liệu: `docs/mo-hinh-du-lieu.md` mục 8.

> Phân tích thời gian chạy (Big-O lý thuyết và đo thực tế) nằm ở `docs/phase2-thoi-gian-chay.md`.

## 1. Cách đọc các bảng

- **Tỉ lệ** = `objective` của thuật toán / `objective` của ILP trên cùng instance và mức ngân sách. `objective` là **tổng điểm rủi ro** ô được phủ. Giá trị trong bảng là **trung bình trên các instance**; `n` là số instance dùng được.
- **`n` có thể nhỏ hơn 30** vì instance có ILP tối ưu bằng 0 (ở mức pin thấp không UAV nào đủ pin bay route nào) bị loại khỏi tỉ lệ. Ví dụ lưới 10×10 ở 25%: n = 20.
- **ILP `best-known`**: CBC hết giờ, chưa chứng minh tối ưu, nên tỉ lệ so với nghiệm tốt nhất ILP tìm được và **có thể > 1** (đã xảy ra, xem mục 4).
- **Thắng/hòa/thua** là số instance mà `proposed` > / ≈ / < thuật toán so sánh (dung sai 1e-9). **Wilcoxon** hai phía ghép cặp theo instance (cả hai thuật toán đều deterministic nên n = số instance, không phải số seed).
- **Kết quả chính (mục 2) chạy trên 350 ảnh**: toàn bộ ảnh của tập validation RescueNet có ít nhất 60 ô điểm > 0 (350/449). Không phải mẫu ngẫu nhiên: 99 ảnh còn lại bị loại vì quá ít ô để phủ (45 ảnh không có ô nào). Các phần ablation chi tiết, sensitivity (mục 3b, 4) dùng **lần chạy thử 30 ảnh phân tầng** (seed 2026, 10 ảnh mỗi tầng; cả 30 ảnh đều nằm trong 350). P-value nhỏ cho thấy chênh lệch ổn định *trên các ảnh này*, không phải xác suất tổng quát cho mọi tình huống RescueNet.

## 2. Kết quả chính: toàn bộ 350 ảnh đủ điều kiện (`full_g20_default`: lưới 20×20, Tree = 0, K = 4 UAV)

350 instance × 4 mức ngân sách = 1400 lần giải cho mỗi thuật toán. Quy mô instance: `m` từ 61 đến 400 (trung bình 174), `n` từ 251 đến 1097 (trung bình 719), `R` từ 86 đến 720. Chia theo mức hư hại (tam phân vị trong 350 ảnh): 116 thấp, 116 vừa, 118 cao. Validator: **8400 file kết quả, 0 lỗi**.

**Trạng thái ILP** (giới hạn 120 giây, **không** chạy lại 600 giây): 1007 `optimal`, **393 `best-known`** (28%). Theo mức ngân sách (optimal / best-known): 25%: 344 / 6; 50%: 251 / 99; 75%: 218 / 132; 100%: 194 / 156. Các ca `best-known` có `m` trung bình 249, các ca `optimal` có `m` trung bình 145. Một ca ở mức 25% có tối ưu ILP bằng 0 (bị loại khỏi tỉ lệ, nên n = 349 ở mức đó).

Tỉ lệ objective so với ILP, trung bình (nhỏ nhất trong ngoặc):

| Mức | `proposed` | `naive` | n |
|---|---|---|---|
| 25% | 0.9839 (0.8815) | 0.9328 (0.3689) | 349 |
| 50% | 0.9706 (0.8619) | 0.9084 (0.6594) | 350 |
| 75% | 0.9728 (0.8897) | 0.9211 (0.6722) | 350 |
| 100% | 0.9843 (0.9054) | 0.9410 (0.6941) | 350 |

`proposed` so với `naive`, theo instance:

| Mức | Thắng/hòa/thua | Wilcoxon p |
|---|---|---|
| 25% | 265 / 83 / 1 | 4.511e-45 |
| 50% | 321 / 23 / 6 | 8.208e-55 |
| 75% | 333 / 6 / 11 | 1.251e-56 |
| 100% | 334 / 1 / 15 | 3.894e-57 |

**Tách theo trạng thái ILP** (tỉ lệ trung bình `proposed` / `naive`):

| Mức | ILP `optimal` (n) | ILP `best-known` (n) |
|---|---|---|
| 25% | 0.9838 / 0.9324 (343) | 0.9867 / 0.9566 (6) |
| 50% | 0.9715 / 0.9013 (251) | 0.9682 / 0.9265 (99) |
| 75% | 0.9702 / 0.9079 (218) | 0.9772 / 0.9429 (132) |
| 100% | 0.9787 / 0.9222 (194) | 0.9913 / 0.9645 (156) |

**Heuristic vượt ILP:** chỉ xảy ra ở các ca ILP `best-known` (`proposed` 38 lần, `naive` 11 lần trên 1400), lớn nhất 1.0391; **không lần nào vượt ILP `optimal`** (validator kiểm tra mọi file). Nghĩa là ILP `best-known` không phải cận trên, và tỉ lệ ở các ca đó chỉ là so với nghiệm tốt nhất ILP tìm được.

**Ablation trên 350 ảnh** (tỉ lệ trung bình; `proposed` đầy đủ so với bản bỏ bớt: thắng / hòa / thua):

| Biến thể | 25% | 50% | 75% | 100% |
|---|---|---|---|---|
| `abl_ratio_only` | 0.9456 | 0.9190 | 0.9301 | 0.9545 |
| `abl_no_seed` | 0.9587 | 0.9367 | 0.9451 | 0.9670 |
| `abl_no_ls` | 0.9793 | 0.9630 | 0.9672 | 0.9809 |
| `proposed` | 0.9839 | 0.9706 | 0.9728 | 0.9843 |
| `naive` | 0.9328 | 0.9084 | 0.9211 | 0.9410 |

| So với | 25% | 50% | 75% | 100% |
|---|---|---|---|---|
| `abl_no_ls` | 100/249/0 | 192/158/0 | 237/113/0 | 249/101/0 |
| `abl_no_seed` | 203/142/4 | 283/57/10 | 301/29/20 | 312/19/19 |
| `abl_ratio_only` | 257/92/0 | 326/24/0 | 338/12/0 | 347/3/0 |

(Mọi p-value Wilcoxon của ablation nằm trong khoảng 1e-18 đến 1e-58.) Kết luận ablation giống lần chạy thử 30 ảnh: mỗi thành phần đều đóng góp, bỏ **seed** mất nhiều hơn bỏ **local search**, và riêng ratio greedy per-UAV (`abl_ratio_only`) chỉ hơn `naive` khoảng 0.9 đến 1.4 điểm phần trăm.

**Theo mức hư hại của ảnh** (tỉ lệ trung bình so với ILP, gộp 4 mức; `proposed` / `naive`): thấp 0.9807 / 0.9217 (n = 463), vừa 0.9778 / 0.9277 (n = 464), cao 0.9752 / 0.9281 (n = 472). Không có khác biệt lớn giữa các tầng.

**Ca ngoại lệ:** `naive` đạt thấp nhất 0.3689 ở ảnh 11511 (mức 25%, tầng vừa, `m` = 91, `n` = 399), nơi `proposed` đạt 1.0000 so với ILP `optimal`.

**So với lần chạy thử 30 ảnh** (`proposed` / `naive` ở 25 / 50 / 75 / 100%): 30 ảnh cho 0.987 / 0.974 / 0.969 / 0.980 và 0.938 / 0.898 / 0.909 / 0.922; 350 ảnh cho 0.984 / 0.971 / 0.973 / 0.984 và 0.933 / 0.908 / 0.921 / 0.941. Chênh nhau tối đa khoảng 2 điểm phần trăm, **kết luận không đổi**.

**Thời gian** (xem `docs/phase2-thoi-gian-chay.md` mục 8): `proposed` trung bình 46,4 ms, lớn nhất 245 ms; `naive` 66,5 ms, lớn nhất 294 ms; ILP trung bình 3,2 / 42,2 / 60,0 / 66,2 giây theo mức 25 / 50 / 75 / 100% (nhiều ca chạm giới hạn 120 giây), tổng 16,7 giờ CPU so với 65 giây của `proposed`.

## 2b. Lần chạy thử trên 30 ảnh phân tầng (`g20_default`: lưới 20×20, Tree = 0, K = 4 UAV)

ILP: 100/120 `optimal`, 20/120 `best-known` (giới hạn 120 giây, ca chưa tối ưu chạy lại 600 giây). Mức 25%: 30/30 optimal; mức 50%: 5, 75%: 8, 100%: 7 ca best-known.

| Mức | `proposed` | `naive` (ngân sách chung + sửa + lấp lại) | n |
|---|---|---|---|
| 25% | 0.9872 | 0.9382 | 30 |
| 50% | 0.9744 | 0.8976 | 30 |
| 75% | 0.9689 | 0.9085 | 30 |
| 100% | 0.9796 | 0.9218 | 30 |

Giá trị nhỏ nhất của `proposed`: 0.9324 / 0.9042 / 0.8897 / 0.9243; của `naive`: 0.7649 / 0.7178 / 0.7923 / 0.7547 (mức 25 / 50 / 75 / 100%).

`proposed` so với `naive`, theo instance:

| Mức | Thắng/hòa/thua | Wilcoxon p (n = 30) |
|---|---|---|
| 25% | 19 / 11 / 0 | 1.318e-04 |
| 50% | 25 / 3 / 2 | 9.843e-06 |
| 75% | 29 / 1 / 0 | 2.563e-06 |
| 100% | 28 / 0 / 2 | 1.863e-08 |

Có 4 ca `naive` tốt hơn `proposed` (2 ở mức 50%, 2 ở mức 100%): `proposed` không thống trị tuyệt đối.

## 3. Ablation trên 30 ảnh (`g20_default`)

Tỉ lệ trung bình so với ILP (n = 30):

| Biến thể | 25% | 50% | 75% | 100% |
|---|---|---|---|---|
| `abl_ratio_only` (chỉ ratio greedy per-UAV + gói đơn tốt nhất) | 0.9631 | 0.9150 | 0.9147 | 0.9492 |
| `abl_no_seed` (có local search, không seed) | 0.9722 | 0.9330 | 0.9389 | 0.9607 |
| `abl_no_ls` (có seed, không local search) | 0.9822 | 0.9632 | 0.9610 | 0.9752 |
| `proposed` (đầy đủ) | 0.9872 | 0.9744 | 0.9689 | 0.9796 |
| `naive` (để so) | 0.9382 | 0.8976 | 0.9085 | 0.9218 |

`proposed` đầy đủ so với từng bản bỏ bớt (thắng/hòa/thua, Wilcoxon p):

| Bản bỏ bớt | 25% | 50% | 75% | 100% |
|---|---|---|---|---|
| `abl_no_ls` | 9/21/0, p=7.686e-03 | 18/12/0, p=1.964e-04 | 21/9/0, p=5.957e-05 | 23/7/0, p=2.702e-05 |
| `abl_no_seed` | 14/16/0, p=9.815e-04 | 25/5/0, p=1.229e-05 | 25/3/2, p=1.228e-05 | 28/0/2, p=2.552e-07 |
| `abl_ratio_only` | 18/12/0, p=1.964e-04 | 26/4/0, p=8.298e-06 | 30/0/0, p=1.863e-09 | 30/0/0, p=1.863e-09 |

**Diễn giải (từ các số trên):**
- Mỗi thành phần đều đóng góp: `proposed` thắng hoặc hòa mọi bản bỏ bớt ở mọi mức (trừ 2 ca ở mỗi mức 75% và 100% mà bản bỏ seed lại tốt hơn).
- Bỏ **seed** làm mất nhiều hơn bỏ **local search** (ở 50%: 0.9330 so với 0.9632, nghĩa là đầy đủ 0.9744 hơn lần lượt 4.1 và 1.1 điểm phần trăm).
- Chỉ riêng việc xét pin theo từng UAV lúc chọn (`abl_ratio_only`) hơn `naive` ở cả 4 mức (0.9631 vs 0.9382, 0.9150 vs 0.8976, 0.9147 vs 0.9085, 0.9492 vs 0.9218), nhưng chênh lệch nhỏ ở mức 75% (0.6 điểm). **Phần lớn cải thiện của `proposed` so với `naive` đến từ seed và local search**, không chỉ từ việc xét ngân sách riêng. `naive` cũng dùng seed và local search, nhưng ở pha ngân sách chung.

## 4. Sensitivity: kết luận có phụ thuộc bảng điểm / lưới không?

Cùng 30 ảnh (trừ ghi chú), đổi một thông số. Tỉ lệ trung bình so với ILP (`proposed` / `naive`):

| Cấu hình | n | 25% | 50% | 75% | 100% |
|---|---|---|---|---|---|
| `g20_default` | 30 | 0.9872 / 0.9382 | 0.9744 / 0.8976 | 0.9689 / 0.9085 | 0.9796 / 0.9218 |
| `g20_tree1` (Tree = 1) | 30 | 0.9801 / 0.9303 | 0.9727 / 0.9248 | 0.9757 / 0.9341 | 0.9889 / 0.9550 |
| `g20_convex` (điểm 1/4/9) | 30 | 0.9846 / 0.9366 | 0.9834 / 0.9071 | 0.9741 / 0.9188 | 0.9821 / 0.9298 |
| `g20_damage_only` | 14/18/20/20 | 0.9978 / 0.9770 | 0.9870 / 0.9394 | 0.9772 / 0.9054 | 0.9834 / 0.9229 |
| `g10_default` (lưới 10×10) | 20/29/30/30 | 1.0000 / 0.9993 | 0.9887 / 0.9479 | 0.9697 / 0.8876 | 0.9782 / 0.8626 |

(`n` theo thứ tự mức 25/50/75/100% khi khác nhau. `damage_only` bỏ 8/30 ảnh, tất cả thuộc tầng hư hại thấp, vì không còn ô điểm > 0.)

`proposed` so với `naive` (thắng/hòa/thua; p < 0.05 ở mọi ô trừ ô được ghi chú):

| Cấu hình | 25% | 50% | 75% | 100% |
|---|---|---|---|---|
| `g20_tree1` | 24/6/0, p=1.822e-05 | 27/1/2, p=8e-06 | 27/1/2, p=3.902e-06 | 28/0/2, p=3.539e-08 |
| `g20_convex` | 18/11/1, p=1.822e-04 | 27/3/0, p=5.606e-06 | 29/1/0, p=2.563e-06 | 30/0/0, p=1.863e-09 |
| `g20_damage_only` | 5/9/0, p=0.04311 | 13/5/0, p=1.474e-03 | 14/6/0, p=9.815e-04 | 17/3/0, p=2.931e-04 |
| `g10_default` | 1/19/0, **p=0.3173** | 16/13/0, p=4.378e-04 | 22/7/1, p=3.088e-05 | 29/1/0, p=2.563e-06 |

**Kết luận từ các số trên:** `proposed` ≥ `naive` ở mọi cấu hình và mọi mức về trung bình; thứ tự hai thuật toán không đổi khi đổi bảng điểm hoặc lưới. Ngoại lệ đáng nêu: lưới 10×10 ở mức 25% hai thuật toán gần như bằng nhau (1/19/0, p = 0.3173, không khác biệt đáng kể).

**Cảnh báo về ILP trong sensitivity (chỉ chạy lượt 120 giây, không chạy lại 600 giây):**

| Cấu hình | `best-known` / tổng ca ILP |
|---|---|
| `g20_tree1` | 56 / 120 (mức 50%: 17, 75%: 19, 100%: 20) |
| `g20_convex` | 21 / 120 (50%: 5, 75%: 7, 100%: 9) |
| `g10_default` | 1 / 120 (100%: 1) |
| `g20_damage_only` | 0 / 88 |

- Ở `tree1` ILP yếu rõ rệt (nhiều ô điểm > 0 hơn, m lớn hơn), nên gap ở đó là gap so với nghiệm tốt nhất ILP tìm được, **không phải** so với tối ưu.
- **Tỉ lệ > 1 đã xảy ra**: `proposed` ở `tree1` có tỉ lệ lớn nhất 1.0157 (mức 100%), 1.0084 (mức 50%); ở `convex` 1.0145 (mức 50%); `naive` ở `tree1` 1.0070 (mức 100%). Nghĩa là heuristic tìm được nghiệm tốt hơn nghiệm ILP best-known; **ILP best-known không phải cận trên**. Không ca nào ILP `optimal` bị heuristic vượt (validator kiểm tra mọi file).

## 5. Giới hạn cần nêu trong báo cáo

1. **Instance tổng hợp.** Route, pin, K = 4 UAV và công thức ngân sách do nhóm thiết kế; chỉ bản đồ rủi ro dựa trên nhãn thật của RescueNet (tập validation).
2. **Mức pin thấp khắc nghiệt.** Trên 30 ảnh `g20_default` (chưa đo lại cho 350 ảnh), số cặp (instance, UAV) có pin nhỏ hơn route rẻ nhất của chính UAV đó: 28/120 ở mức 25%, 9 ở 50%, 3 ở 75%, 1 ở 100%.
3. **ILP không phải luôn tối ưu** (mục 2 và 4): trên 350 ảnh có 393/1400 ca (28%) chỉ `best-known` sau 120 giây, tập trung ở `m` lớn và mức ngân sách cao (156/350 ở mức 100%). Mọi tỉ lệ ở các ca `best-known` là so với best-known và có thể > 1.
4. **Chọn ảnh:** kết quả chính dùng mọi ảnh có ít nhất 60 ô điểm > 0 (350/449); 99 ảnh bị loại vì quá ít ô. Nhóm hư hại suy từ mask (tập validation không có nhãn 0/1/2). Chỉ dùng tập validation, không có tập test độc lập. Các kết quả ablation chi tiết và sensitivity (mục 3, 4) chỉ chạy trên 30 ảnh.
5. **Baseline `naive` đã được sửa** thêm bước lấp lại pin dư sau khi bản đầu (chỉ bỏ route) cho thấy quá yếu (0.15 đến 0.71 so với ILP); số liệu trong tài liệu này là của bản đã sửa.
6. **Chi phí tham chiếu `R`** do CBC giới hạn 120 giây có thể là cận trên khi hết giờ; chỉ ảnh hưởng thang ngân sách, dùng chung cho mọi thuật toán.
7. **Khoảng cách tuyệt đối khiêm tốn:** trên 350 ảnh, `proposed` hơn `naive` khoảng 4,3 đến 6,2 điểm phần trăm và còn kém ILP khoảng 1,6 đến 2,9 điểm (tính trên tỉ lệ trung bình, gồm cả ca ILP `best-known`).

## 6. Tái lập

```bash
python pipeline/07_rn_prepare.py select
python pipeline/07_rn_prepare.py build                                  # g20_default
python pipeline/08_ilp_uav.py                                           # ILP, 120 giây
python pipeline/09_greedy_uav.py --algorithm proposed
python pipeline/09_greedy_uav.py --algorithm naive
python pipeline/09_greedy_uav.py --algorithm proposed --name abl_no_ls --ls-rounds 0
python pipeline/09_greedy_uav.py --algorithm proposed --name abl_no_seed --seeds 0
python pipeline/09_greedy_uav.py --algorithm proposed --name abl_ratio_only --seeds 0 --ls-rounds 0
python pipeline/10_validate_uav.py
python pipeline/11_summarize_rn.py
# sensitivity: build --table tree1|convex|damage_only  hoặc  build --grid 10, rồi 08–11 với --tag g20_<bảng> / g10_default
```

Ca ILP `best-known` của `g20_default` được chạy lại với `--time-limit 600 --instances <id> --levels <mức>`.

**Chạy đầy đủ trên 350 ảnh** (tag `full_g20_default`; instance và kết quả từng ảnh bị `.gitignore` chặn vì dung lượng, chỉ `selection_all.json`, `skipped_*.json` và `summary.csv` được lưu trong git):

```bash
python pipeline/07_rn_prepare.py select --all                           # -> data/rescuenet/selection_all.json
for k in 0 1 2 3 4 5 6 7 8 9; do                                        # build song song 10 phần
  python pipeline/07_rn_prepare.py build --selection selection_all.json --tag full_g20_default --shard $k/10 &
done; wait
python pipeline/09_greedy_uav.py --algorithm proposed --tag full_g20_default      # và naive, abl_* như trên
python pipeline/08_ilp_uav.py --tag full_g20_default --instances <danh sách>      # chia thành ~10 phần chạy song song, ~2 giờ
python pipeline/10_validate_uav.py --tag full_g20_default
python pipeline/11_summarize_rn.py --tag full_g20_default
```

