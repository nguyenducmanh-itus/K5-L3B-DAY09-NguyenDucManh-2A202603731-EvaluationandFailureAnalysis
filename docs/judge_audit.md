# Judge audit

Đã replay 100 cặp nhãn người/judge. Kappa đo đồng thuận vượt ngẫu nhiên; precision/recall xem FAIL là lớp dương. Ngưỡng quyết định: κ≥0.6, P≥0.8, R≥0.7.

| Tiêu chí | n | κ | Precision | Recall | Floors | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone | 100 | 0.757 | 0.857 | 0.800 | đạt | dùng cho tiêu chí tone đã định nghĩa |
| helpful | 100 | 0.375 | 1.000 | 0.300 | không đạt | không dùng làm gate |

Tone confusion: TP=24, FP=4, FN=6, TN=66. Tỷ lệ FAIL quan sát 0.28; Rogan–Gladen hiệu chỉnh thành 0.30. Helpful có 21 FN/30 lỗi thật: độ chính xác 1.0 không cứu được recall 0.3; judge bỏ sót phần lớn câu trả lời không hữu ích.

## Audit bất đồng tone

| Case | Judge | Human | Nhận định / hành động rubric |
|---|---|---|---|
| H-008 | PASS | FAIL | Đừng coi lời khẳng định “đã hoàn tiền” là tone tốt nếu chưa có bằng chứng xử lý; tách giọng điệu khỏi tính đúng. |
| H-017 | PASS | FAIL | Một câu lịch sự nhưng khẳng định sai số tiền vẫn là lỗi; rubric tone không thay grader tiền. |
| H-029 | PASS | FAIL | Câu “đang xử lý” cần nêu trạng thái/cam kết cụ thể; bổ sung ví dụ trả lời vòng vo. |
| H-042 | FAIL | PASS | Judge phạt nhầm cách diễn đạt lịch sự; thêm ví dụ chuẩn với thời gian xử lý. |
| H-051 | FAIL | PASS | Judge phạt nhầm câu trả lời rõ ràng; chuẩn hóa tiêu chí tone độc lập với số tiền. |

## Kết luận

Chỉ dùng judge tone cho đúng tiêu chí tone sau calibration. Không dùng helpful làm gate: recall thấp tạo nhiều false negative. Cả hai chỉ được replay trên CSV công khai; cần nhãn held-out mới trước khi dùng làm bằng chứng chất lượng thật.
