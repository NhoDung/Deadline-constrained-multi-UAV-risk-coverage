# Báo cáo audit: paper `paper/main.tex` so với nguồn trong project

*Ngày audit: 12/10/2026. Bản paper audit: `main.tex` sau khi tác giả tự sửa đoạn mở đầu Giới thiệu và đoạn so sánh proposed/naive ở mục VI-B. Chưa chỉnh sửa gì — chờ chấp thuận.*

## 1. Các section đã rà soát

Toàn bộ: Abstract, I. Giới thiệu, II. Công trình liên quan, III. Bài toán và mô hình hóa (A/B/C), IV. Thuật toán (A/B), V. Thiết lập thực nghiệm, VI. Kết quả (A–E) + 5 bảng + 6 hình (caption), VII. Thảo luận, VIII. Kết luận, Tài liệu tham khảo.

## 2. CONFLICT — mâu thuẫn giữa paper và nguồn (cần quyết định trước khi sửa)

| # | Khẳng định trong paper | Nguồn thực tế | Phân loại |
|---|---|---|---|
| C1 | Mục III-C: *"Ngân sách $B_u$ phân bổ theo tỉ lệ tổng rủi ro tiếp cận được của từng UAV"* | `pipeline/rn/routes.py` (hàm build): `raw = [1 + uniform(-0.2, 0.2) for each UAV]` rồi chuẩn hóa — tức share ngẫu nhiên **±20% quanh giá trị bằng nhau**. `pipeline/rn/budgets.py`: `B_u = floor(level × R × share_u / 100)`. Tài liệu thiết kế `docs/phase2-rescuenet-thiet-ke.md` mục 5 chốt: *"mỗi UAV có pin riêng B_u khác nhau (khoảng ±20% quanh giá trị chung)"*. **Không có nguồn nào nói "theo tỉ lệ rủi ro tiếp cận được".** | CONFLICT |

Hướng xử lý đề xuất (chờ chấp thuận): sửa câu III-C theo code + design doc, ví dụ: *"Ngân sách $B_u = \lfloor \text{mức\%} \times R \times s_u \rfloor$, trong đó $s_u$ là hệ số riêng từng UAV, ngẫu nhiên trong khoảng $\pm 20\%$ quanh giá trị bằng nhau (chốt trong tài liệu thiết kế)."*

## 3. UNCLEAR — câu chữ lệch code, đề xuất chỉnh từ (giữ nguyên ý đúng)

| # | Vị trí | Hiện trạng | Bằng chứng | Đề xuất |
|---|---|---|---|---|
| U1 | Mục III-C: *"theo chiến lược tham lam rủi ro"* | Code là **random walk có trọng số** theo `risk[ô] + 0.1`, không phải tham lam thuần; docstring `routes.py`: *"lệch về ô có rủi ro cao"* | `pipeline/rn/routes.py::random_route` | Sửa thành *"lệch về ô có rủi ro cao"* |
| U2 | Caption hình 2: *"★: điểm xuất phát ở 4 góc"* | Đúng với K=4: `start_cells` cho 4 góc đầu tiên (`4 góc rồi 4 trung điểm cạnh`) | `pipeline/rn/routes.py::start_cells`; instance `11690.json` có `uav_starts` = 4 góc | VERIFIED — giữ nguyên |

## 4. [CẦN XÁC MINH] — người viết phải xử lý

1. `\bibitem{ohlsson1999}` — thiếu thông tin trích dẫn đầy đủ (đã có TODO trong file).
2. `\bibitem{pulp}` — chưa có trích dẫn chuẩn (đã có TODO trong file).
3. Comment dòng 8 của `main.tex` ("Tên tác giả và thông tin liên hệ" còn thiếu) đã lỗi thời — tác giả đã điền đủ; nên xóa dòng này khi chỉnh sửa.

## 5. Bảng đối chiếu số liệu (kết quả audit: 100% khớp)

| Số liệu trong paper | Nguồn đối chiếu | Kết quả |
|---|---|---|
| Pha 1: 0,435/0,410/0,408 (greedy thuần); 0,994/0,994/0,997 (greedy+seed+LS); thời gian 1,6–4,5 ms và 26–64 ms; thấp nhất 98,5% | Tính lại từ 270 file `data/results/{greedy,greedy_ls}/` (135 file/thuật toán, kèm `data/results/summary_phase1.csv` sinh bởi `pipeline/13_summarize_phase1.py`) | KHỚP |
| 45/45 ca ILP optimal (Pha 1) | `data/results/ilp/` (180 file, README dòng "tất cả optimal") | KHỚP |
| Bảng OPT khớp 45/45 khi tái lập bằng ILP | `pipeline/opt_reference.py` docstring + README | KHỚP |
| Pha 2: 0,984/0,971/0,973/0,984 (proposed), 0,933/0,908/0,921/0,941 (naive); n = 349/350/350/350; min .882/.862/.890/.905 và .369/.659/.672/.694 | `docs/phase2-ket-qua.md` mục 2 (bảng dán từ output `11_summarize_rn.py`); `data/rescuenet/full_g20_default/summary.csv` (8400 dòng) | KHỚP |
| 1007 optimal / 393 best-known; 25%: 344/6, 50%: 251/99, 75%: 218/132, 100%: 194/156 | `docs/phase2-ket-qua.md` mục 2 | KHỚP |
| W/T/L 265/83/1, 321/23/6, 333/6/11, 334/1/15; p = 4,5e-45, 8,2e-55, 1,3e-56, 3,9e-57 | `docs/phase2-ket-qua.md` mục 2 | KHỚP |
| Ablation 4 biến thể × 4 mức; ratio-only hơn naive 0,9–1,4 điểm; p < 10⁻¹⁸ | `docs/phase2-ket-qua.md` mục 2 (ablation 350 ảnh) | KHỚP |
| Sensitivity: tree 56/120 best-known; tỉ lệ >1 lớn nhất 1,016; lưới 10×10 mức 25% p = 0,32 | `docs/phase2-ket-qua.md` mục 4 | KHỚP |
| Thời gian: proposed 46,4 ms (max 245), naive 66,5 ms (max 294), ILP 3,2/42,2/60,0/66,2 s, tổng 16,7 giờ CPU vs 65 giây | `docs/phase2-ket-qua.md` mục 2, `docs/phase2-thoi-gian-chay.md` mục 8 | KHỚP |
| Seed: 5 seed cho phần lớn cải thiện; 20→80 seed +0,3–0,5 điểm, +87 ms; 10 seed −41% thời gian, −0,2–0,6 điểm; n: hệ số mũ 1,06 | `docs/phase2-thoi-gian-chay.md` mục 3.5, 3.6 | KHỚP |
| 350/449 ảnh, ngưỡng ≥ 60 ô điểm dương, 99 ảnh loại (45 ảnh 0 ô) | `pipeline/07_rn_prepare.py` (`--min-cells` mặc định 60), `docs/phase2-rescuenet-thiet-ke.md` cập nhật 08/10/2026 | KHỚP |
| Risk cell = trung bình pixel score trong ô | `pipeline/rn/risk.py::cell_risk` (`.mean(axis=(1,3))`) | KHỚP |
| Chi phí route = cất cánh + độ dài (tỷ lệ độ dài) | `pipeline/rn/routes.py::build_instance` (`takeoff_cost + cell_cost * len(path)`) | KHỚP |
| R = chi phí phủ trọn nhỏ nhất (ILP), B_u từ R | `pipeline/rn/budgets.py::reference_cost, budgets_for_level` | KHỚP |
| Validator tự tính lại; 8400 file, 0 lỗi; cấm heuristic > ILP optimal | `pipeline/05_validate_solution.py`, `pipeline/10_validate_uav.py`, `docs/phase2-ket-qua.md` mục 2 | KHỚP |
| K = 4, xuất phát 4 góc | `routes.py::start_cells`, instance JSON | KHỚP |
| "82 test pytest" | Chạy `pytest tests/`: 82 passed | KHỚP |
| Giới hạn ILP 120 s; mức ngân sách 25/50/75/100%; 45 thực thể OR-Library bộ 4/5/6/A–D | README, `docs/ilp-solver-thiet-ke.md` | KHỚP |

## 6. Lỗi trình bày/LaTeX phát hiện trong bản hiện tại (do chỉnh tay gần đây)

| # | Vị trí | Vấn đề | Đề xuất |
|---|---|---|---|
| L1 | Mục VI-B, đoạn "Bảng III trình bày..." | Dùng ký tự unicode `10⁻⁴⁴` thay vì LaTeX `$10^{-44}$` — font TeX Gyre Termes có thể thiếu glyph superscript → render sai | Thay bằng `$10^{-44}$` |
| L2 | Cùng đoạn | Viết cứng "Bảng III" thay vì `Bảng~\ref{tab:wlt}`; đồng thời tham chiếu `hình~\ref{fig:main}` đã bị xóa → `fig:main` (hình 4) không còn được nhắc trong văn bản | Khôi phục `\ref` cho cả bảng và hình |
| L3 | Cùng đoạn | `"ngân sách.. Không"` (hai dấu chấm) và thiếu dấu chấm kết thúc trước "Không có ca nào" | Sửa dấu câu |
| L4 | Comment đầu file, dòng 8 | Ghi "Tên tác giả... còn thiếu" trong khi đã điền đủ | Xóa mục lỗi thời |

## 7. Các khẳng định đã kiểm tra và thấy an toàn (không cần sửa)

- Không có chỗ nào khẳng định bảo đảm xấp xỉ cho multi-budget (mục II và VII nói đúng "chưa kiểm chứng").
- Phân biệt optimal/best-known nhất quán ở bảng II, III, hình 3, 4 và VII.3.
- Route/pin/K=4 được khai báo là mô hình tổng hợp ở I (Phạm vi mô hình), VI hình 2 caption, VII.1.
- Không có citation bị bỏ, không có citation phát sinh, không có số liệu mới không nguồn.
- Phần lặp số giữa Abstract / VI-B / VIII là vị trí quy ước (abstract–thân–kết luận), VI-B có chi tiết per-level riêng nên không tính là lặp rỗng.

## 8. Đề xuất danh sách chỉnh sửa (chờ chấp thuận)

1. **C1 (bắt buộc):** sửa câu phân bổ B_u ở III-C theo code + design doc.
2. **U1:** đổi "tham lam rủi ro" → "lệch về ô có rủi ro cao" ở III-C.
3. **L1–L3:** sửa đoạn VI-B (math mode cho 10⁻⁴⁴, khôi phục `\ref{tab:wlt}` + `\ref{fig:main}`, sửa dấu câu) — chỉnh tối thiểu, giữ nguyên câu chữ của tác giả.
4. **L4:** xóa dòng comment lỗi thời về tác giả.
5. Sửa xong xuất sang file mới `paper/main_v2.tex` (không ghi đè `main.tex`), biên dịch kiểm chứng bằng tectonic.

Việc 4 + 5 không đụng nội dung nghiên cứu. Không mục nào khác cần sửa về nội dung.

## 9. Kết quả thực thi (12/10/2026)

Người viết chấp thuận: "Viết theo code, tất cả lấy source code làm chuẩn". Đã thực hiện
C1, U1, L1–L3, L4 và xuất **`paper/main_v2.tex`** (không ghi đè `main.tex`). Biên dịch
thành công bằng tectonic (XeTeX), 6 trang (thêm ~1 đoạn nên tài liệu tham khảo [6]–[9]
tràn sang trang 6; sẽ co lại khi hoàn thiện 2 trích dẫn TODO). Đã kiểm tra render: đoạn
VI-B hiển thị đúng `25 %`, `100 %`, `10⁻⁴⁴`, tham chiếu Bảng III (`tab:wlt`) và Hình 4
(`fig:main`) đầy đủ. Không số liệu, công thức, citation nào thay đổi ngoài 5 mục đã liệt
kê. Còn lại cho người viết: hoàn thiện 2 trích dẫn `ohlsson1999`, `pulp`.
