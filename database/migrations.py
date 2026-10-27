"""Small, idempotent migrations for databases created before account approval."""

from database.connection import get_db_connection


def ensure_core_schema():
    """Add missing structures, backfill only new/empty fields; never reseed users."""
    from database.operational_schema import MYSQL_TABLES
    connection, engine = get_db_connection()
    try:
        if engine != 'mysql':
            return
        cursor = connection.cursor()
        additions = (
            ('users','user_code','VARCHAR(50) NULL'),
            ('projects','project_code','VARCHAR(50) NULL'),
            ('sprints','sprint_code','VARCHAR(50) NULL'),
            ('tasks','task_code','VARCHAR(50) NULL'),
            ('tasks','progress_percent','INT NOT NULL DEFAULT 0'),
            ('ai_drafts','version','INT NOT NULL DEFAULT 1'),
            ('ai_drafts','validation_json','LONGTEXT NULL'),
        )
        for table, field, definition in additions:
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{field}'")
            if not cursor.fetchone():
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {field} {definition}')
                if field == 'progress_percent':
                    cursor.execute("UPDATE tasks SET progress_percent=100 WHERE status='done'")
        for sql in MYSQL_TABLES:
            cursor.execute(sql)
        for table, field in (('projects','description'),('project_members','skills'),('tasks','description'),
                             ('tasks','blockers'),('sprints','goal'),('sprints','completion_criteria'),
                             ('comments','content'),('meeting_notes','content')):
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{field}'")
            current = cursor.fetchone()
            if current and current[1].lower() != 'longtext':
                cursor.execute(f'ALTER TABLE {table} MODIFY COLUMN {field} LONGTEXT' + (' NOT NULL' if field == 'content' else ' NULL'))
        cursor.execute("SHOW COLUMNS FROM notifications LIKE 'event_type'")
        column = cursor.fetchone()
        if column and column[1].lower().startswith('enum(') and 'task_overdue' not in column[1]:
            cursor.execute('ALTER TABLE notifications MODIFY COLUMN event_type VARCHAR(50) NOT NULL')
        for table, field, prefix in (('users','user_code','USR'),('projects','project_code','PRJ'),
                                      ('sprints','sprint_code','SP'),('tasks','task_code','TASK')):
            cursor.execute(f'SELECT id, {field} FROM {table}')
            rows = cursor.fetchall()
            used = {str(row[1]).upper() for row in rows if row[1]}
            for identifier, code in rows:
                if not code:
                    candidate = f'{prefix}-{identifier:06d}'
                    while candidate.upper() in used:
                        candidate += 'X'
                    used.add(candidate.upper())
                    cursor.execute(f'UPDATE {table} SET {field}=%s WHERE id=%s', (candidate,identifier))
        # Seed old primary assignments without disturbing existing supporters.
        cursor.execute('''INSERT IGNORE INTO task_assignees(task_id,user_id,is_primary)
                          SELECT id,assignee_id,TRUE FROM tasks WHERE assignee_id IS NOT NULL''')
        connection.commit()
        cursor.close()
    finally:
        connection.close()


def ensure_account_approval_schema():
    connection, engine = get_db_connection()
    try:
        if engine != 'mysql':
            return
        cursor = connection.cursor()
        cursor.execute("SHOW COLUMNS FROM users LIKE 'status'")
        column = cursor.fetchone()
        if column and "pending" not in column[1]:
            cursor.execute(
                "ALTER TABLE users MODIFY COLUMN status "
                "ENUM('active', 'pending', 'rejected', 'locked') NOT NULL DEFAULT 'active'"
            )
            connection.commit()
        cursor.close()
    finally:
        connection.close()


def ensure_ai_schema():
    """Upgrade existing MySQL AI tables without changing existing draft content."""
    connection, engine = get_db_connection()
    try:
        if engine != 'mysql':
            return
        cursor = connection.cursor()
        for table, column, definition in (
            ('ai_drafts', 'input_params_json', 'LONGTEXT NOT NULL'),
            ('ai_drafts', 'draft_content', 'LONGTEXT NOT NULL'),
            ('ai_drafts', 'source_references_json', 'LONGTEXT NOT NULL'),
            ('meeting_minutes', 'summary', 'LONGTEXT NOT NULL'),
            ('meeting_minutes', 'decisions', 'LONGTEXT NULL'),
            ('meeting_minutes', 'action_items', 'LONGTEXT NULL'),
        ):
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
            current = cursor.fetchone()
            if current and current[1].lower() != 'longtext':
                cursor.execute(f'ALTER TABLE {table} MODIFY COLUMN {column} {definition}')
        cursor.execute("SHOW COLUMNS FROM ai_drafts LIKE 'structured_result_json'")
        if not cursor.fetchone():
            cursor.execute('ALTER TABLE ai_drafts ADD COLUMN structured_result_json LONGTEXT NULL')
        cursor.execute("SHOW COLUMNS FROM ai_drafts LIKE 'status'")
        status_column = cursor.fetchone()
        if status_column and 'needs_verification' not in status_column[1]:
            cursor.execute("ALTER TABLE ai_drafts MODIFY COLUMN status ENUM('draft', 'needs_verification', 'confirmed', 'rejected') NOT NULL DEFAULT 'draft'")
        cursor.execute("SHOW COLUMNS FROM ai_history LIKE 'draft_id'")
        if not cursor.fetchone():
            cursor.execute('ALTER TABLE ai_history ADD COLUMN draft_id INT NULL')
        cursor.execute("SHOW COLUMNS FROM ai_history LIKE 'confirmation_status'")
        history_status = cursor.fetchone()
        if history_status and 'needs_verification' not in history_status[1]:
            cursor.execute("ALTER TABLE ai_history MODIFY COLUMN confirmation_status ENUM('draft', 'needs_verification', 'confirmed', 'rejected') NOT NULL DEFAULT 'draft'")
        connection.commit()
        cursor.close()
    finally:
        connection.close()
