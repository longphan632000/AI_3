from functools import wraps
from flask import session, jsonify, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Vui lòng đăng nhập để thực hiện thao tác này.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Vui lòng đăng nhập.'}), 401
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Từ chối quyền: Yêu cầu quyền Quản trị viên.'}), 403
        return f(*args, **kwargs)
    return decorated_function
