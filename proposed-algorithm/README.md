# Thuật toán đề xuất (Pha 2)

**Chưa bắt đầu.** Thư mục dành cho thuật toán mở rộng của Pha 2 (ví dụ submodular greedy có ngân sách, tách ngân sách riêng từng UAV, trọng số rủi ro theo ô từ RescueNet). Hướng cụ thể chưa được nhóm chốt: xem `project-brief.md` mục 9.4 và `report/phan_cong_cong_viec.md`.

## Yêu cầu cho mọi thuật toán đặt ở đây

- Đọc instance ở `data/processed/` và ghi kết quả JSON vào `data/results/<tên thuật toán>/` theo đúng format của baseline (xem `baseline/README.md`, mục "Thêm thuật toán baseline mới").
- Chạy validator trước khi báo cáo kết quả: `python scripts/validate_solution.py --results-dir data/results/<tên thuật toán>`. Validator kiểm tra chi phí ≤ B, số ô phủ khai báo, và Hệ quả 1 (không phủ 100% khi B < OPT).
- Nếu thuật toán có yếu tố ngẫu nhiên: chạy 20–30 seed, ghi `seed` vào kết quả.
- So sánh với baseline (`data/results/greedy/`) và ILP tối ưu (`data/results/ilp/`), và không chỉnh thuật toán cho khớp đáp án ILP.
