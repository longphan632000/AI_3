"""Reusable professional profiles and aggregate staffing facts, without task text."""
from datetime import datetime
from database.connection import query_db, execute_db, atomic
from services.validation import text, number, availability_percent, ValidationError
from services.audit_service import log_audit


def public_profile_defaults(user_id):
    row = query_db('SELECT skills,availability,capacity_hours FROM member_profiles WHERE user_id=%s', (user_id,), one=True)
    if not row:
        row = query_db('''SELECT skills,availability,capacity_hours FROM project_members WHERE user_id=%s
            AND project_role<>'viewer' ORDER BY CASE WHEN COALESCE(skills,'')<>'' THEN 0 ELSE 1 END,id DESC LIMIT 1''', (user_id,),one=True)
    if not row:
        return {'skills':'', 'availability':'100%', 'capacity_hours':40}
    try:
        percent = availability_percent(row['availability'])
    except ValidationError:
        percent = 100
    return {'skills':row['skills'] or '', 'availability':f'{percent:g}%',
            'capacity_hours':float(row['capacity_hours'] if row['capacity_hours'] is not None else 40)}


def list_professional_profiles(user_id=None):
    where, params = (' AND u.id=%s', (user_id,)) if user_id else ('', ())
    rows = query_db('''SELECT u.id AS user_id,u.full_name,u.username,u.user_code,u.role AS system_role,
        mp.user_id AS profile_id,mp.skills AS global_skills,mp.availability AS global_availability,
        mp.capacity_hours AS global_capacity,mp.updated_at,
        pm.skills AS previous_skills,pm.availability AS previous_availability,pm.capacity_hours AS previous_capacity
        FROM users u LEFT JOIN member_profiles mp ON mp.user_id=u.id
        LEFT JOIN project_members pm ON pm.id=(SELECT pm2.id FROM project_members pm2
            WHERE pm2.user_id=u.id AND pm2.project_role<>'viewer'
            ORDER BY CASE WHEN COALESCE(pm2.skills,'')<>'' THEN 0 ELSE 1 END,pm2.id DESC LIMIT 1)
        WHERE u.status='active' AND u.role IN ('member','leader')''' + where + ' ORDER BY u.id', params) or []
    if not rows:
        return []
    ids = [r['user_id'] for r in rows]
    placeholders = ','.join(['%s']*len(ids))
    tasks = query_db('''SELECT a.user_id,t.id,t.due_date,t.status,t.estimated_hours,t.is_archived
        FROM tasks t JOIN projects p ON p.id=t.project_id JOIN (
            SELECT task_id,user_id FROM task_assignees UNION
            SELECT id AS task_id,assignee_id AS user_id FROM tasks WHERE assignee_id IS NOT NULL
        ) a ON a.task_id=t.id WHERE p.is_archived=FALSE AND t.is_archived=FALSE AND t.status<>'done'
        AND a.user_id IN (''' + placeholders + ')', tuple(ids)) or []
    from services.task_service import is_task_overdue
    metrics = {uid:{'current_workload_hours':0.0,'active_task_count':0,'overdue_task_count':0,'missing_estimate_count':0} for uid in ids}
    for task in tasks:
        m = metrics[task['user_id']]
        hours = float(task['estimated_hours'] or 0)
        m['current_workload_hours'] += hours
        m['active_task_count'] += 1
        m['overdue_task_count'] += bool(is_task_overdue(task['due_date'],task['status'],False))
        m['missing_estimate_count'] += hours <= 0
    result = []
    for r in rows:
        declared = r['profile_id'] is not None
        skills = r['global_skills'] if declared else r['previous_skills']
        availability = r['global_availability'] if declared else r['previous_availability']
        capacity = r['global_capacity'] if declared else r['previous_capacity']
        warnings = []
        if not declared:
            warnings.append('Chưa cập nhật hồ sơ chung; dùng thông tin năng lực đã khai báo hoặc giá trị mặc định.')
        try:
            percent = availability_percent(availability)
        except ValidationError:
            percent = 100
            warnings.append('Mức sẵn sàng cũ cần được xác minh.')
        cap = float(capacity if capacity is not None else 40)
        effective = round(cap*percent/100,2)
        metric = metrics[r['user_id']]
        metric['current_workload_hours'] = round(metric['current_workload_hours'],2)
        result.append({key:r[key] for key in ('user_id','full_name','username','user_code','system_role','updated_at')} | {
            'skills':skills or '', 'availability':f'{percent:g}%', 'availability_percent':percent,
            'nominal_capacity_hours':cap, 'capacity_hours':effective, 'effective_capacity_hours':effective,
            'profile_declared':declared, 'profile_warnings':warnings,
            'is_currently_overloaded':metric['current_workload_hours']>effective, **metric})
    return result


@atomic
def update_professional_profile(user_id, skills, availability, capacity_hours):
    user = query_db('SELECT role,status FROM users WHERE id=%s', (user_id,), one=True)
    if not user or user['status']!='active' or user['role'] not in ('member','leader'):
        raise ValidationError('Tài khoản không có hồ sơ phân công hợp lệ.')
    skills = text(skills,'Kỹ năng hồ sơ chung',60000)
    availability = f'{availability_percent(availability):g}%'
    capacity = number(capacity_hours,'Năng lực')
    if query_db('SELECT user_id FROM member_profiles WHERE user_id=%s',(user_id,),one=True):
        execute_db('UPDATE member_profiles SET skills=%s,availability=%s,capacity_hours=%s,updated_at=%s WHERE user_id=%s',
                   (skills,availability,capacity,datetime.now(),user_id))
    else:
        execute_db('INSERT INTO member_profiles(user_id,skills,availability,capacity_hours) VALUES (%s,%s,%s,%s)',
                   (user_id,skills,availability,capacity))
    log_audit(user_id,'UPDATE_MEMBER_PROFILE','USER',user_id,{'availability':availability,'capacity_hours':capacity})
    return list_professional_profiles(user_id)[0]
