from services.validation import json_object
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from services.auth_service import authenticate_user, get_user_by_id, register_user

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_bp.admin_page'))
        return redirect(url_for('project_bp.dashboard_page'))
    return render_template('login.html')

@auth_bp.route('/api/auth/login', methods=['POST'])
def login_api():
    data = json_object()
    username_or_email = data.get('username_or_email', '').strip()
    password = data.get('password', '')
    
    if not username_or_email or not password:
        return jsonify({'success': False, 'error': 'Vui lòng nhập tên đăng nhập và mật khẩu.'}), 400
        
    ip = request.remote_addr or '127.0.0.1'
    success, msg, user = authenticate_user(username_or_email, password, ip)
    
    if not success:
        return jsonify({'success': False, 'error': msg}), 401
        
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['full_name'] = user['full_name']
    session['role'] = user['role']
    session.permanent = True
    
    # Quản trị viên chỉ quản lý hệ thống, chuyển hướng thẳng vào /admin
    if user['role'] == 'admin':
        redirect_target = url_for('admin_bp.admin_page')
    else:
        redirect_target = url_for('project_bp.dashboard_page')
        
    return jsonify({
        'success': True,
        'message': msg,
        'user': user,
        'redirect_url': redirect_target
    }), 200

@auth_bp.route('/api/auth/register', methods=['POST'])
def register_api():
    data = json_object()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'member')
    
    ip = request.remote_addr or '127.0.0.1'
    success, msg, user = register_user(username, email, password, full_name, role, ip)
    
    if not success:
        return jsonify({'success': False, 'error': msg}), 400
        
    return jsonify({
        'success': True,
        'message': msg,
        'user': user
    }), 202 if user['status'] == 'pending' else 201


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login_page'))

@auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'logged_in': False}), 200
    user = get_user_by_id(session['user_id'])
    return jsonify({'logged_in': True, 'user': user}), 200
