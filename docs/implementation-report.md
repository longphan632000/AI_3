# Đối chiếu implementation theo Skill

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

| UC | Module hiện hữu | Kiểm tra đã thực hiện |
| --- | --- | --- |
| UC001, Đăng nhập, đăng xuất | routes/auth_routes.py, services/auth_service.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC002, Quản lý tài khoản | routes/admin_routes.py, services/account_service.py, services/audit_service.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC003, Quản lý dự án | routes/project_routes.py, services/project_service.py, database/archive_schema.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC004, Quản lý thành viên | routes/project_routes.py, services/project_member_service.py, services/member_profile_service.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC005, Quản lý nhiệm vụ | routes/task_routes.py, services/task_service.py, static/js/kanban.js | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC006, Quản lý Sprint/Mốc | routes/sprint_routes.py, services/sprint_service.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC007, Cộng tác | routes/collaboration_routes.py, services/collaboration_service.py, services/attachment_service.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC008, Tra cứu & Báo cáo | routes/report_routes.py, services/report_service.py, static/js/reports.js | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC009, AI Tóm tắt tiến độ | routes/ai_routes.py, services/ai_assistant_service.py, services/project_data_retriever.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC010, AI Sinh biên bản họp | routes/ai_routes.py, services/meeting_minutes_service.py, services/ai_draft_service.py, services/ai_confirmation_service.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC011, AI Gợi ý phân công | routes/ai_routes.py, services/staffing_service.py, static/js/staffing.js | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC012, Lịch sử AI | routes/ai_routes.py, services/ai_history_service.py | Đọc mã + liên kết requirements/test; không tái lập trình |
| UC013, Nhận thông báo | routes/notification_routes.py, services/notification_service.py, services/email_service.py, services/deadline_worker.py | Đọc mã + liên kết requirements/test; không tái lập trình |

Lượt này không triển khai lại core, provider, AI coordinator, API hay UI. Các prompt 04/14/15/16/17 được áp dụng dưới dạng đọc và kiểm chứng hiện trạng đúng phạm vi user; không trình bày như vừa viết mới các module. 89 tệp runtime/cấu hình giữ nguyên hash, schema/migration không chạy, server không restart.

Linter đã chạy thực tế và còn 8 cảnh báo; tests và defects ở test-report.md/code-review.md. Các Skill procedure được bổ sung vì các bản cũ quá rút gọn, đây là thay đổi tài liệu phát triển, không là code runtime.
