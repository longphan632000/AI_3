from services.validation import json_object
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from routes import login_required
from services.project_service import (
    get_projects_for_user, get_project_by_id, create_project, 
    update_project, archive_project, delete_project
)
from services.project_member_service import (
    get_project_members, add_project_member, add_project_members,
    update_member_capacity, remove_project_member, check_user_project_role
)
from database.connection import query_db

project_bp = Blueprint('project_bp', __name__)

@project_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('project_bp.dashboard_page'))
    return redirect(url_for('auth_bp.login_page'))

@project_bp.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login_page'))
    return render_template('dashboard.html', user=session)

@project_bp.route('/api/projects', methods=['GET'])
@login_required
def list_projects_api():
    projects = get_projects_for_user(session['user_id'], session['role'], archived=request.args.get('archived') == 'true')
    return jsonify({'success': True, 'projects': projects}), 200

@project_bp.route('/api/projects', methods=['POST'])
@login_required
def create_project_api():
    if session['role'] not in ['leader', 'admin']:
        return jsonify({'success': False, 'error': 'Chỉ Trưởng nhóm hoặc Quản trị viên mới có thể tạo dự án.'}), 403
        
    data = json_object()
    success, msg, project_id = create_project(
        creator_id=session['user_id'],
        name=data.get('name'),
        description=data.get('description', ''),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        initial_member_ids=data.get('member_ids', data.get('initial_member_ids')),
        project_code=data.get('project_code')
    )
    status_code = 201 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg, 'project_id': project_id}), status_code


@project_bp.route('/api/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project_api(project_id):
    project = get_project_by_id(project_id, session['user_id'], session['role'], include_archived=True)
    if not project:
        return jsonify({'success': False, 'error': 'Dự án không tồn tại hoặc bạn không có quyền truy cập.'}), 404
    return jsonify({'success': True, 'project': project}), 200

@project_bp.route('/api/projects/<int:project_id>', methods=['PUT'])
@login_required
def update_project_api(project_id):
    has_access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access or role not in ['leader', 'admin']:
        return jsonify({'success': False, 'error': 'Từ chối quyền: Chỉ Trưởng nhóm hoặc Quản trị viên mới có thể chỉnh sửa dự án.'}), 403
        
    data = json_object()
    success, msg = update_project(
        user_id=session['user_id'],
        project_id=project_id,
        name=data.get('name'),
        description=data.get('description'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        status=data.get('status', 'active'),
        project_code=data.get('project_code')
    )
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

@project_bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project_api(project_id):
    has_access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access or role not in ['leader', 'admin']:
        return jsonify({'success': False, 'error': 'Từ chối quyền: Chỉ Trưởng nhóm hoặc Quản trị viên mới có thể xóa dự án.'}), 403
        
    permanent = request.args.get('permanent', 'false').lower() == 'true'
    if permanent:
        if session.get('role') != 'admin':
            return jsonify(success=False, error='Chỉ Quản trị viên được xóa vĩnh viễn theo BR-08.'), 403
        delete_project(session['user_id'], project_id)
        return jsonify({'success': True, 'message': 'Đã xóa vĩnh viễn dự án thành công.'}), 200
    else:
        archive_project(session['user_id'], project_id)
        return jsonify({'success': True, 'message': 'Đã lưu trữ dự án thành công.'}), 200

# Thành viên dự án
@project_bp.route('/api/projects/<int:project_id>/members', methods=['GET'])
@login_required
def get_members_api(project_id):
    has_access, _ = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
    members = get_project_members(project_id)
    return jsonify({'success': True, 'members': members}), 200

@project_bp.route('/api/projects/<int:project_id>/members', methods=['POST'])
@login_required
def add_member_api(project_id):
    has_access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access or role not in ['leader', 'admin']:
        return jsonify({'success': False, 'error': 'Từ chối quyền: Chỉ Trưởng nhóm mới có thể thêm thành viên.'}), 403
        
    data = json_object()
    
    # Hỗ trợ thêm hàng loạt (batch) hoặc thêm từng người
    user_ids = data.get('user_ids')
    if isinstance(user_ids, list) and user_ids:
        success, msg, count = add_project_members(
            leader_id=session['user_id'],
            project_id=project_id,
            user_ids=user_ids,
            project_role=data.get('project_role', 'member')
        )
        status_code = 200 if success else 400
        return jsonify({'success': success, 'message' if success else 'error': msg, 'added_count': count}), status_code

    success, msg = add_project_member(
        leader_id=session['user_id'],
        project_id=project_id,
        user_id=data.get('user_id'),
        project_role=data.get('project_role', 'member'),
        skills=data.get('skills', ''),
        availability=data.get('availability', 'Full-time'),
        capacity_hours=data.get('capacity_hours', 40.0)
    )
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

@project_bp.route('/api/projects/<int:project_id>/eligible-users', methods=['GET'])
@login_required
def eligible_users_api(project_id):
    has_access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access or role != 'leader' or session.get('role') != 'leader':
        return jsonify({'success': False, 'error': 'Chỉ Trưởng nhóm của dự án được xem danh sách này.'}), 403
    users = query_db("""
        SELECT id, user_code, full_name, username, role FROM users
        WHERE status = 'active' AND role IN ('member', 'leader')
          AND id NOT IN (SELECT user_id FROM project_members WHERE project_id = %s)
        ORDER BY full_name;
    """, (project_id,))
    return jsonify({'success': True, 'users': users}), 200

@project_bp.route('/api/users/assignable', methods=['GET'])
@login_required
def assignable_users_api():
    """Lấy danh sách tất cả tài khoản hợp lệ để chọn khi tạo dự án mới."""
    if session['role'] not in ('leader','admin'):
        return jsonify(success=False, error='Chỉ Trưởng nhóm hoặc Quản trị viên được tra cứu tài khoản để phân công.'), 403
    users = query_db("""
        SELECT id, user_code, full_name, username, role FROM users
        WHERE status = 'active' AND role IN ('member', 'leader')
        ORDER BY full_name;
    """)
    return jsonify({'success': True, 'users': users}), 200


@project_bp.route('/api/projects/<int:project_id>/members/<int:user_id>/capacity', methods=['PUT'])
@login_required
def update_capacity_api(project_id, user_id):
    has_access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access or role not in ['leader', 'admin']:
        return jsonify({'success': False, 'error': 'Từ chối quyền: Chỉ Trưởng nhóm mới có thể sửa năng lực thành viên.'}), 403
        
    data = json_object()
    success, msg = update_member_capacity(
        leader_id=session['user_id'],
        project_id=project_id,
        user_id=user_id,
        skills=data.get('skills', ''),
        availability=data.get('availability', 'Full-time'),
        capacity_hours=data.get('capacity_hours', 40.0)
    )
    return jsonify({'success': success, 'message' if success else 'error': msg}), 200 if success else 400


@project_bp.route('/api/projects/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
@login_required
def remove_member_api(project_id, user_id):
    access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not access or role not in ('leader', 'admin'):
        return jsonify(success=False, error='Chỉ Trưởng nhóm được xóa thành viên.'), 403
    success, message = remove_project_member(session['user_id'], project_id, user_id)
    return jsonify(success=success, **({'message': message} if success else {'error': message})), 200 if success else 400


@project_bp.route('/api/projects/<int:project_id>/restore', methods=['POST'])
@login_required
def restore_project_api(project_id):
    access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not access or role not in ('leader', 'admin'):
        return jsonify(success=False, error='Không có quyền khôi phục dự án.'), 403
    from services.project_service import restore_project
    success, message = restore_project(session['user_id'], project_id)
    return jsonify(success=success, message=message)

