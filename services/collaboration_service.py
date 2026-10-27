from services.validation import text, local_datetime
from services.access_service import require_active_task, require_active_project
from database.connection import query_db, execute_db, atomic
from services.audit_service import log_audit

# 1. Bình luận (Comments - UC007 / FR-08)
def get_task_comments(task_id):
    query = """
        SELECT c.id, c.task_id, c.user_id, u.full_name AS user_name, u.role AS user_role,
               c.content, c.created_at
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.task_id = %s
        ORDER BY c.created_at ASC;
    """
    return query_db(query, (task_id,))

@atomic
def add_comment(user_id, task_id, content):
    if not content or not content.strip():
        return False, "Nội dung bình luận không được để trống."
        
    from services.task_service import get_task_by_id
    require_active_task(get_task_by_id(task_id))
    content = text(content, 'Bình luận', 60000, required=True)
    query = "INSERT INTO comments (task_id, user_id, content) VALUES (%s, %s, %s);"
    comment_id = execute_db(query, (task_id, user_id, content.strip()))
    return True, "Thêm bình luận thành công."

# 2. Tài liệu đính kèm (Attachments - UC007 / FR-08)
def get_task_attachments(task_id):
    query = """
        SELECT a.id, a.project_id, a.task_id, a.file_name, a.file_path, a.file_size,
               a.file_type, a.uploaded_by, u.full_name AS uploader_name, a.created_at
        FROM attachments a
        JOIN users u ON a.uploaded_by = u.id
        WHERE a.task_id = %s
        ORDER BY a.created_at DESC;
    """
    return query_db(query, (task_id,))

@atomic
def add_attachment(user_id, project_id, task_id, file_name, file_path, file_size, file_type):
    query = """
        INSERT INTO attachments (project_id, task_id, file_name, file_path, file_size, file_type, uploaded_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    att_id = execute_db(query, (project_id, task_id or None, file_name, file_path, file_size, file_type, user_id))
    log_audit(user_id, 'UPLOAD_ATTACHMENT', 'ATTACHMENT', att_id, {"file_name": file_name})
    return True, "Đính kèm tệp thành công."

# 3. Ghi chú cuộc họp (Meeting Notes - FR-08 / FR-13)
def get_project_meeting_notes(project_id):
    query = """
        SELECT mn.id, mn.project_id, mn.title, mn.meeting_date, mn.attendees,
               mn.content, mn.created_by, u.full_name AS creator_name, mn.created_at
        FROM meeting_notes mn
        JOIN users u ON mn.created_by = u.id
        WHERE mn.project_id = %s
        ORDER BY mn.meeting_date DESC;
    """
    return query_db(query, (project_id,))

def get_meeting_note_by_id(note_id):
    query = """
        SELECT mn.id, mn.project_id, mn.title, mn.meeting_date, mn.attendees,
               mn.content, mn.created_by, u.full_name AS creator_name, mn.created_at
        FROM meeting_notes mn
        JOIN users u ON mn.created_by = u.id
        WHERE mn.id = %s;
    """
    return query_db(query, (note_id,), one=True)

@atomic
def create_meeting_note(user_id, project_id, title, meeting_date, attendees, content):
    if not title or not content:
        return False, "Tiêu đề và nội dung cuộc họp không được để trống.", None
        
    require_active_project(project_id)
    title = text(title, 'Tiêu đề', 200, required=True)
    content = text(content, 'Nội dung', 120000, required=True)
    attendees = text(attendees, 'Người tham dự', 60000)
    meeting_date = local_datetime(meeting_date)
    if meeting_date is None:
        return False, 'Phải cung cấp ngày giờ họp.', None
    query = """
        INSERT INTO meeting_notes (project_id, title, meeting_date, attendees, content, created_by)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    note_id = execute_db(query, (project_id, title.strip(), meeting_date, attendees, content.strip(), user_id))
    log_audit(user_id, 'CREATE_MEETING_NOTE', 'MEETING_NOTE', note_id, {"title": title})
    return True, "Tạo ghi chú cuộc họp thành công.", note_id
