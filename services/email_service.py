import hashlib
import logging
import threading
from uuid import uuid4
from datetime import timedelta
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database.connection import query_db, execute_db, atomic, transaction
from services.task_service import is_task_overdue
from services.notification_service import create_notification

@atomic
def claim_delivery(task, now):
    """Persist a lease before sending; unique key prevents concurrent duplicate claims."""
    repeat_hours = max(1, min(168, int(os.getenv('OVERDUE_REPEAT_HOURS', '24'))))
    key = hashlib.sha256(f"{task['id']}:{task['assignee_id']}:{task['due_date']}".encode()).hexdigest()
    existing = query_db('SELECT * FROM email_deliveries WHERE claim_key=%s', (key,), one=True)
    token = uuid4().hex
    if existing:
        # Failed delivery retries are bounded; completed/demo deliveries are not repeated.
        from services.validation import local_datetime
        retry_after = max(60, int(os.getenv('OVERDUE_RETRY_SECONDS', '300')))
        age = (now-local_datetime(existing['updated_at'])).total_seconds()
        if existing['status'] in ('SENT','SIMULATED'):
            if age < repeat_hours * 3600:
                return None
            changed = execute_db("""UPDATE email_deliveries SET status='PROCESSING',claim_token=%s,
                attempts=1,attempted_at=%s,updated_at=%s WHERE id=%s AND claim_token=%s""",
                (token,now,now,existing['id'],existing['claim_token']))
            return (existing['id'],token) if changed == 1 else None
        if existing['status'] not in ('FAILED', 'PROCESSING') or age < retry_after or existing['attempts'] >= 3:
            return None
        changed = execute_db("""UPDATE email_deliveries SET status='PROCESSING',claim_token=%s,
            attempts=attempts+1,updated_at=%s WHERE id=%s AND claim_token=%s""",
            (token,now,existing['id'],existing['claim_token']))
        return (existing['id'],token) if changed == 1 else None
    identifier = execute_db("""INSERT INTO email_deliveries
        (task_id,user_id,claim_key,claim_token,status,attempted_at,updated_at)
        VALUES (%s,%s,%s,%s,'PROCESSING',%s,%s)""", (task['id'],task['assignee_id'],key,token,now,now))
    return identifier,token


def check_and_send_overdue_email_alerts(project_id=None, user_id=None, allowed_projects=None, task_id=None):
    """Scoped BR-09 scan. Call only after the business transaction has committed."""
    clauses = ["t.is_archived=FALSE", "p.is_archived=FALSE", "t.status<>'done'",
               "t.due_date < %s", "u.status='active'",
               "EXISTS (SELECT 1 FROM project_members pm WHERE pm.project_id=t.project_id AND pm.user_id=u.id AND pm.project_role IN ('leader','member'))"]
    args = [datetime.now()]
    if task_id is not None:
        clauses.append('t.id=%s')
        args.append(task_id)
    if project_id is not None:
        clauses.append('t.project_id=%s')
        args.append(project_id)
    if user_id is not None:
        clauses.append('t.assignee_id=%s')
        args.append(user_id)
    if allowed_projects is not None:
        if not allowed_projects:
            return []
        clauses.append('t.project_id IN (' + ','.join(['%s']*len(allowed_projects)) + ')')
        args.extend(allowed_projects)
    tasks = query_db("""SELECT t.id,t.title,t.due_date,t.project_id,t.assignee_id,
        p.name AS project_name,u.email AS assignee_email,u.full_name AS assignee_name
        FROM tasks t JOIN projects p ON p.id=t.project_id JOIN users u ON u.id=t.assignee_id
        WHERE """ + ' AND '.join(clauses) + ' ORDER BY t.id', tuple(args))
    alerts = []
    for task in tasks:
        now = datetime.now()
        try:
            claim = claim_delivery(task, now)
        except Exception as error:
            # Another process may have inserted the same unique delivery key.
            from sqlite3 import IntegrityError
            from mysql.connector import IntegrityError as MySQLIntegrityError
            if isinstance(error, (IntegrityError,MySQLIntegrityError)):
                continue
            raise
        if not claim:
            continue
        subject = f"[CẢNH BÁO TRỄ HẠN] {task['title']}"
        body = (f"Xin chào {task['assignee_name']},\n"
                f"Nhiệm vụ {task['title']} trong dự án {task['project_name']} đã quá hạn {task['due_date']}.\n"
                'Vui lòng kiểm tra và cập nhật tiến độ.')
        try:
            sent_status = send_smtp_email(task['assignee_email'], subject, body)
        except Exception:
            sent_status = 'FAILED'
        status = 'SENT' if sent_status in ('SUCCESS','MOCKED') else 'SIMULATED' if sent_status.startswith('SIMULATED') else 'FAILED'
        with transaction():
            changed = execute_db('UPDATE email_deliveries SET status=%s,updated_at=%s WHERE id=%s AND claim_token=%s',
                                (status,datetime.now(),claim[0],claim[1]))
            if changed:
                create_notification(task['assignee_id'],task['project_id'],task['id'],'task_overdue',
                    f"Cảnh báo trễ hạn: {task['title']}",
                    f"Nhiệm vụ đã quá hạn {task['due_date']}. Trạng thái email: {status}.")
        alerts.append({'task_id':task['id'],'task_title':task['title'], 'project_name':task['project_name'],
            'assignee_name':task['assignee_name'],'assignee_email':task['assignee_email'],
            'due_date':str(task['due_date']),'subject':subject,'body_preview':body,
            'sent_status':status,'dispatched_at':now.strftime('%Y-%m-%d %H:%M:%S')})
    return alerts


_worker = None
_worker_stop = threading.Event()


def start_deadline_worker():
    """One daemon per app process; delivery leases coordinate multiple processes."""
    global _worker
    if os.getenv('DEADLINE_WORKER_ENABLED','true').lower() != 'true' or (_worker and _worker.is_alive()):
        return
    def work():
        interval = max(10, int(os.getenv('DEADLINE_SCAN_SECONDS', '60')))
        while not _worker_stop.is_set():
            try:
                check_and_send_overdue_email_alerts()
            except Exception:
                logging.getLogger(__name__).exception('Deadline scan failed')
            _worker_stop.wait(interval)
    _worker = threading.Thread(target=work, name='deadline-alerts', daemon=True)
    _worker.start()


def send_smtp_email(recipient_email, subject, body_text):
    if os.getenv('SMTP_ENABLED', 'false').lower() != 'true':
        return 'SIMULATED_DEMO_SUCCESS'
    smtp_user = os.getenv('SMTP_USER', '').strip()
    smtp_password = os.getenv('SMTP_PASSWORD', '').strip()
    
    # Chế độ Demo: Mô phỏng gửi email an toàn, không gián đoạn bài báo cáo
    if not smtp_user or not smtp_password:
        return "FAILED_CONFIG"
        
    try:
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_from = os.getenv('SMTP_FROM', 'noreply@aiprojectmanager.local')
        
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=3)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return "SUCCESS"
    except Exception as e:
        logging.getLogger(__name__).warning('SMTP failed (%s)', type(e).__name__)
        return 'FAILED'

