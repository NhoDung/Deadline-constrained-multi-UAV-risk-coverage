# Deadline-constrained multi-UAV risk coverage

## Mô tả chung (Overview)

Project nghiên cứu bài toán **Maximum Risk Coverage**, thuộc lớp bài toán Selective Coverage Path Planning. Mục tiêu của project là tìm kiếm chiến lược định tuyến và hoạch định đường đi tối ưu cho hệ thống đa máy bay không người lái (Multi-UAV). Dựa trên bản đồ rủi ro (risk map) dạng lưới ô vuông được trích xuất từ ảnh chụp không gian thực, thuật toán sẽ điều phối các UAV sao cho tối đa hóa được vùng bao phủ. Khác với quy hoạch quét toàn bộ (complete coverage), mô hình này ưu tiên quỹ đạo đi qua các khu vực có trọng số rủi ro cao, đồng thời đảm bảo thỏa mãn các ràng buộc khắt khe về giới hạn năng lượng (Energy) và thời gian hoàn thành nhiệm vụ (Deadline).