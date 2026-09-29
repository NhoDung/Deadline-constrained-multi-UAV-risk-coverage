# Deadline-constrained multi-UAV risk coverage

## Mô tả chung (Overview)

Project nghiên cứu bài toán **Maximum Risk Coverage**, thuộc lớp bài toán Selective Coverage Path Planning. Mục tiêu của project là tìm kiếm chiến lược định tuyến và hoạch định đường đi tối ưu cho hệ thống đa máy bay không người lái (Multi-UAV). Dựa trên bản đồ rủi ro (risk map) dạng lưới ô vuông được trích xuất từ ảnh chụp không gian thực, thuật toán sẽ điều phối các UAV sao cho tối đa hóa được vùng bao phủ. Khác với quy hoạch quét toàn bộ (complete coverage), mô hình này ưu tiên quỹ đạo đi qua các khu vực có trọng số rủi ro cao, đồng thời đảm bảo thỏa mãn các ràng buộc khắt khe về giới hạn năng lượng (Energy) và thời gian hoàn thành nhiệm vụ (Deadline).

## Cấu trúc repo

| Thư mục / file | Nội dung |
|---|---|
| `data/raw/OR-Library/` | 45 file Set Covering gốc (bộ 4, 5, 6, A–D) |
| `data/processed/` | JSON đã chuyển sang chiều gói→ô, 0-indexed (`m, n, costs, sets`) |
| `data/results/ilp/` | 180 kết quả ILP (45 instance × setcover + budgeted 75/50/25%), tất cả `optimal` |
| `data/results/greedy/` | 135 kết quả greedy thuần (45 instance × 75/50/25%) |
| `scripts/` | `download_orlib.py`, `convert_to_input.py`, `solve_ilp.py`, `opt_reference.py` (bảng OPT), `validate_solution.py` (validator) |
| `baseline/` | Thuật toán baseline (hiện có greedy thuần) — xem `baseline/README.md` |
| `proposed-algorithm/` | Thuật toán đề xuất cho Pha 2 (chưa bắt đầu) |
| `docs/` | Mô hình dữ liệu, thiết kế ILP, thiết kế greedy |
| `report/` | Phân công công việc |
| `tests/` | Test bằng pytest |
| `project-brief.md` | Tài liệu tham chiếu tổng hợp: đề bài, dữ liệu, quy ước, kế hoạch |

## Cài đặt và chạy

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt        # gồm pytest và PuLP

python scripts/download_orlib.py           # tải 45 file raw (đã có sẵn trong repo)
python scripts/convert_to_input.py         # raw -> data/processed/
python scripts/solve_ilp.py --time-limit 600          # ILP cho toàn bộ 45 instance
python baseline/greedy_pure.py                        # greedy thuần, 45 instance x 75/50/25%
python scripts/validate_solution.py                   # kiểm tra mọi kết quả trong data/results/
python -m pytest tests/
```

## Validator

`scripts/validate_solution.py` là script kiểm tra chung cho **mọi** thuật toán: nó bỏ qua số liệu thuật toán tự báo cáo, đọc `selected_packages` rồi tự tính lại chi phí và số ô phủ từ `data/processed/`. Nó báo lỗi (thoát mã 1) nếu chi phí vượt ngân sách `B`, `budget_value` không khớp `floor(mức% × OPT)`, số liệu khai báo lệch số tính lại, gói ngoài phạm vi/trùng, hoặc phủ 100% ô khi `B < OPT` (Hệ quả 1). **Hãy chạy validator trước khi nộp hoặc báo cáo kết quả của bất kỳ thuật toán mới nào.** Chi tiết: `docs/ilp-solver-thiet-ke.md` mục 6.

## Trạng thái hiện tại (Pha 1)

- Xong: dữ liệu, ILP (45/45 khớp bảng OPT), greedy thuần, validator.
- Chưa xong: các thuật toán còn lại theo `project-brief.md` mục 7, bảng tổng hợp gap và xuất CSV (mục 8), Pha 2 (RescueNet).
