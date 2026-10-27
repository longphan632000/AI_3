from services.validation import json_object
from flask import Blueprint, render_template, request, session, jsonify
from routes import admin_required
from services.account_service import (
    list_all_users, create_user, update_user_status, update_user_role,
    review_leader_request, delete_user
)
from services.audit_service import get_recent_audit_logs
from services.project_member_service import get_project_leaders, assign_project_leader, demote_project_leader
from services.project_service import get_project_by_id
from services.ai_provider_service import AIProviderService
from services.gemini_service import AIProviderError, GeminiService

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/admin', methods=['GET'])
def admin_page():
    if session.get('role') != 'admin':
        return render_template('login.html', error='Yêu cầu quyền Quản trị viên để truy cập trang này.')
    return render_template('admin.html', user=session)


@admin_bp.route('/api/admin/ai-status', methods=['GET'])
@admin_required
def ai_status_api():
    """Expose configuration state to admins without returning the API key."""
    try:
        service = AIProviderService().provider
    except AIProviderError as error:
        return jsonify({'success': False, 'configured': False, 'error': str(error), 'error_code': error.code}), 503
    checked = request.args.get('probe') == '1'
    reachable, message = None, None
    checks = {}
    error_code = None
    if checked:
        general_ok, general_message = service.probe_model()
        general_check = {'model': service.model, 'reachable': general_ok,
                         'error_code': getattr(service, 'last_probe_error_code', None),
                         'diagnostics': getattr(service, 'last_probe_diagnostics', {})}
        if service.meeting_model == service.model:
            meeting_ok, meeting_message = general_ok, general_message
            meeting_check = dict(general_check)
        else:
            meeting_ok, meeting_message = service.probe_model(service.meeting_model)
            meeting_check = {'model': service.meeting_model, 'reachable': meeting_ok,
                             'error_code': getattr(service, 'last_probe_error_code', None),
                             'diagnostics': getattr(service, 'last_probe_diagnostics', {})}
        checks = {'general': general_check, 'meeting': meeting_check}
        error_code = general_check['error_code'] or meeting_check['error_code']
        reachable = general_ok and meeting_ok
        message = f'Tác vụ chung: {general_message} Biên bản: {meeting_message}'
    return jsonify({
        'success': True,
        'configured': service.configured,
        'model': service.model,
        'meeting_model': service.meeting_model,
        'api_checked': checked,
        'api_reachable': reachable,
        'message': message,
        'error_code': error_code,
        'checks': checks,
        'probe_scope': 'model_metadata_only' if checked else None,
    }), 200

@admin_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users_api():
    users = list_all_users()
    return jsonify({'success': True, 'users': users}), 200

@admin_bp.route('/api/admin/users', methods=['POST'])
@admin_required
def create_user_api():
    data = json_object()
    success, msg = create_user(
        admin_id=session['user_id'],
        username=data.get('username'),
        email=data.get('email'),
        password=data.get('password'),
        full_name=data.get('full_name'),
        role=data.get('role', 'member'),
        user_code=data.get('user_code')
    )
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user_api(user_id):
    from database.connection import query_db
    from services.account_service import update_user
    current = query_db('SELECT full_name,email FROM users WHERE id=%s', (user_id,), one=True)
    if not current:
        return jsonify(success=False, error='Tài khoản không tồn tại.'), 404
    data = json_object()
    success, message = update_user(session['user_id'], user_id,
        data.get('full_name', current['full_name']), data.get('email', current['email']), data.get('password'))
    return jsonify(success=success, **({'message': message} if success else {'error': message})), 200 if success else 400

@admin_bp.route('/api/admin/users/<int:user_id>/status', methods=['POST'])
@admin_required
def update_status_api(user_id):
    data = json_object()
    new_status = data.get('status')
    success, msg = update_user_status(session['user_id'], user_id, new_status)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

@admin_bp.route('/api/admin/users/<int:user_id>/role', methods=['POST'])
@admin_required
def update_role_api(user_id):
    data = json_object()
    new_role = data.get('role')
    success, msg = update_user_role(session['user_id'], user_id, new_role)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

@admin_bp.route('/api/admin/users/<int:user_id>/review', methods=['POST'])
@admin_required
def review_leader_request_api(user_id):
    data = json_object()
    success, msg = review_leader_request(
        session['user_id'],
        user_id,
        data.get('decision'),
        custom_user_code=data.get('user_code')
    )
    return jsonify({'success': success, 'message' if success else 'error': msg}), 200 if success else 400

@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_bp.route('/api/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user_api(user_id):
    """Xóa vĩnh viễn tài khoản người dùng bởi Quản trị viên (FR-02)."""
    success, msg = delete_user(session['user_id'], user_id)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code


@admin_bp.route('/api/admin/audit-logs', methods=['GET'])
@admin_required
def get_audit_logs_api():
    limit = request.args.get('limit', 50, type=int)
    logs = get_recent_audit_logs(limit)
    return jsonify({'success': True, 'logs': logs}), 200

@admin_bp.route('/api/admin/projects/<int:project_id>/leaders', methods=['GET'])
@admin_required
def list_project_leaders_api(project_id):
    if not get_project_by_id(project_id, session['user_id'], 'admin'):
        return jsonify({'success': False, 'error': 'Dự án không tồn tại.'}), 404
    return jsonify({'success': True, 'leaders': get_project_leaders(project_id)}), 200

@admin_bp.route('/api/admin/projects/<int:project_id>/leaders', methods=['POST'])
@admin_required
def assign_project_leader_api(project_id):
    data = json_object()
    user_id = data.get('user_id')
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return jsonify({'success': False, 'error': 'user_id phải là số nguyên.'}), 400
    success, msg = assign_project_leader(session['user_id'], project_id, user_id)
    return jsonify({'success': success, 'message' if success else 'error': msg}), 200 if success else 400

@admin_bp.route('/api/admin/projects/<int:project_id>/leaders/<int:user_id>', methods=['DELETE'])
@admin_required
def demote_project_leader_api(project_id, user_id):
    success, msg = demote_project_leader(session['user_id'], project_id, user_id)
    return jsonify({'success': success, 'message' if success else 'error': msg}), 200 if success else 400
    success, msg = demote_project_leader(session['user_id'], project_id, user_id)
    return jsonify({'success': success, 'message' if success else 'error': msg}), 200 if success else 400


@admin_bp.route('/api/admin/ai-history', methods=['GET'])
@admin_required
def admin_ai_history_api():
    """Xem lịch sử sử dụng AI toàn hệ thống cho Quản trị viên (UC012 / FR-15)."""
    from services.ai_history_service import get_ai_history
    limit = request.args.get('limit', 100, type=int)
    project_id = request.args.get('project_id', type=int)
    history = get_ai_history(session['user_id'], 'admin', project_id=project_id, limit=limit)
    return jsonify({'success': True, 'history': history or []}), 200
