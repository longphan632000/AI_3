# Phạm vi Trợ lý AI

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Task | Ai tạo | Dữ liệu | Đầu ra/kiểm định |
| --- | --- | --- | --- |
| weekly_summary | PM của dự án | Khoảng tuần + task tạo/cập nhật/có hạn trong hai cận bao gồm; sprint tùy chọn | Tiến độ/rủi ro/ưu tiên có Task ID; không kết luận thời điểm hoàn thành từ snapshot |
| meeting_minutes | PM/Member có quyền | Ghi chú thuộc project hoặc raw/tệp; chia passage khi dài | Thảo luận/quyết định/action_items, tham chiếu passage; chưa có người/hạn thì để chưa xác định |
| assignment_suggestion | PM của dự án | Task + hồ sơ/năng lực/tải; v2 recruitment không cần task | ID đủ điều kiện/số lượng, lý do/số liệu dựng từ nguồn; không tự thêm/giao |

FR-12/13/14 bắt buộc; lịch sử FR-15 được triển khai, prompt_version còn REQ-10. AI trong sản phẩm khác Codex áp dụng Skill ở quá trình phát triển. An toàn dựa BR-06/07; xác nhận riêng PM, không cho AI tool ghi DB.
