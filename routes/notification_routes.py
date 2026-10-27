from flask import Blueprint, render_template, request, session, jsonify
from routes import login_required
from services.notification_service import (
    get_user_notifications, get_unread_count,
    mark_notification_as_read, mark_all_as_read
)
from services.email_service import check_and_send_overdue_email_alerts

notification_bp = Blueprint('notification_bp', __name__)

@notification_bp.route('/notifications')
def notifications_page():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('notifications.html', user=session)

@notification_bp.route('/api/notifications', methods=['GET'])
@login_required
def list_notifications_api():
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 30, type=int)
    notis = get_user_notifications(session['user_id'], unread_only, limit)
    return jsonify({'success': True, 'notifications': notis}), 200

@notification_bp.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def unread_count_api():
    count = get_unread_count(session['user_id'])
    return jsonify({'success': True, 'unread_count': count}), 200

@notification_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read_api(notification_id):
    mark_notification_as_read(notification_id, session['user_id'])
    return jsonify({'success': True, 'message': 'Đã đánh dấu đã đọc.'}), 200

@notification_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read_api():
    mark_all_as_read(session['user_id'])
    return jsonify({'success': True, 'message': 'Đã đánh dấu tất cả là đã đọc.'}), 200

@notification_bp.route('/api/notifications/trigger-overdue-check', methods=['POST'])
@login_required
def trigger_overdue_check_api():
    """
    Thực hiện quét nhiệm vụ trễ hạn và kích hoạt email cảnh báo theo BR-09 & FR-17.
    """
    from services.project_member_service import check_user_project_role
    project_id = request.args.get('project_id', type=int)
    user_id = None
    allowed_projects = None
    if project_id:
        access, role = check_user_project_role(session['user_id'], project_id, session['role'])
        if not access or role == 'viewer':
            return jsonify(success=False, error='Không có quyền quét cảnh báo dự án này.'), 403
        if role == 'member':
            user_id = session['user_id']
    elif session['role'] != 'admin':
        from database.connection import query_db
        memberships = query_db("SELECT project_id FROM project_members WHERE user_id=%s AND project_role<>'viewer'", (session['user_id'],))
        allowed_projects = [row['project_id'] for row in memberships]
        # A leader's member projects must not grant access to other people's alerts.
        if session['role'] == 'leader':
            allowed_projects = [row['project_id'] for row in query_db("SELECT project_id FROM project_members WHERE user_id=%s AND project_role='leader'", (session['user_id'],))]
        else:
            user_id = session['user_id']
    alerts = check_and_send_overdue_email_alerts(project_id=project_id, user_id=user_id, allowed_projects=allowed_projects)
    return jsonify({
        'success': True,
        'message': f'Đã quét xong. Đã phát hiện và xử lý cảnh báo cho {len(alerts)} nhiệm vụ trễ hạn.',
        'alerts': alerts
    }), 200
