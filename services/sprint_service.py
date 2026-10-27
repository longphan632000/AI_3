from database.connection import query_db, execute_db, atomic
from services.audit_service import log_audit
from services.validation import text, iso_date, choice, ValidationError
from services.access_service import require_active_project

def get_sprints_by_project(project_id, archived=False):
    """Lấy danh sách sprint của dự án kèm tỷ lệ hoàn thành (BR-04)."""
    sprints = query_db("""
        SELECT s.id, s.project_id, s.sprint_code, s.name, s.goal, s.start_date, s.end_date,
               s.status, s.completion_criteria, s.is_archived, s.created_at
        FROM sprints s
        WHERE s.project_id = %s AND s.is_archived = %s
        ORDER BY s.start_date DESC;
    """, (project_id, archived))
    
    # Tính tỷ lệ hoàn thành cho từng sprint theo BR-04
    for sp in sprints:
        stats = calculate_sprint_metrics(sp['id'])
        sp['total_tasks'] = stats['total_tasks']
        sp['done_tasks'] = stats['done_tasks']
        sp['completion_rate'] = stats['completion_rate']
        
    return sprints

def get_sprint_by_id(sprint_id):
    sp = query_db("SELECT * FROM sprints WHERE id = %s;", (sprint_id,), one=True)
    if sp:
        stats = calculate_sprint_metrics(sprint_id)
        sp.update(stats)
    return sp

def calculate_sprint_metrics(sprint_id):
    """
    Quy tắc nghiệp vụ BR-04:
    Tỷ lệ hoàn thành = (số nhiệm vụ Done / tổng nhiệm vụ trong sprint) * 100%.
    Nếu không có nhiệm vụ thì hiển thị 0%.
    """
    query = """
        SELECT COUNT(*) AS total_count,
               SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done_count
        FROM tasks
        WHERE sprint_id = %s AND is_archived = FALSE;
    """
    res = query_db(query, (sprint_id,), one=True)
    total = int(res['total_count'] or 0)
    done = int(res['done_count'] or 0)
    
    if total == 0:
        rate = 0.0
    else:
        rate = round((float(done) / float(total)) * 100.0, 1)
        
    return {
        'total_tasks': total,
        'done_tasks': done,
        'completion_rate': rate
    }

@atomic
def create_sprint(user_id, project_id, name, goal, start_date, end_date, completion_criteria, sprint_code=None):
    """
    Tạo sprint mới (FR-07).
    Tuân thủ BR-03: Ngày bắt đầu không sau ngày kết thúc.
    """
    if not name or not name.strip():
        return False, "Tên sprint không được để trống.", None
        
    if not start_date or not end_date:
        return False, "Phải cung cấp đầy đủ ngày bắt đầu và kết thúc.", None
        
    require_active_project(project_id)
    name = text(name, 'Tên sprint', 100, required=True)
    goal = text(goal, 'Mục tiêu', 60000)
    completion_criteria = text(completion_criteria, 'Tiêu chí hoàn thành', 60000)
    try:
        d_start = iso_date(start_date, 'Ngày bắt đầu', required=True)
        d_end = iso_date(end_date, 'Ngày kết thúc', required=True)
    except ValidationError as error:
        return False, str(error), None
    if d_start > d_end:
        return False, "Quy tắc BR-03: Ngày bắt đầu sprint không được sau ngày kết thúc.", None

    clean_code = text(sprint_code, 'Mã sprint', 50).upper()
    if not clean_code:
        from uuid import uuid4
        clean_code = 'SP-' + uuid4().hex[:10].upper()

    # Kiểm tra trùng lặp mã sprint trong cùng dự án
    existing_code = query_db("SELECT id FROM sprints WHERE project_id = %s AND UPPER(sprint_code) = %s AND is_archived = FALSE;", (project_id, clean_code), one=True)
    if existing_code:
        return False, f"Mã Sprint '{clean_code}' đã tồn tại trong dự án này.", None
        
    query = """
        INSERT INTO sprints (project_id, sprint_code, name, goal, start_date, end_date, status, completion_criteria, is_archived)
        VALUES (%s, %s, %s, %s, %s, %s, 'planning', %s, FALSE);
    """
    sprint_id = execute_db(query, (project_id, clean_code, name.strip(), goal, d_start, d_end, completion_criteria))
    log_audit(user_id, 'CREATE_SPRINT', 'SPRINT', sprint_id, {"name": name, "sprint_code": clean_code, "project_id": project_id})
    return True, "Tạo sprint thành công.", sprint_id

@atomic
def update_sprint(user_id, sprint_id, name, goal, start_date, end_date, status, completion_criteria, sprint_code=None):
    """Cập nhật sprint (BR-03 kiểm tra ngày)."""
    sp = get_sprint_by_id(sprint_id)
    if not sp:
        return False, 'Sprint không tồn tại.'
    require_active_project(sp['project_id'])
    name = text(name, 'Tên sprint', 100, required=True)
    goal = text(goal, 'Mục tiêu', 60000)
    completion_criteria = text(completion_criteria, 'Tiêu chí hoàn thành', 60000)
    status = choice(status, ('planning','active','completed','archived'), 'Trạng thái')
    try:
        start_date = iso_date(start_date, 'Ngày bắt đầu', required=True)
        end_date = iso_date(end_date, 'Ngày kết thúc', required=True)
    except ValidationError as error:
        return False, str(error)
    if str(start_date) > str(end_date):
        return False, "Quy tắc BR-03: Ngày bắt đầu sprint không được sau ngày kết thúc."

    clean_code = (sprint_code or '').strip().upper() if sprint_code else None
    if clean_code:
        sp = query_db("SELECT project_id FROM sprints WHERE id = %s;", (sprint_id,), one=True)
        if sp:
            existing = query_db("SELECT id FROM sprints WHERE project_id = %s AND UPPER(sprint_code) = %s AND id != %s AND is_archived = FALSE;", (sp['project_id'], clean_code, sprint_id), one=True)
            if existing:
                return False, f"Mã Sprint '{clean_code}' đã tồn tại trong dự án."

    if clean_code:
        query = """
            UPDATE sprints
            SET sprint_code = %s, name = %s, goal = %s, start_date = %s, end_date = %s, status = %s, completion_criteria = %s
            WHERE id = %s;
        """
        execute_db(query, (clean_code, name, goal, start_date, end_date, status, completion_criteria, sprint_id))
    else:
        query = """
            UPDATE sprints
            SET name = %s, goal = %s, start_date = %s, end_date = %s, status = %s, completion_criteria = %s
            WHERE id = %s;
        """
        execute_db(query, (name, goal, start_date, end_date, status, completion_criteria, sprint_id))

    execute_db("UPDATE sprints SET is_archived=%s WHERE id=%s", (status == 'archived', sprint_id))
    log_audit(user_id, 'UPDATE_SPRINT', 'SPRINT', sprint_id, {"status": status, "sprint_code": clean_code})
    return True, "Cập nhật sprint thành công."

@atomic
def assign_task_to_sprint(user_id, task_id, sprint_id):
    """
    Gán nhiệm vụ vào sprint.
    Tuân thủ BR-03: Một nhiệm vụ chỉ thuộc tối đa 1 sprint tại 1 thời điểm.
    """
    execute_db("UPDATE tasks SET sprint_id = %s WHERE id = %s;", (sprint_id or None, task_id))
    log_audit(user_id, 'ASSIGN_TASK_SPRINT', 'TASK', task_id, {"sprint_id": sprint_id})
    return True, "Đã cập nhật sprint cho nhiệm vụ."


@atomic
def archive_sprint(user_id, sprint_id):
    sp = get_sprint_by_id(sprint_id)
    if not sp:
        return False, 'Sprint không tồn tại.'
    require_active_project(sp['project_id'])
    execute_db("UPDATE sprints SET status='archived', is_archived=TRUE WHERE id=%s", (sprint_id,))
    log_audit(user_id, 'ARCHIVE_SPRINT', 'SPRINT', sprint_id)
    return True, 'Đã lưu trữ sprint; lịch sử nhiệm vụ được giữ nguyên.'


@atomic
def restore_sprint(user_id, sprint_id):
    sp = get_sprint_by_id(sprint_id)
    if not sp:
        return False, 'Sprint không tồn tại.'
    require_active_project(sp['project_id'])
    execute_db("UPDATE sprints SET status='planning', is_archived=FALSE WHERE id=%s", (sprint_id,))
    log_audit(user_id, 'RESTORE_SPRINT', 'SPRINT', sprint_id)
    return True, 'Đã khôi phục sprint.'
