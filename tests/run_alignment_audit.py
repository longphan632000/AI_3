"""Reproduce alignment observations on disposable SQLite; never send email/AI.

These are recorded observations, separate from the regression pass/fail count.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.update(AI_CONFIG_SOURCE='process', AI_PROVIDER='gemini',
                  GEMINI_API_KEY='qa_fake_key', SMTP_ENABLED='false',
                  DEADLINE_WORKER_ENABLED='false', LOCAL_AI_MODEL_ENABLED='false')


def main():
    from database import connection, init_db
    observations = []
    with tempfile.TemporaryDirectory() as directory:
        connection._SQLITE_PATH = init_db.SQLITE_PATH = str(Path(directory) / 'audit.sqlite3')
        connection.set_engine_mode('sqlite')
        with contextlib.redirect_stdout(io.StringIO()):
            init_db.init_sqlite_fallback()
        from app import app
        from database.connection import query_db, execute_db
        from services.account_service import create_user
        from services.project_member_service import assign_project_leader
        from services.project_service import create_project
        from services.sprint_service import create_sprint
        from services.task_service import create_task, update_task_status
        from services.notification_service import scan_and_create_deadline_notifications
        from services.email_service import send_smtp_email

        clients = {}
        for uid, role in ((1, 'admin'), (2, 'leader'), (3, 'member')):
            client = app.test_client()
            with client.session_transaction() as session:
                session.update(user_id=uid, role=role)
            clients[role] = client

        ok, message = create_user(1, 'audit_leader', 'audit@example.invalid',
                                  'Password123!', 'Audit leader', 'leader')
        assert ok, message
        uid = query_db("SELECT id FROM users WHERE username='audit_leader'", one=True)['id']
        ok, message, pid = create_project(2, 'Alignment audit', '', initial_member_ids=[3, 4])
        assert ok, message
        ok, message = assign_project_leader(1, pid, uid)
        assert ok, message
        due = (datetime.now() + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
        ok, message, tid = create_task(2, pid, 'Soon task', assignee_id=3,
                                       support_member_ids=[4], due_date=due, estimated_hours=2)
        assert ok, message
        execute_db('DELETE FROM notifications WHERE project_id=%s', (pid,))
        response = clients['member'].get('/api/notifications')
        assert response.status_code == 200
        count = query_db("SELECT COUNT(*) AS n FROM notifications WHERE task_id=%s AND event_type='due_soon_reminder'", (tid,), one=True)['n']
        observations.append({'id': 'AUD-FR16-A', 'observation': 'Opening notification list does not run due-soon scan',
                             'due_in_hours': 12, 'due_soon_notifications': count})
        assert count == 0
        scan_and_create_deadline_notifications(target_project_id=pid)
        recipients = query_db("SELECT user_id FROM notifications WHERE task_id=%s AND event_type='due_soon_reminder' ORDER BY user_id", (tid,))
        observations.append({'id': 'AUD-FR16-B', 'observation': 'Manual scan works but notifies assignees/supporters only',
                             'recipients': [r['user_id'] for r in recipients], 'project_leaders': [2, uid]})
        execute_db('DELETE FROM notifications WHERE project_id=%s', (pid,))
        ok, message = update_task_status(3, tid, 'in_progress')
        assert ok, message
        recipients = query_db("SELECT user_id FROM notifications WHERE task_id=%s AND event_type='status_changed' ORDER BY user_id", (tid,))
        observations.append({'id': 'AUD-FR16-C', 'observation': 'Member status change omits supporter and second project leader',
                             'recipients': [r['user_id'] for r in recipients], 'supporter': 4, 'other_leader': uid})

        ok, message, null_tid = create_task(2, pid, 'No due date and zero estimate')
        assert ok, message
        row = query_db('SELECT due_date, estimated_hours FROM tasks WHERE id=%s', (null_tid,), one=True)
        observations.append({'id': 'AUD-DATA-01', 'observation': 'Task accepts missing due date and zero estimate unlike source data dictionary',
                             'actual': row, 'source': 'Detai33 tables 37-38: due NOT NULL; estimate NULL or >0'})
        ok, message, sid = create_sprint(2, pid, 'Empty criteria', '', '2026-10-28', '2026-10-29', '')
        assert ok, message
        observations.append({'id': 'AUD-DATA-02', 'observation': 'Sprint accepts empty completion criteria', 'sprint_id': sid})
        observations.append({'id': 'AUD-FR17', 'observation': 'Disabled SMTP reports simulated success, not a real email',
                             'result': send_smtp_email('nobody@example.invalid', 'audit', 'audit')})

        # Lock/demotion are valid admin actions; record the operational gap without
        # inventing a requirement that security locks must always be prohibited.
        ok, message, solo_pid = create_project(uid, 'Sole leader audit', '')
        assert ok, message
        lock = clients['admin'].post(f'/api/admin/users/{uid}/status', json={'status': 'locked'})
        assert lock.status_code == 200
        observations.append({'id': 'AUD-OPS-01', 'observation': 'Admin can lock a sole project leader without replacement',
                             'http': lock.status_code, 'project_id': solo_pid, 'classification': 'operational risk; needs explicit policy'})

    payload = {'database': 'disposable SQLite', 'real_api_calls': False,
               'real_emails': False, 'kind': 'alignment observations, not regression success count',
               'timestamp': datetime.now().isoformat(), 'observations': observations}
    (ROOT / 'logstest/qa-alignment-observations.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(f'Recorded {len(observations)} alignment observations on disposable SQLite.')


if __name__ == '__main__':
    main()
