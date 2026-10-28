# Từ điển dữ liệu 17 bảng

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

Trích tĩnh từ database/schema.sql; kiểu/ràng buộc không được suy từ tên. Giá trị cụ thể dữ liệu người dùng không được đưa vào hồ sơ.

## users

Tài khoản/role/status; hash mật khẩu không gửi ra AI. Nguồn: `database/schema.sql:14`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| user_code | VARCHAR(50) UNIQUE |
| username | VARCHAR(50) NOT NULL UNIQUE |
| email | VARCHAR(100) NOT NULL UNIQUE |
| password_hash | VARCHAR(255) NOT NULL |
| full_name | VARCHAR(100) NOT NULL |
| role | ENUM('admin', 'leader', 'member') NOT NULL DEFAULT 'member' |
| status | ENUM('active', 'pending', 'rejected', 'locked') NOT NULL DEFAULT 'active' |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `INDEX idx_user_role (role)`
- `INDEX idx_user_status (status)`

## projects

Dự án, trạng thái, người lưu trữ. Nguồn: `database/schema.sql:30`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| project_code | VARCHAR(50) UNIQUE |
| name | VARCHAR(150) NOT NULL |
| description | LONGTEXT |
| start_date | DATE |
| end_date | DATE |
| status | ENUM('planning', 'active', 'completed', 'archived') NOT NULL DEFAULT 'planning' |
| created_by | INT NOT NULL |
| is_archived | BOOLEAN NOT NULL DEFAULT FALSE |
| archived_by | INT NULL |
| archived_at | DATETIME NULL |
| pre_archive_status | VARCHAR(20) NULL |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT`
- `INDEX idx_proj_status (status)`
- `INDEX idx_proj_archived (is_archived)`

## project_members

Quan hệ người–dự án và năng lực riêng. Nguồn: `database/schema.sql:51`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| project_id | INT NOT NULL |
| user_id | INT NOT NULL |
| project_role | ENUM('leader', 'member', 'viewer') NOT NULL DEFAULT 'member' |
| skills | LONGTEXT |
| availability | VARCHAR(50) DEFAULT 'Full-time' |
| capacity_hours | DECIMAL(6,2) DEFAULT 40.00 |
| joined_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `UNIQUE KEY uk_project_user (project_id, user_id)`
- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_pm_project (project_id)`
- `INDEX idx_pm_user (user_id)`

## sprints

Sprint, ngày, mục tiêu/tiêu chí. Nguồn: `database/schema.sql:68`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| sprint_code | VARCHAR(50) |
| project_id | INT NOT NULL |
| name | VARCHAR(100) NOT NULL |
| goal | LONGTEXT |
| start_date | DATE NOT NULL |
| end_date | DATE NOT NULL |
| status | ENUM('planning', 'active', 'completed', 'archived') NOT NULL DEFAULT 'planning' |
| completion_criteria | LONGTEXT |
| is_archived | BOOLEAN NOT NULL DEFAULT FALSE |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `INDEX idx_sprint_proj (project_id)`
- `INDEX idx_sprint_status (status)`

## tasks

Nhiệm vụ, trạng thái, phần trăm. Nguồn: `database/schema.sql:87`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| task_code | VARCHAR(50) |
| project_id | INT NOT NULL |
| sprint_id | INT NULL |
| title | VARCHAR(200) NOT NULL |
| description | LONGTEXT |
| assignee_id | INT NULL |
| reporter_id | INT NOT NULL |
| status | ENUM('backlog', 'todo', 'in_progress', 'review', 'done') NOT NULL DEFAULT 'backlog' |
| priority | ENUM('low', 'medium', 'high', 'urgent') NOT NULL DEFAULT 'medium' |
| due_date | DATETIME NULL |
| estimated_hours | DECIMAL(6,2) DEFAULT 0.00 |
| labels | VARCHAR(255) NULL |
| blockers | LONGTEXT NULL |
| progress_percent | INT NOT NULL DEFAULT 0 |
| is_archived | BOOLEAN NOT NULL DEFAULT FALSE |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `UNIQUE KEY uk_task_code(project_id,task_code)`
- `CHECK (estimated_hours >= 0)`
- `CHECK (progress_percent BETWEEN 0 AND 100)`
- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE SET NULL`
- `FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL`
- `FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE RESTRICT`
- `INDEX idx_task_proj_status (project_id, status)`
- `INDEX idx_task_assignee (assignee_id)`
- `INDEX idx_task_due_date (due_date)`
- `INDEX idx_task_sprint (sprint_id)`
- `INDEX idx_task_archived (is_archived)`

## comments

Trao đổi nhiệm vụ. Nguồn: `database/schema.sql:121`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| task_id | INT NOT NULL |
| user_id | INT NOT NULL |
| content | LONGTEXT NOT NULL |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE`
- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_comment_task (task_id)`

## attachments

Thông tin tệp/link, lưu file ngoài static. Nguồn: `database/schema.sql:133`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| project_id | INT NOT NULL |
| task_id | INT NULL |
| file_name | VARCHAR(255) NOT NULL |
| file_path | VARCHAR(500) NOT NULL |
| file_size | INT NOT NULL |
| file_type | VARCHAR(100) |
| uploaded_by | INT NOT NULL |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE`
- `FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_attach_task (task_id)`

## meeting_notes

Nguồn cuộc họp. Nguồn: `database/schema.sql:150`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| project_id | INT NOT NULL |
| title | VARCHAR(200) NOT NULL |
| meeting_date | DATETIME NOT NULL |
| attendees | TEXT |
| content | LONGTEXT NOT NULL |
| created_by | INT NOT NULL |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_note_proj (project_id)`

## meeting_minutes

Biên bản chính thức. Nguồn: `database/schema.sql:166`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| project_id | INT NOT NULL |
| meeting_note_id | INT NULL |
| title | VARCHAR(200) NOT NULL |
| summary | LONGTEXT NOT NULL |
| decisions | LONGTEXT |
| action_items | LONGTEXT |
| status | ENUM('draft', 'confirmed') NOT NULL DEFAULT 'draft' |
| created_by | INT NOT NULL |
| confirmed_by | INT NULL |
| confirmed_at | DATETIME NULL |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `FOREIGN KEY (meeting_note_id) REFERENCES meeting_notes(id) ON DELETE SET NULL`
- `FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE`
- `FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL`
- `INDEX idx_minutes_proj (project_id)`
- `INDEX idx_minutes_status (status)`

## ai_drafts

Bản nháp/validation snapshot/version. Nguồn: `database/schema.sql:189`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| project_id | INT NOT NULL |
| task_type | ENUM('weekly_summary', 'meeting_minutes', 'assignment_suggestion') NOT NULL |
| input_params_json | LONGTEXT NOT NULL |
| draft_content | LONGTEXT NOT NULL |
| source_references_json | LONGTEXT NOT NULL |
| structured_result_json | LONGTEXT NULL |
| status | ENUM('draft', 'needs_verification', 'confirmed', 'rejected') NOT NULL DEFAULT 'draft' |
| version | INT NOT NULL DEFAULT 1 |
| validation_json | LONGTEXT NULL |
| created_by | INT NOT NULL |
| confirmed_by | INT NULL |
| confirmed_at | DATETIME NULL |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE`
- `FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL`
- `INDEX idx_draft_proj (project_id)`
- `INDEX idx_draft_type (task_type)`

## ai_history

Người yêu cầu, provider/prompt version/tham chiếu. Nguồn: `database/schema.sql:212`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| draft_id | INT NULL |
| project_id | INT NOT NULL |
| requester_id | INT NOT NULL |
| task_type | ENUM('weekly_summary', 'meeting_minutes', 'assignment_suggestion') NOT NULL |
| model_provider | VARCHAR(50) NOT NULL DEFAULT 'deepseek' |
| prompt_version | VARCHAR(50) NOT NULL DEFAULT 'v1.0' |
| data_references_json | TEXT |
| result_summary | TEXT NOT NULL |
| confirmation_status | ENUM('draft', 'needs_verification', 'confirmed', 'rejected') NOT NULL DEFAULT 'draft' |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_aih_proj (project_id)`
- `INDEX idx_aih_req (requester_id)`

## notifications

Thông báo theo người/sự kiện/trạng thái đọc. Nguồn: `database/schema.sql:231`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| user_id | INT NOT NULL |
| project_id | INT NOT NULL |
| task_id | INT NULL |
| event_type | ENUM('task_assigned', 'assignee_changed', 'deadline_changed', 'status_changed', 'task_overdue', 'due_soon_reminder') NOT NULL |
| title | VARCHAR(200) NOT NULL |
| message | TEXT NOT NULL |
| is_read | BOOLEAN NOT NULL DEFAULT FALSE |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`
- `FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE`
- `FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL`
- `INDEX idx_noti_user_read (user_id, is_read)`

## audit_logs

Hành động, đối tượng, người/thời gian. Nguồn: `database/schema.sql:248`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| user_id | INT NULL |
| action | VARCHAR(100) NOT NULL |
| target_type | VARCHAR(50) NOT NULL |
| target_id | INT NULL |
| details_json | TEXT |
| ip_address | VARCHAR(50) NULL |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL`
- `INDEX idx_audit_user (user_id)`
- `INDEX idx_audit_time (created_at)`

## task_assignees

Người chính/hỗ trợ, chống đếm trùng. Nguồn: `database/schema.sql:263`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| task_id | INT NOT NULL |
| user_id | INT NOT NULL |
| is_primary | BOOLEAN NOT NULL DEFAULT FALSE |
| assigned_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `UNIQUE KEY uk_task_user(task_id,user_id)`
- `FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE`
- `FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`

## ai_draft_revisions

Lịch sử chỉnh sửa draft. Nguồn: `database/schema.sql:271`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| draft_id | INT NOT NULL |
| version | INT NOT NULL |
| edited_by | INT NULL |
| draft_content | LONGTEXT NOT NULL |
| structured_result_json | LONGTEXT |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `UNIQUE KEY uk_draft_version(draft_id,version)`
- `FOREIGN KEY(draft_id) REFERENCES ai_drafts(id) ON DELETE CASCADE`
- `FOREIGN KEY(edited_by) REFERENCES users(id) ON DELETE SET NULL`

## email_deliveries

Lease/dedup/retry gửi email. Nguồn: `database/schema.sql:280`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| id | INT AUTO_INCREMENT PRIMARY KEY |
| task_id | INT NOT NULL |
| user_id | INT NOT NULL |
| claim_key | VARCHAR(64) NOT NULL UNIQUE |
| claim_token | VARCHAR(32) NOT NULL |
| status | VARCHAR(32) NOT NULL |
| attempts | INT NOT NULL DEFAULT 1 |
| attempted_at | DATETIME NOT NULL |
| updated_at | DATETIME NOT NULL |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE`
- `FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`

## member_profiles

Hồ sơ năng lực chung. Nguồn: `database/schema.sql:290`.

| Trường | Kiểu và ràng buộc cột theo DDL |
| --- | --- |
| user_id | INT PRIMARY KEY |
| skills | LONGTEXT |
| availability | VARCHAR(50) NOT NULL DEFAULT '100%' |
| capacity_hours | DECIMAL(8,2) NOT NULL DEFAULT 40 |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP |

Ràng buộc/chỉ mục cấp bảng:

- `FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
