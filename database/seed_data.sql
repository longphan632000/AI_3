-- ====================================================================
-- Dữ liệu mẫu (Seed Data) chuẩn hóa cho Đề tài 33
-- Mật khẩu mặc định của tất cả các tài khoản mẫu: Password123!
-- ====================================================================

USE ai_project_management;

-- 1. Chèn Users
INSERT INTO users (id, username, email, password_hash, full_name, role, status) VALUES
(1, 'admin', 'admin@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Quản trị viên Hệ thống', 'admin', 'active'),
(2, 'leader_long', 'phanchanlong@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Phan Chân Long (Trưởng nhóm 33)', 'leader', 'active'),
(3, 'member_my', 'luutramy@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Lưu Trà My (Thành viên 33)', 'member', 'active'),
(4, 'member_khanh', 'lenamkhanh@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Lê Nam Khánh (Thành viên 33)', 'member', 'active'),
(5, 'locked_user', 'locked@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Tài khoản Bị Khóa Kiểm Thử', 'member', 'locked')
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

-- 2. Chèn Dự án mẫu (Đề tài 33)
INSERT INTO projects (id, name, description, start_date, end_date, status, created_by, is_archived) VALUES
(1, 'Hệ thống Quản lý Dự án Nhóm Tích hợp AI', 'Dự án môn Phân tích Thiết kế Hệ thống - Nhóm 33. Hệ thống quản lý dự án linh hoạt, tích hợp 3 chức năng trợ lý AI an toàn có kiểm duyệt con người.', '2026-09-01', '2026-10-31', 'active', 2, FALSE)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 3. Chèn Thành viên dự án với Kỹ năng, Mức sẵn sàng và Năng lực BR-05
INSERT INTO project_members (id, project_id, user_id, project_role, skills, availability, capacity_hours) VALUES
(1, 1, 2, 'leader', 'Phân tích hệ thống, Kiến trúc phần mềm, Quản lý dự án, Python Flask, MySQL', '100% (Toàn thời gian)', 40.00),
(2, 1, 3, 'member', 'Thiết kế giao diện UI/UX, Frontend HTML/CSS/JS, Testing, Tài liệu URD', '80% (Bán thời gian)', 32.00),
(3, 1, 4, 'member', 'Backend API, Cơ sở dữ liệu MySQL, Tích hợp AI Gemini, PlantUML', '100% (Toàn thời gian)', 40.00)
ON DUPLICATE KEY UPDATE skills=VALUES(skills);

-- 4. Chèn Sprint mẫu (Tuân thủ BR-03)
INSERT INTO sprints (id, project_id, name, goal, start_date, end_date, status, completion_criteria) VALUES
(1, 1, 'Sprint 1: Phân tích & Kiến trúc Core', 'Hoàn tất URD, sơ đồ kiến trúc, CSDL MySQL và khung ứng dụng Flask', '2026-09-01', '2026-09-20', 'completed', 'Tất cả tài liệu URD, ERD, Schema được duyệt qua Human Gate 1 & 2'),
(2, 1, 'Sprint 2: Lập trình Core & Tích hợp AI', 'Xây dựng Kanban 5 trạng thái, 3 module AI an toàn và hệ thống thông báo', '2026-09-21', '2026-10-10', 'active', 'Hoàn tất FR-01 đến FR-14 và kiểm thử tự động pass 100%')
ON DUPLICATE KEY UPDATE goal=VALUES(goal);

-- 5. Chèn Nhiệm vụ mẫu (Đầy đủ 5 trạng thái Kanban theo BR-01 & điều kiện BR-02)
INSERT INTO tasks (id, project_id, sprint_id, title, description, assignee_id, reporter_id, status, priority, due_date, estimated_hours, labels, blockers) VALUES
-- Nhiệm vụ 1: Hoàn thành (Done)
(1, 1, 1, 'Thiết kế mô hình hệ thống và tài liệu URD', 'Phân tích yêu cầu FR-01..FR-17, BR-01..BR-09 và vẽ Use Case Diagram', 2, 2, 'done', 'high', '2026-09-10 17:00:00', 16.00, 'Tài liệu, URD', NULL),
-- Nhiệm vụ 2: Hoàn thành (Done)
(2, 1, 1, 'Thiết kế CSDL MySQL chuẩn 3NF', 'Xây dựng schema.sql 13 bảng với đầy đủ ràng buộc PK, FK, CHECK', 4, 2, 'done', 'high', '2026-09-18 17:00:00', 12.00, 'Database, MySQL', NULL),
-- Nhiệm vụ 3: Đang làm (In Progress)
(3, 1, 2, 'Lập trình Bảng Kanban tương tác và API Nhiệm vụ', 'Xây dựng kéo thả Kanban 5 cột theo BR-01, API CRUD nhiệm vụ, lọc và phân trang', 3, 2, 'in_progress', 'high', '2026-09-28 17:00:00', 20.00, 'Frontend, Kanban', NULL),
-- Nhiệm vụ 4: Cần làm (To do)
(4, 1, 2, 'Xây dựng Pipeline 5 bước Trợ lý AI và Gemini Adapter', 'Triển khai Request Analyzer, Data Retriever, Context Builder, Response Validator', 4, 2, 'todo', 'urgent', '2026-09-30 17:00:00', 24.00, 'AI, Gemini, Backend', NULL),
-- Nhiệm vụ 5: Kiểm tra (Review)
(5, 1, 2, 'Thiết kế giao diện 3D Tech và Dark Mode', 'Triển khai hiệu ứng 3D tilt card, vòng tiến độ isometric và theme tối công nghệ', 3, 2, 'review', 'medium', '2026-09-26 17:00:00', 14.00, 'UI/UX, 3D', 'Chờ feedback từ Trưởng nhóm'),
-- Nhiệm vụ 6: Tồn đọng (Backlog)
(6, 1, 2, 'Tích hợp hệ thống Email cảnh báo nhiệm vụ trễ hạn (FR-17)', 'Tự động gửi email đến người phụ trách theo quy tắc BR-09 khi quá hạn', 4, 2, 'backlog', 'medium', '2026-10-05 17:00:00', 8.00, 'Notification, Email', NULL),
-- Nhiệm vụ 7: Trễ hạn (Overdue Task để test BR-02 & BR-09)
(7, 1, 2, 'Rà soát tài liệu kiểm thử và ma trận truy vết', 'Đối chiếu test-cases.md với requirements-traceability.md', 3, 2, 'in_progress', 'high', '2026-09-22 17:00:00', 10.00, 'Testing, QA', 'Cần bổ sung test case AI injection')
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 6. Chèn Bình luận mẫu (UC007)
INSERT INTO comments (id, task_id, user_id, content) VALUES
(1, 3, 2, 'Phan Chân Long: Lưu ý áp dụng đúng quy tắc BR-01 khi kéo thả nhiệm vụ qua 5 cột trạng thái nhé.'),
(2, 3, 3, 'Lưu Trà My: Đã nắm rõ ạ, em đang hoàn thiện hiệu ứng 3D tilt và animation kéo thả mượt mà.')
ON DUPLICATE KEY UPDATE content=VALUES(content);

-- 7. Chèn Ghi chú cuộc họp mẫu (FR-08 / Đầu vào cho AI Biên bản họp FR-13)
INSERT INTO meeting_notes (id, project_id, title, meeting_date, attendees, content, created_by) VALUES
(1, 1, 'Họp Sprint Review 1 và Lập kế hoạch Sprint 2', '2026-09-21 09:00:00', 'Phan Chân Long, Lưu Trà My, Lê Nam Khánh', 
'Nội dung cuộc họp:
1. Đánh giá Sprint 1: Nhóm đã hoàn thành xuất sắc URD và kiến trúc hệ thống, được GV Nguyễn Đình Dũng duyệt thông qua Human Gate 1.
2. Mục tiêu Sprint 2: Hoàn thiện lập trình hệ thống quản lý dự án tích hợp AI.
3. Thảo luận các rủi ro: Đảm bảo AI không được tự ý ghi CSDL, bắt buộc Trưởng nhóm phải xác nhận bản nháp biên bản họp và bản tóm tắt tiến độ tuần.
4. Phân công nhiệm vụ cụ thể:
- Lưu Trà My: Chịu trách nhiệm hoàn thành giao diện Kanban 5 cột và phong cách 3D công nghệ, thời hạn đến 28/09/2026.
- Lê Nam Khánh: Hoàn thiện pipeline 5 bước Trợ lý AI và Gemini adapter, thời hạn đến 30/09/2026.
- Phan Chân Long: Giám sát chung, review code, kiểm thử bảo mật và kết nối CSDL MySQL.
5. Quyết định: Buổi họp tiếp theo sẽ diễn ra vào sáng thứ Hai tuần tới lúc 09:00.', 2)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 8. Chèn Thông báo mẫu (FR-16)
INSERT INTO notifications (id, user_id, project_id, task_id, event_type, title, message, is_read) VALUES
(1, 3, 1, 3, 'task_assigned', 'Nhiệm vụ mới được giao', 'Bạn được phân công phụ trách nhiệm vụ: Lập trình Bảng Kanban tương tác và API Nhiệm vụ.', FALSE),
(2, 4, 1, 4, 'task_assigned', 'Nhiệm vụ mới được giao', 'Bạn được phân công phụ trách nhiệm vụ: Xây dựng Pipeline 5 bước Trợ lý AI và Gemini Adapter.', FALSE),
(3, 3, 1, 7, 'due_soon_reminder', 'Cảnh báo nhiệm vụ trễ hạn', 'Nhiệm vụ "Rà soát tài liệu kiểm thử và ma trận truy vết" đã quá hạn từ ngày 22/09/2026.', FALSE)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 9. Chèn Audit Log mẫu (FR-02)
INSERT INTO audit_logs (id, user_id, action, target_type, target_id, details_json, ip_address) VALUES
(1, 1, 'INITIALIZE_SYSTEM', 'SYSTEM', 1, '{"message": "Khởi tạo hệ thống quản lý dự án nhóm AI Nhóm 33"}', '127.0.0.1'),
(2, 2, 'CREATE_PROJECT', 'PROJECT', 1, '{"name": "Hệ thống Quản lý Dự án Nhóm Tích hợp AI"}', '127.0.0.1')
ON DUPLICATE KEY UPDATE action=VALUES(action);
