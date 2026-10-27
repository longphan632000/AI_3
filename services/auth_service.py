from services.validation import text, ValidationError
from uuid import uuid4
from werkzeug.security import check_password_hash, generate_password_hash
from database.connection import query_db, execute_db, atomic
from services.audit_service import log_audit

def authenticate_user(username_or_email, password, ip_address='127.0.0.1'):
    """
    Xác thực đăng nhập người dùng (FR-01).
    Từ chối tài khoản bị khóa mà không làm lộ thông tin nhạy cảm.
    """
    query = """
        SELECT id, user_code, username, email, password_hash, full_name, role, status
        FROM users
        WHERE username = %s OR email = %s;
    """
    user = query_db(query, (username_or_email, username_or_email), one=True)
    
    if not user:
        return False, "Tên đăng nhập hoặc mật khẩu không chính xác.", None
        
    if not check_password_hash(user['password_hash'], password):
        log_audit(user['id'], 'LOGIN_FAILED_WRONG_PASSWORD', 'USER', user['id'], 
                  {"username": user['username']}, ip_address)
        return False, "Tên đăng nhập hoặc mật khẩu không chính xác.", None

    if user['status'] != 'active':
        log_audit(user['id'], 'LOGIN_BLOCKED_INACTIVE_ACCOUNT', 'USER', user['id'],
                  {"username": user['username'], "status": user['status']}, ip_address)
        messages = {
            'locked': "Tài khoản của bạn đang bị khóa. Vui lòng liên hệ Quản trị viên.",
            'pending': "Tài khoản của bạn đang chờ Quản trị viên (Admin) phê duyệt trước khi có thể đăng nhập.",
            'rejected': "Yêu cầu đăng ký tài khoản đã bị từ chối. Vui lòng liên hệ Quản trị viên."
        }
        return False, messages.get(user['status'], "Tài khoản chưa được kích hoạt."), None
        
    # Đăng nhập thành công
    log_audit(user['id'], 'LOGIN_SUCCESS', 'USER', user['id'], 
              {"username": user['username'], "role": user['role']}, ip_address)
    
    # Không trả password_hash ra ngoài
    user_data = {
        'id': user['id'],
        'user_code': user.get('user_code'),
        'username': user['username'],
        'email': user['email'],
        'full_name': user['full_name'],
        'role': user['role'],
        'status': user['status']
    }
    return True, "Đăng nhập thành công.", user_data

def get_user_by_id(user_id):
    query = """
        SELECT id, user_code, username, email, full_name, role, status, created_at
        FROM users
        WHERE id = %s;
    """
    return query_db(query, (user_id,), one=True)

@atomic
def register_user(username, email, password, full_name, role='member', ip_address='127.0.0.1'):
    """
    Đăng ký tài khoản người dùng mới (Mọi tài khoản đều ở trạng thái chờ Admin duyệt để tránh rác CSDL).
    """
    username = text(username, 'Tên đăng nhập', 50, required=True)
    email = text(email, 'Email', 100, required=True).lower()
    full_name = text(full_name, 'Họ tên', 100, required=True)
    if not isinstance(password, str) or not 6 <= len(password) <= 255:
        return False, 'Mật khẩu phải có từ 6 đến 255 ký tự.', None
    
    if not username or len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự.", None
    if not email or '@' not in email:
        return False, "Email không hợp lệ.", None
    if not password or len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự.", None
    if not full_name:
        return False, "Vui lòng nhập họ và tên.", None
        
    allowed_roles = ['member', 'leader']
    if role not in allowed_roles:
        role = 'member'
        
    # Kiểm tra trùng lặp username hoặc email
    existing_user = query_db("SELECT id, username, email FROM users WHERE username = %s OR email = %s;", (username, email), one=True)
    if existing_user:
        if existing_user['username'].lower() == username.lower():
            return False, "Tên đăng nhập này đã được sử dụng.", None
        else:
            return False, "Địa chỉ email này đã được sử dụng.", None
            
    password_hash = generate_password_hash(password)
    # Mọi tài khoản tự đăng ký đều bắt buộc chờ Admin phê duyệt để tránh ô nhiễm DB
    account_status = 'pending'
    
    # Quy chuẩn mã HR: ADM-xxx cho admin, TL-xxx cho leader, NV-xxx cho member
    prefix = 'TL' if role == 'leader' else 'NV'
    clean_code = prefix + '-' + uuid4().hex[:12].upper()

    query = """
        INSERT INTO users (user_code, username, email, password_hash, full_name, role, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    user_id = execute_db(query, (clean_code, username, email, password_hash, full_name, role, account_status))
    
    log_audit(user_id, 'USER_REGISTERED', 'USER', user_id, 
              {"username": username, "user_code": clean_code, "email": email, "role": role, "status": account_status}, ip_address)
              
    new_user = {
        'id': user_id,
        'user_code': clean_code,
        'username': username,
        'email': email,
        'full_name': full_name,
        'role': role,
        'status': account_status
    }
    message = "Đăng ký thành công! Tài khoản của bạn đang chờ Quản trị viên (Admin) phê duyệt trước khi có thể đăng nhập."
    return True, message, new_user
