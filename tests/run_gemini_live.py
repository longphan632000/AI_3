"""Test Gemini and fallback with synthetic data in disposable SQLite only."""

from datetime import date, timedelta, datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['SMTP_ENABLED'] = 'false'
os.environ['DEADLINE_WORKER_ENABLED'] = 'false'


def main():
    from database import connection, init_db
    from services.ai_provider_service import AIProviderService
    from services.local_model_service import stop_owned_runtime
    provider = AIProviderService()
    if provider.primary_provider_name != 'gemini':
        raise SystemExit('Set AI_PROVIDER=gemini before running the Gemini check.')
    service = provider.provider
    report = {
        'timestamp': datetime.now(timezone(timedelta(hours=7))).isoformat(),
        'provider': 'gemini', 'model': service.model if service else None,
        'meeting_model': service.meeting_model if service else None,
        'database': 'disposable SQLite; application MySQL never used',
        'input': 'synthetic QA data only', 'records': [],
    }
    try:
        if service is None:
            ok, message, code = False, str(provider.primary_error), provider.primary_error.code
        else:
            ok, message = service.probe_model()
            code = service.last_probe_error_code
        report['generation_probe'] = {'passed': ok, 'code': code, 'message': message,
                                      'configured': bool(service and service.configured)}
        print('Gemini generation probe:', ok, code, flush=True)
        with tempfile.TemporaryDirectory() as directory:
            connection.set_engine_mode('sqlite')
            connection._SQLITE_PATH = init_db.SQLITE_PATH = str(Path(directory) / 'gemini.sqlite3')
            init_db.init_sqlite_fallback()
            from app import app
            from database.connection import query_db, execute_db
            from services.project_service import create_project
            from services.project_member_service import update_member_capacity
            from services.task_service import create_task, update_task_status
            for uid in range(1, 6):
                execute_db('UPDATE users SET full_name=%s,username=%s,email=%s WHERE id=%s',
                           (f'QA User {uid}', f'qa_user_{uid}', f'qa{uid}@example.test', uid))
            success, message, project_id = create_project(2, 'Gemini QA', 'Synthetic fixture',
                initial_member_ids=[3, 4], project_code='QA-GEMINI-LIVE')
            assert success, message
            update_member_capacity(2, project_id, 3, 'Python, testing', '100%', 40)
            update_member_capacity(2, project_id, 4, 'Frontend, documentation', '80%', 32)
            success, _, done_id = create_task(2, project_id, 'Verify test data', assignee_id=3, estimated_hours=1)
            assert success
            assert update_task_status(2, done_id, 'done')[0]
            success, _, task_id = create_task(2, project_id, 'Write Python unit tests',
                description='Test login with synthetic data.', estimated_hours=2, labels='Python, testing')
            assert success
            leader, member = app.test_client(), app.test_client()
            for client, uid, role in ((leader, 2, 'leader'), (member, 3, 'member')):
                with client.session_transaction() as session:
                    session.update(user_id=uid, role=role)
            today = date.today()
            cases = (
                ('weekly_summary', leader, {'week_start': (today - timedelta(days=6)).isoformat(), 'week_end': today.isoformat()}),
                ('meeting_minutes', member, {'raw_notes': 'Cuộc họp kiểm thử.\nĐã thống nhất kiểm tra dữ liệu.\nQA User 3 sẽ kiểm thử trước 30/10/2026.'}),
                ('assignment_suggestion', leader, {'task_id': task_id}),
            )
            for task_type, client, fields in cases:
                started = time.monotonic()
                result = client.post('/api/ai', json={'task_type': task_type, 'project_id': project_id, **fields})
                data = result.get_json() or {}
                engine = data.get('engine', {})
                draft = query_db('SELECT status FROM ai_drafts WHERE id=%s', (data['draft_id'],), one=True) if data.get('draft_id') else None
                used = engine.get('used_providers', [])
                record = {
                    'task_type': task_type, 'http': result.status_code,
                    'pipeline_passed': result.status_code == 200 and data.get('success') is True and bool(draft),
                    'gemini_only_success': used == ['gemini'] and result.status_code == 200 and bool(draft),
                    'engine': engine, 'status': data.get('status'), 'error_code': data.get('error_code'),
                    'error': data.get('error'), 'warnings': data.get('warnings', []),
                    'draft_saved': bool(draft), 'seconds': round(time.monotonic() - started, 3),
                }
                if draft:
                    history = query_db('SELECT model_provider FROM ai_history WHERE draft_id=%s', (data['draft_id'],), one=True)
                    assert history['model_provider'] == '+'.join(used)
                report['records'].append(record)
                print(json.dumps(record, ensure_ascii=True), flush=True)
            task = query_db('SELECT assignee_id FROM tasks WHERE id=%s', (task_id,), one=True)
            official = query_db('SELECT COUNT(*) AS total FROM meeting_minutes WHERE project_id=%s', (project_id,), one=True)['total']
            confirmed = query_db("SELECT COUNT(*) AS total FROM ai_drafts WHERE project_id=%s AND status='confirmed'", (project_id,), one=True)['total']
            report['safety'] = {'task_still_unassigned': task['assignee_id'] is None,
                                'official_meeting_count': official, 'confirmed_draft_count': confirmed}
            assert task['assignee_id'] is None and official == 0 and confirmed == 0
        report['integration_success'] = all(row['pipeline_passed'] for row in report['records'])
        report['cloud_success'] = ok and all(row['gemini_only_success'] for row in report['records'])
        report['cloud_status'] = ('not_configured' if code == 'AI_KEY_MISSING' else
                                  'passed' if report['cloud_success'] else 'failed_or_partial')
        report['success'] = report['integration_success'] and report['cloud_success']
    except Exception:
        report['success'] = False
        report['execution_error'] = 'Live test did not complete; inspect the local test log.'
        raise
    finally:
        stop_owned_runtime()
        output = ROOT / 'docs/qa-gemini-live-results.json'
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Integration:', report['integration_success'], 'Gemini cloud:', report['cloud_status'], flush=True)
    return 0 if report['success'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
