# Truy vết mô hình hệ thống

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Thành phần/quan hệ | Nguồn | Implementation | Trạng thái |
| --- | --- | --- | --- |
| UC001 Đăng nhập, đăng xuất | [URD L0245](source/urd-extracted.txt), FR-01 | routes/auth_routes.py, services/auth_service.py | Có mã; xem issue cho sai lệch |
| UC002 Quản lý tài khoản | [URD L0246](source/urd-extracted.txt), FR-02 | routes/admin_routes.py, services/account_service.py, services/audit_service.py | Có mã; xem issue cho sai lệch |
| UC003 Quản lý dự án | [URD L0247](source/urd-extracted.txt), FR-03 | routes/project_routes.py, services/project_service.py, database/archive_schema.py | Có mã; xem issue cho sai lệch |
| UC004 Quản lý thành viên | [URD L0248](source/urd-extracted.txt), FR-04 | routes/project_routes.py, services/project_member_service.py, services/member_profile_service.py | Có mã; xem issue cho sai lệch |
| UC005 Quản lý nhiệm vụ | [URD L0249](source/urd-extracted.txt), FR-05, FR-06 | routes/task_routes.py, services/task_service.py, static/js/kanban.js | Có mã; xem issue cho sai lệch |
| UC006 Quản lý Sprint/Mốc | [URD L0250](source/urd-extracted.txt), FR-07 | routes/sprint_routes.py, services/sprint_service.py | Có mã; xem issue cho sai lệch |
| UC007 Cộng tác | [URD L0251](source/urd-extracted.txt), FR-08 | routes/collaboration_routes.py, services/collaboration_service.py, services/attachment_service.py | Có mã; xem issue cho sai lệch |
| UC008 Tra cứu & Báo cáo | [URD L0252](source/urd-extracted.txt), FR-09, FR-10, FR-11 | routes/report_routes.py, services/report_service.py, static/js/reports.js | Có mã; xem issue cho sai lệch |
| UC009 AI Tóm tắt tiến độ | [URD L0253](source/urd-extracted.txt), FR-12 | routes/ai_routes.py, services/ai_assistant_service.py, services/project_data_retriever.py | Có mã; xem issue cho sai lệch |
| UC010 AI Sinh biên bản họp | [URD L0254](source/urd-extracted.txt), FR-13 | routes/ai_routes.py, services/meeting_minutes_service.py, services/ai_draft_service.py, services/ai_confirmation_service.py | Có mã; xem issue cho sai lệch |
| UC011 AI Gợi ý phân công | [URD L0255](source/urd-extracted.txt), FR-14 | routes/ai_routes.py, services/staffing_service.py, static/js/staffing.js | Có mã; xem issue cho sai lệch |
| UC012 Lịch sử AI | [URD L0256](source/urd-extracted.txt), FR-15 | routes/ai_routes.py, services/ai_history_service.py | Có mã; xem issue cho sai lệch |
| UC013 Nhận thông báo | [URD L0257](source/urd-extracted.txt), FR-16, FR-17 | routes/notification_routes.py, services/notification_service.py, services/email_service.py, services/deadline_worker.py | Có mã; xem issue cho sai lệch |

| Khái niệm nguồn | Bảng thật | Điểm khác |
| --- | --- | --- |
| TaiKhoan | users | Vai trò enum ba mức; nhiều trạng thái account hơn bit trong nguồn |
| DuAn | projects | start_date/end_date, provenance archive; không dùng cột ThoiGian đơn |
| ThanhVienDuAn | project_members | id PK + unique(project_id,user_id); thuộc tính kỹ năng/capacity |
| Sprint | sprints | Tiêu chí hoàn thành có thể NULL |
| NhiemVu | tasks + task_assignees | Hỗ trợ nhiều người, phần trăm tiến độ; hạn và sprint có thể NULL |
| LichSuAI | ai_history + ai_drafts + ai_draft_revisions | Tách bản nháp, phiên bản và lịch sử; prompt_version hiện cố định |
