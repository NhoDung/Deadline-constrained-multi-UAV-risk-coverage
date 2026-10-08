# Deadline-constrained multi-UAV risk coverage

## Mô tả chung (Overview)

Project nghiên cứu bài toán **Maximum Risk Coverage**, thuộc lớp bài toán Selective Coverage Path Planning. Mục tiêu của project là tìm kiếm chiến lược định tuyến và hoạch định đường đi tối ưu cho hệ thống đa máy bay không người lái (Multi-UAV). Dựa trên bản đồ rủi ro (risk map) dạng lưới ô vuông được trích xuất từ ảnh chụp không gian thực, thuật toán sẽ điều phối các UAV sao cho tối đa hóa được vùng bao phủ. Khác với quy hoạch quét toàn bộ (complete coverage), mô hình này ưu tiên quỹ đạo đi qua các khu vực có trọng số rủi ro cao, đồng thời đảm bảo thỏa mãn các ràng buộc khắt khe về giới hạn năng lượng (Energy) và thời gian hoàn thành nhiệm vụ (Deadline).

Đây là bài tập lớn môn Design and Analysis of Algorithms (đề: *Deadline-constrained multi-UAV risk coverage*), gồm hai pha:

- **Pha 1:** cài đặt thuật toán baseline trên bộ benchmark đã công bố (OR-Library Set Covering), với **một ngân sách chung**.
- **Pha 2:** chạy trên bản đồ rủi ro tạo từ dữ liệu RescueNet, với **ngân sách pin riêng từng UAV** (mỗi UAV chọn nhiều route miễn tổng chi phí ≤ pin của nó) và trọng số rủi ro theo ô.

## Bài toán và khái niệm nền

**Budgeted Maximum Coverage.** Cho `m` ô (universe) và `n` gói; gói `j` có chi phí `c_j > 0` và phủ một tập ô `S_j`. Chọn tập gói `X` sao cho tổng chi phí ≤ ngân sách `B` và **tối đa hóa** số ô (Pha 2: tổng điểm rủi ro của ô) được ít nhất một gói trong `X` phủ; ô phủ nhiều lần chỉ tính một lần. Cách hiểu theo UAV: ô là vùng cần quan sát, gói là một đường bay phủ một số ô, chi phí là pin/thời gian, `B` là giới hạn năng lượng.

**OPT** là chi phí nhỏ nhất để phủ **hết** mọi ô (bài toán Set Cover). Ngân sách của các thí nghiệm đặt theo `OPT`: `B = floor(mức% × OPT)` với mức 75 / 50 / 25% (Pha 1). OPT không có trong file dữ liệu; bảng OPT của 45 instance lấy từ Ohlsson, Peterson & Söderberg (1999, arXiv:cs/9902025, bảng C2; số liệu gốc của Beasley, 1987) và nằm ở `pipeline/opt_reference.py`. Cả 45 giá trị đã được tái lập bằng ILP (`pipeline/03_solve_ilp.py`) và khớp.

**Hệ quả 1 (dùng để bắt lỗi code).** Nếu `B < OPT` thì **không thể** phủ 100% ô: nếu có lời giải phủ hết với chi phí ≤ `B < OPT` thì đó là một Set Cover rẻ hơn OPT, mâu thuẫn định nghĩa OPT. Nên mọi kết quả báo phủ 100% ở `B < OPT` đều có bug; validator Pha 1 kiểm tra điều này. Ở `B = OPT`, đáp án tối ưu của Set Cover chắc chắn phủ 100% ô nên mức 100% chỉ là mốc kiểm tra. Với trọng số rủi ro, hệ quả này cần mọi ô có điểm > 0 (vì vậy Pha 2 loại các ô điểm 0 khỏi universe).

**Bảo đảm xấp xỉ.** (a) Greedy chọn gói phủ nhiều ô mới nhất, hoặc greedy theo tỉ lệ (ô mới / chi phí) đơn thuần, **không có bảo đảm xấp xỉ** cho bài toán có chi phí. (b) Bản Khuller–Moss–Naor (1999) đơn giản, lấy kết quả tốt hơn giữa greedy theo tỉ lệ và gói đơn tốt nhất, bảo đảm khoảng `½(1 − 1/e) ≈ 0,32` so với tối ưu cho bài toán **một ngân sách**. (c) Mức `1 − 1/e ≈ 0,63` chỉ đúng khi mọi gói cùng chi phí (chọn tối đa `k` gói), hoặc khi duyệt mọi bộ ba gói đầu tiên (Sviridenko, 2004), không khả thi với `n` từ 1000 trở lên. (d) Với **nhiều ngân sách** (mỗi UAV một ngân sách, Pha 2), nhóm **chưa kiểm chứng** cận nào từ tài liệu gốc, nên không khẳng định thuật toán Pha 2 có bảo đảm lý thuyết. Kiểm thử thực nghiệm chỉ phát hiện lỗi, không chứng minh code đúng.

**Nguyên tắc làm việc.** Solver ILP và các heuristic được làm độc lập. **Không chỉnh heuristic để khớp đáp án solver**; báo cáo trung thực khoảng cách (gap) giữa heuristic và tối ưu. Thuật toán có yếu tố ngẫu nhiên phải chạy 20–30 seed (các thuật toán hiện có đều deterministic).

## Cấu trúc repo

| Thư mục / file | Nội dung |
|---|---|
| `pipeline/` | Các bước chạy, đánh số theo thứ tự. **Pha 1:** `01_download_orlib`, `02_convert_to_input`, `03_solve_ilp`, `04_greedy_pure`, `05_validate_solution`, `06_greedy_ls`; `opt_reference.py` là bảng OPT dùng chung. **Pha 2:** `07_rn_prepare` (chọn ảnh, sinh instance), `08_ilp_uav`, `09_greedy_uav` (thuật toán đề xuất `proposed` và baseline `naive`), `10_validate_uav`, `11_summarize_rn`, `12_timing_rn` |
| `pipeline/rn/` | Thư viện Pha 2: `risk.py` (mask → bản đồ rủi ro), `select.py` (chọn ảnh), `routes.py` (sinh route và instance), `budgets.py` (chi phí tham chiếu, ngân sách từng UAV), `store.py` (đường dẫn, đọc/ghi) |
| `data/raw/OR-Library/` | 45 file Set Covering gốc (bộ 4, 5, 6, A–D) |
| `data/processed/` | JSON đã chuyển sang chiều gói→ô, 0-indexed (`m, n, costs, sets`) |
| `data/results/` | Kết quả Pha 1: `ilp/` (180 file, tất cả `optimal`), `greedy/` và `greedy_ls/` (135 file mỗi thư mục) |
| `data/RescueNet/` | **Không nằm trong git** (2,3 GB): tập validation RescueNet, xem mục "Dữ liệu Pha 2" |
| `data/rescuenet/` | Pha 2: `selection.json` (30 ảnh) và `selection_all.json` (350 ảnh), `g*/` (lần chạy 30 ảnh: instance, kết quả, `summary.csv`), `full_g20_default/` (lần chạy 350 ảnh, chỉ `summary.csv` và danh sách ảnh nằm trong git), các file `timing_*.csv` |
| `docs/` | Tài liệu Pha 1 (`huong-dan-chay`, `mo-hinh-du-lieu`, `ilp-solver-thiet-ke`, `greedy-thuan-thiet-ke`, `greedy-ls-thiet-ke`) và Pha 2 (xem mục "Đọc theo thứ tự nào") |
| `docs/superpowers/plans/` | Kế hoạch triển khai Pha 2 và nhật ký quyết định, kể cả các lỗi đã gặp |
| `proposed-algorithm/` | Con trỏ tới thuật toán đề xuất của Pha 2 (code nằm ở `pipeline/09_greedy_uav.py`) |
| `report/` | Phân công công việc |
| `tests/` | Test bằng pytest (78 test) |

## Cài đặt và chạy

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt        # pytest, PuLP, numpy, Pillow, scipy

# Pha 1 (OR-Library)
python pipeline/01_download_orlib.py       # tải 45 file raw (đã có sẵn trong repo)
python pipeline/02_convert_to_input.py     # raw -> data/processed/
python pipeline/03_solve_ilp.py --time-limit 600    # ILP cho toàn bộ 45 instance
python pipeline/04_greedy_pure.py          # greedy thuần, 45 instance x 75/50/25%
python pipeline/06_greedy_ls.py            # ratio greedy + seed + local search
python pipeline/05_validate_solution.py    # kiểm tra mọi kết quả trong data/results/

# Pha 2 (RescueNet, cần data/RescueNet/); ví dụ cấu hình 30 ảnh
python pipeline/07_rn_prepare.py select && python pipeline/07_rn_prepare.py build
python pipeline/08_ilp_uav.py              # ILP có trọng số, ngân sách riêng từng UAV
python pipeline/09_greedy_uav.py --algorithm proposed
python pipeline/09_greedy_uav.py --algorithm naive
python pipeline/10_validate_uav.py && python pipeline/11_summarize_rn.py

python -m pytest tests/
```

Input, output và cách đọc kết quả của từng bước: [`docs/huong-dan-chay.md`](docs/huong-dan-chay.md). Lệnh chạy đầy đủ trên 350 ảnh: `docs/phase2-ket-qua.md` mục 6.

## Dữ liệu Pha 2

RescueNet (Rahnemoonfar, Chowdhury & Murphy, 2023, *Scientific Data* 10:913): ảnh UAV độ phân giải cao chụp sau Hurricane Michael (10/2018) kèm mask phân đoạn 11 lớp (nhãn 0–10). Tải từ Figshare (DOI `10.6084/m9.figshare.c.6647354.v1`), đặt tập validation vào `data/RescueNet/segmentation-validationset/` (gồm `val-label-img/` và `val-org-img/`, 449 ảnh). Chỉ cần thư mục mask `val-label-img/` để chạy pipeline.

RescueNet **không** có khái niệm UAV, pin, route hay đáp án tối ưu. Route, pin, số UAV (K = 4) và công thức ngân sách là **mô hình tổng hợp do nhóm thiết kế** dựa trên nhãn thật; bản đồ rủi ro dựa trên nhãn thật. Mọi con số cần dùng trong báo cáo phải nói rõ điều này.

## Validator

- `pipeline/05_validate_solution.py` (Pha 1) bỏ qua số liệu thuật toán tự báo cáo, đọc `selected_packages` rồi tự tính lại chi phí và số ô phủ từ `data/processed/`. Báo lỗi (thoát mã 1) nếu chi phí vượt `B`, `budget_value` không khớp `floor(mức% × OPT)`, số liệu khai báo lệch số tính lại, gói ngoài phạm vi/trùng, hoặc phủ 100% ô khi `B < OPT` (Hệ quả 1). Chi tiết: `docs/ilp-solver-thiet-ke.md` mục 6.
- `pipeline/10_validate_uav.py` (Pha 2) làm tương tự, nhưng kiểm tra **pin của từng UAV**, tổng rủi ro phủ, và không heuristic nào vượt ILP đã `optimal`.

**Hãy chạy validator trước khi nộp hoặc báo cáo kết quả của bất kỳ thuật toán nào.**

## Trạng thái hiện tại

**Pha 1 (xong).** Dữ liệu, ILP (45/45 khớp bảng OPT), greedy thuần, validator và `greedy_ls`, đạt trung bình 99,4–99,7% so với ILP, mỗi lần chạy ≤ 0,2 giây (`docs/greedy-ls-thiet-ke.md`).

**Pha 2 (code và thực nghiệm xong; báo cáo chưa viết).**
- Đã làm: pipeline đầy đủ từ mask RescueNet đến bảng thống kê; ILP có trọng số và ngân sách từng UAV; thuật toán `proposed` (ratio greedy theo từng UAV + gói đơn tốt nhất + seed + local search) và baseline `naive` (ngân sách chung rồi sửa); validator; ablation; sensitivity (bảng điểm và kích thước lưới, trên 30 ảnh); phân tích thời gian chạy (Big-O và đo thực tế).
- Kết quả chính (350 ảnh, tỉ lệ objective so với ILP, mức ngân sách 25 / 50 / 75 / 100%): `proposed` 0,984 / 0,971 / 0,973 / 0,984, `naive` 0,933 / 0,908 / 0,921 / 0,941. `proposed` mất trung bình 46 ms, ILP vài chục đến vài trăm giây (khoảng 28% số ca ILP chỉ đạt nghiệm tốt nhất tìm được, chưa chứng minh tối ưu). Chi tiết và giới hạn: `docs/phase2-ket-qua.md`.

**Chưa làm.** Bài báo cáo (Abstract đến Conclusion), biểu đồ, các thuật toán Pha 1 còn lại (random, GRASP, simulated annealing/GA), kiểm chứng bảo đảm xấp xỉ cho trường hợp nhiều ngân sách, chạy sensitivity trên 350 ảnh, và kiểm chứng trên một mẫu ảnh khác. Instance và kết quả từng ảnh của lần chạy 350 ảnh không nằm trong git (chạy lại cần khoảng 2 giờ cho ILP).

## Đọc theo thứ tự nào (Pha 2)

1. [`docs/phase2-ket-qua.md`](docs/phase2-ket-qua.md): kết quả, giới hạn, cách tái lập.
2. [`docs/phase2-rescuenet-thiet-ke.md`](docs/phase2-rescuenet-thiet-ke.md): lý do mọi lựa chọn thiết kế (lưới, bảng điểm, chọn ảnh, mô hình UAV), kèm điểm yếu và cách bảo vệ.
3. [`docs/phase2-thoi-gian-chay.md`](docs/phase2-thoi-gian-chay.md): độ phức tạp Big-O và thời gian đo thực tế.
4. [`docs/huong-dan-chay.md`](docs/huong-dan-chay.md) (mục Pha 2) và [`docs/mo-hinh-du-lieu.md`](docs/mo-hinh-du-lieu.md) mục 8: cách chạy và định dạng dữ liệu.
5. Code: `pipeline/09_greedy_uav.py` (thuật toán chính), `08_ilp_uav.py`, `rn/routes.py`, `rn/budgets.py`, `rn/risk.py`; sau đó `10_validate_uav.py`, `11_summarize_rn.py`, `07_rn_prepare.py`, `12_timing_rn.py`.
6. [`docs/superpowers/plans/2026-10-07-phase2-rescuenet-multi-uav.md`](docs/superpowers/plans/2026-10-07-phase2-rescuenet-multi-uav.md): nhật ký quyết định và các lỗi đã gặp.
