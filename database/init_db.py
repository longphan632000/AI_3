import os
import sys
import re
import sqlite3
import mysql.connector
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ai_project_management')

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')
SEED_PATH = os.path.join(os.path.dirname(__file__), 'seed_data.sql')
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'fallback_database.sqlite3')

def init_mysql():
    """Install MySQL; fail on SQL errors and never overwrite existing seed data."""
    conn = None
    try:
        if not re.fullmatch(r'[A-Za-z0-9_]+', DB_NAME):
            raise ValueError('Tên database không hợp lệ.')
        conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                                       password=DB_PASSWORD, connect_timeout=5)
        cursor = conn.cursor()
        cursor.execute(f'CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        cursor.execute(f'USE `{DB_NAME}`')
        # SQL files contain no routines; strip full-line comments before splitting.
        def statements(path):
            value = re.sub(r'^\s*--.*$', '', open(path, encoding='utf-8').read(), flags=re.M)
            return [item.strip() for item in value.split(';') if item.strip()]
        for sql in statements(SCHEMA_PATH):
            if not sql.upper().startswith(('CREATE DATABASE', 'USE ')):
                cursor.execute(sql)
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            for sql in statements(SEED_PATH):
                if not sql.upper().startswith('USE '):
                    cursor.execute(sql)
        conn.commit()
        cursor.close()
        from database import connection
        connection.DB_NAME = DB_NAME
        from database.migrations import ensure_core_schema, ensure_account_approval_schema, ensure_ai_schema
        ensure_account_approval_schema()
        ensure_core_schema()
        ensure_ai_schema()
        print('[+] MySQL đã sẵn sàng; dữ liệu hiện có được giữ nguyên.')
        return True
    except Exception as error:
        if conn is not None:
            conn.rollback()
        print(f'[-] Khởi tạo MySQL thất bại ({type(error).__name__}); không chuyển sang SQLite.')
        return False
    finally:
        if conn is not None:
            conn.close()


def init_sqlite_fallback():
    print("[*] Đang khởi tạo Fallback Database (SQLite) để đảm bảo hệ thống luôn chạy được ngay...")
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    
    # SQLite schema tương đương
    sqlite_schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        user_code TEXT UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'member',
        status TEXT NOT NULL DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_code TEXT UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        start_date DATE,
        end_date DATE,
        status TEXT NOT NULL DEFAULT 'planning',
        created_by INTEGER NOT NULL,
        is_archived BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS project_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        project_role TEXT NOT NULL DEFAULT 'member',
        skills TEXT,
        availability TEXT DEFAULT 'Full-time',
        capacity_hours DECIMAL(6,2) DEFAULT 40.00,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(project_id, user_id),
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS sprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        sprint_code TEXT,
        name TEXT NOT NULL,
        goal TEXT,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status TEXT NOT NULL DEFAULT 'planning',
        completion_criteria TEXT,
        is_archived BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        sprint_id INTEGER NULL,
        task_code TEXT,
        title TEXT NOT NULL,
        description TEXT,
        assignee_id INTEGER NULL,
        reporter_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'backlog',
        priority TEXT NOT NULL DEFAULT 'medium',
        due_date DATETIME NULL,
        estimated_hours DECIMAL(6,2) DEFAULT 0.00,
        labels TEXT NULL,
        blockers TEXT NULL,
        progress_percent INTEGER NOT NULL DEFAULT 0,
        is_archived BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE SET NULL,
        FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (reporter_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS task_assignees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        is_primary BOOLEAN NOT NULL DEFAULT 0,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(task_id, user_id),
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        task_id INTEGER NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        file_type TEXT,
        uploaded_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (uploaded_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS meeting_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        meeting_date DATETIME NOT NULL,
        attendees TEXT,
        content TEXT NOT NULL,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS meeting_minutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        meeting_note_id INTEGER NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        decisions TEXT,
        action_items TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        created_by INTEGER NOT NULL,
        confirmed_by INTEGER NULL,
        confirmed_at DATETIME NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (meeting_note_id) REFERENCES meeting_notes(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id),
        FOREIGN KEY (confirmed_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS ai_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        task_type TEXT NOT NULL,
        input_params_json TEXT NOT NULL,
        draft_content TEXT NOT NULL,
        source_references_json TEXT NOT NULL,
        structured_result_json TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        created_by INTEGER NOT NULL,
        confirmed_by INTEGER NULL,
        confirmed_at DATETIME NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id),
        FOREIGN KEY (confirmed_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS ai_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        draft_id INTEGER,
        project_id INTEGER NOT NULL,
        requester_id INTEGER NOT NULL,
        task_type TEXT NOT NULL,
        model_provider TEXT NOT NULL DEFAULT 'gemini',
        prompt_version TEXT NOT NULL DEFAULT 'v1.0',
        data_references_json TEXT,
        result_summary TEXT NOT NULL,
        confirmation_status TEXT NOT NULL DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (requester_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        task_id INTEGER NULL,
        event_type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NULL,
        action TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id INTEGER NULL,
        details_json TEXT,
        ip_address TEXT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    cursor.executescript(sqlite_schema)
    from database.operational_schema import SQLITE_TABLES
    for statement in SQLITE_TABLES:
        cursor.execute(statement)
    current = {row[1] for row in cursor.execute('PRAGMA table_info(ai_drafts)').fetchall()}
    for name, definition in (('version', 'INTEGER NOT NULL DEFAULT 1'), ('validation_json','TEXT')):
        if name not in current:
            cursor.execute(f'ALTER TABLE ai_drafts ADD COLUMN {name} {definition}')

    
    # Chèn dữ liệu mẫu cho SQLite
    sqlite_seed = """
    INSERT INTO users (id, username, email, password_hash, full_name, role, status) VALUES
    (1, 'admin', 'admin@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Quản trị viên Hệ thống', 'admin', 'active'),
    (2, 'leader_long', 'phanchanlong@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Phan Chân Long (Trưởng nhóm 33)', 'leader', 'active'),
    (3, 'member_my', 'luutramy@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Lưu Trà My (Thành viên 33)', 'member', 'active'),
    (4, 'member_khanh', 'lenamkhanh@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Lê Nam Khánh (Thành viên 33)', 'member', 'active'),
    (5, 'locked_user', 'locked@aiproject.local', 'scrypt:32768:8:1$OzyQpss4UjIqOz7P$ae46d56f0c93e3b8b4098656dc51611c5c4dcd93560557d17bbcf44ef0feebc692d3c7f32b9269e720badcc52853d220cd9a3c82b07b4092b98a0ea50154893d', 'Tài khoản Bị Khóa Kiểm Thử', 'member', 'locked');

    INSERT INTO projects (id, name, description, start_date, end_date, status, created_by, is_archived) VALUES
    (1, 'Hệ thống Quản lý Dự án Nhóm Tích hợp AI', 'Dự án môn Phân tích Thiết kế Hệ thống - Nhóm 33. Hệ thống quản lý dự án linh hoạt, tích hợp 3 chức năng trợ lý AI an toàn có kiểm duyệt con người.', '2026-09-01', '2026-10-31', 'active', 2, 0);

    INSERT INTO project_members (id, project_id, user_id, project_role, skills, availability, capacity_hours) VALUES
    (1, 1, 2, 'leader', 'Phân tích hệ thống, Kiến trúc phần mềm, Quản lý dự án, Python Flask, MySQL', '100% (Toàn thời gian)', 40.00),
    (2, 1, 3, 'member', 'Thiết kế giao diện UI/UX, Frontend HTML/CSS/JS, Testing, Tài liệu URD', '80% (Bán thời gian)', 32.00),
    (3, 1, 4, 'member', 'Backend API, Cơ sở dữ liệu MySQL, Tích hợp AI Gemini, PlantUML', '100% (Toàn thời gian)', 40.00);

    INSERT INTO sprints (id, project_id, name, goal, start_date, end_date, status, completion_criteria) VALUES
    (1, 1, 'Sprint 1: Phân tích & Kiến trúc Core', 'Hoàn tất URD, sơ đồ kiến trúc, CSDL MySQL và khung ứng dụng Flask', '2026-09-01', '2026-09-20', 'completed', 'Tất cả tài liệu URD, ERD, Schema được duyệt qua Human Gate 1 & 2'),
    (2, 1, 'Sprint 2: Lập trình Core & Tích hợp AI', 'Xây dựng Kanban 5 trạng thái, 3 module AI an toàn và hệ thống thông báo', '2026-09-21', '2026-10-10', 'active', 'Hoàn tất FR-01 đến FR-14 và kiểm thử tự động pass 100%');

    INSERT INTO tasks (id, project_id, sprint_id, title, description, assignee_id, reporter_id, status, priority, due_date, estimated_hours, labels, blockers) VALUES
    (1, 1, 1, 'Thiết kế mô hình hệ thống và tài liệu URD', 'Phân tích yêu cầu FR-01..FR-17, BR-01..BR-09 và vẽ Use Case Diagram', 2, 2, 'done', 'high', '2026-09-10 17:00:00', 16.00, 'Tài liệu, URD', NULL),
    (2, 1, 1, 'Thiết kế CSDL MySQL chuẩn 3NF', 'Xây dựng schema.sql 13 bảng với đầy đủ ràng buộc PK, FK, CHECK', 4, 2, 'done', 'high', '2026-09-18 17:00:00', 12.00, 'Database, MySQL', NULL),
    (3, 1, 2, 'Lập trình Bảng Kanban tương tác và API Nhiệm vụ', 'Xây dựng kéo thả Kanban 5 cột theo BR-01, API CRUD nhiệm vụ, lọc và phân trang', 3, 2, 'in_progress', 'high', '2026-09-28 17:00:00', 20.00, 'Frontend, Kanban', NULL),
    (4, 1, 2, 'Xây dựng Pipeline 5 bước Trợ lý AI và Gemini Adapter', 'Triển khai Request Analyzer, Data Retriever, Context Builder, Response Validator', 4, 2, 'todo', 'urgent', '2026-09-30 17:00:00', 24.00, 'AI, Gemini, Backend', NULL),
    (5, 1, 2, 'Thiết kế giao diện 3D Tech và Dark Mode', 'Triển khai hiệu ứng 3D tilt card, vòng tiến độ isometric và theme tối công nghệ', 3, 2, 'review', 'medium', '2026-09-26 17:00:00', 14.00, 'UI/UX, 3D', 'Chờ feedback từ Trưởng nhóm'),
    (6, 1, 2, 'Tích hợp hệ thống Email cảnh báo nhiệm vụ trễ hạn (FR-17)', 'Tự động gửi email đến người phụ trách theo quy tắc BR-09 khi quá hạn', 4, 2, 'backlog', 'medium', '2026-10-05 17:00:00', 8.00, 'Notification, Email', NULL),
    (7, 1, 2, 'Rà soát tài liệu kiểm thử và ma trận truy vết', 'Đối chiếu test-cases.md với requirements-traceability.md', 3, 2, 'in_progress', 'high', '2026-09-22 17:00:00', 10.00, 'Testing, QA', 'Cần bổ sung test case AI injection');

    INSERT INTO comments (id, task_id, user_id, content) VALUES
    (1, 3, 2, 'Phan Chân Long: Lưu ý áp dụng đúng quy tắc BR-01 khi kéo thả nhiệm vụ qua 5 cột trạng thái nhé.'),
    (2, 3, 3, 'Lưu Trà My: Đã nắm rõ ạ, em đang hoàn thiện hiệu ứng 3D tilt và animation kéo thả mượt mà.');

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
    5. Quyết định: Buổi họp tiếp theo sẽ diễn ra vào sáng thứ Hai tuần tới lúc 09:00.', 2);

    INSERT INTO notifications (id, user_id, project_id, task_id, event_type, title, message, is_read) VALUES
    (1, 3, 1, 3, 'task_assigned', 'Nhiệm vụ mới được giao', 'Bạn được phân công phụ trách nhiệm vụ: Lập trình Bảng Kanban tương tác và API Nhiệm vụ.', 0),
    (2, 4, 1, 4, 'task_assigned', 'Nhiệm vụ mới được giao', 'Bạn được phân công phụ trách nhiệm vụ: Xây dựng Pipeline 5 bước Trợ lý AI và Gemini Adapter.', 0),
    (3, 3, 1, 7, 'due_soon_reminder', 'Cảnh báo nhiệm vụ trễ hạn', 'Nhiệm vụ "Rà soát tài liệu kiểm thử và ma trận truy vết" đã quá hạn từ ngày 22/09/2026.', 0);

    INSERT INTO audit_logs (id, user_id, action, target_type, target_id, details_json, ip_address) VALUES
    (1, 1, 'INITIALIZE_SYSTEM', 'SYSTEM', 1, '{"message": "Khởi tạo hệ thống quản lý dự án nhóm AI Nhóm 33"}', '127.0.0.1'),
    (2, 2, 'CREATE_PROJECT', 'PROJECT', 1, '{"name": "Hệ thống Quản lý Dự án Nhóm Tích hợp AI"}', '127.0.0.1');
    """
    cursor.execute("SELECT count(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        cursor.executescript(sqlite_seed)
        conn.commit()
    conn.close()
    print("[+] Fallback Database SQLite khởi tạo thành công!")

if __name__ == '__main__':
    raise SystemExit(0 if init_mysql() else 1)
