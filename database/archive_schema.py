"""Add archive provenance and recover only actors evidenced by audit records."""


def ensure_archive_schema(connection, engine):
    cursor = connection.cursor()
    try:
        fields = (('archived_by', 'INT NULL' if engine == 'mysql' else 'INTEGER'),
                  ('archived_at', 'DATETIME NULL'), ('pre_archive_status', 'VARCHAR(20) NULL'))
        if engine == 'mysql':
            for name, definition in fields:
                cursor.execute(f"SHOW COLUMNS FROM projects LIKE '{name}'")
                if not cursor.fetchone():
                    cursor.execute(f'ALTER TABLE projects ADD COLUMN {name} {definition}')
        else:
            existing = {row[1] for row in cursor.execute('PRAGMA table_info(projects)').fetchall()}
            for name, definition in fields:
                if name not in existing:
                    cursor.execute(f'ALTER TABLE projects ADD COLUMN {name} {definition}')
        cursor.execute('''SELECT p.id,u.id,a.created_at FROM projects p
            JOIN audit_logs a ON a.id=(SELECT MAX(a2.id) FROM audit_logs a2
                WHERE a2.target_type='PROJECT' AND a2.target_id=p.id AND a2.action='ARCHIVE_PROJECT')
            LEFT JOIN users u ON u.id=a.user_id
            WHERE p.is_archived=TRUE AND p.archived_by IS NULL AND p.archived_at IS NULL''')
        rows = cursor.fetchall()
        placeholder = '%s' if engine == 'mysql' else '?'
        for project_id, actor, timestamp in rows:
            cursor.execute(f'UPDATE projects SET archived_by={placeholder},archived_at={placeholder} WHERE id={placeholder}',
                           (actor, timestamp, project_id))
    finally:
        cursor.close()
