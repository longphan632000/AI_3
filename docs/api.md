# API hiện trạng

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

Kiểm kê tĩnh 82 tuyến route/decorator trong app.py và routes/. Bảng gồm trang HTML lẫn API để không bỏ mất entry point; HEAD/OPTIONS tự động của Flask không liệt kê. Vai trò tóm tắt không thay điều kiện trong handler/service.

| Phương thức | Đường dẫn | Quyền tóm tắt | Handler nguồn | Trường đọc trực tiếp trong handler |
| --- | --- | --- | --- | --- |
| GET | `/sw.js` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | app.py:182 (service_worker) | Xem handler/service |
| GET | `/api/health` | Public; chỉ health, không secret | app.py:189 (health_check) | Xem handler/service |
| GET | `/api/system/db-status` | Admin tại backend | app.py:201 (db_status_api) | Xem handler/service |
| GET | `/admin` | Admin tại backend | routes/admin_routes.py:26 (admin_page) | Xem handler/service |
| GET | `/api/admin/ai-status` | Admin tại backend | routes/admin_routes.py:34 (ai_status_api) | request.args:probe |
| GET | `/api/admin/users` | Admin tại backend | routes/admin_routes.py:85 (get_users_api) | Xem handler/service |
| POST | `/api/admin/users` | Admin tại backend | routes/admin_routes.py:91 (create_user_api) | data:email, data:full_name, data:password, data:role, data:user_code, data:username |
| PUT | `/api/admin/users/<int:user_id>` | Admin tại backend | routes/admin_routes.py:108 (update_user_api) | data:email, data:full_name, data:password |
| POST | `/api/admin/users/<int:user_id>/status` | Admin tại backend | routes/admin_routes.py:121 (update_status_api) | data:status |
| POST | `/api/admin/users/<int:user_id>/role` | Admin tại backend | routes/admin_routes.py:130 (update_role_api) | data:role |
| POST | `/api/admin/users/<int:user_id>/review` | Admin tại backend | routes/admin_routes.py:139 (review_leader_request_api) | data:decision, data:user_code |
| DELETE | `/api/admin/users/<int:user_id>` | Admin tại backend | routes/admin_routes.py:152 (delete_user_api) | Xem handler/service |
| POST | `/api/admin/users/<int:user_id>/delete` | Admin tại backend | routes/admin_routes.py:152 (delete_user_api) | Xem handler/service |
| GET | `/api/admin/audit-logs` | Admin tại backend | routes/admin_routes.py:161 (get_audit_logs_api) | request.args:limit |
| GET | `/api/admin/projects/<int:project_id>/leaders` | Admin tại backend | routes/admin_routes.py:168 (list_project_leaders_api) | Xem handler/service |
| POST | `/api/admin/projects/<int:project_id>/leaders` | Admin tại backend | routes/admin_routes.py:175 (assign_project_leader_api) | data:user_id |
| DELETE | `/api/admin/projects/<int:project_id>/leaders/<int:user_id>` | Admin tại backend | routes/admin_routes.py:185 (demote_project_leader_api) | Xem handler/service |
| GET | `/api/admin/ai-history` | Admin tại backend | routes/admin_routes.py:194 (admin_ai_history_api) | request.args:limit, request.args:project_id |
| GET | `/ai-assistant` | Session + project scope; weekly/staffing/confirm chỉ PM; meeting PM/Member; history Admin/PM | routes/ai_routes.py:12 (ai_assistant_page) | Xem handler/service |
| POST | `/api/ai` | Session + project scope; weekly/staffing/confirm chỉ PM; meeting PM/Member; history Admin/PM | routes/ai_routes.py:19 (process_ai_api) | Xem handler/service |
| POST | `/api/ai/drafts/<int:draft_id>/confirm` | Session + project scope; weekly/staffing/confirm chỉ PM; meeting PM/Member; history Admin/PM | routes/ai_routes.py:35 (confirm_draft_api) | Xem handler/service |
| GET | `/api/ai/history` | Session + project scope; weekly/staffing/confirm chỉ PM; meeting PM/Member; history Admin/PM | routes/ai_routes.py:56 (get_ai_history_api) | request.args:limit, request.args:project_id |
| POST | `/api/ai/upload-meeting-file` | Session + project scope; weekly/staffing/confirm chỉ PM; meeting PM/Member; history Admin/PM | routes/ai_routes.py:72 (upload_meeting_file_api) | Xem handler/service |
| GET | `/api/projects/<int:project_id>/meeting-minutes` | Session + project scope; weekly/staffing/confirm chỉ PM; meeting PM/Member; history Admin/PM | routes/ai_routes.py:166 (get_project_meeting_minutes_api) | Xem handler/service |
| GET, PUT | `/api/ai/drafts/<int:draft_id>` | Session + project scope; weekly/staffing/confirm chỉ PM; meeting PM/Member; history Admin/PM | routes/ai_routes.py:196 (read_edit_draft_api) | data:version |
| GET | `/login` | Login/register public; /me theo session; logout xóa phiên | routes/auth_routes.py:8 (login_page) | Xem handler/service |
| POST | `/api/auth/login` | Login/register public; /me theo session; logout xóa phiên | routes/auth_routes.py:16 (login_api) | data:password, data:username_or_email |
| POST | `/api/auth/register` | Login/register public; /me theo session; logout xóa phiên | routes/auth_routes.py:50 (register_api) | data:email, data:full_name, data:password, data:role, data:username |
| GET, POST | `/logout` | Login/register public; /me theo session; logout xóa phiên | routes/auth_routes.py:72 (logout) | Xem handler/service |
| GET | `/api/auth/me` | Login/register public; /me theo session; logout xóa phiên | routes/auth_routes.py:77 (get_current_user) | Xem handler/service |
| GET, POST | `/api/tasks/<int:task_id>/attachments` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/collaboration_routes.py:17 (task_attachments_api) | data:name, data:url |
| GET | `/api/attachments/<int:attachment_id>/download` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/collaboration_routes.py:43 (download_attachment_api) | Xem handler/service |
| GET | `/api/tasks/<int:task_id>/comments` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/collaboration_routes.py:61 (get_comments_api) | Xem handler/service |
| POST | `/api/tasks/<int:task_id>/comments` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/collaboration_routes.py:75 (add_comment_api) | data:content |
| GET | `/api/projects/<int:project_id>/meeting-notes` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/collaboration_routes.py:93 (get_notes_api) | Xem handler/service |
| POST | `/api/projects/<int:project_id>/meeting-notes` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/collaboration_routes.py:103 (create_note_api) | data:attendees, data:content, data:meeting_date, data:title |
| GET | `/notifications` | Chính user; trigger theo project/role; không xem hộ | routes/notification_routes.py:12 (notifications_page) | Xem handler/service |
| GET | `/api/notifications` | Chính user; trigger theo project/role; không xem hộ | routes/notification_routes.py:19 (list_notifications_api) | request.args:limit, request.args:unread_only |
| GET | `/api/notifications/unread-count` | Chính user; trigger theo project/role; không xem hộ | routes/notification_routes.py:27 (unread_count_api) | Xem handler/service |
| POST | `/api/notifications/<int:notification_id>/read` | Chính user; trigger theo project/role; không xem hộ | routes/notification_routes.py:33 (mark_read_api) | Xem handler/service |
| POST | `/api/notifications/read-all` | Chính user; trigger theo project/role; không xem hộ | routes/notification_routes.py:39 (mark_all_read_api) | Xem handler/service |
| POST | `/api/notifications/trigger-overdue-check` | Chính user; trigger theo project/role; không xem hộ | routes/notification_routes.py:45 (trigger_overdue_check_api) | request.args:project_id |
| GET | `/team` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:18 (team_page) | Xem handler/service |
| GET | `/` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:24 (index) | Xem handler/service |
| GET | `/dashboard` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:30 (dashboard_page) | Xem handler/service |
| GET | `/api/projects` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:37 (list_projects_api) | request.args:archived |
| POST | `/api/projects` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:43 (create_project_api) | data:description, data:end_date, data:initial_member_ids, data:member_ids, data:name, data:project_code, data:start_date |
| GET | `/api/projects/<int:project_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:63 (get_project_api) | Xem handler/service |
| PUT | `/api/projects/<int:project_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:71 (update_project_api) | data:description, data:end_date, data:name, data:project_code, data:start_date, data:status |
| DELETE | `/api/projects/<int:project_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:92 (delete_project_api) | request.args:permanent |
| GET | `/api/projects/<int:project_id>/members` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:110 (get_members_api) | Xem handler/service |
| POST | `/api/projects/<int:project_id>/members` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:119 (add_member_api) | data:availability, data:capacity_hours, data:project_role, data:skills, data:use_professional_profile, data:user_id, data:user_ids |
| GET | `/api/projects/<int:project_id>/eligible-users` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:153 (eligible_users_api) | Xem handler/service |
| GET | `/api/users/assignable` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:167 (assignable_users_api) | Xem handler/service |
| PUT | `/api/projects/<int:project_id>/members/<int:user_id>/capacity` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:181 (update_capacity_api) | data:availability, data:capacity_hours, data:skills |
| DELETE | `/api/projects/<int:project_id>/members/<int:user_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/project_routes.py:201 (remove_member_api) | Xem handler/service |
| POST | `/api/projects/<int:project_id>/restore` | Project scope; archive chỉ Admin hoặc PM archived_by; restore role kiểm lại | routes/project_routes.py:211 (restore_project_api) | Xem handler/service |
| GET, PUT | `/api/me/professional-profile` | Chính session member/leader; bỏ qua user_id từ client | routes/project_routes.py:222 (professional_profile_api) | data:availability, data:capacity_hours, data:skills |
| POST | `/api/projects/<int:project_id>/staffing-preview` | Admin/PM của dự án; read-only POST có kiểm scope | routes/project_routes.py:239 (staffing_preview_api) | data:limit, data:offset, data:search |
| GET | `/projects/<int:project_id>/archived` | Project scope; archive chỉ Admin hoặc PM archived_by; restore role kiểm lại | routes/project_routes.py:261 (archived_project_page) | Xem handler/service |
| GET | `/api/projects/<int:project_id>/archive-details` | Project scope; archive chỉ Admin hoặc PM archived_by; restore role kiểm lại | routes/project_routes.py:271 (archived_project_details_api) | request.args:limit, request.args:offset |
| GET | `/api/projects/<int:project_id>/report` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/report_routes.py:13 (project_report_api) | request.args:sprint_id |
| GET | `/reports` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/report_routes.py:26 (reports_page) | Xem handler/service |
| GET | `/api/projects/<int:project_id>/dashboard-metrics` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/report_routes.py:33 (get_metrics_api) | request.args:sprint_id |
| GET | `/api/projects/<int:project_id>/workload-stats` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/report_routes.py:44 (get_workload_api) | request.args:sprint_id |
| GET | `/sprints` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/sprint_routes.py:13 (sprints_page) | Xem handler/service |
| GET | `/api/projects/<int:project_id>/sprints` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/sprint_routes.py:20 (list_sprints_api) | request.args:archived |
| POST | `/api/projects/<int:project_id>/sprints` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/sprint_routes.py:30 (create_sprint_api) | data:completion_criteria, data:end_date, data:goal, data:name, data:sprint_code, data:start_date |
| PUT | `/api/sprints/<int:sprint_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/sprint_routes.py:54 (update_sprint_api) | data:completion_criteria, data:end_date, data:goal, data:name, data:sprint_code, data:start_date, data:status |
| POST | `/api/tasks/<int:task_id>/assign-sprint` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/sprint_routes.py:83 (assign_sprint_api) | data:sprint_id |
| DELETE | `/api/sprints/<int:sprint_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/sprint_routes.py:103 (archive_or_restore_sprint_api) | Xem handler/service |
| POST | `/api/sprints/<int:sprint_id>/restore` | Project scope; archive chỉ Admin hoặc PM archived_by; restore role kiểm lại | routes/sprint_routes.py:103 (archive_or_restore_sprint_api) | Xem handler/service |
| GET | `/api/sync` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/sync_routes.py:15 (sync_status) | Xem handler/service |
| GET | `/kanban` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/task_routes.py:22 (kanban_page) | Xem handler/service |
| GET | `/api/projects/<int:project_id>/tasks` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/task_routes.py:29 (list_tasks_api) | request.args:archived, request.args:assignee_id, request.args:due_from, request.args:due_to, request.args:keyword, request.args:limit, request.args:offset, request.args:overdue_only, request.args:priority, request.args:sort_by, request.args:sort_order, request.args:sprint_id, request.args:status |
| POST | `/api/projects/<int:project_id>/tasks` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/task_routes.py:60 (create_task_api) | data:assignee_id, data:blockers, data:description, data:due_date, data:estimated_hours, data:labels, data:priority, data:sprint_id, data:support_member_ids, data:supporters, data:task_code, data:title |
| GET | `/api/tasks/<int:task_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/task_routes.py:90 (get_task_api) | Xem handler/service |
| PUT | `/api/tasks/<int:task_id>/status` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/task_routes.py:103 (update_status_api) | data:status |
| POST, PUT | `/api/tasks/<int:task_id>/progress` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/task_routes.py:129 (update_progress_api) | data:progress_percent |
| PUT | `/api/tasks/<int:task_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/task_routes.py:155 (update_task_api) | data:assignee_id, data:blockers, data:description, data:due_date, data:estimated_hours, data:labels, data:priority, data:progress_percent, data:sprint_id, data:support_member_ids, data:supporters, data:task_code, data:title |
| DELETE | `/api/tasks/<int:task_id>` | Session + project/object scope; write theo PM/member được giao/hỗ trợ; viewer read-only | routes/task_routes.py:187 (archive_task_api) | Xem handler/service |
| POST | `/api/tasks/<int:task_id>/restore` | Project scope; archive chỉ Admin hoặc PM archived_by; restore role kiểm lại | routes/task_routes.py:203 (restore_task_api) | Xem handler/service |

## Hợp đồng AI

`POST /api/ai`: JSON có project_id, task_type. weekly_summary cần week_start/week_end (YYYY-MM-DD, không đảo hai cận; sprint_id tùy chọn). meeting_minutes cần meeting_note_id hoặc raw_notes tối đa 120.000 ký tự. assignment_suggestion cần task_id với nhánh cũ; chế độ staffing_version=2 thêm purpose assignment/recruitment, candidate_scope system/project, requested_count 1–100, user_note. recruitment không yêu cầu task, cần mô tả nhu cầu. requester_id và role lấy session.

Thành công: success, draft_id, version, result, source_references, status draft/needs_verification, warnings, engine, structured_result. `POST /api/ai/drafts/<id>/confirm` gửi version; chỉ PM có quyền và draft hợp lệ mới chuyển confirmed. `PUT /api/ai/drafts/<id>` chỉnh có version, ghi revisions, không sửa bản confirmed. ID thiếu/ngoài quyền không được dùng như nguồn thật.

Ví dụ payload không chứa dữ liệu người thật/khóa:

```json
{"project_id": 123, "task_type": "assignment_suggestion", "staffing_version": 2, "purpose": "recruitment", "candidate_scope": "system", "requested_count": 5, "user_note": "Tôi cần 5 người backend"}
```

## Mã phản hồi

200/201 thành công; 202 đăng ký chờ duyệt; 400 đầu vào sai; 401 chưa đăng nhập/account không còn active; 403 ngoài quyền; 404 không tồn tại/không được xem; 409 xung đột version/toàn vẹn hoặc dữ liệu archived; 413 quá dung lượng; 422 xử lý AI không phù hợp; 503 database/provider không sẵn sàng. Phân loại cụ thể tùy route, không khẳng định mọi lỗi đều cùng status. Thông báo provider được chuẩn hóa, không trả body/key/stack trace.

Các trường trong cột kiểm kê chỉ là get() trực tiếp, không phải OpenAPI schema đầy đủ: ví dụ multipart/file và dữ liệu chuyển tiếp tới service cần đọc handler. `POST /staffing-preview` chỉ tính dữ liệu; thêm thành viên qua POST members; giao việc qua PUT task là các thao tác riêng có xác nhận.

## Quyền cộng tác đã quan sát riêng

PROBE-02 dùng SQLite tạm: Admin POST comment và meeting-note được 201, POST attachment bị 403. Viewer bị write middleware chặn. Admin không được mô tả chung là chỉ xem mọi thao tác UC007; chính sách thao tác cần nhóm đối chiếu REQ-02.

Bảng phân biệt thao tác của từng vai trò: [role-permissions](tables/role-permissions.md).
