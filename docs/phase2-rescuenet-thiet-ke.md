# Thiết kế Pha 2: instance RescueNet và mô hình multi-UAV

> **Trạng thái: BẢN NHÁP, chờ duyệt** (soạn 07/10/2026). Mục đích: ghi lại **lý do** của từng lựa chọn thiết kế để trả lời khi bị hỏi lúc báo cáo. Mỗi lựa chọn có: lý do, điểm yếu thừa nhận, và thí nghiệm nhạy cảm (sensitivity) dùng để bảo vệ. Các lựa chọn đánh dấu **[CHỜ DUYỆT]** là đề xuất, chưa được chốt.

## 0. Nguyên tắc trung thực (nói thẳng khi bị hỏi)

- RescueNet **không có** khái niệm UAV, pin, route, risk score, hay đáp án tối ưu. Toàn bộ ánh xạ dưới đây là **mô hình tổng hợp do nhóm tự thiết kế**, dựa trên nhãn thật của RescueNet. Báo cáo phải gọi đây là *synthetic instances built from real RescueNet labels*, không phải "dữ liệu cứu hộ thực".
- Các hằng số (kích thước lưới, bảng điểm, số instance, K, pin) là **lựa chọn có lý do, không phải chân lý**. Cách bảo vệ đúng là **chạy sensitivity** và cho thấy kết luận so sánh thuật toán không đổi, chứ không phải chứng minh rằng con số đó "đúng".

## 1. Dữ liệu đã có (đã kiểm chứng ngày 07/10/2026)

`data/RescueNet/segmentation-validationset/` là **tập validation của RescueNet**:
- 449 ảnh gốc `.jpg` + 449 mask `.png`, ghép cặp khớp theo tên (`14238.jpg` ↔ `14238_lab.png`); số 449 trùng kích thước tập validation trong bài báo.
- Ảnh 4000×3000 (một số ít 4056×3040), EXIF DJI FC220, chụp 13/10/2018 (sau Hurricane Michael).
- Mask grayscale 8-bit, giá trị 0–10 đủ 11 lớp → **không cần đổi màu RGB sang nhãn**.
- **Không có** train/test và **không có** CSV nhãn phân loại ảnh (0/1/2) → mức hư hại của từng ảnh phải **suy từ mask** (mục 4).
- Thư mục 2.3 GB, chưa nằm trong `.gitignore` (nên ignore; chỉ commit instance đã sinh).

Đo trên 449 mask (downsample ×4):
- 70.6% ảnh có ít nhất một công trình (nhãn 2–5).
- 44.3% ảnh có pixel hư hại nặng (nhãn 4, 5, 8); 57.9% có hư hại từ mức trung bình (nhãn 3, 4, 5, 8).
- **Trung vị tỉ lệ pixel hư hại nặng của một ảnh = 0.** Hơn một nửa ảnh gần như không có hư hại nặng.
- Phân bố pixel toàn cục (mẫu 45 ảnh): Background 55.7%, Tree 19.3%, Water 7.2%, Road-Clear 6.2%, các lớp công trình 2–5 cộng lại khoảng 9.2%, Road-Blocked 1.9%.

## 1b. Hai bước tách biệt: risk map và sinh instance

Hai bước trả lời hai câu hỏi khác nhau: *"khu vực này nguy hiểm chỗ nào?"* (risk map) và *"UAV có thể bay những đường nào để phủ chỗ đó?"* (sinh instance).

**Bước risk map** (`pipeline/rn/risk.py`): ảnh → bảng điểm.
- Đầu vào: một mask 4000×3000, mỗi pixel là một nhãn 0–10.
- Việc làm: đổi nhãn thành điểm bằng bảng điểm (mục 3), chia ảnh thành lưới `G×G`, lấy điểm trung bình của pixel trong mỗi ô.
- Đầu ra: bảng `G×G` số thực "ô này nguy hiểm bao nhiêu". Chưa có UAV, đường bay hay pin.

Ví dụ: mask 4×4, lưới 2×2, mỗi ô 2×2 pixel.

```
Mask (nhãn)         Điểm theo pixel       Risk map (trung bình mỗi ô)
5 0 | 0 0           3 0 | 0 0
5 0 | 0 0           3 0 | 0 0             1.5  0.0
----+----           ----+----             0.0  3.0
0 0 | 4 4           0 0 | 3 3
0 0 | 4 4           0 0 | 3 3
```

Ô trên-trái: 2 pixel nhãn 5 (3 điểm) + 2 pixel nền (0 điểm) → trung bình 1.5. Ô dưới-phải toàn nhãn 4 → 3.0.

**Bước sinh instance** (`pipeline/rn/routes.py`, `budgets.py`): bảng điểm → bài toán tối ưu. Risk map chưa phải một bài toán; cần có "ô cần phủ", "gói", "chi phí", "ngân sách" như file OR-Library của Pha 1.

| Thành phần của bài toán | Lấy từ đâu |
|---|---|
| Ô cần phủ (universe) và trọng số | Các ô của risk map có điểm > 0; điểm của ô là trọng số |
| Gói (route) | **Sinh ra**: đường đi liền mạch trên lưới từ điểm xuất phát của một UAV; phủ các ô điểm > 0 nó đi qua |
| Chi phí gói | Chi phí cất cánh + số ô đi qua |
| Chủ của gói | UAV mà route xuất phát (điểm khác Pha 1) |
| Ngân sách | Pin riêng từng UAV, tính từ `R` (chi phí tối thiểu để phủ hết) và hệ số chia `share_u` |

Tiếp ví dụ trên: universe có 2 ô (trọng số 1.5 và 3.0; hai ô điểm 0 bị loại). UAV 0 xuất phát ở góc trên-trái; một route của nó đi qua (0,0) → (0,1) → (1,1), phủ cả hai ô, chi phí 2 + 3 = 5, thuộc UAV 0.

**Vì sao tách hai bước:**
1. Các lựa chọn thiết kế nằm ở hai chỗ khác nhau: lưới và bảng điểm thuộc bước 1; số UAV, độ dài route, công thức pin thuộc bước 2. Tách ra thì sensitivity dễ: đổi bảng điểm hay lưới chỉ cần chạy lại từ bước 1.
2. Test độc lập: risk map test bằng mask 4×4 tự dựng, không cần route; sinh instance test bằng bảng điểm tự viết, không cần ảnh thật.
3. Dễ trả lời khi bị hỏi: "bản đồ rủi ro từ đâu?" là bước 1; "đường bay và ngân sách từ đâu?" là bước 2.

Tương ứng với Pha 1: risk map cho ra `m` và `weights`; sinh instance cho ra `n`, `costs`, `sets` và thêm `route_uav`. Gộp lại có một file giống `scp41.json` cộng trọng số và chủ của route.

## 2. Kích thước lưới: G×G = 20×20 → m = 400 ô tối đa **[CHỜ DUYỆT]**

**Lý do:**
1. **So sánh được với Pha 1.** Các instance OR-Library lớn nhất có m = 200–400 ô (scp4–scpd). Lưới 20×20 cho m ≤ 400 nên ILP giải được trong thời gian tương đương Pha 1, và nhận xét "heuristic vs ILP" cùng thang đo.
2. **Đủ mịn để định vị hư hại.** Ô 200×150 pixel (30.000 pixel) đủ nhỏ để một công trình hư hại hay một đoạn đường bị chặn chiếm phần đáng kể của ô, nhưng đủ lớn để mỗi ô gom nhiều pixel và bớt nhiễu nhãn. (Chưa biết độ phân giải mặt đất GSD thật, **không** quy ra mét trong báo cáo.)
3. **Giữ số route ứng viên và ILP ở mức kiểm soát được.** Lưới 40×40 (1600 ô) làm số route và kích thước ILP tăng mạnh.

**Điểm yếu:** 20 là con số chọn, không suy ra từ dữ liệu. Sau khi lọc ô điểm 0, m thực tế chỉ còn khoảng 44–220 tùy bảng điểm (mục 3), nhỏ hơn OR-Library.

**Bảo vệ:** chạy sensitivity G ∈ {10, 20} trên toàn bộ instance, và G = 40 trên một tập con nhỏ nếu ILP kịp. Báo cáo: xếp hạng thuật toán và gap có giữ nguyên không.

## 3. Điểm rủi ro theo lớp nhãn **[CHỜ DUYỆT]**

Bảng đề xuất (khác proposal ở chỗ **Tree = 0**):

| Điểm | Lớp nhãn | Lý do |
|---|---|---|
| 3 | Building-Major-Damage (4), Building-Total-Destruction (5), Road-Blocked (8) | Cần cứu hộ/khảo sát gấp nhất: công trình hư hại nặng/sập có thể có người mắc kẹt; đường bị chặn cản trở lực lượng tiếp cận. |
| 2 | Building-Minor-Damage (3) | Hư hại một phần, ưu tiên thấp hơn nhưng vẫn cần đánh giá. |
| 1 | Water (1), Building-No-Damage (2), Vehicle (6), Road-Clear (7), Pool (10) | Có giá trị **khảo sát/xác nhận tình trạng** (nước lũ có thể có người mắc kẹt, xe/đường cần kiểm tra), nhưng không phải hư hại đã xác nhận. |
| 0 | Background (0), **Tree (9)** | Không có giá trị cứu hộ trực tiếp. |

Điểm của ô = trung bình điểm theo pixel trong ô (như code mẫu trong proposal). Ô có điểm 0 **bị loại khỏi universe**, nếu không mệnh đề "ngân sách < OPT thì không thể phủ 100%" (project-brief mục 5) mất ý nghĩa.

**Lý do chọn thang thứ tự 3/2/1/0:** thang này **thứ tự (ordinal)**, bám theo mức nghiêm trọng của hư hại (định nghĩa theo FEMA mà bài báo RescueNet dùng). Không có căn cứ định lượng cho tỉ lệ 3:2:1, nên không khẳng định đó là "rủi ro thật".

**Vì sao Tree = 0 (khác proposal):** Tree chiếm khoảng 19% pixel. Nếu cho 1 điểm thì khoảng 55% số ô có điểm > 0 chỉ vì có cây, làm loãng bản đồ rủi ro. Đo thực tế (G = 20): tỉ lệ ô có điểm > 0 trung bình là 55% nếu Tree = 1, **34% nếu Tree = 0**, 11% nếu chỉ tính nhãn hư hại. Chọn Tree = 0 để bản đồ rủi ro tập trung vào vùng có ý nghĩa, mà vẫn đủ ô (khoảng 136 ô trung bình) để bài toán có cấu trúc.

**Điểm yếu thừa nhận:** (a) thang điểm là chủ quan; (b) chọn Tree = 0 hay 1 là phán đoán; (c) trọng số 1 cho "không hư hại" có thể bị hỏi vì sao không bằng 0.

**Bảo vệ:** chạy sensitivity với 3 bảng điểm thay thế: (i) Tree = 1 như proposal gốc; (ii) thang lồi 1/4/9 cho mức 1/2/3; (iii) chỉ nhãn hư hại (3, 4, 5, 8) có điểm. Nếu xếp hạng thuật toán và gap so với ILP không đổi, kết luận **không phụ thuộc** vào chi tiết bảng điểm. Đây là câu trả lời chính khi bị hỏi.

## 4. Chọn instance: 1 ảnh = 1 instance, khoảng 30 ảnh phân tầng **[CHỜ DUYỆT]**

**Vì sao không dùng cả 449 ảnh:**
- Chi phí chạy: mỗi instance cần ILP có ràng buộc per-UAV cho nhiều mức ngân sách, và ILP là phần chậm nhất. 449 × nhiều mức × nhiều cấu hình sensitivity không kịp hạn 11/10.
- Nhiều ảnh gần như vô nghĩa: trung vị tỉ lệ pixel hư hại nặng bằng 0, nhiều ảnh cho rất ít ô điểm > 0 (instance tầm thường, ngân sách 25% đã phủ hết). Dùng tất cả sẽ làm loãng kết luận.

**Vì sao khoảng 30:** (1) kiểm định Wilcoxon cần ít nhất khoảng 20–30 cặp để có sức mạnh thống kê hợp lý, trùng khoảng 20–30 seed mà đề yêu cầu; (2) vừa sức tính toán. Đây là quy ước thực hành, **không phải con số có căn cứ chặt**. Nếu ILP chạy nhanh, nên tăng lên (ví dụ 45–60) thay vì giữ cứng 30.

**Cách chọn (không chọn tay từng ảnh, tránh bị nghi cherry-pick):**
1. Tính cho mỗi ảnh tỉ lệ pixel hư hại (nhãn 3, 4, 5, 8) và số ô điểm > 0 theo bảng điểm đã chốt.
2. **Lọc đủ điều kiện:** số ô điểm > 0 ≥ một ngưỡng tối thiểu (đề xuất 60; sẽ chỉnh sau khi xem phân bố, ghi rõ ngưỡng cuối).
3. **Phân tầng** theo mức hư hại thành 3 nhóm (nhẹ/vừa/nặng, cắt theo tam phân vị của tỉ lệ hư hại trong số ảnh đủ điều kiện) vì tập validation không có CSV nhãn 0/1/2.
4. Từ mỗi nhóm lấy **ngẫu nhiên với seed cố định** cùng số ảnh. Ghi danh sách ảnh và seed vào repo để tái lập.

**Điểm yếu:** nhóm hư hại tự suy từ mask, không trùng với nhãn 0/1/2 chính thức của bài báo. Chỉ có tập validation, không có tập test độc lập.

**Bảo vệ:** nêu rõ trong báo cáo; dùng seed và danh sách cố định; kiểm tra thêm bằng cách chạy lại trên một mẫu 30 ảnh khác (seed khác) để xem kết luận có ổn định không.

## 5. Mô hình multi-UAV (đã được chốt)

- **K UAV** (đề xuất K = 3 hoặc 4), mỗi UAV `u` có pin riêng `B_u` khác nhau (khoảng ±20% quanh giá trị chung) để ngân sách riêng có ý nghĩa.
- **Route:** đường đi liền mạch trên lưới xuất phát từ điểm xuất phát của UAV, sinh bằng code. Chi phí route = số bước × pin mỗi ô + chi phí cất cánh. Mỗi route là một "gói" phủ một tập ô.
- **Mỗi UAV chọn nhiều route** miễn tổng chi phí các route đó ≤ `B_u` (đã chốt ngày 07/10, vì đúng "ngân sách từng UAV" hơn). Hệ quả: đây là bài toán submodular với **nhiều ràng buộc knapsack** (một knapsack cho mỗi UAV), không phải partition matroid. Cận xấp xỉ phải **tra lại từ bài báo gốc** trước khi trích, không tự khẳng định (greedy cho cận ½ chỉ biết chắc với ràng buộc partition matroid).
- **Mục tiêu:** tối đa tổng điểm rủi ro của các ô được phủ; ô phủ nhiều lần chỉ tính một lần.
- **Ngân sách:** `B_u` đặt theo % của mức pin cần để phủ hết (do ILP/ước lượng tính), mức 100/75/50/25% như Pha 1.

## 6. So sánh thực nghiệm dự kiến

| Phương pháp | Vai trò |
|---|---|
| ILP có trọng số và biến gán `x_{u,j}` | Đáp án tối ưu tham chiếu. **Cần viết lại**: ILP Pha 1 bỏ qua `weights` và chỉ có một ngân sách. |
| Naive: greedy_ls với ngân sách chung `ΣB_u`, sau đó chia route cho UAV | Mốc để thấy việc xét per-UAV có ý nghĩa; có thể vi phạm ngân sách riêng, cần bước sửa hoặc tính là không hợp lệ. |
| Đề xuất: greedy theo cặp (UAV, route) + local search đổi route giữa các UAV | Tái dùng `lazy_ratio_greedy` và `drop_and_refill` của `pipeline/06_greedy_ls.py`. |

**Rủi ro nói trước:** trên OR-Library greedy_ls đã đạt khoảng 99% so với ILP, nên trên RescueNet gap cũng có thể chỉ 1–3%. Khi đó đóng góp là mô hình per-UAV và kết quả trung thực "gần tối ưu, nhanh hơn ILP X lần", **không hứa trước** mức cải thiện.

### Giao thức và giới hạn của ILP (ghi nhận 07/10/2026)

- ILP giải bằng CBC (PuLP). Lượt 1: giới hạn **120 giây** cho cả 120 lần giải (30 instance × mức 100/75/50/25%). Lượt 2: các ca chưa chứng minh tối ưu sau lượt 1 (23 ca) chạy lại với giới hạn **600 giây**.
- Kết quả cuối: **100/120 `optimal`**, **20/120 `best-known`** (mức 25%: 30/30 optimal; mức 50%: 5, mức 75%: 8, mức 100%: 7 ca best-known). Các ca best-known tập trung ở instance lớn (m ≥ khoảng 190).
- Nhãn `optimal` chỉ gán khi `sol_status` của CBC = 1. (`LpStatus` của PuLP vẫn báo "Optimal" khi CBC hết giờ mà có nghiệm khả thi, nên không dùng được để phân biệt.)
- Với ca `best-known`, "gap" là gap so với nghiệm tốt nhất ILP tìm được, **không phải** so với tối ưu tuyệt đối; tỉ lệ heuristic/ILP có thể > 1. Báo cáo phải nêu rõ, và nên tách số liệu thành hai nhóm (ca optimal / ca best-known).
- Không có cận trên (dual bound) cho các ca best-known vì script chưa lấy được từ PuLP; đã quyết định không tăng thời gian chạy thêm (tăng 5× chỉ giải thêm 3 ca).

## 7. Việc cần làm trước khi viết code

1. Bạn duyệt hoặc sửa mục 2, 3, 4 (đánh dấu CHỜ DUYỆT).
2. Thêm `data/RescueNet/` vào `.gitignore`.
3. Sau khi duyệt: viết kế hoạch triển khai (script risk map, sinh route, ILP per-UAV, validator có trọng số, thuật toán đề xuất), làm theo TDD như repo hiện có.
4. Trước khi trích bảo đảm xấp xỉ cho nhiều knapsack: mở bài gốc để kiểm tra.
