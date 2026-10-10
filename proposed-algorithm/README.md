# Thuật toán đề xuất (Pha 2)

Thư mục này **không còn chứa code**; thuật toán đề xuất của Pha 2 nằm cùng các bước pipeline khác để dùng chung thư viện:

| Thành phần | Vị trí |
|---|---|
| Thuật toán đề xuất `proposed` và baseline `naive` | `pipeline/09_greedy_uav.py` |
| ILP có trọng số và ngân sách riêng từng UAV (đáp án tham chiếu) | `pipeline/08_ilp_uav.py` |
| Sinh instance từ mask RescueNet (risk map, route, ngân sách) | `pipeline/07_rn_prepare.py`, `pipeline/rn/` |
| Validator, tổng hợp thống kê, đo thời gian | `pipeline/10_validate_uav.py`, `11_summarize_rn.py`, `12_timing_rn.py` |

## Thuật toán `proposed` (tóm tắt)

Hướng mở rộng của Pha 2 là **ngân sách riêng từng UAV**: K UAV, mỗi UAV chọn nhiều route miễn tổng chi phí ≤ pin của nó, mục tiêu là tổng điểm rủi ro ô được phủ. `proposed` phát triển từ `pipeline/06_greedy_ls.py` (Pha 1) và gồm bốn bước:

1. **Ratio greedy theo từng UAV:** chọn route có (rủi ro mới / chi phí) lớn nhất, miễn route còn vừa pin của chính UAV sở hữu nó; dùng lazy evaluation (CELF).
2. **Route đơn tốt nhất** vừa pin, giữ nếu tốt hơn bước 1.
3. **Seed:** chạy lại bước 1 bắt đầu từ mỗi route trong nhóm 20 route phủ nhiều nhất và 20 route có tỉ lệ tốt nhất.
4. **Local search drop-and-refill:** thử bỏ lần lượt từng route đã chọn rồi lấp lại pin còn dư bằng ratio greedy.

Thuật toán deterministic. Với trường hợp nhiều ngân sách, nhóm chưa kiểm chứng bảo đảm xấp xỉ từ tài liệu gốc. Thiết kế, kết quả và giới hạn: `docs/phase2-rescuenet-thiet-ke.md`, `docs/phase2-ket-qua.md`, `docs/phase2-thoi-gian-chay.md`.

## Quy ước cho thuật toán mới của Pha 2

- Đọc instance ở `data/rescuenet/<tag>/instances/` (định dạng: `docs/mo-hinh-du-lieu.md` mục 8) và ghi kết quả JSON vào `data/rescuenet/<tag>/results/<tên thuật toán>/<instance>_<mức>.json` theo đúng schema kết quả Pha 2.
- Chạy `python pipeline/10_validate_uav.py --tag <tag>` trước khi báo cáo kết quả. Validator kiểm tra pin từng UAV, tổng rủi ro phủ, và không heuristic nào vượt ILP đã `optimal`.
- Nếu thuật toán có yếu tố ngẫu nhiên: chạy 20–30 seed và ghi `seed` vào kết quả.
- So sánh với `naive` và ILP (`.../results/ilp/`); **không chỉnh thuật toán cho khớp đáp án ILP**.
