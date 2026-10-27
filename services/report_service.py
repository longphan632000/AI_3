from datetime import datetime
from database.connection import query_db
from services.task_service import is_task_overdue

def get_project_dashboard_metrics(project_id, sprint_id=None):
    """
    Bảng điều khiển tiến độ dự án (FR-10, BR-04).
    """
    conditions = ["project_id = %s", "is_archived = FALSE"]
    params = [project_id]
    
    if sprint_id:
        conditions.append("sprint_id = %s")
        params.append(sprint_id)
        
    where_clause = " AND ".join(conditions)
    
    # 1. Thống kê theo 5 trạng thái
    query = f"""
        SELECT 
            COUNT(*) AS total_tasks,
            SUM(CASE WHEN status = 'backlog' THEN 1 ELSE 0 END) AS count_backlog,
            SUM(CASE WHEN status = 'todo' THEN 1 ELSE 0 END) AS count_todo,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS count_in_progress,
            SUM(CASE WHEN status = 'review' THEN 1 ELSE 0 END) AS count_review,
            SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS count_done
        FROM tasks
        WHERE {where_clause};
    """
    metrics = query_db(query, tuple(params), one=True) or {}
    metrics = {key: int(value or 0) for key, value in metrics.items()}
    total = metrics.get('total_tasks') or 0
    done = metrics.get('count_done') or 0
    
    # Tỷ lệ hoàn thành theo BR-04 (0% nếu không có task)
    completion_rate = round((done / total) * 100.0, 1) if total > 0 else 0.0
    
    # 2. Đếm số nhiệm vụ trễ hạn theo BR-02
    all_tasks = query_db(f"""
        SELECT due_date, status, is_archived
        FROM tasks
        WHERE {where_clause};
    """, tuple(params))
    
    overdue_count = sum(1 for t in all_tasks if is_task_overdue(t['due_date'], t['status'], t['is_archived']))
    
    return {
        'total_tasks': total,
        'count_backlog': metrics.get('count_backlog') or 0,
        'count_todo': metrics.get('count_todo') or 0,
        'count_in_progress': metrics.get('count_in_progress') or 0,
        'count_review': metrics.get('count_review') or 0,
        'count_done': done,
        'completion_rate': completion_rate,
        'overdue_count': overdue_count
    }

def get_member_workload_statistics(project_id, sprint_id=None):
    """FR-11/BR-05: the same scoped workload feeds reports and AI."""
    from services.validation import availability_percent, ValidationError
    members = query_db("""SELECT pm.user_id,u.full_name,u.email,u.status AS account_status,
        pm.project_role,pm.skills,pm.availability,pm.capacity_hours
        FROM project_members pm JOIN users u ON u.id=pm.user_id WHERE pm.project_id=%s""", (project_id,))
    clauses = ['project_id=%s','is_archived=FALSE']
    params = [project_id]
    if sprint_id:
        clauses.append('sprint_id=%s')
        params.append(sprint_id)
    tasks = query_db('SELECT id,assignee_id,title,status,due_date,estimated_hours,is_archived FROM tasks WHERE ' + ' AND '.join(clauses), tuple(params))
    links = query_db('SELECT ta.task_id,ta.user_id FROM task_assignees ta JOIN tasks t ON t.id=ta.task_id WHERE t.project_id=%s AND t.is_archived=FALSE', (project_id,))
    assignments = {}
    for link in links:
        assignments.setdefault(link['task_id'],set()).add(link['user_id'])
    per_user = {}
    for task in tasks:
        recipients = assignments.get(task['id'],set()).copy()
        if task['assignee_id']:
            recipients.add(task['assignee_id'])
        for uid in recipients:
            per_user.setdefault(uid,[]).append(task)
    report = []
    for member in members:
        cap = float(member['capacity_hours']) if member['capacity_hours'] is not None else 40.0
        try:
            percent = availability_percent(member['availability'])
            config_warning = None
        except ValidationError:
            percent = 100.0
            config_warning = 'Mức sẵn sàng cũ chưa rõ tỷ lệ; hãy cập nhật.'
        effective = round(cap * percent / 100, 2)
        active = [task for task in per_user.get(member['user_id'],[]) if task['status'] != 'done']
        workload = sum(float(task['estimated_hours'] or 0) for task in active)
        report.append({**member, 'capacity_hours':cap, 'availability_percent':percent,
            'effective_capacity_hours':effective, 'configuration_warning':config_warning,
            'current_workload_hours':round(workload,2), 'active_task_count':len(active),
            'overdue_task_count':sum(is_task_overdue(task['due_date'],task['status'],False) for task in active),
            'missing_estimate_count':sum(float(task['estimated_hours'] or 0)<=0 for task in active),
            'is_overloaded':workload > effective})
    return report
