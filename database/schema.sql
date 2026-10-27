-- ====================================================================
-- CSDL: ai_project_management
-- Hệ thống Quản lý Dự án Nhóm Tích hợp AI (Đề tài 33)
-- Chuẩn hóa 3NF, đầy đủ Khóa chính PK, Khóa ngoại FK, Ràng buộc CHECK và INDEX
-- ====================================================================

CREATE DATABASE IF NOT EXISTS ai_project_management 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE ai_project_management;

-- 1. Bảng Users (Tài khoản người dùng)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_code VARCHAR(50) UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'leader', 'member') NOT NULL DEFAULT 'member',
    status ENUM('active', 'pending', 'rejected', 'locked') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_role (role),
    INDEX idx_user_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Bảng Projects (Dự án)
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) UNIQUE,
    name VARCHAR(150) NOT NULL,
    description LONGTEXT,
    start_date DATE,
    end_date DATE,
    status ENUM('planning', 'active', 'completed', 'archived') NOT NULL DEFAULT 'planning',
    created_by INT NOT NULL,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_proj_status (status),
    INDEX idx_proj_archived (is_archived)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Bảng Project Members (Thành viên trong từng dự án & cấu hình năng lực BR-05)
CREATE TABLE IF NOT EXISTS project_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    user_id INT NOT NULL,
    project_role ENUM('leader', 'member', 'viewer') NOT NULL DEFAULT 'member',
    skills LONGTEXT,
    availability VARCHAR(50) DEFAULT 'Full-time',
    capacity_hours DECIMAL(6,2) DEFAULT 40.00,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_project_user (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_pm_project (project_id),
    INDEX idx_pm_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Bảng Sprints (Đợt làm việc ngắn theo BR-03)
CREATE TABLE IF NOT EXISTS sprints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sprint_code VARCHAR(50),
    project_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    goal LONGTEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('planning', 'active', 'completed', 'archived') NOT NULL DEFAULT 'planning',
    completion_criteria LONGTEXT,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_sprint_proj (project_id),
    INDEX idx_sprint_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Bảng Tasks (Nhiệm vụ - Kanban 5 trạng thái theo BR-01)
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_code VARCHAR(50),
    project_id INT NOT NULL,
    sprint_id INT NULL,
    title VARCHAR(200) NOT NULL,
    description LONGTEXT,
    assignee_id INT NULL,
    reporter_id INT NOT NULL,
    status ENUM('backlog', 'todo', 'in_progress', 'review', 'done') NOT NULL DEFAULT 'backlog',
    priority ENUM('low', 'medium', 'high', 'urgent') NOT NULL DEFAULT 'medium',
    due_date DATETIME NULL,
    estimated_hours DECIMAL(6,2) DEFAULT 0.00,
    labels VARCHAR(255) NULL,
    blockers LONGTEXT NULL,
    progress_percent INT NOT NULL DEFAULT 0,
    UNIQUE KEY uk_task_code(project_id,task_code),
    CHECK (estimated_hours >= 0),
    CHECK (progress_percent BETWEEN 0 AND 100),
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE SET NULL,
    FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_task_proj_status (project_id, status),
    INDEX idx_task_assignee (assignee_id),
    INDEX idx_task_due_date (due_date),
    INDEX idx_task_sprint (sprint_id),
    INDEX idx_task_archived (is_archived)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Bảng Comments (Bình luận trao đổi theo UC007)
CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    content LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_comment_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Bảng Attachments (Tài liệu đính kèm theo UC007)
CREATE TABLE IF NOT EXISTS attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    task_id INT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    file_type VARCHAR(100),
    uploaded_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_attach_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Bảng Meeting Notes (Ghi chú cuộc họp gốc theo FR-08 / FR-13)
CREATE TABLE IF NOT EXISTS meeting_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    meeting_date DATETIME NOT NULL,
    attendees TEXT,
    content LONGTEXT NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_note_proj (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Bảng Meeting Minutes (Biên bản họp chính thức theo UC010 / FR-13)
CREATE TABLE IF NOT EXISTS meeting_minutes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    meeting_note_id INT NULL,
    title VARCHAR(200) NOT NULL,
    summary LONGTEXT NOT NULL,
    decisions LONGTEXT,
    action_items LONGTEXT,
    status ENUM('draft', 'confirmed') NOT NULL DEFAULT 'draft',
    created_by INT NOT NULL,
    confirmed_by INT NULL,
    confirmed_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (meeting_note_id) REFERENCES meeting_notes(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_minutes_proj (project_id),
    INDEX idx_minutes_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Bảng AI Drafts (Quản lý các bản nháp/đề xuất của AI phục vụ xác nhận)
CREATE TABLE IF NOT EXISTS ai_drafts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    task_type ENUM('weekly_summary', 'meeting_minutes', 'assignment_suggestion') NOT NULL,
    input_params_json LONGTEXT NOT NULL,
    draft_content LONGTEXT NOT NULL,
    source_references_json LONGTEXT NOT NULL,
    structured_result_json LONGTEXT NULL,
    status ENUM('draft', 'needs_verification', 'confirmed', 'rejected') NOT NULL DEFAULT 'draft',
    version INT NOT NULL DEFAULT 1,
    validation_json LONGTEXT NULL,
    created_by INT NOT NULL,
    confirmed_by INT NULL,
    confirmed_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_draft_proj (project_id),
    INDEX idx_draft_type (task_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Bảng AI History (Lịch sử sử dụng AI theo FR-15 / UC012)
CREATE TABLE IF NOT EXISTS ai_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    draft_id INT NULL,
    project_id INT NOT NULL,
    requester_id INT NOT NULL,
    task_type ENUM('weekly_summary', 'meeting_minutes', 'assignment_suggestion') NOT NULL,
    model_provider VARCHAR(50) NOT NULL DEFAULT 'gemini',
    prompt_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    data_references_json TEXT,
    result_summary TEXT NOT NULL,
    confirmation_status ENUM('draft', 'needs_verification', 'confirmed', 'rejected') NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_aih_proj (project_id),
    INDEX idx_aih_req (requester_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Bảng Notifications (Thông báo trong ứng dụng theo FR-16 / UC013)
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    project_id INT NOT NULL,
    task_id INT NULL,
    event_type ENUM('task_assigned', 'assignee_changed', 'deadline_changed', 'status_changed', 'task_overdue', 'due_soon_reminder') NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    INDEX idx_noti_user_read (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Bảng Audit Logs (Nhật ký kiểm toán hệ thống theo FR-02)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INT NULL,
    details_json TEXT,
    ip_address VARCHAR(50) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_time (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS task_assignees (
        id INT AUTO_INCREMENT PRIMARY KEY, task_id INT NOT NULL, user_id INT NOT NULL,
        is_primary BOOLEAN NOT NULL DEFAULT FALSE, assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_task_user(task_id,user_id),
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_draft_revisions (
        id INT AUTO_INCREMENT PRIMARY KEY, draft_id INT NOT NULL, version INT NOT NULL,
        edited_by INT NULL, draft_content LONGTEXT NOT NULL, structured_result_json LONGTEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_draft_version(draft_id,version),
        FOREIGN KEY(draft_id) REFERENCES ai_drafts(id) ON DELETE CASCADE,
        FOREIGN KEY(edited_by) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS email_deliveries (
        id INT AUTO_INCREMENT PRIMARY KEY, task_id INT NOT NULL, user_id INT NOT NULL,
        claim_key VARCHAR(64) NOT NULL UNIQUE, claim_token VARCHAR(32) NOT NULL,
        status VARCHAR(32) NOT NULL, attempts INT NOT NULL DEFAULT 1,
        attempted_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
