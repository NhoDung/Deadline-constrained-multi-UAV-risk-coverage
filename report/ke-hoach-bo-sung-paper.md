# Kế hoạch bổ sung để viết paper IEEE (tiếng Việt, cả hai pha)

*Ngày lập: 11/10/2026 (bản chi tiết hóa). Trạng thái dự án: Pha 1 xong, Pha 2 code + thực nghiệm xong, báo cáo chưa viết.*

---

## Phần 1: Ánh xạ tài liệu hiện có → 7 mục của paper

| Mục paper | Nguồn chính | Trạng thái |
|---|---|---|
| Abstract | Viết mới, tóm từ VI + VII | Chưa có |
| I. Introduction | `README.md` mục "Mô tả chung" + "Bài toán và khái niệm nền" | ~80%, cần viết lại văn phong |
| II. Related Work | `docs/greedy-ls-thiet-ke.md` mục 9, README "Bảo đảm xấp xỉ" | ~70% |
| III. Proposed Method | `docs/mo-hinh-du-lieu.md`, `docs/greedy-thuan-thiet-ke.md`, `docs/greedy-ls-thiet-ke.md`, `docs/phase2-rescuenet-thiet-ke.md`, `proposed-algorithm/README.md` | Đầy đủ nhất |
| IV. Experiment Results | `docs/phase2-ket-qua.md`, `docs/phase2-thoi-gian-chay.md`, các doc Pha 1 mục "Kết quả" | Số liệu đủ, **thiếu biểu đồ** |
| V. Discussion | `docs/phase2-ket-qua.md` mục 5 (7 giới hạn), `docs/phase2-rescuenet-thiet-ke.md` mục 0 | ~90% |
| VI. Conclusion | Viết mới | Chưa có |

---

## Phần 2: VIỆC BẮT BUỘC — thông số chi tiết

### B1. Các biểu đồ (matplotlib, xuất PDF để nhúng LaTeX)

Quy ước chung cho mọi hình: cột đơn rộng 3,5 in, cột đôi rộng 7,16 in, font 8–9 pt, bảng màu an toàn người mù màu (ví dụ `tab:10` hoặc Okabe–Ito), luôn ghi `n` và mức ngân sách trong caption. Script gợi ý: `pipeline/14_plots_paper.py`, hàm `plot_h3() … plot_h6()`, xuất vào `data/figures/` (thêm vào `.gitignore` nếu nặng; PDF thì nhẹ, nên commit).

**H1 — Sơ đồ pipeline (đồ thị, không cần dữ liệu).** Các khối: `mask RescueNet → risk.py (bảng điểm) → select.py (30/350 ảnh) → routes.py (lưới G×G, route, K=4) → budgets.py (R, B_u) → {08 ILP | 09 proposed/naive} → 10 validate → 11 summary`. Vẽ bằng TikZ (nếu nộp LaTeX) hoặc matplotlib box+arrow. Ước lượng 2–3 giờ.

**H2 — Minh họa một ảnh thật, 3 panel ngang (rộng 7,16 in).** Chọn 1 ảnh tầng hư hại cao từ `data/rescuenet/g20_default/instances/` (trường `tier`, cần `image_id`; ảnh gốc ở `data/RescueNet/segmentation-validationset/val-org-img/` — **không có trong git**, phải chạy trên máy có dữ liệu):
- Panel (a): ảnh gốc RGB.
- Panel (b): heatmap lưới 20×20 từ `cell_rc` (risk per cell), colormap `magma`/`inferno`, kèm colorbar.
- Panel (c): các route của 4 UAV — vẽ `paths` (danh sách toạ độ ô theo từng UAV, phân biệt màu/marker), đánh dấu `uav_starts`.
Caption phải ghi: ảnh là dữ liệu thật, còn lưới/route/pin là mô hình tổng hợp của nhóm. Ước lượng 3–4 giờ.

**H3 — Kết quả chính 350 ảnh, grouped bar (cột đơn).** Trục x = 4 mức ngân sách (25/50/75/100%), trục y = tỉ lệ objective so với ILP (0,85–1,05), 2 series: `proposed`, `naive`. Nguồn: tự tính lại từ `data/rescuenet/full_g20_default/summary.csv` (cột `covered_weight`, nhóm theo `algorithm`, `budget_level`; mẫu ILP tương ứng từ kết quả `ilp` cùng tag — hoặc dùng bảng số ở `docs/phase2-ket-qua.md` mục 2: proposed 0.9839/0.9706/0.9728/0.9843, naive 0.9328/0.9084/0.9211/0.9410). Vẽ thêm thanh error (min–max hoặc IQR) nếu muốn. 1 giờ.

**H4 — Chất lượng–thời gian theo số seed, 2 trục y (cột đơn).** Nguồn `data/rescuenet/g20_default/timing_seeds.csv` (cột: `instance, level, n_seeds, time, ratio_to_ilp`). Trục x = `n_seeds`; trục y trái = `time` (ms), trục y phải = `ratio_to_ilp`; một đường cho mỗi mức ngân sách (4 đường). Kèm chú thích điểm cân bằng (seed mà sau đó ratio tăng < 0,5% nhưng time tăng gấp đôi). 2 giờ.

**H5 — Pha 1: gap so với ILP trên OR-Library, grouped bar (cột đơn).** Trục x = 3 mức (75/50/25%), trục y = gap trung bình so với ILP (%) = `(objective_ILP − objective_heuristic) / objective_ILP`; 2 series: `greedy` (thuần) và `greedy_ls`. Nguồn: `data/results/summary_phase1.csv` từ C1 (chưa tồn tại — H5 chờ C1). Chú thích dưới hình: greedy_ls trung bình 99,4–99,7% so ILP, mỗi lần chạy ≤ 0,2 giây. 1 giờ.

**H6 — Scale-up (cột đơn, tùy nhưng rẻ).** Nguồn `data/rescuenet/timing_scale.csv` (cột `sweep, parameter, n, m, k, time`): trục x = `m` (hoặc `n`), trục y = `time` (thang log), phân biệt sweep. Dùng cho mục độ phức tạp. 1 giờ.

### B2. Chốt thuật ngữ "deadline" (quyết định chặn mọi việc viết)

Code chỉ có ràng buộc **pin từng UAV** (`uav_share`), không có deadline thời gian. Hai lựa chọn:

- **A (khuyên dùng):** paper đặt vấn đề là *maximum risk coverage under per-UAV energy budgets*. Câu gợi ý cho Introduction: *"Đề bài gốc nêu ràng buộc deadline; trong khuôn khổ này nhóm mô hình hóa ràng buộc thời gian dưới dạng ngân sách năng lượng (chi phí route = thời gian bay/pin) cho từng UAV; việc bổ sung mốc thời gian riêng cho từng ô là hướng phát triển."* Deadline xuất hiện duy nhất ở Future Work.
- **B:** thêm ràng buộc deadline thật → sửa model + code + chạy lại toàn bộ (~1 tuần), gần như không kịp trước 28/10.

### B3. Template IEEE

- LaTeX `IEEEtran`, chế độ conference, 2 cột, 6–8 trang. Tiêu đề nháp: *"Phủ rủi ro có ngân sách trên bản đồ lưới từ RescueNet: greedy tỉ lệ lazy kết hợp seed và tìm kiếm cục bộ cho hệ đa UAV"*.
- Tác giả: điền từ `report/phan_cong_cong_viec.md` (5 người, cột tên còn trống).
- Tài liệu tham khảo tối thiểu (8 mục): Beasley 1987/OR-Library; Nemhauser–Wolsey–Fisher 1978; Khuller–Moss–Naor 1999; Sviridenko 2004; Ohlsson–Peterson–Söderberg 1999 (arXiv:cs/9902025); Rahnemoonfar–Chowdhury–Murphy 2023 (Scientific Data 10:913, RescueNet, DOI figshare `10.6084/m9.figshare.c.6647354.v1`); Cormen et al. (NP-hard, nếu cần); CBC/PuLP (Mitchell; Forest et al.).

### B4. Ba mục viết mới

- **Abstract (150–250 từ):** bài toán → mô hình (lưới rủi ro từ RescueNet, K=4 UAV, pin riêng) → phương pháp (lazy ratio greedy per-UAV + best-single + seed + local search) → kết quả số (0,971–0,984 so với ILP trên 350 ảnh, ~46 ms so với ILP vài chục–vài trăm giây) → đóng góp chính.
- **Introduction (0,75–1 trang):** bối cảnh UAV sau thiên tai → bài toán chọn route dưới ngân sách → NP-hard → đóng góp dạng bullet (4 gạch: mô hình instance từ RescueNet; thuật toán proposed; đánh giá đối chứng ILP 1400 lần giải + thống kê Wilcoxon; ablation + sensitivity).
- **Conclusion (0,25–0,5 trang):** tóm kết quả + 3 future work (deadline thời gian; cận xấp xỉ multi-budget; kiểm định trên tập ảnh độc lập).

---

## Phần 3: VIỆC NÊN LÀM — thông số chi tiết

### C1. Script `pipeline/13_summarize_phase1.py` — 1–2 giờ

- **Đọc:** `data/processed/*.json` (45 file: `m, n, costs, sets`); `data/results/ilp/*_budgeted_{75,50,25}.json` (135); `data/results/greedy/*.json` (135); `data/results/greedy_ls/*.json` (135). Định dạng chung đã xác minh: `instance, budget_level, budget_value, objective, cost, selected_packages, solve_time_seconds, status` (`greedy` không có `covered_weight` — bài toán chưa có trọng số ở Pha 1).
- **Ghi:** `data/results/summary_phase1.csv`, mỗi dòng một (instance, thuật toán, mức):
  `instance, algorithm, budget_level, budget_value, objective, cost, coverage_pct, gap_vs_ilp, solve_time_seconds`, trong đó `gap_vs_ilp = (objective_ILP − objective_thuật_toán) / objective_ILP` (khớp theo cặp `instance` + `budget_level` với kết quả ILP cùng mức).
- **Tự kiểm:** in cảnh báo nếu `budget_value ≠ floor(mức% × OPT)` (OPT lấy từ `pipeline/opt_reference.py`) hoặc trạng thái ILP ≠ `optimal` (không đáng lẽ xảy ra: 45/45 đã optimal).
- **Chạy:** `python pipeline/13_summarize_phase1.py`. Phục vụ H5 và bảng Pha 1 trong paper.

### C2. Sửa `pipeline/11_summarize_rn.py` ghi thống kê ra file — 1 giờ

Thêm tham số `--stats-out` (mặc định `<tag>/summary_stats.csv` trong thư mục tag). Nội dung: mỗi dòng một phép so sánh — `tag, comparison (proposed_vs_naive | proposed_vs_<abl> | <abl>_vs_naive), budget_level, n, wins, ties, losses, wilcoxon_p, mean_ratio_a, mean_ratio_b`. Lưu ý giữ nguyên stdout như cũ để không phá thói quen cũ; sau khi sửa, chạy lại để có file stats cho tag `full_g20_default` (chỉ cần summary.csv, không cần chạy lại thuật toán — hàm đọc từ summary.csv hoặc tính lại từ results tuỳ cấu trúc hiện tại; nếu hàm Wilcoxon hiện đọc từ results từng file thì viết bản đọc summary.csv).

### C3. Baseline random cho Pha 1 — `pipeline/15_random_baseline.py` — 2–3 giờ

- Thuật toán: xáo trộn thứ tự gói bằng seed, nhặt gói đến khi vượt ngân sách thì dừng; chạy **20 seed**/instance/mức (đúng nguyên tắc 20–30 seed trong README).
- Kết quả ghi `data/results/random/` cùng schema với `greedy/` (thêm trường `seed`); hợp nhất qua C1 thành cột `algorithm = random`, gap lấy **trung bình ± độ lệch chuẩn trên 20 seed**.
- Điểm tạo ra trong paper: có mốc tham chiếu ngẫu nhiên để thấy greedy_ls tốt hơn "may mắn" bao nhiêu. Không chỉnh bất kỳ thứ gì theo đáp án ILP.

### C4. Phụ lục lý thuyết — 2–3 giờ, không cần chứng minh mới

3 đoạn:
1. **NP-hard:** quy về Budgeted Maximum Coverage (Khuller–Moss–Naor 1999).
2. **Cận ½(1−1/e) ≈ 0,32** cho greedy tỉ lệ + best-single, điều kiện **một ngân sách** → đúng cho Pha 1; chép kỹ giả định chi phí dương, hàm phủ modular hóa.
3. **Khai báo trung thực:** trường hợp nhiều ngân sách (Pha 2) nhóm **chưa kiểm chứng** cận nào từ tài liệu; đánh giá Pha 2 thuần thực nghiệm qua ILP. Nêu thêm lý do không dùng cận 1−1/e (Sviridenko 2004 cần duyệt bộ ba gói đầu, không khả thi với n ≥ 1000).
Kèm bảng Big-O từng thuật toán: chép từ `docs/phase2-thoi-gian-chay.md` mục 2 và các doc Pha 1 mục "Độ phức tạp".

### C5. Sensitivity 1 cấu hình trên 350 ảnh — ~2 giờ chạy máy, không viết code mới

`select --all` đã có; `build --table tree1 --selection selection_all.json --tag full_g20_tree1 --shard k/10` rồi 08–11 với `--tag`. ILP chia ~10 phần song song (~2 giờ). Chỉ làm khi B1–B4 xong.

---

## Phần 4: TÙY CHỌN

- **T1.** Tập kiểm định độc lập: chọn mẫu từ 99 ảnh bị loại (sửa điều kiện lọc `select.py`, ví dụ ≥ 20 ô điểm > 0 thay vì 60), chạy g20_default — ~30 phút chạy + chỉnh nhỏ.
- **T2.** GRASP hoặc simulated annealing cho Pha 1 (mỗi cái ~1 ngày) — chỉ nếu C3 xong mà vẫn dư thời gian.
- **T3.** Deadline thời gian thật (Lựa chọn B ở B2) — để Future Work.
- **T4.** Dọn 2 điểm không nhất quán: giải thích 10 file `skipped_*of10.json` rỗng của `full_g20_default` trong `docs/huong-dan-chay.md`; thêm `skipped.json` cho `g20_default` cho đồng nhất với 4 tag sensitivity.

---

## Phần 5: Bố cục paper 6–8 trang (khung chi tiết, đánh số hình/bảng)

| Mục | Độ dài | Hình/Bảng | Nội dung chính |
|---|---|---|---|
| Abstract | 150–250 từ | — | Như B4 |
| I. Introduction | 0,75–1 tr. | H1 | Bối cảnh → bài toán → 4 đóng góp |
| II. Related Work | 0,5–0,75 tr. | — | Max coverage có ngân sách; submodular; UAV coverage planning; RescueNet |
| III. Bài toán & mô hình | 1 tr. | — | Ký hiệu (universe m, gói n, chi phí, B, B_u); định nghĩa BMC; mô hình multi-UAV (route, uav_share, R); Hệ quả 1; NP-hard |
| IV. Thuật toán | 1–1,25 tr. | — | greedy thuần; greedy_ls (lazy ratio + seed + LS); naive; proposed (per-UAV); ILP đối chứng; bảng Big-O |
| V. Thiết lập thực nghiệm | 0,5–0,75 tr. | H2 | OR-Library 45; RescueNet; bảng điểm rủi ro; sinh instance; 4 mức ngân sách; tiêu chí đánh giá |
| VI. Kết quả | 2–2,5 tr. | Bảng T1 (Pha 1 gap), T2 (Pha 2 chính 350), T3 (W/T/L + Wilcoxon), T4 (ablation), T5 (sensitivity); H3, H4, H5, H6 | Pha 1 trước, Pha 2 là trọng tâm; thời gian chạy |
| VII. Discussion | 0,5–0,75 tr. | — | 7 giới hạn từ `phase2-ket-qua.md` mục 5 (chép thẳng, chỉnh văn phong) |
| VIII. Conclusion | 0,25–0,5 tr. | — | Như B4 |
| Tài liệu tham khảo | — | — | ≥ 8 mục như B3 |

Chú thích bắt buộc dưới mọi bảng có tỉ lệ: *"Tỉ lệ > 1 xảy ra khi ILP chỉ đạt `best-known` sau 120 giây (393/1400 ca ở lần chạy 350 ảnh); các ca đó so với nghiệm tốt nhất ILP tìm được, không phải tối ưu."*

---

## Phần 6: Thứ tự làm đề xuất (deadline 28/10)

1. **Ngay:** B2 (họp 30 phút chốt thuật ngữ) → C1 → H3 → H5 (cần C1) → H1.
2. **18–21/10:** H2, H4, H6, C2, C3, C4; viết nháp mục III–VI từ bảng ánh xạ Phần 1.
3. **22–28/10:** viết I, Abstract, VIII; ghép IEEEtran; review chéo toàn nhóm; nộp.
4. **Khi dư:** C5, T1–T4.

*Nguyên tắc số liệu: mọi số trong paper phải sinh từ file (summary.csv / summary_phase1.csv / summary_stats.csv) bằng script, không chép tay từ doc — tránh lệch số khi tái sử dụng.*
