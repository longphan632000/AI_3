from services.validation import text, ValidationError
from uuid import uuid4
from werkzeug.security import generate_password_hash
from database.connection import query_db, execute_db, atomic
from services.audit_service import log_audit

def list_all_users():
    """Lấy danh sách tất cả người dùng (FR-02 - Dành cho Quản trị viên)."""
    query = """
        SELECT id, user_code, username, email, full_name, role, status, created_at, updated_at
        FROM users
        ORDER BY id ASC;
    """
    return query_db(query)

@atomic
def create_user(admin_id, username, email, password, full_name, role='member', user_code=None):
    """Tạo tài khoản mới bởi Quản trị viên (FR-02)."""
    username = text(username, 'Tên đăng nhập', 50, required=True)
    email = text(email, 'Email', 100, required=True).lower()
    full_name = text(full_name, 'Họ tên', 100, required=True)
    if len(username) < 3 or len(username) > 50:
        return False, "Tên đăng nhập phải có từ 3 đến 50 ký tự."
    if not email or '@' not in email or len(email) > 100:
        return False, "Email không hợp lệ."
    if not full_name or len(full_name) > 100:
        return False, "Họ tên không hợp lệ."
    if not password or len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự."
    if role not in ['admin', 'leader', 'member']:
        return False, "Vai trò không hợp lệ."
    # Kiểm tra trùng lặp username hoặc email
    existing = query_db("SELECT id FROM users WHERE username = %s OR email = %s;", (username, email), one=True)
    if existing:
        return False, "Tên đăng nhập hoặc email đã tồn tại."

    clean_code = text(user_code, 'Mã tài khoản', 50).upper()
    if clean_code:
        existing_code = query_db("SELECT id FROM users WHERE UPPER(user_code) = %s;", (clean_code,), one=True)
        if existing_code:
            return False, f"Mã thành viên '{clean_code}' đã tồn tại, vui lòng chọn mã khác."
    else:
        prefix = 'ADM' if role == 'admin' else ('TL' if role == 'leader' else 'NV')
        clean_code = prefix + '-' + uuid4().hex[:12].upper()

    password_hash = generate_password_hash(password)
    query = """
        INSERT INTO users (user_code, username, email, password_hash, full_name, role, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'active');
    """
    user_id = execute_db(query, (clean_code, username, email, password_hash, full_name, role))
    log_audit(admin_id, 'CREATE_USER', 'USER', user_id, 
              {"username": username, "user_code": clean_code, "email": email, "role": role})
    return True, f"Tạo tài khoản thành công với mã [{clean_code}]."

@atomic
def update_user_status(admin_id, target_user_id, new_status):
    """Khóa hoặc mở khóa tài khoản (FR-02)."""
    if new_status not in ['active', 'locked']:
        return False, "Trạng thái không hợp lệ."
        
    if admin_id == target_user_id and new_status == 'locked':
        return False, "Quản trị viên không thể tự khóa tài khoản của chính mình."

    target = query_db("SELECT role, status FROM users WHERE id = %s;", (target_user_id,), one=True)
    if not target:
        return False, "Tài khoản không tồn tại."
    if target['status'] in ['pending', 'rejected']:
        return False, "Yêu cầu tài khoản phải được xử lý qua thao tác duyệt hoặc từ chối."
    if target['role'] == 'admin' and target['status'] == 'active' and new_status == 'locked':
        admin_count = query_db("SELECT COUNT(*) AS total FROM users WHERE role = 'admin' AND status = 'active';", one=True)
        if admin_count['total'] <= 1:
            return False, "Không thể khóa Quản trị viên đang hoạt động cuối cùng."
        
    query = "UPDATE users SET status = %s WHERE id = %s;"
    execute_db(query, (new_status, target_user_id))
    log_audit(admin_id, 'UPDATE_USER_STATUS', 'USER', target_user_id, {"status": new_status})
    return True, f"Đã chuyển trạng thái tài khoản sang {new_status}."

@atomic
def update_user_role(admin_id, target_user_id, new_role):
    """Gán vai trò hệ thống (FR-02)."""
    if new_role not in ['admin', 'leader', 'member']:
        return False, "Vai trò không hợp lệ."

    target = query_db("SELECT role, status FROM users WHERE id = %s;", (target_user_id,), one=True)
    if not target:
        return False, "Tài khoản không tồn tại."
    if target['status'] in ['pending', 'rejected']:
        return False, "Yêu cầu tài khoản đang chờ xử lý hoặc đã bị từ chối."
    if admin_id == target_user_id and new_role != 'admin':
        return False, "Quản trị viên không thể tự hạ vai trò của chính mình."
    if target['role'] == 'admin' and target['status'] == 'active' and new_role != 'admin':
        admin_count = query_db("SELECT COUNT(*) AS total FROM users WHERE role = 'admin' AND status = 'active';", one=True)
        if admin_count['total'] <= 1:
            return False, "Không thể hạ vai trò Quản trị viên đang hoạt động cuối cùng."
        
    query = "UPDATE users SET role = %s WHERE id = %s;"
    execute_db(query, (new_role, target_user_id))
    log_audit(admin_id, 'UPDATE_USER_ROLE', 'USER', target_user_id, {"role": new_role})
    return True, f"Đã cập nhật vai trò người dùng thành {new_role}."


@atomic
def review_user_request(admin_id, target_user_id, decision, custom_user_code=None):
    """Phê duyệt hoặc từ chối yêu cầu đăng ký tài khoản (cả Member và Leader)."""
    if decision not in ['approve', 'reject', 'reopen']:
        return False, "Quyết định không hợp lệ."
    target = query_db("SELECT id, role, status, user_code FROM users WHERE id = %s;", (target_user_id,), one=True)
    expected_status = 'rejected' if decision == 'reopen' else 'pending'
    if not target or target['status'] != expected_status:
        return False, "Không tìm thấy yêu cầu tài khoản đang chờ duyệt."
    new_status = {'approve': 'active', 'reject': 'rejected', 'reopen': 'pending'}[decision]

    assigned_code = target['user_code']
    if decision == 'approve':
        clean_code = (custom_user_code or '').strip().upper()
        if clean_code:
            existing_code = query_db("SELECT id FROM users WHERE UPPER(user_code) = %s AND id != %s;", (clean_code, target_user_id), one=True)
            if existing_code:
                return False, f"Mã tài khoản '{clean_code}' đã tồn tại, vui lòng chọn mã khác."
            assigned_code = clean_code
        elif not assigned_code:
            prefix = 'TL' if target['role'] == 'leader' else 'NV'
            assigned_code = prefix + '-' + uuid4().hex[:12].upper()

    changed = execute_db(
        "UPDATE users SET status = %s, user_code = %s WHERE id = %s AND status = %s;",
        (new_status, assigned_code, target_user_id, expected_status)
    )
    if changed != 1:
        return False, "Yêu cầu đã được xử lý trước đó."
    log_audit(admin_id, 'REVIEW_USER_REQUEST', 'USER', target_user_id,
              {'decision': decision, 'status': new_status, 'user_code': assigned_code})
    role_name = "Trưởng nhóm" if target['role'] == 'leader' else ("Thành viên" if target['role'] == 'member' else target['role'])
    messages = {
        'approve': f"Đã duyệt tài khoản {role_name} thành công (Mã: {assigned_code}).",
        'reject': f"Đã từ chối yêu cầu tài khoản {role_name}.",
        'reopen': f"Đã mở lại yêu cầu tài khoản {role_name} để xét duyệt."
    }
    return True, messages[decision]

def review_leader_request(admin_id, target_user_id, decision, custom_user_code=None):
    """Alias tương thích ngược."""
    return review_user_request(admin_id, target_user_id, decision, custom_user_code)
@atomic
def delete_user(admin_id, target_user_id):
    """
    Xóa vĩnh viễn tài khoản người dùng bởi Quản trị viên (UC002)
    Bảo toàn toàn vẹn dữ liệu: Chuyển giao các tài nguyên dự án/nhiệm vụ sang Quản trị viên trước khi xóa.
    """
    if admin_id == target_user_id:
        return False, "Quản trị viên không thể tự xóa tài khoản của chính mình."

    target = query_db("SELECT id, username, email, full_name, role, status FROM users WHERE id = %s;", (target_user_id,), one=True)
    if not target:
        return False, "Tài khoản không tồn tại."

    if target['role'] == 'admin' and target['status'] == 'active':
        admin_count = query_db("SELECT COUNT(*) AS total FROM users WHERE role = 'admin' AND status = 'active';", one=True)
        if admin_count['total'] <= 1:
            return False, "Không thể xóa Quản trị viên đang hoạt động cuối cùng trong hệ thống."

    # 1. Chuyển giao quyền sở hữu dự án (projects.created_by ON DELETE RESTRICT) sang Quản trị viên
    execute_db("UPDATE projects SET created_by = %s WHERE created_by = %s;", (admin_id, target_user_id))

    # 2. Chuyển giao người tạo nhiệm vụ (tasks.reporter_id ON DELETE RESTRICT) sang Quản trị viên
    execute_db("UPDATE tasks SET reporter_id = %s WHERE reporter_id = %s;", (admin_id, target_user_id))

    for table, column in (('comments','user_id'), ('attachments','uploaded_by'),
                          ('meeting_notes','created_by'), ('meeting_minutes','created_by'),
                          ('ai_drafts','created_by'), ('ai_history','requester_id')):
        execute_db(f'UPDATE {table} SET {column}=%s WHERE {column}=%s', (admin_id,target_user_id))
    for table in ('meeting_minutes','ai_drafts'):
        execute_db(f'UPDATE {table} SET confirmed_by=NULL WHERE confirmed_by=%s', (target_user_id,))
    execute_db('UPDATE audit_logs SET user_id=NULL WHERE user_id=%s', (target_user_id,))
    execute_db('UPDATE tasks SET assignee_id=NULL WHERE assignee_id=%s', (target_user_id,))
    execute_db('DELETE FROM task_assignees WHERE user_id=%s', (target_user_id,))
    execute_db('DELETE FROM notifications WHERE user_id=%s', (target_user_id,))
    execute_db('DELETE FROM project_members WHERE user_id=%s', (target_user_id,))
    # 3. Xóa người dùng khỏi bảng users (các bảng con sẽ tự động CASCADE hoặc SET NULL)
    execute_db("DELETE FROM users WHERE id = %s;", (target_user_id,))

    # 4. Ghi nhật ký kiểm toán (Audit Log)
    log_audit(admin_id, 'DELETE_USER', 'USER', target_user_id, {
        "username": target['username'],
        "email": target['email'],
        "full_name": target['full_name'],
        "role": target['role']
    })

    return True, f"Đã xóa vĩnh viễn tài khoản {target['full_name']} ({target['username']})."



@atomic
def update_user(admin_id, target_user_id, full_name, email, password=None):
    current = query_db('SELECT id FROM users WHERE id=%s', (target_user_id,), one=True)
    if not current:
        return False, 'Tài khoản không tồn tại.'
    full_name = text(full_name, 'Họ tên', 100, required=True)
    email = text(email, 'Email', 100, required=True).lower()
    if '@' not in email:
        return False, 'Email không hợp lệ.'
    if query_db('SELECT id FROM users WHERE email=%s AND id<>%s', (email,target_user_id), one=True):
        return False, 'Email đã được sử dụng.'
    if password:
        if not isinstance(password, str) or not 6 <= len(password) <= 255:
            return False, 'Mật khẩu phải có từ 6 đến 255 ký tự.'
        execute_db('UPDATE users SET password_hash=%s WHERE id=%s', (generate_password_hash(password),target_user_id))
    execute_db('UPDATE users SET full_name=%s,email=%s WHERE id=%s', (full_name,email,target_user_id))
    log_audit(admin_id, 'UPDATE_USER', 'USER', target_user_id, {'full_name':full_name,'email':email})
    return True, 'Đã cập nhật tài khoản.'
