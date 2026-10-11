# Paper (bản nháp IEEE, tiếng Việt)

## Biên dịch

**Quan trọng:** upload **cả `main.tex` lẫn thư mục `figures/`** — thiếu `figures/`
là lỗi và treo ở giữa văn bản.

**Overleaf:** tạo project mới, upload `main.tex` + thư mục `figures/`, vào
Menu → Compiler chọn **XeLaTeX** (font Unicode đầy đủ dấu tiếng Việt qua
fontspec/Tex Gyre Termes). Chọn pdfLaTeX cũng chạy được nhưng cần gói vntex
và font T5 có thể thiếu glyph một số máy.

**Máy cục bộ (đã kiểm chứng với tectonic 0.15, engine XeTeX):**

```bash
cd paper
tectonic -X compile main.tex
```

## Vẽ lại các hình

```bash
python pipeline/13_summarize_phase1.py     # tổng hợp Pha 1 -> data/results/summary_phase1.csv
python pipeline/14_plots_paper.py          # vẽ cả 6 hình vào paper/figures/
python pipeline/14_plots_paper.py --figs h3   # hoặc chỉ từng hình: h1..h6
```

H2 đọc instance + kết quả `proposed` mức 100% của `g20_default`; chọn ảnh khác:
`--instance data/rescuenet/g20_default/instances/<id>.json`.

## Trạng thái bản nháp

- Đủ 8 mục + 9 tài liệu tham khảo; **6 hình đã vẽ** (h1–h6, PDF + PNG) và đã chèn
  vào `main.tex`; 5 bảng số liệu lấy từ `docs/phase2-ket-qua.md` và
  `data/results/summary_phase1.csv`.
- **Placeholder còn lại** (tìm `TODO` trong `main.tex`):
  1. Trích dẫn `ohlsson1999` và `pulp` chưa hoàn chỉnh. Tác giả đã điền đủ 5 người.
- Hình H2 hiện chỉ có 2 panel (risk map + route) vì ảnh gốc RescueNet (2,3 GB)
  không có trên máy; khi có dữ liệu, có thể chèn panel ảnh gốc bên trái.
- Việc còn lại theo kế hoạch: `report/ke-hoach-bo-sung-paper.md`
  (baseline random C3, phụ lục lý thuyết C4, lưu stats ra file C2).
