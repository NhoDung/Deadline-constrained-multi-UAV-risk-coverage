# Nhận xét tổng hợp báo cáo "Deadline-Constrained Multi-UAV Risk Coverage"

Ngày kiểm tra: 12/10/2026. File được kiểm: `paper_giai_thuat_uav 9.pdf`.

## 0. Phương pháp và phạm vi

Đối chiếu với ba nguồn:
1. Các chat trước trong project (kế hoạch, đề bài, tài liệu RescueNet).
2. Repo local `Deadline-constrained-multi-UAV-risk-coverage`: `docs/phase2-ket-qua.md`, `pipeline/08_ilp_uav.py`, `git log`, và `data/rescuenet/full_g20_default/summary.csv` (8400 dòng).
3. Tự tính lại một số con số từ `summary.csv` (tỉ lệ so với ILP, thời gian, số ca chạm giới hạn).

Chưa kiểm: nội dung Pha 1 trong repo (45 instance OR-Library), 82 test pytest, thông tin xuất bản các bài trích dẫn (chỉ đối chiếu với hiểu biết chung), và Hình 6 (chỉ xem qua bản trích văn bản).

## 1. Kết luận ngắn

- **Số liệu chính của báo cáo khớp với dữ liệu trong repo.** Bảng II, III, IV, V và các con số thời gian đều tái lập được từ `summary.csv`.
- **Ablation có thật, chạy trên 350 ảnh.** Thư mục kết quả có đủ 3 biến thể `abl_*` với 1400 dòng mỗi biến thể.
- **Thời gian ILP là số liệu bị cắt ở 120 giây**, nên cách diễn đạt "ILP cần 3,2–66,2 giây" gây hiểu nhầm. Đây là điểm cần sửa quan trọng nhất.
- Còn một số lỗi sự kiện, trích dẫn và trình bày (mục 4, 5).

## 2. Những điểm đã xác nhận đúng

| Nội dung báo cáo | Kết quả đối chiếu |
|---|---|
| Bảng II: tỉ lệ `proposed` / `naive` so với ILP | Khớp đến 4 chữ số thập phân khi tính lại từ `summary.csv` |
| Bảng IV: ablation 350 ảnh | Khớp: `abl_ratio_only` 0,9456 / 0,9190 / 0,9301 / 0,9545, v.v. |
| Bảng V: 46,4 ms (`proposed`), 66,5 ms (`naive`), max 245 / 294 ms | Khớp |
| ILP: 3,2 / 42,2 / 60,0 / 66,2 s, tổng 16,7 giờ CPU | Khớp (3,2 / 42,2 / 60,0 / 66,2; 16,69 giờ) |
| 8400 file kết quả | Khớp: 6 thuật toán × 1400 dòng |
| "hơn naive 4,3–6,2 điểm phần trăm" | Đúng: chênh 5,11 / 6,22 / 5,17 / 4,33 điểm theo số chưa làm tròn |
| Bảng III, p-value Wilcoxon | Khớp `docs/phase2-ket-qua.md` (chưa chạy lại Wilcoxon) |
| Cận ½(1 − 1/e) chỉ cho một ngân sách, không khẳng định bảo đảm cho nhiều ngân sách | Đúng, phù hợp với chat trước |
| Mô tả RescueNet là dữ liệu thị giác máy tính, không có UAV/pin; route, pin, K do nhóm thiết kế | Đúng |

Lưu ý: ở một lượt trước mình nói "4,3–6,2 tính ra 6,3 ở mức 50%". Đó là do làm tròn số ở 3 chữ số; tính từ số gốc thì 6,22. Mình rút lại nhận xét đó.

## 3. Điểm cần sửa quan trọng: thời gian ILP

### 3.1. Vấn đề

Báo cáo viết (tóm tắt, mục VI.E, kết luận) rằng ILP "cần từ 3,2 đến 66,2 giây". Thực tế:
- ILP bị giới hạn **120 giây** (`--time-limit 120`).
- 66,2 giây là **trung bình của các thời gian đã bị cắt**, không phải thời gian giải xong.
- Ở mức 100%: **156/350 ca** chạm giới hạn và dừng, chưa chứng minh tối ưu. 194 ca còn lại xong sớm, trung bình **22,9 giây**.
- Số ca chạm giới hạn theo mức (25 / 50 / 75 / 100%): 6 / 99 / 133 / 156. Tổng 394 theo thời gian chạy (báo cáo ghi 393 ca `best-known`; chênh 1 ca ở mức 75%, có thể là một ca xong ngay sát giới hạn, chưa kiểm status từng file).

### 3.2. Lần chạy 600 giây

Chạy lại các ca best-known với giới hạn 600 giây chỉ có trên **bản 30 ảnh** (`g20_default`), không có trên bản 350 ảnh. Kết quả ba ca mẫu:

| Ca | Lần 350 ảnh (120 s) | Lần chạy lại (600 s) |
|---|---|---|
| 12437, mức 75% | 120,11 s, best-known | 600,2 s, **vẫn best-known** |
| 13085, mức 100% | 120,14 s, best-known | 600,2 s, **vẫn best-known** |
| 11690, mức 100% | 120,07 s, best-known | **optimal** sau 286 s |

Như vậy không có mâu thuẫn: những ca khó bị bỏ dở ở 120 giây, và có ca 10 phút vẫn chưa xong. Trung bình 66,2 giây chỉ là hệ quả của việc cắt.

### 3.3. Báo cáo chưa nói gì

- Không nhắc lần chạy lại 600 giây trên bản 30 ảnh.
- Cách viết "ILP cần ..." làm người đọc hiểu ILP giải xong trong khoảng thời gian đó.

### 3.4. Câu thay thế gợi ý

**Tóm tắt** (thay cụm "trong khi ILP cần từ 3,2 đến 66,2 giây"):

> Mỗi lần giải của thuật toán đề xuất mất khoảng 46 ms, trong khi ILP (giới hạn 120 giây) mất trung bình 3,2–66,2 giây theo mức ngân sách và vẫn có 28% số ca chưa chứng minh được tối ưu khi hết giờ.

**Mục VI.E** (thêm sau câu về ILP):

> Các thời gian ILP là sau khi bị cắt ở 120 giây: ở mức 100%, 156/350 ca chạm giới hạn, nên trung bình 66,2 giây là cận dưới của thời gian giải thật. Trên bản 30 ảnh, các ca chưa tối ưu được chạy lại với giới hạn 600 giây; một số ca vẫn chưa chứng minh được tối ưu.

**Kết luận** (thay "so với 3,2–66,2 giây của ILP"):

> so với ILP, vốn bị cắt ở 120 giây và vẫn để lại 28% số ca chưa chứng minh tối ưu.

## 4. Lỗi sự kiện và mâu thuẫn nội bộ

1. **Mâu thuẫn về ablation (mục VII.6 và Bảng IV).** Bảng IV ghi "ablation trên 350 ảnh", trong khi mục VII.6 ghi "ablation chi tiết, độ nhạy chỉ chạy trên 30 ảnh phân tầng". Repo xác nhận: ablation chạy cả 350 ảnh (và một bản 30 ảnh); **sensitivity** và **số seed (Hình 5)** chỉ chạy trên 30 ảnh. Nên viết lại VII.6: "Ablation: 350 ảnh (ngoài ra có bản 30 ảnh). Sensitivity và khảo sát số seed: chỉ 30 ảnh."
2. **"RescueNet gồm 449 ảnh" (mục I).** Sai: RescueNet có 4494 ảnh. 449 là tập validation mà nhóm dùng.
3. **Tóm tắt: "Cả bộ thực nghiệm đều xây từ RescueNet".** Sai: Pha 1 dùng OR-Library. Chỉ Pha 2 dựa trên RescueNet.
4. **Pha 1: "Cả 45 ca ILP đều đạt optimal".** Cách đếm chưa rõ: mỗi heuristic có 135 lần giải (45 × 3 mức). Nên viết "135 lần giải ILP đều optimal" nếu đúng như vậy. Chưa kiểm status Pha 1 trong repo.
5. **Từ "seed" dùng hai nghĩa.** Trong báo cáo, "seed" là các khởi tạo thứ tự route; trong đề bài, "20–30 seed" nghĩa là hạt giống ngẫu nhiên. Thuật toán `proposed` deterministic, nên người chấm có thể hiểu là chưa đáp ứng yêu cầu 20–30 seed. Gợi ý: đổi tên thành "khởi tạo đa điểm" (multi-start), và nói rõ phần ngẫu nhiên duy nhất là hệ số pin sᵤ (±20%) khi sinh instance, đã cố định trong dữ liệu.
6. **Chưa gọi tên hướng mở rộng Pha 2 theo danh sách của đề.** Đề yêu cầu chọn ít nhất một hướng (đa mục tiêu, online, robust, approximation-aware...). Báo cáo có ngân sách riêng từng UAV và trọng số rủi ro (là mở rộng mô hình) nhưng không nêu hướng nào. Có thể nêu rõ: thuật toán đề xuất là *greedy adaptive / approximation-aware heuristic* (đúng hướng của chính đề #2), và robust/online là hướng phát triển.
7. **Bảo đảm lý thuyết.** Báo cáo trung thực khi nói chưa có bảo đảm cho nhiều ngân sách. Nên giữ nguyên, tránh viết `proposed` "kế thừa bảo đảm" của KMN.

## 5. Trích dẫn và trình bày

**Trích dẫn**
- Thiếu **Chandran & Vipin (2024)**, bài tham khảo chính của đề #2 (bài khảo sát mạng đa UAV cho giám sát thiên tai); nên thêm vào Introduction hoặc Related Work.
- [5] Ohlsson, Peterson, Söderberg thiếu tên bài; cần tên bài và năm đầy đủ.
- "Số liệu gốc Beasley [1]" nhưng [1] là bài OR-Library (1990); nguồn gốc OPT là Beasley (1987), *An algorithm for set covering problems*, EJOR 31:85–93. Nên thêm bài này.
- Thông tin xuất bản của RescueNet nên lấy lại từ trang tạp chí để chắc chắn.

**Trình bày**
- Email thiếu chữ "n": `sis.hust.edu.v` (phải là `.vn`).
- Chú thích Hình 2: ký hiệu ★ bị mất trong bản trích văn bản; kiểm lại trên PDF.
- Hình 6 nói thời gian "gần như không phụ thuộc m"; nên viết "thay đổi ít" nếu đường theo m vẫn dao động (chưa kiểm dữ liệu gốc).
- Giá trị `p < 10⁻⁴⁴` ở tóm tắt và `10⁻¹⁸` ở ablation khớp tài liệu repo; không cần sửa.

## 6. Hạn chế đã được báo cáo nêu đúng (nên giữ)

- Instance tổng hợp; route, pin, K = 4 do nhóm thiết kế.
- ILP không luôn tối ưu (28%); tỉ lệ có thể lớn hơn 1 ở các ca best-known (trong repo, `proposed` tối đa 1,0391 trên 350 ảnh).
- Chỉ dùng tập validation; 99/449 ảnh bị loại do quá ít ô.
- Chênh lệch tuyệt đối so với `naive` khiêm tốn (4,3–6,2 điểm) và vẫn kém ILP khoảng 1,6–2,9 điểm.

## 7. Việc nên làm trước khi nộp (theo thứ tự ưu tiên)

1. Sửa cách diễn đạt thời gian ILP ở tóm tắt, VI.E và kết luận (mục 3.4).
2. Sửa mâu thuẫn VII.6 về ablation và sensitivity (mục 4.1).
3. Sửa "449 ảnh" và "cả bộ thực nghiệm đều xây từ RescueNet" (mục 4.2, 4.3).
4. Đổi tên "seed", nêu rõ hướng mở rộng Pha 2 (mục 4.5, 4.6).
5. Bổ sung trích dẫn Chandran & Vipin, Beasley (1987), tên bài [5] (mục 5).
6. Sửa email và chú thích hình (mục 5).
