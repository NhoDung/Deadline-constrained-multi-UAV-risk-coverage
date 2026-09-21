# PHÂN CÔNG DỰ ÁN: DEADLINE-CONSTRAINED MULTI-UAV RISK COVERAGE

*Điền tên thành viên vào cột "Tên thành viên" sau khi họp. Mỗi dòng là một đầu việc chính. Mốc thời gian dựa trên deadline 28/10, viết báo cáo bắt đầu từ 8/10.*

---

## 1. (Modeling & Theory Lead)

| Trường | Nội dung |
|---|---|
| **Tên thành viên** | *(điền tên)* |
| **Vai trò / phần việc** | Mô hình hóa bài toán & chứng minh lý thuyết |
| **Kết quả cần đạt** | Có một định nghĩa toán học chính thức của bài toán (universe, sets, budget, objective) mà tất cả các thành viên khác code theo, và một chứng minh/khảo cứu về cận xấp xỉ (1−1/e) cho phần thuật toán nâng cao. |
| **Các việc cần làm** | • Đọc kỹ RescueNet (paper + annotation schema) để hiểu input thực tế: 10 class, damage level, cấu trúc ảnh.<br>• Định nghĩa mapping: grid cell = phần tử có trọng số rủi ro; UAV route = "tập hợp" phủ một số cell với chi phí (thời gian bay/pin).<br>• Viết formal model: biến quyết định, hàm mục tiêu (maximize risk-weight covered), ràng buộc (deadline, budget/pin).<br>• Phân tích độ phức tạp bài toán (NP-hard vì quy về Budgeted Maximum Coverage).<br>• Tổng hợp/chứng minh cận (1−1/e) cho greedy trên submodular function (dựa Nemhauser-Wolsey-Fisher 1978, Khuller-Moss-Naor 1999).<br>• Hỗ trợ debug khi kết quả thực nghiệm (từ người 2, 3) không khớp lý thuyết. |
| **Sản phẩm bàn giao** | • Tài liệu mô hình hóa (input/output shape, ký hiệu toán học) — nộp trước 24/9 để người khác code theo.<br>• Chứng minh cận xấp xỉ (viết tay/LaTeX) — nộp trước 5/10.<br>• Phần "Proposed Method" (mục toán học) cho báo cáo cuối. |
| **Nội dung báo cáo** | Mô hình hóa bài toán (Proposed Method – phần lý thuyết), độ phức tạp, chứng minh approximation guarantee, Related Work (Khuller-Moss-Naor, Nemhauser-Wolsey-Fisher). |
| **Nội dung thuyết trình** | Giới thiệu bài toán, mô hình hóa toán học, ý nghĩa cận (1−1/e) (khoảng 3 phút). |
| **Điều kiện hoàn thành & phối hợp** | Model phải chốt xong **trước 24/9** vì người 2, 3, 4 đều code dựa trên input/output shape này — chậm ở đây làm chậm cả nhóm. Sau tuần 2, hỗ trợ người 5 làm sensitivity/statistical test nếu rảnh. |

---

## 2. (Baseline Algorithm Engineer)

| Trường | Nội dung |
|---|---|
| **Tên thành viên** | *(điền tên)* |
| **Vai trò / phần việc** | Cài đặt thuật toán baseline (Pha 1 – bắt buộc) |
| **Kết quả cần đạt** | Thuật toán greedy/nearest-neighbor chạy đúng, có kết quả so sánh với optimal/best-known trên OR-Library, đủ điều kiện nộp Pha 1. |
| **Các việc cần làm** | • Nhận model từ người 1, cài đặt hàm chung: input = risk-weighted grid + route set + budget, output = tập route được chọn.<br>• Cài đặt thuật toán greedy (chọn route có tỉ lệ risk-covered/chi phí tốt nhất mỗi bước) và nearest-neighbor.<br>• Tải bộ instance Maximum Coverage/Set Cover từ OR-Library.<br>• Chạy baseline trên các instance này, ghi coverage đạt được, so với optimal/best-known đã công bố.<br>• Đo runtime, độ phức tạp thực nghiệm.<br>• Viết code sạch, có hướng dẫn chạy, đẩy lên repo chung. |
| **Sản phẩm bàn giao** | • Code baseline (repo, có README) — nộp trước **1/10** (deadline Pha 1).<br>• Bảng kết quả: coverage %, runtime, gap so với optimal trên OR-Library.<br>• Sau đó: chạy lại baseline trên RescueNet-derived instances (từ người 4) để làm cột so sánh cho người 3. |
| **Nội dung báo cáo** | Mô tả thuật toán baseline, bảng kết quả OR-Library (Pha 1), bảng so sánh baseline vs. advanced trên RescueNet (Pha 2, phối hợp người 3). |
| **Nội dung thuyết trình** | Thuật toán baseline hoạt động thế nào, kết quả trên OR-Library (khoảng 3 phút). |
| **Điều kiện hoàn thành & phối hợp** | Cần model từ người 1 (trước 24/9) để bắt đầu code. Deadline Pha 1: **1/10**. Sau đó phối hợp với người 3 để đảm bảo hai thuật toán chạy trên cùng format instance (cả OR-Library lẫn RescueNet-derived). |

---

## 3. (Advanced Algorithm Engineer)

| Trường | Nội dung |
|---|---|
| **Tên thành viên** | *(điền tên)* |
| **Vai trò / phần việc** | Cài đặt thuật toán nâng cao – Submodular Maximization (Pha 2 – hướng "Approximation/guarantee") |
| **Kết quả cần đạt** | Thuật toán submodular chạy đúng, đạt tỉ lệ gần với cận lý thuyết (1−1/e) trên OR-Library, và cho kết quả tốt hơn baseline trên cả OR-Library lẫn RescueNet-derived instances. |
| **Các việc cần làm** | • Nghiên cứu lý thuyết submodular maximization cùng người 1 (2/10 trở đi khi model đã chốt).<br>• Cài đặt thuật toán submodular-greedy có ràng buộc budget/deadline.<br>• Chạy validate trên OR-Library, so sánh với baseline (người 2) và optimal/best-known.<br>• Sau khi có instance RescueNet (từ người 4), chạy thuật toán trên đó.<br>• Tune thuật toán, kiểm tra các trường hợp biên (edge case) cùng người 1.<br>• Ghi log toàn bộ tham số, seed để người 5 chạy multi-seed/statistical test. |
| **Sản phẩm bàn giao** | • Code thuật toán advanced (repo, README) — hoàn thành validate trên OR-Library trước **12/10**.<br>• Kết quả trên RescueNet-derived instances trước **21/10**.<br>• Bảng so sánh: advanced vs. baseline vs. cận lý thuyết. |
| **Nội dung báo cáo** | Mô tả thuật toán submodular, so sánh với baseline, phân tích khoảng cách với cận (1−1/e) trên cả hai bộ instance. |
| **Nội dung thuyết trình** | Thuật toán nâng cao khác baseline ở đâu, cải thiện bao nhiêu %, minh họa trên case RescueNet (khoảng 4 phút). |
| **Điều kiện hoàn thành & phối hợp** | Cần chứng minh/lý thuyết từ người 1 và code baseline từ người 2 để so sánh. Cần instance từ người 4 trước khi chạy trên RescueNet. Deadline validate OR-Library: **12/10**; deadline RescueNet: **21/10**. |

---

## 4. (Data / Instance Engineer)

| Trường | Nội dung |
|---|---|
| **Tên thành viên** | *(điền tên)* |
| **Vai trò / phần việc** | Xử lý dữ liệu RescueNet & sinh instance bài toán |
| **Kết quả cần đạt** | Có pipeline chuyển ground-truth mask của RescueNet thành risk map dạng lưới (grid), và bộ instance đầy đủ (route/budget/deadline) để người 2, 3 chạy thuật toán. |
| **Các việc cần làm** | • Tải bộ annotation RescueNet từ Figshare (mask + classification label, không cần chạy CNN — dùng thẳng ground-truth).<br>• Thiết kế bảng ánh xạ 10 class → mức rủi ro (có lý giải rõ ràng, ví dụ Building-Total-Destruction/Road-Blocked = rủi ro cao).<br>• Viết code chia ảnh mask thành lưới M×N, tính risk-weight trung bình mỗi ô.<br>• Sinh instance tổng hợp: tập route UAV khả thi trên lưới, chi phí (thời gian/pin) cho mỗi route, deadline tổng.<br>• Sinh thêm vài instance kích thước nhỏ để người 5 chạy exact-solver so sánh.<br>• Viết tài liệu mô tả format instance để người 2, 3 dùng thống nhất. |
| **Sản phẩm bàn giao** | • Script xử lý mask → risk grid (nộp cùng lúc code baseline, trước **1/10**, để không chặn Pha 1 nếu cần sớm; bắt buộc trước **2/10** để không chặn Pha 2).<br>• Bộ instance RescueNet-derived (nhiều kích thước, gồm bản nhỏ cho exact-solver).<br>• Tài liệu mô tả cách sinh risk-weight và format instance. |
| **Nội dung báo cáo** | Mô tả nguồn dữ liệu RescueNet, cách xây risk map (bảng ánh xạ class→trọng số, lý do chọn), cách sinh instance tổng hợp (route, budget, deadline). |
| **Nội dung thuyết trình** | Dataset RescueNet là gì, cách biến ảnh vệ tinh/UAV thành risk map, minh họa trực quan (khoảng 3 phút). |
| **Điều kiện hoàn thành & phối hợp** | Cần format input/output từ người 1. Không chặn Pha 1 (baseline chạy trên OR-Library trước), nhưng **bắt buộc xong trước 2/10** để người 2, 3 có instance chạy trong Pha 2. |

---

## 5. (Experiments & Report Integration Lead)

| Trường | Nội dung |
|---|---|
| **Tên thành viên** | *(điền tên)* |
| **Vai trò / phần việc** | Thực nghiệm thống kê, so sánh exact-solver & tổng hợp báo cáo |
| **Kết quả cần đạt** | Có bộ kết quả thực nghiệm đầy đủ (multi-seed, sensitivity, so sánh exact-solver) và một báo cáo hoàn chỉnh đúng cấu trúc bài báo khoa học, nộp đúng hạn 28/10. |
| **Các việc cần làm** | • Từ 18/9: dựng khung báo cáo, viết Abstract/Introduction/Related Work sớm (không phụ thuộc kết quả thực nghiệm).<br>• Từ 2/10: dựng harness chạy multi-seed (20–30 seed) cho cả baseline và advanced.<br>• Chạy exact-solver (ILP/brute-force) trên các instance nhỏ (từ người 4) để tính optimality gap thật.<br>• Làm sensitivity analysis (số UAV, kích thước grid, deadline).<br>• Chạy kiểm định thống kê (t-test/Wilcoxon) so sánh baseline vs. advanced.<br>• Vẽ bảng/biểu đồ kết quả.<br>• Tổng hợp toàn bộ phần của 4 người thành báo cáo hoàn chỉnh, quản lý danh mục tài liệu tham khảo, chuẩn bị slide chung. |
| **Sản phẩm bàn giao** | • Khung báo cáo + phần Intro/Related Work — nộp trước **12/10**.<br>• Kết quả thực nghiệm đầy đủ (bảng, biểu đồ, thống kê) — trước **21/10**.<br>• Báo cáo hoàn chỉnh (đủ 7 mục: Abstract, Introduction, Related Work, Proposed Method, Experiment Results, Discussion, Conclusion) — trước **28/10**. |
| **Nội dung báo cáo** | Experiment Results (toàn bộ bảng/biểu đồ), Discussion (phân tích, hạn chế), tổng hợp và format toàn bộ báo cáo. |
| **Nội dung thuyết trình** | Quy trình thực nghiệm, kết quả so sánh, đánh đổi giữa chất lượng và thời gian chạy; hỗ trợ tổng hợp slide chung (khoảng 4 phút). |
| **Điều kiện hoàn thành & phối hợp** | Nhận kết quả từ người 2 (baseline), người 3 (advanced), người 4 (instance nhỏ cho exact-solver). Hai thuật toán phải chạy trên cùng format dữ liệu và cấu hình mới so sánh được. Cần bắt đầu viết báo cáo sớm (từ 8/10) song song với thực nghiệm để không dồn việc vào tuần cuối. |

---

## Mốc thời gian chung (tham chiếu nhanh)

| Giai đoạn | Thời gian | Việc chính |
|---|---|---|
| Pha 1 | 18/9 – 1/10 | Model (người 1) → Baseline + OR-Library (người 2) |
| Pha 2 (A) | 2/10 – 12/10 | Advanced algo + validate OR-Library (người 3), Risk-grid instances (người 4), khung báo cáo (người 5) |
| Pha 2 (B) | 13/10 – 21/10 | Chạy trên RescueNet instances (người 2, 3), exact-solver + thống kê (người 5) |
| Hoàn thiện | 22/10 – 28/10 | Review chéo, hoàn thiện báo cáo, nộp |
