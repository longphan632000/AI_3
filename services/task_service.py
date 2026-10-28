from datetime import datetime
from database.connection import query_db, execute_db, atomic, after_commit
from services.audit_service import log_audit

from services.validation import text, number, integer, choice, iso_date, local_datetime, ValidationError
from services.access_service import require_active_project, require_active_task

KANBAN_STATUSES = ['backlog', 'todo', 'in_progress', 'review', 'done']

def validate_task_links(project_id, sprint_id=None, assignee_id=None):
    """Keep task references inside its project."""
    require_active_project(project_id)
    if sprint_id:
        sprint = query_db(
            "SELECT id FROM sprints WHERE id = %s AND project_id = %s AND is_archived = FALSE;",
            (sprint_id, project_id), one=True
        )
        if not sprint:
            return False, "Sprint không thuộc dự án này."
    if assignee_id:
        assignee = query_db(
            "SELECT pm.user_id FROM project_members pm JOIN users u ON u.id = pm.user_id "
            "WHERE pm.user_id = %s AND pm.project_id = %s AND u.status = 'active' AND pm.project_role IN ('leader','member');",
            (assignee_id, project_id), one=True
        )
        if not assignee:
            return False, "Người phụ trách không thuộc dự án hoặc tài khoản chưa hoạt động."
    return True, ""

def is_task_overdue(due_date, status, is_archived):
    """
    Quy tắc nghiệp vụ BR-02:
    Nhiệm vụ trễ khi đã quá hạn, chưa Hoàn thành và chưa bị lưu trữ.
    """
    if not due_date or is_archived or status == 'done':
        return False
    
    try:
        return local_datetime(due_date) < datetime.now()
    except ValidationError:
        return False


def validate_supporters(project_id, values):
    if values is None:
        return None
    if not isinstance(values, (list, tuple)) or len(values) > 200:
        raise ValidationError('Danh sách người hỗ trợ không hợp lệ.')
    result = list(dict.fromkeys(integer(v, 'Người hỗ trợ', minimum=1) for v in values))
    for uid in result:
        valid, error = validate_task_links(project_id, assignee_id=uid)
        if not valid:
            raise ValidationError(error)
    return result


def task_fields(title, description, sprint_id, assignee_id, priority, due_date, estimated_hours, labels, blockers):
    return (text(title, 'Tiêu đề', 200, required=True), text(description, 'Mô tả', 60000),
            integer(sprint_id, 'Sprint', minimum=1, optional=True),
            integer(assignee_id, 'Người phụ trách', minimum=1, optional=True),
            choice(priority, ('low','medium','high','urgent'), 'Ưu tiên'),
            local_datetime(due_date), number(0 if estimated_hours is None or estimated_hours == '' else estimated_hours, 'Ước lượng'),
            text(labels, 'Nhãn', 255), text(blockers, 'Vướng mắc', 60000))


def queue_overdue(project_id, task_id):
    from services.email_service import check_and_send_overdue_email_alerts
    after_commit(lambda: check_and_send_overdue_email_alerts(project_id=project_id, task_id=task_id))


def sync_task_assignees(task_id, primary_assignee_id=None, support_member_ids=None):
    """
    Đồng bộ bảng task_assignees:
    - primary_assignee_id: người phụ trách chính (is_primary=True)
    - support_member_ids: danh sách thành viên cùng hỗ trợ (is_primary=False)
    """
    all_assigned_uids = []
    if primary_assignee_id:
        try:
            all_assigned_uids.append(int(primary_assignee_id))
        except (ValueError, TypeError):
            pass

    valid_supporters = []
    if support_member_ids and isinstance(support_member_ids, (list, tuple, set)):
        for sid in support_member_ids:
            try:
                sid_int = int(sid)
                if sid_int not in all_assigned_uids:
                    all_assigned_uids.append(sid_int)
                    valid_supporters.append(sid_int)
            except (ValueError, TypeError):
                continue

    if not all_assigned_uids:
        execute_db("DELETE FROM task_assignees WHERE task_id = %s;", (task_id,))
        return

    placeholders = ', '.join(['%s'] * len(all_assigned_uids))
    execute_db(f"DELETE FROM task_assignees WHERE task_id = %s AND user_id NOT IN ({placeholders});",
               tuple([task_id] + all_assigned_uids))

    if primary_assignee_id:
        p_uid = int(primary_assignee_id)
        existing = query_db("SELECT id, is_primary FROM task_assignees WHERE task_id = %s AND user_id = %s;", (task_id, p_uid), one=True)
        if existing:
            if not existing['is_primary']:
                execute_db("UPDATE task_assignees SET is_primary = TRUE WHERE id = %s;", (existing['id'],))
        else:
            execute_db("INSERT INTO task_assignees (task_id, user_id, is_primary) VALUES (%s, %s, TRUE);", (task_id, p_uid))

    for sid_int in valid_supporters:
        existing = query_db("SELECT id, is_primary FROM task_assignees WHERE task_id = %s AND user_id = %s;", (task_id, sid_int), one=True)
        if existing:
            if existing['is_primary']:
                execute_db("UPDATE task_assignees SET is_primary = FALSE WHERE id = %s;", (existing['id'],))
        else:
            execute_db("INSERT INTO task_assignees (task_id, user_id, is_primary) VALUES (%s, %s, FALSE);", (task_id, sid_int))


def get_tasks_by_project(project_id, sprint_id=None, assignee_id=None, status=None, 
                         is_overdue_only=False, keyword=None, limit=100, offset=0, priority=None, due_from=None, due_to=None, sort_by='priority', sort_order='desc', archived=False):
    """
    Tìm kiếm, lọc, phân trang nhiệm vụ theo FR-09 & BR-02 (kèm người hỗ trợ).
    """
    conditions = ["t.project_id = %s", "t.is_archived = TRUE" if archived else "t.is_archived = FALSE"]
    params = [project_id]
    
    if sprint_id:
        conditions.append("t.sprint_id = %s")
        params.append(sprint_id)
        
    if assignee_id:
        conditions.append("(t.assignee_id = %s OR t.id IN (SELECT task_id FROM task_assignees WHERE user_id = %s))")
        params.extend([assignee_id, assignee_id])
        
    if status and status in KANBAN_STATUSES:
        conditions.append("t.status = %s")
        params.append(status)
        
    if keyword and keyword.strip():
        conditions.append("(t.title LIKE %s OR t.description LIKE %s OR t.labels LIKE %s)")
        kw = f"%{keyword.strip()}%"
        params.extend([kw, kw, kw])
        
    limit = integer(limit, 'Số lượng', minimum=1, maximum=500)
    offset = integer(offset, 'Vị trí', minimum=0)
    if priority:
        conditions.append('t.priority = %s')
        params.append(choice(priority, ('low','medium','high','urgent'), 'Ưu tiên'))
    if due_from:
        conditions.append('DATE(t.due_date) >= %s')
        params.append(iso_date(due_from, 'Từ ngày', required=True))
    if due_to:
        conditions.append('DATE(t.due_date) <= %s')
        params.append(iso_date(due_to, 'Đến ngày', required=True))
    if due_from and due_to and due_from > due_to:
        raise ValidationError('Khoảng hạn hoàn thành không hợp lệ.')
    if is_overdue_only:
        conditions.extend(["t.status != 'done'", 't.due_date < %s'])
        params.append(datetime.now())
    columns = {'title': 't.title', 'due_date': 't.due_date', 'created_at': 't.created_at',
               'status': 't.status', 'priority': "CASE t.priority WHEN 'urgent' THEN 4 WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END"}
    if sort_by not in columns or sort_order.lower() not in ('asc','desc'):
        raise ValidationError('Cách sắp xếp không hợp lệ.')
    order_clause = columns[sort_by] + ' ' + sort_order.upper() + ', t.id DESC'
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT t.id, t.task_code, t.project_id, t.sprint_id, s.name AS sprint_name,
               t.title, t.description, t.assignee_id, u_ass.full_name AS assignee_name,
               t.reporter_id, u_rep.full_name AS reporter_name,
               t.status, t.priority, t.due_date, t.estimated_hours, t.labels, t.blockers,
               t.progress_percent,
               t.is_archived, t.created_at, t.updated_at
        FROM tasks t
        LEFT JOIN sprints s ON t.sprint_id = s.id
        LEFT JOIN users u_ass ON t.assignee_id = u_ass.id
        LEFT JOIN users u_rep ON t.reporter_id = u_rep.id
        WHERE {where_clause}
        ORDER BY {order_clause}
        LIMIT %s OFFSET %s;
    """
    params.extend([limit, offset])
    tasks = query_db(query, tuple(params))
    
    # Gắn cờ is_overdue theo BR-02
    results = []
    for t in tasks:
        t['is_overdue'] = is_task_overdue(t['due_date'], t['status'], t['is_archived'])
        results.append(t)
        
    if results:
        task_ids = [t['id'] for t in results]
        placeholders = ', '.join(['%s'] * len(task_ids))
        assignee_rows = query_db(f"""
            SELECT ta.task_id, ta.user_id, ta.is_primary, u.full_name, u.username, u.email
            FROM task_assignees ta
            JOIN users u ON ta.user_id = u.id
            WHERE ta.task_id IN ({placeholders})
            ORDER BY ta.is_primary DESC, u.full_name ASC;
        """, tuple(task_ids)) or []
        
        assignee_map = {}
        for row in assignee_rows:
            assignee_map.setdefault(row['task_id'], []).append({
                'user_id': row['user_id'],
                'full_name': row['full_name'],
                'username': row['username'],
                'email': row['email'],
                'is_primary': bool(row['is_primary'])
            })
            
        for t in results:
            t_assignees = assignee_map.get(t['id'], [])
            t['all_assignees'] = t_assignees
            t['supporters'] = [a for a in t_assignees if not a['is_primary']]
            t['support_count'] = len(t['supporters'])
            t['support_member_ids'] = [s['user_id'] for s in t['supporters']]

    return results

def get_task_by_id(task_id):
    query = """
        SELECT t.id, t.task_code, t.project_id, t.sprint_id, s.name AS sprint_name,
               t.title, t.description, t.assignee_id, u_ass.full_name AS assignee_name,
               u_ass.email AS assignee_email,
               t.reporter_id, u_rep.full_name AS reporter_name,
               t.status, t.priority, t.due_date, t.estimated_hours, t.labels, t.blockers,
               t.progress_percent,
               t.is_archived, t.created_at, t.updated_at
        FROM tasks t
        LEFT JOIN sprints s ON t.sprint_id = s.id
        LEFT JOIN users u_ass ON t.assignee_id = u_ass.id
        LEFT JOIN users u_rep ON t.reporter_id = u_rep.id
        WHERE t.id = %s;
    """
    task = query_db(query, (task_id,), one=True)
    if task:
        task['is_overdue'] = is_task_overdue(task['due_date'], task['status'], task['is_archived'])
        assignee_rows = query_db("""
            SELECT ta.user_id, ta.is_primary, ta.assigned_at, u.full_name, u.username, u.email
            FROM task_assignees ta
            JOIN users u ON ta.user_id = u.id
            WHERE ta.task_id = %s
            ORDER BY ta.is_primary DESC, u.full_name ASC;
        """, (task_id,)) or []
        task['all_assignees'] = assignee_rows
        task['supporters'] = [r for r in assignee_rows if not r['is_primary']]
        task['support_count'] = len(task['supporters'])
        task['support_member_ids'] = [s['user_id'] for s in task['supporters']]
    return task

@atomic
def create_task(user_id, project_id, title, description='', sprint_id=None, assignee_id=None,
                priority='medium', due_date=None, estimated_hours=0.0, labels=None, blockers=None,
                support_member_ids=None, task_code=None):
    """Tạo nhiệm vụ mới (FR-05) với hỗ trợ phân công nhiều thành viên."""
    if not title or not title.strip():
        return False, "Tiêu đề nhiệm vụ không được để trống.", None
    title, description, sprint_id, assignee_id, priority, due_date, estimated_hours, labels, blockers = task_fields(
        title, description, sprint_id, assignee_id, priority, due_date, estimated_hours, labels, blockers)
    support_member_ids = validate_supporters(project_id, support_member_ids)
    task_code = text(task_code, 'Mã nhiệm vụ', 50).upper()
    if task_code and query_db('SELECT id FROM tasks WHERE project_id=%s AND UPPER(task_code)=%s', (project_id, task_code), one=True):
        raise ValidationError('Mã nhiệm vụ đã tồn tại trong dự án.')
    valid, error = validate_task_links(project_id, sprint_id, assignee_id)
    if not valid:
        return False, error, None
        
    query = """
        INSERT INTO tasks (project_id, sprint_id, title, description, assignee_id, reporter_id,
                           status, priority, due_date, estimated_hours, labels, blockers, is_archived)
        VALUES (%s, %s, %s, %s, %s, %s, 'backlog', %s, %s, %s, %s, %s, FALSE);
    """
    task_id = execute_db(query, (
        project_id, sprint_id or None, title.strip(), description, assignee_id or None, user_id,
        priority, due_date or None, float(estimated_hours or 0), labels, blockers
    ))

    # Tự động gán mã nhiệm vụ Jira-style (ví dụ: QLNT-33) hoặc mã tùy chọn
    if task_code and task_code.strip():
        clean_code = task_code.strip().upper()
    else:
        prj = query_db("SELECT project_code FROM projects WHERE id = %s;", (project_id,), one=True)
        p_code = (prj['project_code'] if prj and prj.get('project_code') else f"PRJ-{project_id}").strip().upper()
        clean_code = f"{p_code}-{task_id}"
    execute_db("UPDATE tasks SET task_code = %s WHERE id = %s;", (clean_code, task_id))
    
    # Đồng bộ người phụ trách chính và các thành viên hỗ trợ
    sync_task_assignees(task_id, assignee_id, support_member_ids)
    
    log_audit(user_id, 'CREATE_TASK', 'TASK', task_id, {"title": title, "task_code": clean_code, "project_id": project_id})
    
    # Gửi thông báo nếu có gán người phụ trách chính ngay khi tạo (FR-16)
    from services.notification_service import create_notification
    if assignee_id:
        create_notification(
            user_id=assignee_id,
            project_id=project_id,
            task_id=task_id,
            event_type='task_assigned',
            title='Nhiệm vụ mới được giao',
            message=f'Bạn được phân công phụ trách chính nhiệm vụ: "{title}".'
        )
        
    # Gửi thông báo cho các thành viên hỗ trợ (FR-16)
    if support_member_ids:
        for sid in support_member_ids:
            try:
                sid_int = int(sid)
                if sid_int != assignee_id:
                    create_notification(
                        user_id=sid_int,
                        project_id=project_id,
                        task_id=task_id,
                        event_type='task_assigned',
                        title='Phân công hỗ trợ nhiệm vụ',
                        message=f'Bạn được phân công tham gia hỗ trợ nhiệm vụ: "{title}".'
                    )
            except (ValueError, TypeError):
                continue
        
    queue_overdue(project_id, task_id)
    return True, "Tạo nhiệm vụ thành công.", task_id


@atomic
def update_task_status(user_id, task_id, new_status):
    """
    Chuyển trạng thái Kanban (FR-06, BR-01).
    Hệ thống kiểm tra trạng thái hợp lệ và từ chối nếu không đúng quy tắc.
    """
    if new_status not in KANBAN_STATUSES:
        return False, f"Trạng thái không hợp lệ. Phải thuộc: {', '.join(KANBAN_STATUSES)}"
        
    old_task = get_task_by_id(task_id)
    if not old_task:
        return False, "Nhiệm vụ không tồn tại."
        
    require_active_task(old_task)
    old_status = old_task['status']
    if old_status == new_status:
        return True, "Trạng thái không đổi."
        
    if new_status == 'done':
        execute_db("UPDATE tasks SET status = %s, progress_percent = 100 WHERE id = %s;", (new_status, task_id))
    elif old_status == 'done' and new_status != 'done':
        execute_db("UPDATE tasks SET status = %s, progress_percent = CASE WHEN progress_percent = 100 THEN 0 ELSE progress_percent END WHERE id = %s;", (new_status, task_id))
    else:
        execute_db("UPDATE tasks SET status = %s WHERE id = %s;", (new_status, task_id))

    log_audit(user_id, 'UPDATE_TASK_STATUS', 'TASK', task_id, 
              {"old_status": old_status, "new_status": new_status})
              
    # Thông báo FR-16 khi đổi trạng thái cho người phụ trách và người tạo
    from services.notification_service import create_notification
    recipients = set(filter(None, [old_task['assignee_id'], old_task['reporter_id']]))
    recipients.discard(user_id) # Không gửi cho chính người thực hiện
    for recipient_id in recipients:
        create_notification(
            user_id=recipient_id,
            project_id=old_task['project_id'],
            task_id=task_id,
            event_type='status_changed',
            title='Trạng thái nhiệm vụ đã thay đổi',
            message=f'Nhiệm vụ "{old_task["title"]}" được chuyển từ [{old_status}] sang [{new_status}].'
        )
        
    queue_overdue(old_task['project_id'], task_id)
    return True, f"Cập nhật trạng thái sang {new_status} thành công."

@atomic
def update_task_progress(user_id, task_id, progress_percent):
    """
    Cập nhật % tiến độ thực tế (0% - 100%) của nhiệm vụ bởi Assignee, Supporter, Leader hoặc Admin.
    """
    progress_val = integer(progress_percent, 'Tiến độ', maximum=100)

    task = get_task_by_id(task_id)
    if not task:
        return False, "Nhiệm vụ không tồn tại."
        
    require_active_task(task)
    new_status = task['status']
    if progress_val == 100 and task['status'] != 'done':
        new_status = 'done'
    elif progress_val > 0 and task['status'] in ['todo', 'backlog']:
        new_status = 'in_progress'
    elif progress_val < 100 and task['status'] == 'done':
        new_status = 'in_progress'

    execute_db(
        "UPDATE tasks SET progress_percent = %s, status = %s WHERE id = %s;",
        (progress_val, new_status, task_id)
    )
    
    log_audit(user_id, 'UPDATE_TASK_PROGRESS', 'TASK', task_id, {
        "old_progress": task.get('progress_percent', 0),
        "new_progress": progress_val,
        "new_status": new_status
    })
    
    queue_overdue(task['project_id'], task_id)
    return True, f"Đã cập nhật tiến độ nhiệm vụ thành {progress_val}%."

@atomic
def update_task_details(user_id, task_id, title, description, sprint_id, assignee_id,
                        priority, due_date, estimated_hours, labels, blockers,
                        support_member_ids=None, task_code=None, progress_percent=None):
    """Cập nhật chi tiết nhiệm vụ, bổ sung thành viên hỗ trợ và kích hoạt thông báo FR-16."""
    old_task = get_task_by_id(task_id)
    if not old_task:
        return False, "Nhiệm vụ không tồn tại."
    if not title or not title.strip():
        return False, "Tiêu đề nhiệm vụ không được để trống."
    require_active_task(old_task)
    title, description, sprint_id, assignee_id, priority, due_date, estimated_hours, labels, blockers = task_fields(
        title, description, sprint_id, assignee_id, priority, due_date, estimated_hours, labels, blockers)
    if support_member_ids is not None:
        support_member_ids = validate_supporters(old_task['project_id'], support_member_ids)
    if progress_percent is not None:
        progress_percent = integer(progress_percent, 'Tiến độ', maximum=100)
    task_code = text(task_code, 'Mã nhiệm vụ', 50).upper()
    if task_code and query_db('SELECT id FROM tasks WHERE project_id=%s AND UPPER(task_code)=%s AND id<>%s', (old_task['project_id'], task_code, task_id), one=True):
        raise ValidationError('Mã nhiệm vụ đã tồn tại trong dự án.')
    valid, error = validate_task_links(old_task['project_id'], sprint_id, assignee_id)
    if not valid:
        return False, error
        
    query = """
        UPDATE tasks 
        SET title = %s, description = %s, sprint_id = %s, assignee_id = %s,
            priority = %s, due_date = %s, estimated_hours = %s, labels = %s, blockers = %s
        WHERE id = %s;
    """
    execute_db(query, (
        title, description, sprint_id or None, assignee_id or None,
        priority, due_date or None, float(estimated_hours or 0), labels, blockers, task_id
    ))
    if task_code and task_code.strip():
        execute_db("UPDATE tasks SET task_code = %s WHERE id = %s;", (task_code.strip().upper(), task_id))
    
    if progress_percent is not None:
        update_task_progress(user_id, task_id, progress_percent)

    # Cập nhật các thành viên cùng hỗ trợ nếu có truyền vào
    if support_member_ids is not None:
        old_supporters = set(old_task.get('support_member_ids') or [])
        new_supporters = []
        for sid in support_member_ids:
            try:
                sid_int = int(sid)
                if sid_int not in old_supporters and sid_int != assignee_id:
                    new_supporters.append(sid_int)
            except (ValueError, TypeError):
                continue
                
        sync_task_assignees(task_id, assignee_id, support_member_ids)
        
        # Gửi thông báo cho thành viên vừa được bổ sung vào hỗ trợ (đặc biệt khi trễ hạn)
        if new_supporters:
            from services.notification_service import create_notification
            is_overdue = old_task.get('is_overdue')
            noti_title = 'Điều phối hỗ trợ nhiệm vụ trễ hạn (BR-02)' if is_overdue else 'Bổ sung hỗ trợ nhiệm vụ'
            noti_msg = (
                f'Trưởng nhóm vừa phân công bạn vào hỗ trợ xử lý nhiệm vụ đang trễ hạn: "{title}".'
                if is_overdue else f'Bạn vừa được phân công tham gia hỗ trợ nhiệm vụ: "{title}".'
            )
            for sid_int in new_supporters:
                create_notification(
                    user_id=sid_int,
                    project_id=old_task['project_id'],
                    task_id=task_id,
                    event_type='task_assigned',
                    title=noti_title,
                    message=noti_msg
                )
    elif assignee_id != old_task.get('assignee_id'):
        # Nếu chỉ đổi assignee_id mà không truyền support_member_ids thì cập nhật lại primary trong task_assignees
        sync_task_assignees(task_id, assignee_id, old_task.get('support_member_ids'))

    log_audit(user_id, 'UPDATE_TASK', 'TASK', task_id, {"title": title})
    
    from services.notification_service import create_notification
    # Kiểm tra đổi người phụ trách chính
    if assignee_id and assignee_id != old_task['assignee_id']:
        create_notification(
            user_id=assignee_id,
            project_id=old_task['project_id'],
            task_id=task_id,
            event_type='assignee_changed',
            title='Bạn được phân công nhiệm vụ mới',
            message=f'Bạn được chỉ định làm người phụ trách chính của: "{title}".'
        )
        
    # Kiểm tra đổi hạn
    if str(due_date or '') != str(old_task['due_date'] or ''):
        recipients_due = set(filter(None, [assignee_id, old_task.get('assignee_id')]))
        for sid in (old_task.get('support_member_ids') or []):
            recipients_due.add(sid)
        recipients_due.discard(user_id)
        for rid in recipients_due:
            create_notification(
                user_id=rid,
                project_id=old_task['project_id'],
                task_id=task_id,
                event_type='deadline_changed',
                title='Thời hạn nhiệm vụ đã cập nhật',
                message=f'Thời hạn của nhiệm vụ "{title}" đã đổi sang {due_date}.'
            )
            
    queue_overdue(old_task['project_id'], task_id)
    return True, "Cập nhật nhiệm vụ thành công."


@atomic
def archive_task(user_id, task_id):
    """Xóa mềm / lưu trữ nhiệm vụ theo BR-08."""
    require_active_task(get_task_by_id(task_id))
    execute_db("UPDATE tasks SET is_archived = TRUE WHERE id = %s;", (task_id,))
    log_audit(user_id, 'ARCHIVE_TASK', 'TASK', task_id)
    return True, "Nhiệm vụ đã được lưu trữ (xóa mềm)."
