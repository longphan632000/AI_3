# Chuẩn hóa và kiểm quyền yêu cầu AI

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Task | Ai tạo | Dữ liệu | Đầu ra/kiểm định |
| --- | --- | --- | --- |
| weekly_summary | PM của dự án | Khoảng tuần + task tạo/cập nhật/có hạn trong hai cận bao gồm; sprint tùy chọn | Tiến độ/rủi ro/ưu tiên có Task ID; không kết luận thời điểm hoàn thành từ snapshot |
| meeting_minutes | PM/Member có quyền | Ghi chú thuộc project hoặc raw/tệp; chia passage khi dài | Thảo luận/quyết định/action_items, tham chiếu passage; chưa có người/hạn thì để chưa xác định |
| assignment_suggestion | PM của dự án | Task + hồ sơ/năng lực/tải; v2 recruitment không cần task | ID đủ điều kiện/số lượng, lý do/số liệu dựng từ nguồn; không tự thêm/giao |

Structured request luôn có task_type, project_id, requester_id từ session, requester_role từ membership. Weekly cần hai ngày ISO, đầu không sau cuối. Meeting cần note_id hoặc raw_notes string <=120.000 ký tự. Assignment nhánh cũ cần task_id; v2 có purpose/scope/count/skills/user_note được normalize_staffing_options xử lý. Không nhận trường status=confirmed hoặc requester_role từ client để cấp quyền.

Các quy tắc active/archived cũng được kiểm ngoài analyzer bởi middleware/coordinator. Admin xem history/draft theo quyền nhưng không được gọi weekly/meeting/staffing hoặc confirm chỉ vì là Admin. Meeting Member chỉ đọc/sửa draft meeting của chính họ khi chưa confirmed; bản confirmed theo scope.

Validation đầu vào sai không được ghi một phần dữ liệu. Một số lỗi analyzer trả 403, ValidationError trả 400; không giả định tất cả validation có cùng HTTP code.
