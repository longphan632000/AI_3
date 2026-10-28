from database.connection import query_db
from services.task_service import is_task_overdue

def retrieve_ai_data(structured_request):
    """
    Module truy xuất dữ liệu an toàn cho AI (project-data-retrieval skill).
    Sử dụng 100% Parameterized SQL, giới hạn đúng phạm vi dự án và quyền truy cập.
    Không gửi mật khẩu, secret hoặc dữ liệu dự án khác ra ngoài.
    """
    task_type = structured_request['task_type']
    project_id = structured_request['project_id']
    
    source_references = {
        'tasks': [],
        'members': [],
        'meeting_notes': []
    }
    
    if task_type == 'weekly_summary':
        # Truy xuất danh sách nhiệm vụ trong khoảng tuần của dự án
        sprint_id = structured_request.get('sprint_id')
        conds = ["t.project_id = %s", "t.is_archived = FALSE",
                 "((DATE(t.created_at) BETWEEN %s AND %s) OR "
                 "(DATE(t.updated_at) BETWEEN %s AND %s) OR "
                 "(DATE(t.due_date) BETWEEN %s AND %s))"]
        params = [project_id, structured_request['week_start'], structured_request['week_end'],
                  structured_request['week_start'], structured_request['week_end'],
                  structured_request['week_start'], structured_request['week_end']]
        
        if sprint_id:
            conds.append("t.sprint_id = %s")
            params.append(sprint_id)
            
        where_clause = " AND ".join(conds)
        
        query = f"""
            SELECT t.id, t.title, t.status, t.priority, t.due_date, t.estimated_hours,
                   t.blockers, t.labels, u.full_name AS assignee_name, u.id AS assignee_id,
                   s.name AS sprint_name
            FROM tasks t
            LEFT JOIN users u ON t.assignee_id = u.id
            LEFT JOIN sprints s ON t.sprint_id = s.id
            WHERE {where_clause}
            ORDER BY t.priority DESC, t.due_date ASC;
        """
        tasks = query_db(query, tuple(params))
        
        retrieved_tasks = []
        for t in tasks:
            is_overdue = is_task_overdue(t['due_date'], t['status'], False)
            source_references['tasks'].append(t['id'])
            if t['assignee_id']:
                source_references['members'].append(t['assignee_id'])
                
            retrieved_tasks.append({
                'task_id': t['id'],
                'title': t['title'],
                'status': t['status'],
                'priority': t['priority'],
                'due_date': str(t['due_date']) if t['due_date'] else "Không có",
                'is_overdue': is_overdue,
                'assignee': t['assignee_name'] or "Chưa phân công",
                'assignee_id': t['assignee_id'],
                'sprint': t['sprint_name'] or "Không thuộc sprint",
                'blockers': t['blockers'] or "Không có",
                'estimated_hours': float(t['estimated_hours'] or 0)
            })
            
        return {
            'type': 'weekly_summary_data',
            'week_start': structured_request['week_start'],
            'week_end': structured_request['week_end'],
            'tasks': retrieved_tasks
        }, source_references
        
    elif task_type == 'meeting_minutes':
        note_id = structured_request.get('meeting_note_id')
        raw_notes = structured_request.get('raw_notes')
        
        note_info = None
        if note_id:
            note_info = query_db("""
                SELECT mn.id, mn.title, mn.meeting_date, mn.attendees, mn.content,
                       u.full_name AS creator_name
                FROM meeting_notes mn
                JOIN users u ON mn.created_by = u.id
                WHERE mn.id = %s AND mn.project_id = %s;
            """, (note_id, project_id), one=True)
            if note_info:
                source_references['meeting_notes'].append(note_info['id'])
                
        return {
            'type': 'meeting_minutes_data',
            'note': note_info,
            'raw_notes': raw_notes,
            'project_members': []
        }, source_references

    elif task_type == 'assignment_suggestion':
        if structured_request.get('staffing_v2'):
            from services.staffing_service import build_staffing_data
            data = build_staffing_data(structured_request)
            source_references['tasks'] = [data['task']['id']] if data.get('task') else []
            source_references['members'] = [c['user_id'] for c in data['candidates']]
            return data, source_references
        task_id = structured_request['task_id']
        task = query_db("""
            SELECT id, sprint_id, title, description, priority, due_date, estimated_hours, labels, blockers, status, assignee_id
            FROM tasks
            WHERE id = %s AND project_id = %s AND is_archived=FALSE;
        """, (task_id, project_id), one=True)
        
        if not task:
            return {'type': 'assignment_suggestion_data', 'task': None, 'candidates': []}, source_references
            
        source_references['tasks'].append(task['id'])
        
        from services.report_service import get_member_workload_statistics
        members = get_member_workload_statistics(project_id, task.get('sprint_id'))
        assigned = {row['user_id'] for row in query_db(
            'SELECT user_id FROM task_assignees WHERE task_id=%s', (task['id'],))}
        if task.get('assignee_id'):
            assigned.add(task['assignee_id'])
        candidates = []
        for member in members:
            if member['account_status'] != 'active' or member['project_role'] not in ('leader','member'):
                continue
            source_references['members'].append(member['user_id'])
            candidates.append({'user_id':member['user_id'], 'full_name':member['full_name'],
                'skills':member['skills'] or 'Chưa cập nhật', 'availability':member['availability'],
                'capacity_hours':member['effective_capacity_hours'],
                'current_workload_hours':member['current_workload_hours'],
                'already_assigned':member['user_id'] in assigned,
                'is_currently_overloaded':member['is_overloaded']})

        return {
            'type': 'assignment_suggestion_data',
            'task': task,
            'candidates': candidates
        }, source_references
        
    return {}, source_references
