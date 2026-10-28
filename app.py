import os
import sys
import secrets
from datetime import timedelta, datetime, date
from decimal import Decimal
from flask.json.provider import DefaultJSONProvider
from flask import Flask, jsonify, session
from services.validation import ValidationError, json_object, integer

if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

# Khởi tạo CSDL nếu cần
from database.connection import test_mysql_connection, get_database_status, DatabaseUnavailableError
from database.migrations import ensure_account_approval_schema, ensure_ai_schema, ensure_core_schema

# Khởi tạo Flask App
class ProjectJSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return DefaultJSONProvider.default(value)


app = Flask(__name__, template_folder='templates', static_folder='static')
app.json = ProjectJSONProvider(app)
configured_secret = os.getenv('SECRET_KEY', '').strip()
app.secret_key = (configured_secret if len(configured_secret) >= 32 and
                  configured_secret != 'dev_secret_key_ai_sdlc_2026_super_secure'
                  else secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.context_processor
def shared_app_version():
    from services.app_version_service import get_app_version
    return {'app_version': get_app_version()}


@app.after_request
def prevent_stale_shared_pages(response):
    from flask import request
    if request.path.startswith('/api/') or response.mimetype == 'text/html':
        from services.app_version_service import get_app_version
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-App-Version'] = get_app_version()
    return response

ensure_account_approval_schema()
ensure_core_schema()
ensure_ai_schema()

@app.before_request
def refresh_authenticated_user():
    """Honor locks, approvals and role changes on existing sessions."""
    from flask import request, session, redirect, url_for
    if 'user_id' not in session:
        return None
    from services.auth_service import get_user_by_id
    user = get_user_by_id(session['user_id'])
    if not user or user['status'] != 'active':
        session.clear()
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Tài khoản không còn quyền truy cập.'}), 401
        return redirect(url_for('auth_bp.login_page'))
    session['role'] = user['role']
    session['full_name'] = user['full_name']


@app.before_request
def validate_scope_for_writes():
    """Viewer is read-only; archived data cannot be changed (FR-02, BR-08)."""
    from flask import request
    from database.connection import query_db
    from services.project_member_service import check_user_project_role
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return
    data = json_object() if request.is_json else {}
    for field in ('title', 'name', 'description', 'full_name', 'email', 'username', 'password', 'username_or_email', 'content', 'labels', 'blockers', 'task_code', 'project_code', 'sprint_code', 'user_code'):
        if field in data and data[field] is not None and not isinstance(data[field], str):
            raise ValidationError(f'Trường {field} phải là văn bản.')
    if 'user_id' not in session:
        return
    values = request.view_args or {}
    project_id = values.get('project_id')
    object_row = None
    for key, table in (('task_id', 'tasks'), ('sprint_id', 'sprints'), ('draft_id', 'ai_drafts')):
        if key in values:
            object_row = query_db(f'SELECT * FROM {table} WHERE id=%s', (values[key],), one=True)
            if object_row:
                project_id = object_row['project_id']
    if request.path == '/api/ai' and data.get('project_id') is not None:
        project_id = integer(data['project_id'], 'Dự án', minimum=1)
    if project_id is None:
        return
    if object_row and object_row.get('sprint_id'):
        sprint = query_db('SELECT is_archived FROM sprints WHERE id=%s', (object_row['sprint_id'],), one=True)
        if sprint and sprint['is_archived']:
            return jsonify(success=False, error='Sprint đã lưu trữ; hãy khôi phục trước khi chỉnh sửa nhiệm vụ.'), 409
    access, role = check_user_project_role(session['user_id'], project_id, session['role'])
    if not access:
        return jsonify(success=False, error='Bạn không có quyền truy cập dự án.'), 403
    if role == 'viewer':
        return jsonify(success=False, error='Người xem chỉ có quyền đọc dữ liệu.'), 403
    project = query_db('SELECT is_archived FROM projects WHERE id=%s', (project_id,), one=True)
    if not project:
        return jsonify(success=False, error='Dự án không tồn tại.'), 404
    restoring = request.path.endswith('/restore')
    deleting_permanently = request.method == 'DELETE' and session['role'] == 'admin' and request.args.get('permanent') == 'true'
    if not restoring and not deleting_permanently and (project['is_archived'] or (object_row and object_row.get('is_archived'))):
        return jsonify(success=False, error='Dữ liệu đã lưu trữ; hãy khôi phục trước khi chỉnh sửa.'), 409

# Đăng ký các Blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.project_routes import project_bp
from routes.task_routes import task_bp
from routes.sprint_routes import sprint_bp
from routes.collaboration_routes import collab_bp
from routes.report_routes import report_bp
from routes.ai_routes import ai_bp
from routes.notification_routes import notification_bp
from routes.sync_routes import sync_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(project_bp)
app.register_blueprint(task_bp)
app.register_blueprint(sprint_bp)
app.register_blueprint(collab_bp)
app.register_blueprint(report_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(sync_bp)


@app.after_request
def prevent_stale_client_data(response):
    from flask import request
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
        if (request.method in ('POST','PUT','PATCH','DELETE') and 200 <= response.status_code < 300
                and session.get('user_id') and not request.path.startswith('/api/auth/')):
            data = response.get_json(silent=True)
            if isinstance(data, dict) and data.get('success') is True:
                # The committed business change stays successful even if the optional
                # invalidation marker cannot be written. Normal business audits remain.
                try:
                    from services.audit_service import log_audit
                    log_audit(session['user_id'], 'CLIENT_DATA_CHANGED', 'SYSTEM',
                              details={'endpoint':request.endpoint})
                except Exception:
                    app.logger.warning('Could not record client invalidation marker')
    elif response.mimetype == 'text/html':
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.url_defaults
def version_static_assets(endpoint, values):
    if endpoint == 'static' and 'filename' in values:
        from pathlib import Path
        asset = Path(app.static_folder) / values['filename']
        if asset.is_file():
            values.setdefault('v', str(asset.stat().st_mtime_ns))


@app.route('/sw.js')
def service_worker():
    response = app.send_static_file('sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/api/health')
def health_check():
    mysql_ok, mysql_msg = test_mysql_connection()
    return jsonify({
        'status': 'HEALTHY' if mysql_ok else 'UNAVAILABLE',
        'active_database_engine': 'mysql',
        'mysql_ready': mysql_ok,
        'mysql_diagnostic': mysql_msg,
        'system': 'Hệ thống Quản lý Dự án Nhóm Tích hợp AI (Đề tài 33)',
        'sdlc_process': 'AI-Augmented SDLC with Codex'
    }), 200 if mysql_ok else 503

@app.route('/api/system/db-status')
def db_status_api():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Yêu cầu quyền Quản trị viên.'}), 403
    status = get_database_status()
    return jsonify(status), 200 if status['status'] == 'connected' else 503

@app.errorhandler(DatabaseUnavailableError)
def database_unavailable(error):
    return jsonify({'success': False, 'error': str(error)}), 503

@app.errorhandler(404)
def not_found_error(e):
    return jsonify({'success': False, 'error': 'Endpoint không tồn tại (404).'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'error': 'Lỗi máy chủ nội bộ (500).'}), 500


@app.errorhandler(ValidationError)
def invalid_input(error):
    return jsonify(success=False, error=str(error)), 400


@app.errorhandler(413)
def too_large(error):
    return jsonify(success=False, error='Tệp hoặc nội dung yêu cầu vượt quá giới hạn cho phép.'), 413


import sqlite3
from mysql.connector import IntegrityError as MySQLIntegrityError


@app.errorhandler(sqlite3.IntegrityError)
@app.errorhandler(MySQLIntegrityError)
def integrity_conflict(error):
    return jsonify(success=False, error='Dữ liệu bị trùng hoặc liên kết không còn hợp lệ. Vui lòng tải lại và kiểm tra.'), 409

if __name__ == '__main__':
    print("[+] Kết nối MySQL thành công!")
        
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Hệ thống Quản lý Dự án Nhóm Tích hợp AI đang chạy tại: http://127.0.0.1:{port}")
    from services.email_service import start_deadline_worker
    start_deadline_worker()
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=port,
            debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', use_reloader=False)
