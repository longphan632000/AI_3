"""Schema shared by production migrations and isolated test initialization."""

MYSQL_TABLES = (
    '''CREATE TABLE IF NOT EXISTS member_profiles (
        user_id INT PRIMARY KEY, skills LONGTEXT, availability VARCHAR(50) NOT NULL DEFAULT '100%',
        capacity_hours DECIMAL(8,2) NOT NULL DEFAULT 40,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',
    '''CREATE TABLE IF NOT EXISTS task_assignees (
        id INT AUTO_INCREMENT PRIMARY KEY, task_id INT NOT NULL, user_id INT NOT NULL,
        is_primary BOOLEAN NOT NULL DEFAULT FALSE, assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_task_user(task_id,user_id),
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',
    '''CREATE TABLE IF NOT EXISTS ai_draft_revisions (
        id INT AUTO_INCREMENT PRIMARY KEY, draft_id INT NOT NULL, version INT NOT NULL,
        edited_by INT NULL, draft_content LONGTEXT NOT NULL, structured_result_json LONGTEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_draft_version(draft_id,version),
        FOREIGN KEY(draft_id) REFERENCES ai_drafts(id) ON DELETE CASCADE,
        FOREIGN KEY(edited_by) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',
    '''CREATE TABLE IF NOT EXISTS email_deliveries (
        id INT AUTO_INCREMENT PRIMARY KEY, task_id INT NOT NULL, user_id INT NOT NULL,
        claim_key VARCHAR(64) NOT NULL UNIQUE, claim_token VARCHAR(32) NOT NULL,
        status VARCHAR(32) NOT NULL, attempts INT NOT NULL DEFAULT 1,
        attempted_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',
)

SQLITE_TABLES = (
    '''CREATE TABLE IF NOT EXISTS member_profiles (
        user_id INTEGER PRIMARY KEY, skills TEXT, availability TEXT NOT NULL DEFAULT '100%',
        capacity_hours DECIMAL NOT NULL DEFAULT 40, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)''',
    '''CREATE TABLE IF NOT EXISTS ai_draft_revisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, draft_id INTEGER NOT NULL,
        version INTEGER NOT NULL, edited_by INTEGER,
        draft_content TEXT NOT NULL, structured_result_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(draft_id,version),
        FOREIGN KEY(draft_id) REFERENCES ai_drafts(id) ON DELETE CASCADE,
        FOREIGN KEY(edited_by) REFERENCES users(id) ON DELETE SET NULL)''',
    '''CREATE TABLE IF NOT EXISTS email_deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        claim_key TEXT NOT NULL UNIQUE, claim_token TEXT NOT NULL, status TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 1, attempted_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)''',
)
