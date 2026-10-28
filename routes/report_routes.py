from flask import Blueprint, render_template, request, session, jsonify
from routes import login_required
from services.report_service import get_project_dashboard_metrics, get_member_workload_statistics
from services.project_member_service import check_user_project_role
from database.connection import query_db, transaction
from services.validation import integer

report_bp = Blueprint('report_bp', __name__)


@report_bp.get('/api/projects/<int:project_id>/report')
@login_required
def project_report_api(project_id):
    access, _ = check_user_project_role(session['user_id'], project_id, session['role'])
    if not access:
        return jsonify(success=False, error='Từ chối quyền truy cập dự án.'), 403
    sprint_id = integer(request.args.get('sprint_id'), 'Sprint', minimum=1, optional=True)
    with transaction():
        if sprint_id and not query_db('SELECT id FROM sprints WHERE id=%s AND project_id=%s', (sprint_id, project_id), one=True):
            return jsonify(success=False, error='Sprint không thuộc dự án này.'), 404
        metrics = get_project_dashboard_metrics(project_id, sprint_id)
        workload = get_member_workload_statistics(project_id, sprint_id)
    return jsonify(success=True, metrics=metrics, workload=workload, sprint_id=sprint_id)

@report_bp.route('/reports')
def reports_page():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('reports.html', user=session)

@report_bp.route('/api/projects/<int:project_id>/dashboard-metrics', methods=['GET'])
@login_required
def get_metrics_api(project_id):
    has_access, _ = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
        
    sprint_id = request.args.get('sprint_id', type=int)
    metrics = get_project_dashboard_metrics(project_id, sprint_id)
    return jsonify({'success': True, 'metrics': metrics}), 200

@report_bp.route('/api/projects/<int:project_id>/workload-stats', methods=['GET'])
@login_required
def get_workload_api(project_id):
    has_access, _ = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
        
    sprint_id = request.args.get('sprint_id', type=int)
    workload = get_member_workload_statistics(project_id, sprint_id)
    return jsonify({'success': True, 'workload': workload}), 200
