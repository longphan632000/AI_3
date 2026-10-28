# Mô hình hệ thống hiện trạng

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

## Ranh giới

Trình duyệt HTML/CSS/JavaScript gọi HTTP tới Flask. Flask kiểm tra session/vai trò/project scope, gọi services và lớp database/connection. MySQL là kho nghiệp vụ runtime; SQLite chỉ cho bộ kiểm thử được bật rõ ràng. Gemini qua HTTP ở lớp Provider; có local model/domain rules dự phòng. SMTP là cổng gửi email tùy cấu hình. Máy khách không đọc DB/khóa AI trực tiếp.

## Bảy nhóm chức năng

1. Tài khoản và phân quyền (UC001/002).
2. Dự án và thành viên (UC003/004).
3. Nhiệm vụ và Kanban (UC005).
4. Sprint và mốc thời gian (UC006; milestone độc lập chưa có).
5. Cộng tác (UC007).
6. Tra cứu, báo cáo, lịch sử và thông báo (UC008/012/013).
7. Trợ lý AI (UC009/010/011).

Bảy nhóm trên tổ chức lại các UC đã có để trình bày, không bổ sung UC mới. Vai trò, luật và quan hệ chi tiết nằm trong các bảng và requirements.md.

## Luồng tổng quát

PM tạo dự án → thêm người/năng lực → Sprint/nhiệm vụ → phân công thủ công hoặc xin gợi ý AI → PM quyết định → Member thực hiện/cập nhật/cộng tác → hệ thống tính tiến độ/tải/trễ → người có quyền yêu cầu tóm tắt/biên bản → kiểm định → chỉnh sửa/xác nhận bởi PM. AI không nằm trong đường ghi nghiệp vụ tự động. Tạo draft và nhật ký là lưu vết, không phải phê duyệt chính thức.

## Đối tượng và quan hệ

TaiKhoan↔DuAn qua ThanhVienDuAn; DuAn→Sprint/NhiemVu; NhiemVu↔TaiKhoan qua task_assignees, đồng thời có assignee chính; NhiemVu→comments/attachments; DuAn→meeting_notes/meeting_minutes/ai_drafts/ai_history; draft→revisions; users→member_profiles; notifications/audit/email_deliveries phục vụ theo dõi. ERD bám 17 bảng DDL, không dùng sáu bảng minh họa URD như thể là toàn bộ cơ sở dữ liệu.

## Điều kiện sử dụng mô hình

Mô hình này lập từ URD và mã đang có, chưa có chữ ký Human Gate 0. Được dùng để ghi nhận thiết kế hiện trạng theo phạm vi chủ hệ thống đã cho phép; không dùng làm cớ thực hiện thay đổi phần mềm hoặc khẳng định đã duyệt trước triển khai.
