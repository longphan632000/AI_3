from datetime import datetime, timedelta
from database.connection import query_db, execute_db
from services.task_service import is_task_overdue

def create_notification(user_id, project_id, task_id, event_type, title, message):
    """
    Tạo thông báo trong ứng dụng (FR-16 / UC013).
    Sự kiện: task_assigned, assignee_changed, deadline_changed, status_changed, task_overdue, due_soon_reminder.
    """
    query = """
        INSERT INTO notifications (user_id, project_id, task_id, event_type, title, message, is_read)
        VALUES (%s, %s, %s, %s, %s, %s, FALSE);
    """
    return execute_db(query, (user_id, project_id, task_id, event_type, title, message))

def scan_and_create_deadline_notifications(target_user_id=None, target_project_id=None):
    """
    Tự động quét và phát thông báo "Nhiệm vụ trễ hạn" (BR-02) và "Nhiệm vụ sắp trễ hạn" (FR-16).
    - Trễ hạn: due_date < now(), chưa Done, chưa lưu trữ.
    - Sắp trễ hạn: now() <= due_date <= now() + 24 giờ, chưa Done, chưa lưu trữ.
    Gửi thông báo tới cả Người phụ trách chính và Thành viên cùng hỗ trợ (task_assignees).
    Chống trùng lặp: Không tạo lại thông báo cùng loại trong vòng 24 giờ.
    """
    conds = ["p.is_archived = FALSE", "t.is_archived = FALSE", "t.status != 'done'", "t.due_date IS NOT NULL"]
    params = []
    
    if target_project_id:
        conds.append("t.project_id = %s")
        params.append(target_project_id)
        
    where_clause = " AND ".join(conds)
    
    query = f"""
        SELECT t.id, t.title, t.due_date, t.status, t.is_archived, t.project_id, t.assignee_id,
               p.name AS project_name
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE {where_clause};
    """
    tasks = query_db(query, tuple(params)) or []
    
    now = datetime.now()
    due_soon_window = now + timedelta(hours=24)
    cutoff_time = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    
    new_notifs_count = 0
    
    for t in tasks:
        due_str = t['due_date']
        if not due_str:
            continue
            
        due_dt = None
        if isinstance(due_str, datetime):
            due_dt = due_str
        elif isinstance(due_str, str):
            try:
                due_dt = datetime.fromisoformat(due_str.replace('Z', '+00:00'))
            except Exception:
                try:
                    due_dt = datetime.strptime(due_str, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    continue
        if due_dt and due_dt.tzinfo is not None:
            due_dt = due_dt.replace(tzinfo=None)
            
        is_overdue = is_task_overdue(due_str, t['status'], t['is_archived'])
        is_due_soon = False
        if not is_overdue and due_dt and now <= due_dt <= due_soon_window:
            is_due_soon = True
            
        if not is_overdue and not is_due_soon:
            continue
            
        # Thu thập danh sách người nhận (Người phụ trách chính + Thành viên cùng hỗ trợ)
        recipients = set()
        if t['assignee_id']:
            recipients.add(int(t['assignee_id']))
            
        supporter_rows = query_db("SELECT user_id FROM task_assignees WHERE task_id = %s;", (t['id'],)) or []
        for sr in supporter_rows:
            recipients.add(int(sr['user_id']))
            
        if target_user_id:
            recipients = {uid for uid in recipients if uid == int(target_user_id)}
            
        event_type = 'task_overdue' if is_overdue else 'due_soon_reminder'
        title = f"⚠️ Cảnh báo trễ hạn: {t['title']}" if is_overdue else f"⏰ Sắp đến hạn hoàn thành: {t['title']}"
        message = (
            f"Nhiệm vụ '{t['title']}' trong dự án '{t['project_name']}' đã quá hạn chót ({due_str}). Vui lòng cập nhật ngay (BR-02)."
            if is_overdue else
            f"Nhiệm vụ '{t['title']}' trong dự án '{t['project_name']}' sắp đến thời hạn chót ({due_str}). Hãy kiểm tra và đẩy nhanh tiến độ!"
        )
        
        for uid in recipients:
            # Kiểm tra xem đã có thông báo cùng loại trong 24 giờ qua chưa
            existing = query_db("""
                SELECT id FROM notifications
                WHERE user_id = %s AND task_id = %s AND event_type = %s AND created_at >= %s
                LIMIT 1;
            """, (uid, t['id'], event_type, cutoff_time), one=True)
            
            if not existing:
                create_notification(uid, t['project_id'], t['id'], event_type, title, message)
                new_notifs_count += 1
                
    return new_notifs_count

def get_user_notifications(user_id, unread_only=False, limit=30):
    query = """
        SELECT n.id, n.user_id, n.project_id, p.name AS project_name,
               n.task_id, t.title AS task_title,
               n.event_type, n.title, n.message, n.is_read, n.created_at
        FROM notifications n
        LEFT JOIN projects p ON n.project_id = p.id
        LEFT JOIN tasks t ON n.task_id = t.id
        WHERE n.user_id = %s
    """
    if unread_only:
        query += " AND n.is_read = FALSE"
    query += " ORDER BY n.created_at DESC, n.id DESC LIMIT %s;"
    
    return query_db(query, (user_id, limit))

def get_unread_count(user_id):
    query = "SELECT COUNT(*) AS count FROM notifications WHERE user_id = %s AND is_read = FALSE;"
    res = query_db(query, (user_id,), one=True)
    return res['count'] if res else 0

def mark_notification_as_read(notification_id, user_id):
    execute_db("UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s;", (notification_id, user_id))
    return True

def mark_all_as_read(user_id):
    execute_db("UPDATE notifications SET is_read = TRUE WHERE user_id = %s;", (user_id,))
    return True
