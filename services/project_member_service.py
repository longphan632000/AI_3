from database.connection import query_db, execute_db, atomic
from services.audit_service import log_audit
from services.validation import text, number, availability_percent, integer, ValidationError
from services.access_service import require_active_project

def get_project_members(project_id):
    """
    Lấy danh sách thành viên dự án kèm Kỹ năng, Mức sẵn sàng và Năng lực giờ làm (FR-04, BR-05).
    """
    query = """
        SELECT pm.id AS member_record_id, pm.project_id, pm.user_id, pm.project_role,
               pm.skills, pm.availability, pm.capacity_hours, pm.joined_at,
               u.username, u.email, u.full_name, u.user_code, u.role AS system_role, u.status AS account_status
        FROM project_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.project_id = %s
        ORDER BY pm.project_role ASC, u.full_name ASC;
    """
    members = query_db(query, (project_id,))
    for member in members:
        try:
            member['availability_percent'] = availability_percent(member['availability'])
        except ValidationError:
            member['availability_percent'] = None
    return members

def check_user_project_role(user_id, project_id, system_role='member'):
    """Kiểm tra quyền hạn của người dùng trong dự án."""
    if system_role == 'admin':
        return True, 'admin'
    project = query_db('SELECT is_archived,archived_by FROM projects WHERE id=%s', (project_id,), one=True)
    if project and project['is_archived']:
        if system_role == 'leader' and project['archived_by'] == user_id:
            return True, 'leader'
        return False, None
        
    query = """
        SELECT project_role FROM project_members
        WHERE project_id = %s AND user_id = %s;
    """
    member = query_db(query, (project_id, user_id), one=True)
    if member:
        if member['project_role'] == 'leader' and system_role != 'leader':
            return True, 'member'
        return True, member['project_role']
    return False, None

@atomic
def add_project_member(leader_id, project_id, user_id, project_role='member', skills='', availability='Full-time', capacity_hours=40.0):
    """Thêm thành viên vào dự án (FR-04)."""
    if project_role not in ['leader', 'member', 'viewer']:
        return False, "Vai trò trong dự án không hợp lệ."
    require_active_project(project_id)
    user_id = integer(user_id, 'Thành viên', minimum=1)
    skills = text(skills, 'Kỹ năng', 60000)
    capacity_hours = number(capacity_hours, 'Năng lực')
    availability = f'{availability_percent(availability):g}%'
    target = query_db("SELECT role, status FROM users WHERE id = %s;", (user_id,), one=True)
    if not target or target['status'] != 'active':
        return False, "Tài khoản không tồn tại hoặc chưa được kích hoạt."
    if target['role'] not in ('leader', 'member'):
        return False, 'Tài khoản quản trị không được phân công làm nhân viên dự án.'
    if project_role == 'leader' and target['role'] != 'leader':
        return False, "Chỉ tài khoản Trưởng nhóm đã được duyệt mới có thể làm trưởng nhóm dự án."
    # Kiểm tra trùng lặp
    existing = query_db("SELECT id FROM project_members WHERE project_id = %s AND user_id = %s;", (project_id, user_id), one=True)
    if existing:
        return False, "Thành viên này đã có trong dự án."
        
    query = """
        INSERT INTO project_members (project_id, user_id, project_role, skills, availability, capacity_hours)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    execute_db(query, (project_id, user_id, project_role, skills, availability, capacity_hours))
    log_audit(leader_id, 'ADD_PROJECT_MEMBER', 'PROJECT_MEMBER', user_id, 
              {"project_id": project_id, "role": project_role, "capacity": float(capacity_hours)})
    return True, "Thêm thành viên thành công."

@atomic
def add_project_members(leader_id, project_id, user_ids, project_role='member', use_profiles=False):
    """Thêm một lúc nhiều thành viên vào dự án (FR-04 - Hỗ trợ thao tác hàng loạt)."""
    if not isinstance(user_ids, (list, tuple, set)) or not user_ids:
        return False, "Danh sách thành viên không hợp lệ.", 0
    if project_role not in ['leader', 'member', 'viewer']:
        return False, "Vai trò trong dự án không hợp lệ.", 0

    require_active_project(project_id)
    if len(user_ids) > 500:
        raise ValidationError('Chỉ được thêm tối đa 500 nhân viên mỗi lần.')
    user_ids = list(dict.fromkeys(integer(uid, 'Nhân viên', minimum=1) for uid in user_ids))
    targets = {}
    for uid in user_ids:
        target = query_db('SELECT id,full_name,role,status FROM users WHERE id=%s', (uid,), one=True)
        if not target or target['status'] != 'active' or target['role'] not in ('member','leader'):
            raise ValidationError('Danh sách có tài khoản chưa được duyệt, bị khóa hoặc không hợp lệ.')
        if project_role == 'leader' and target['role'] != 'leader':
            raise ValidationError('Chỉ tài khoản Trưởng nhóm được duyệt mới có thể làm trưởng nhóm dự án.')
        targets[uid] = target
    added_count = 0
    added_names = []
    for user_id in user_ids:
        uid = user_id
        target = targets[uid]

        existing = query_db("SELECT id FROM project_members WHERE project_id = %s AND user_id = %s;", (project_id, uid), one=True)
        if existing:
            continue

        defaults = {'skills':'','availability':'100%','capacity_hours':40}
        if use_profiles:
            from services.member_profile_service import public_profile_defaults
            defaults = public_profile_defaults(uid)
        execute_db("""
            INSERT INTO project_members (project_id, user_id, project_role, skills, availability, capacity_hours)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (project_id, uid, project_role, defaults['skills'], defaults['availability'], defaults['capacity_hours']))
        added_count += 1
        added_names.append(target['full_name'])

    if added_count > 0:
        log_audit(leader_id, 'ADD_PROJECT_MEMBERS_BATCH', 'PROJECT', project_id,
                  {"project_id": project_id, "count": added_count, "members": added_names})
        return True, f"Đã thêm thành công {added_count} thành viên vào dự án.", added_count
    return False, "Không có thành viên mới nào được thêm (các thành viên đã có trong dự án hoặc tài khoản chưa kích hoạt).", 0


@atomic
def update_member_capacity(leader_id, project_id, user_id, skills, availability, capacity_hours):
    """Cập nhật năng lực, kỹ năng và mức sẵn sàng của thành viên (FR-04, BR-05)."""
    require_active_project(project_id)
    if not query_db('SELECT id FROM project_members WHERE project_id=%s AND user_id=%s', (project_id,user_id), one=True):
        return False, 'Thành viên không thuộc dự án.'
    skills = text(skills, 'Kỹ năng', 60000)
    capacity_hours = number(capacity_hours, 'Năng lực')
    availability = f'{availability_percent(availability):g}%'
    query = """
        UPDATE project_members
        SET skills = %s, availability = %s, capacity_hours = %s
        WHERE project_id = %s AND user_id = %s;
    """
    execute_db(query, (skills, availability, capacity_hours, project_id, user_id))
    log_audit(leader_id, 'UPDATE_MEMBER_CAPACITY', 'PROJECT_MEMBER', user_id,
              {"project_id": project_id, "capacity_hours": float(capacity_hours)})
    return True, "Cập nhật năng lực thành viên thành công."

@atomic
def remove_project_member(leader_id, project_id, user_id):
    """Xóa thành viên khỏi dự án."""
    require_active_project(project_id)
    member = query_db('SELECT project_role FROM project_members WHERE project_id=%s AND user_id=%s', (project_id,user_id), one=True)
    if not member:
        return False, 'Thành viên không thuộc dự án.'
    if member['project_role'] == 'leader' and len(get_project_leaders(project_id)) <= 1:
        return False, 'Phải chuyển giao Trưởng nhóm trước khi xóa thành viên này.'
    # Keep task/audit history, remove only active assignments to departed members.
    execute_db("UPDATE tasks SET assignee_id=NULL WHERE project_id=%s AND assignee_id=%s AND is_archived=FALSE AND status<>'done'", (project_id,user_id))
    execute_db("DELETE FROM task_assignees WHERE user_id=%s AND task_id IN (SELECT id FROM tasks WHERE project_id=%s AND is_archived=FALSE AND status<>'done')", (user_id,project_id))
    execute_db("DELETE FROM project_members WHERE project_id = %s AND user_id = %s;", (project_id, user_id))
    log_audit(leader_id, 'REMOVE_PROJECT_MEMBER', 'PROJECT_MEMBER', user_id, {"project_id": project_id})
    return True, "Đã xóa thành viên khỏi dự án."


def get_project_leaders(project_id):
    return query_db("""
        SELECT u.id AS user_id, u.full_name, u.username
        FROM project_members pm JOIN users u ON u.id = pm.user_id
        WHERE pm.project_id = %s AND pm.project_role = 'leader'
          AND u.role = 'leader' AND u.status = 'active'
        ORDER BY u.full_name;
    """, (project_id,))


@atomic
def assign_project_leader(admin_id, project_id, user_id):
    project = query_db("SELECT id FROM projects WHERE id = %s AND is_archived = FALSE;", (project_id,), one=True)
    if not project:
        return False, "Dự án không tồn tại hoặc đã lưu trữ."
    user = query_db("SELECT role, status FROM users WHERE id = %s;", (user_id,), one=True)
    if not user or user['role'] != 'leader' or user['status'] != 'active':
        return False, "Chỉ có thể gán tài khoản Trưởng nhóm đã được duyệt."
    existing = query_db("SELECT project_role FROM project_members WHERE project_id = %s AND user_id = %s;",
                        (project_id, user_id), one=True)
    if existing and existing['project_role'] == 'leader':
        return False, "Tài khoản đã là Trưởng nhóm của dự án."
    if existing:
        execute_db("UPDATE project_members SET project_role = 'leader' WHERE project_id = %s AND user_id = %s;",
                   (project_id, user_id))
    else:
        execute_db("""
            INSERT INTO project_members (project_id, user_id, project_role)
            VALUES (%s, %s, 'leader');
        """, (project_id, user_id))
    log_audit(admin_id, 'ASSIGN_PROJECT_LEADER', 'PROJECT_MEMBER', user_id, {'project_id': project_id})
    return True, "Đã gán Trưởng nhóm vào dự án."


@atomic
def demote_project_leader(admin_id, project_id, user_id):
    existing = query_db("""
        SELECT id FROM project_members
        WHERE project_id = %s AND user_id = %s AND project_role = 'leader';
    """, (project_id, user_id), one=True)
    if not existing:
        return False, "Tài khoản không phải Trưởng nhóm của dự án."
    leaders = get_project_leaders(project_id)
    if len(leaders) <= 1:
        return False, "Dự án phải có ít nhất một Trưởng nhóm đang hoạt động."
    execute_db("UPDATE project_members SET project_role = 'member' WHERE project_id = %s AND user_id = %s;",
               (project_id, user_id))
    log_audit(admin_id, 'DEMOTE_PROJECT_LEADER', 'PROJECT_MEMBER', user_id, {'project_id': project_id})
    return True, "Đã chuyển Trưởng nhóm thành thành viên của dự án."
