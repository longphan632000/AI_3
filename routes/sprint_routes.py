from services.validation import json_object
from flask import Blueprint, render_template, request, session, jsonify
from routes import login_required
from services.sprint_service import (
    get_sprints_by_project, get_sprint_by_id, create_sprint, 
    update_sprint, assign_task_to_sprint
)
from services.project_member_service import check_user_project_role

sprint_bp = Blueprint('sprint_bp', __name__)

@sprint_bp.route('/sprints')
def sprints_page():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('sprints.html', user=session)

@sprint_bp.route('/api/projects/<int:project_id>/sprints', methods=['GET'])
@login_required
def list_sprints_api(project_id):
    has_access, _ = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
        
    sprints = get_sprints_by_project(project_id, archived=request.args.get('archived') == 'true')
    return jsonify({'success': True, 'sprints': sprints}), 200

@sprint_bp.route('/api/projects/<int:project_id>/sprints', methods=['POST'])
@login_required
def create_sprint_api(project_id):
    if session.get('role') == 'admin':
        return jsonify({'success': False, 'error': 'Theo tài liệu đặc tả, Quản trị viên chỉ quản lý tài khoản và nhật ký hệ thống, không có quyền tạo sprint trong dự án.'}), 403

    has_access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access or role != 'leader' or session.get('role') != 'leader':
        return jsonify({'success': False, 'error': 'Từ chối quyền: Chỉ Trưởng nhóm mới có thể tạo sprint (FR-07).'}), 403
        
    data = json_object()
    success, msg, sprint_id = create_sprint(
        user_id=session['user_id'],
        project_id=project_id,
        name=data.get('name'),
        goal=data.get('goal', ''),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        completion_criteria=data.get('completion_criteria', ''),
        sprint_code=data.get('sprint_code')
    )
    status_code = 201 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg, 'sprint_id': sprint_id}), status_code

@sprint_bp.route('/api/sprints/<int:sprint_id>', methods=['PUT'])
@login_required
def update_sprint_api(sprint_id):
    if session.get('role') == 'admin':
        return jsonify({'success': False, 'error': 'Theo tài liệu đặc tả, Quản trị viên không có quyền chỉnh sửa sprint trong dự án.'}), 403

    sprint = get_sprint_by_id(sprint_id)
    if not sprint:
        return jsonify({'success': False, 'error': 'Sprint không tồn tại.'}), 404
        
    has_access, role = check_user_project_role(session['user_id'], sprint['project_id'], session['role'])
    if not has_access or role != 'leader' or session.get('role') != 'leader':
        return jsonify({'success': False, 'error': 'Từ chối quyền: Chỉ Trưởng nhóm mới có thể sửa sprint.'}), 403
        
    data = json_object()
    success, msg = update_sprint(
        user_id=session['user_id'],
        sprint_id=sprint_id,
        name=data.get('name', sprint['name']),
        goal=data.get('goal', sprint['goal']),
        start_date=data.get('start_date', sprint['start_date']),
        end_date=data.get('end_date', sprint['end_date']),
        status=data.get('status', sprint['status']),
        completion_criteria=data.get('completion_criteria', sprint['completion_criteria']),
        sprint_code=data.get('sprint_code')
    )
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

@sprint_bp.route('/api/tasks/<int:task_id>/assign-sprint', methods=['POST'])
@login_required
def assign_sprint_api(task_id):
    from services.task_service import get_task_by_id, validate_task_links
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Nhiệm vụ không tồn tại.'}), 404
    has_access, role = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not has_access or role != 'leader' or session.get('role') != 'leader':
        return jsonify({'success': False, 'error': 'Chỉ Trưởng nhóm của dự án được gán sprint.'}), 403
    data = json_object()
    sprint_id = data.get('sprint_id')
    valid, error = validate_task_links(task['project_id'], sprint_id)
    if not valid:
        return jsonify({'success': False, 'error': error}), 400
    success, msg = assign_task_to_sprint(session['user_id'], task_id, sprint_id)
    return jsonify({'success': success, 'message': msg}), 200


@sprint_bp.route('/api/sprints/<int:sprint_id>', methods=['DELETE'])
@sprint_bp.route('/api/sprints/<int:sprint_id>/restore', methods=['POST'])
@login_required
def archive_or_restore_sprint_api(sprint_id):
    sprint = get_sprint_by_id(sprint_id)
    if not sprint:
        return jsonify(success=False, error='Sprint không tồn tại.'), 404
    access, role = check_user_project_role(session['user_id'], sprint['project_id'], session['role'])
    if not access or role != 'leader' or session['role'] != 'leader':
        return jsonify(success=False, error='Chỉ Trưởng nhóm dự án được quản lý sprint.'), 403
    from services.sprint_service import archive_sprint, restore_sprint
    action = restore_sprint if request.path.endswith('/restore') else archive_sprint
    success, message = action(session['user_id'], sprint_id)
    return jsonify(success=success, message=message), 200 if success else 400
