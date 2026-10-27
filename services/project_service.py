from database.connection import query_db, execute_db, atomic
from services.audit_service import log_audit
from services.validation import text, iso_date, choice, integer, ValidationError
from services.access_service import require_active_project

def get_projects_for_user(user_id, user_role, archived=False):
    """
    Lấy danh sách dự án mà người dùng có quyền truy cập (FR-03, D01, D02).
    Admin có thể xem tất cả; Trưởng nhóm và Thành viên xem dự án tham gia.
    """
    if user_role == 'admin':
        query = """
            SELECT p.id, p.project_code, p.name, p.description, p.start_date, p.end_date, p.status, 
                   p.created_by, u.full_name AS creator_name, p.is_archived, p.created_at,
                   'admin' AS current_user_project_role
            FROM projects p
            LEFT JOIN users u ON p.created_by = u.id
            WHERE p.is_archived = FALSE
            ORDER BY p.id DESC;
        """
        if archived:
            query = query.replace('p.is_archived = FALSE', 'p.is_archived = TRUE')
        return query_db(query)
    else:
        query = """
            SELECT p.id, p.project_code, p.name, p.description, p.start_date, p.end_date, p.status, 
                   p.created_by, u.full_name AS creator_name, p.is_archived, p.created_at,
                   pm.project_role AS current_user_project_role
            FROM projects p
            JOIN project_members pm ON p.id = pm.project_id
            LEFT JOIN users u ON p.created_by = u.id
            WHERE pm.user_id = %s AND p.is_archived = FALSE
            ORDER BY p.id DESC;
        """
        if archived:
            query = query.replace('p.is_archived = FALSE', 'p.is_archived = TRUE')
        return query_db(query, (user_id,))

def get_project_by_id(project_id, user_id, user_role, include_archived=False):
    """Lấy chi tiết dự án sau khi xác thực quyền truy cập."""
    query = """
        SELECT p.id, p.project_code, p.name, p.description, p.start_date, p.end_date, p.status, 
               p.created_by, u.full_name AS creator_name, p.is_archived, p.created_at
        FROM projects p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.id = %s AND p.is_archived = FALSE;
    """
    if include_archived:
        query = query.replace(' AND p.is_archived = FALSE', '')
    project = query_db(query, (project_id,), one=True)
    if not project:
        return None
        
    if user_role == 'admin':
        project['current_user_project_role'] = 'admin'
        return project
        
    member = query_db("""
        SELECT project_role FROM project_members 
        WHERE project_id = %s AND user_id = %s;
    """, (project_id, user_id), one=True)
    
    if not member:
        return None
        
    project['current_user_project_role'] = member['project_role']
    return project

@atomic
def create_project(creator_id, name, description, start_date=None, end_date=None, initial_member_ids=None, project_code=None):
    """Tạo dự án mới, tự động gán người tạo làm Leader và thêm các thành viên ban đầu nếu có (FR-03)."""
    if not name or not name.strip():
        return False, "Tên dự án không được để trống.", None

    name = text(name, 'Tên dự án', 150, required=True)
    description = text(description, 'Mô tả', 60000)
    start_date = iso_date(start_date, 'Ngày bắt đầu')
    end_date = iso_date(end_date, 'Ngày kết thúc')
    # Kiểm tra ràng buộc ngày bắt đầu và kết thúc
    if start_date and end_date and str(start_date) > str(end_date):
        return False, "Ngày bắt đầu dự án không được sau ngày kết thúc.", None

    member_ids = []
    if initial_member_ids is not None:
        if not isinstance(initial_member_ids, (list, tuple, set)) or len(initial_member_ids) > 500:
            raise ValidationError('Danh sách nhân viên phải là danh sách tối đa 500 tài khoản.')
        member_ids = list(dict.fromkeys(integer(uid, 'Nhân viên', minimum=1) for uid in initial_member_ids))
        for uid in member_ids:
            target = query_db('SELECT role,status FROM users WHERE id=%s', (uid,), one=True)
            if not target or target['status'] != 'active' or target['role'] not in ('member','leader'):
                raise ValidationError('Chỉ được chọn nhân viên hoặc Trưởng nhóm đã được Admin duyệt.')

    clean_code = text(project_code, 'Mã dự án', 50).upper()
    if not clean_code:
        import re
        # Tự sinh mã từ tên dự án nếu người dùng chưa nhập
        words = re.findall(r'[a-zA-Z0-9]+', name)
        clean_code = ''.join(w[0] for w in words).upper() if words else 'PRJ'
        clean_code = clean_code[:8]

    # Kiểm tra trùng lặp mã dự án
    existing_code = query_db("SELECT id FROM projects WHERE UPPER(project_code) = %s;", (clean_code,), one=True)
    if existing_code:
        return False, f"Mã dự án '{clean_code}' đã tồn tại, vui lòng chọn mã khác.", None
        
    query = """
        INSERT INTO projects (project_code, name, description, start_date, end_date, status, created_by, is_archived)
        VALUES (%s, %s, %s, %s, %s, 'active', %s, FALSE);
    """
    project_id = execute_db(query, (clean_code, name.strip(), description, start_date or None, end_date or None, creator_id))
    
    # Gán người tạo làm leader trong project_members
    execute_db("""
        INSERT INTO project_members (project_id, user_id, project_role, skills, availability, capacity_hours)
        VALUES (%s, %s, 'leader', 'Quản lý dự án', '100%', 40.00);
    """, (project_id, creator_id))

    # Tự động gán các thành viên được chọn ban đầu vào dự án
    if member_ids:
        from services.project_member_service import add_project_members
        # Loại trừ creator_id vì đã được gán làm leader
        member_ids_to_add = [uid for uid in member_ids if uid != creator_id]
        if member_ids_to_add:
            added, message, count = add_project_members(creator_id, project_id, member_ids_to_add, project_role='member')
            if not added or count != len(member_ids_to_add):
                raise ValidationError(message)
    
    log_audit(creator_id, 'CREATE_PROJECT', 'PROJECT', project_id, {"name": name, "project_code": clean_code})
    return True, "Tạo dự án thành công.", project_id

@atomic
def update_project(user_id, project_id, name, description, start_date=None, end_date=None, status='active', project_code=None):
    """Cập nhật thông tin dự án có kiểm tra ràng buộc hợp lệ."""
    if not name or not name.strip():
        return False, "Tên dự án không được để trống."
        
    name = text(name, 'Tên dự án', 150, required=True)
    description = text(description, 'Mô tả', 60000)
    start_date = iso_date(start_date, 'Ngày bắt đầu')
    end_date = iso_date(end_date, 'Ngày kết thúc')
    require_active_project(project_id)
    status = choice(status, ('planning','active','completed','archived'), 'Trạng thái')
    if status == 'archived':
        return archive_project(user_id, project_id)
    trimmed_name = name.strip()
    
    # Kiểm tra ràng buộc ngày bắt đầu và kết thúc
    if start_date and end_date and str(start_date) > str(end_date):
        return False, "Ngày bắt đầu dự án không được sau ngày kết thúc."

    clean_code = text(project_code, 'Mã dự án', 50).upper() if project_code else None
    if clean_code:
        existing = query_db("SELECT id FROM projects WHERE UPPER(project_code) = %s AND id != %s;", (clean_code, project_id), one=True)
        if existing:
            return False, f"Mã dự án '{clean_code}' đã tồn tại, vui lòng chọn mã khác."

    if clean_code:
        query = """
            UPDATE projects 
            SET project_code = %s, name = %s, description = %s, start_date = %s, end_date = %s, status = %s
            WHERE id = %s;
        """
        execute_db(query, (clean_code, trimmed_name, description, start_date or None, end_date or None, status, project_id))
    else:
        query = """
            UPDATE projects 
            SET name = %s, description = %s, start_date = %s, end_date = %s, status = %s
            WHERE id = %s;
        """
        execute_db(query, (trimmed_name, description, start_date or None, end_date or None, status, project_id))

    log_audit(user_id, 'UPDATE_PROJECT', 'PROJECT', project_id, {
        "name": trimmed_name,
        "project_code": clean_code,
        "status": status,
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None
    })
    return True, "Cập nhật dự án thành công."

@atomic
def delete_project(user_id, project_id):
    """
    Xóa vĩnh viễn dự án (Hard delete) khi Leader tạo sai hoặc muốn xóa bỏ hoàn toàn.
    Dọn dẹp sạch sẽ toàn bộ dữ liệu phụ thuộc (tasks, sprints, members, notes, drafts...)
    trước khi xóa dự án khỏi bảng projects.
    """
    execute_db("DELETE FROM notifications WHERE project_id=%s", (project_id,))
    # Dọn dẹp an toàn các bảng con đa tầng
    execute_db("DELETE FROM task_assignees WHERE task_id IN (SELECT id FROM tasks WHERE project_id = %s);", (project_id,))
    execute_db("DELETE FROM comments WHERE task_id IN (SELECT id FROM tasks WHERE project_id = %s);", (project_id,))
    execute_db("DELETE FROM attachments WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM tasks WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM sprints WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM meeting_minutes WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM meeting_notes WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM ai_drafts WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM ai_history WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM notifications WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM project_members WHERE project_id = %s;", (project_id,))
    execute_db("DELETE FROM projects WHERE id = %s;", (project_id,))

    log_audit(user_id, 'DELETE_PROJECT', 'PROJECT', project_id)
    return True, "Đã xóa vĩnh viễn dự án thành công."

@atomic
def archive_project(user_id, project_id):
    """Lưu trữ dự án (Xóa mềm - BR-08)."""
    execute_db("UPDATE projects SET is_archived = TRUE, status='archived' WHERE id = %s;", (project_id,))
    log_audit(user_id, 'ARCHIVE_PROJECT', 'PROJECT', project_id)
    return True, "Đã lưu trữ dự án thành công."


@atomic
def restore_project(user_id, project_id):
    execute_db("UPDATE projects SET is_archived=FALSE, status='active' WHERE id=%s", (project_id,))
    log_audit(user_id, 'RESTORE_PROJECT', 'PROJECT', project_id)
    return True, 'Đã khôi phục dự án.'
