# Luồng dữ liệu Trợ lý AI

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Task | Ai tạo | Dữ liệu | Đầu ra/kiểm định |
| --- | --- | --- | --- |
| weekly_summary | PM của dự án | Khoảng tuần + task tạo/cập nhật/có hạn trong hai cận bao gồm; sprint tùy chọn | Tiến độ/rủi ro/ưu tiên có Task ID; không kết luận thời điểm hoàn thành từ snapshot |
| meeting_minutes | PM/Member có quyền | Ghi chú thuộc project hoặc raw/tệp; chia passage khi dài | Thảo luận/quyết định/action_items, tham chiếu passage; chưa có người/hạn thì để chưa xác định |
| assignment_suggestion | PM của dự án | Task + hồ sơ/năng lực/tải; v2 recruitment không cần task | ID đủ điều kiện/số lượng, lý do/số liệu dựng từ nguồn; không tự thêm/giao |

1. Backend lấy requester từ session, xác nhận account/project/task_type và active scope.
2. SQL dùng tham số; week_start/week_end ánh xạ trực tiếp các điều kiện DATE BETWEEN, không có tên date_from/date_to giả định.
3. Retrieved data kèm danh sách Task/User/Meeting note hợp lệ. Staffing toàn hệ thống chỉ dùng hồ sơ công khai trong nội bộ và số tổng hợp, không lấy tiêu đề/công việc dự án khác.
4. Context_builder lọc/định dạng; prompt_builder gắn grounding. Ghi chú người dùng là dữ liệu không đáng tin, không được thay role/session.
5. Provider xử lý ngoài DB. Kết quả được kiểm ID/schema/số liệu/nguồn; output giữ draft hoặc cần xác minh. Bí mật chỉ nằm phía backend.
6. Draft, validation snapshot và history được lưu theo transaction. Chưa tạo bản chính thức.
7. PM kiểm tra/chỉnh sửa rồi confirm đúng version; service đổi trạng thái, ghi biên bản/audit và lịch sử; không biến gợi ý nhân sự thành phân công tự động.

Lưu ý: context weekly hiện lấy task/blockers, không có đầy đủ bình luận dù nguồn mô tả có bình luận. Global workload và nguồn dữ liệu ngoài project là phần mở rộng C04, cần đọc cùng chính sách riêng tư trong requirements-decisions.md.
