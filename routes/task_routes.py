from services.validation import json_object
from database.connection import atomic
from flask import Blueprint, render_template, request, session, jsonify
from routes import login_required
from services.task_service import (
    get_tasks_by_project, get_task_by_id, create_task,
    update_task_status, update_task_details, archive_task,
    update_task_progress
)
from services.project_member_service import check_user_project_role

task_bp = Blueprint('task_bp', __name__)


def task_capabilities(task, project_role):
    """Expose the same permissions to every browser; writes still check again."""
    assigned = session['user_id'] == task.get('assignee_id') or session['user_id'] in (task.get('support_member_ids') or [])
    allowed = not task.get('is_archived') and (project_role in ('leader', 'admin') or (project_role == 'member' and assigned))
    return {**task, 'can_update_status': bool(allowed), 'can_update_progress': bool(allowed)}

@task_bp.route('/kanban')
def kanban_page():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('kanban.html', user=session)

@task_bp.route('/api/projects/<int:project_id>/tasks', methods=['GET'])
@login_required
def list_tasks_api(project_id):
    has_access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
        
    sprint_id = request.args.get('sprint_id', type=int)
    assignee_id = request.args.get('assignee_id', type=int)
    status = request.args.get('status')
    is_overdue_only = request.args.get('overdue_only', 'false').lower() == 'true'
    keyword = request.args.get('keyword')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    tasks = get_tasks_by_project(
        project_id=project_id,
        sprint_id=sprint_id,
        assignee_id=assignee_id,
        status=status,
        is_overdue_only=is_overdue_only,
        keyword=keyword,
        limit=limit,
        offset=offset,
        archived=request.args.get('archived') == 'true',
        priority=request.args.get('priority'), due_from=request.args.get('due_from'),
        due_to=request.args.get('due_to'), sort_by=request.args.get('sort_by', 'priority'),
        sort_order=request.args.get('sort_order', 'desc')
    )
    return jsonify({'success': True, 'tasks': [task_capabilities(task, role) for task in tasks]}), 200

@task_bp.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
@login_required
def create_task_api(project_id):
    if session.get('role') == 'admin':
        return jsonify({'success': False, 'error': 'Theo tài liệu đặc tả, Quản trị viên chỉ quản lý tài khoản và nhật ký hệ thống, không có quyền tạo nhiệm vụ trong dự án.'}), 403
        
    has_access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access or role != 'leader' or session.get('role') != 'leader':
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
        
    data = json_object()
    support_member_ids = data.get('support_member_ids') or data.get('supporters')
    success, msg, task_id = create_task(
        user_id=session['user_id'],
        project_id=project_id,
        title=data.get('title'),
        description=data.get('description', ''),
        sprint_id=data.get('sprint_id'),
        assignee_id=data.get('assignee_id'),
        priority=data.get('priority', 'medium'),
        due_date=data.get('due_date'),
        estimated_hours=data.get('estimated_hours', 0.0),
        labels=data.get('labels'),
        blockers=data.get('blockers'),
        support_member_ids=support_member_ids,
        task_code=data.get('task_code')
    )
    status_code = 201 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg, 'task_id': task_id}), status_code

@task_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task_api(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Nhiệm vụ không tồn tại.'}), 404
        
    has_access, role = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập nhiệm vụ.'}), 403
        
    return jsonify({'success': True, 'task': task_capabilities(task, role)}), 200

@task_bp.route('/api/tasks/<int:task_id>/status', methods=['PUT'])
@login_required
def update_status_api(task_id):
    """Cập nhật trạng thái Kanban (FR-06, BR-01)."""
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Nhiệm vụ không tồn tại.'}), 404
        
    has_access, role = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not has_access or role not in ['leader', 'member', 'admin']:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập nhiệm vụ.'}), 403
        
    # Thành viên chỉ được cập nhật nhiệm vụ do mình phụ trách chính hoặc cùng tham gia hỗ trợ
    user_id = session['user_id']
    is_supporter = user_id in (task.get('support_member_ids') or [])
    if role not in ('leader', 'member', 'admin'):
        return jsonify(success=False, error='Bạn chỉ có quyền xem nhiệm vụ.'), 403
    if role == 'member' and task['assignee_id'] != user_id and not is_supporter:
        return jsonify({'success': False, 'error': 'Thành viên chỉ được cập nhật trạng thái nhiệm vụ do mình phụ trách hoặc hỗ trợ.'}), 403
        
    data = json_object()
    new_status = data.get('status')
    success, msg = update_task_status(session['user_id'], task_id, new_status)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

@task_bp.route('/api/tasks/<int:task_id>/progress', methods=['POST', 'PUT'])
@login_required
def update_progress_api(task_id):
    """Cập nhật % tiến độ thực tế (0% - 100%) của nhiệm vụ."""
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Nhiệm vụ không tồn tại.'}), 404
        
    has_access, role = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập nhiệm vụ.'}), 403
        
    user_id = session['user_id']
    is_supporter = user_id in (task.get('support_member_ids') or [])
    if role == 'member' and task['assignee_id'] != user_id and not is_supporter:
        return jsonify({'success': False, 'error': 'Thành viên chỉ được cập nhật tiến độ nhiệm vụ do mình phụ trách hoặc hỗ trợ.'}), 403
        
    data = json_object()
    progress_val = data.get('progress_percent')
    if progress_val is None:
        return jsonify({'success': False, 'error': 'Vui lòng cung cấp giá trị % tiến độ.'}), 400
        
    success, msg = update_task_progress(user_id, task_id, progress_val)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg, 'progress_percent': progress_val}), status_code

@task_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task_api(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Nhiệm vụ không tồn tại.'}), 404
        
    has_access, role = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not has_access or role != 'leader' or session.get('role') != 'leader':
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập nhiệm vụ.'}), 403
        
    data = json_object()
    support_member_ids = data.get('support_member_ids') if 'support_member_ids' in data else data.get('supporters')
    success, msg = update_task_details(
        user_id=session['user_id'],
        task_id=task_id,
        title=data.get('title', task['title']),
        description=data.get('description', task['description']),
        sprint_id=data.get('sprint_id', task['sprint_id']),
        assignee_id=data.get('assignee_id', task['assignee_id']),
        priority=data.get('priority', task['priority']),
        due_date=data.get('due_date', task['due_date']),
        estimated_hours=data.get('estimated_hours', task['estimated_hours']),
        labels=data.get('labels', task['labels']),
        blockers=data.get('blockers', task['blockers']),
        support_member_ids=support_member_ids,
        task_code=data.get('task_code'),
        progress_percent=data.get('progress_percent')
    )
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

@task_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def archive_task_api(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Nhiệm vụ không tồn tại.'}), 404
        
    has_access, role = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not has_access or role != 'leader' or session.get('role') != 'leader':
        return jsonify({'success': False, 'error': 'Từ chối quyền: Chỉ Trưởng nhóm mới có thể lưu trữ nhiệm vụ.'}), 403
        
    archive_task(session['user_id'], task_id)
    return jsonify({'success': True, 'message': 'Đã lưu trữ nhiệm vụ.'}), 200


@task_bp.route('/api/tasks/<int:task_id>/restore', methods=['POST'])
@login_required
@atomic
def restore_task_api(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return jsonify(success=False, error='Nhiệm vụ không tồn tại.'), 404
    access, role = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not access or role != 'leader':
        return jsonify(success=False, error='Chỉ Trưởng nhóm được khôi phục nhiệm vụ.'), 403
    from services.access_service import require_active_project
    from database.connection import execute_db
    from services.audit_service import log_audit
    require_active_project(task['project_id'])
    execute_db('UPDATE tasks SET is_archived=FALSE WHERE id=%s', (task_id,))
    log_audit(session['user_id'], 'RESTORE_TASK', 'TASK', task_id)
    return jsonify(success=True, message='Đã khôi phục nhiệm vụ.')
