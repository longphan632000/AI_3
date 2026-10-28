"""Exercise the installed CPU model and all AI features against disposable SQLite."""

import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'logstest' / 'qa-local-brain-live.json')
    parser.add_argument('--probe-primary', action='store_true', help='Also exercise the configured cloud API with synthetic data.')
    args = parser.parse_args()
    from services.ai_config import resolve_ai_setting, key_is_configured
    primary_provider = resolve_ai_setting('AI_PROVIDER', 'gemini')[0].lower()
    key_setting = 'GEMINI_API_KEY' if primary_provider == 'gemini' else 'OPENAI_API_KEY'
    primary_key = resolve_ai_setting(key_setting)[0] if args.probe_primary else ''
    gemini_model = resolve_ai_setting('GEMINI_MODEL', 'gemini-3.6-flash')[0]
    gemini_meeting_model = resolve_ai_setting('GEMINI_MEETING_MODEL', gemini_model)[0]
    os.environ.update(AI_CONFIG_SOURCE='process', AI_PROVIDER=primary_provider, OPENAI_API_KEY='your_openai_api_key',
                      GEMINI_API_KEY='your_gemini_api_key', GEMINI_MODEL=gemini_model, GEMINI_MEETING_MODEL=gemini_meeting_model,
                      OPENAI_MODEL='deepseek-v4.1-flash-1017', OPENAI_MEETING_MODEL='deepseek-v4.1-flash-1017',
                      AI_LOCAL_FALLBACK_ENABLED='true', LOCAL_AI_MODEL_ENABLED='true', LOCAL_AI_AUTOSTART='true',
                      AI_TOTAL_TIMEOUT_SECONDS='180', LOCAL_AI_TIMEOUT_SECONDS='90',
                      SMTP_ENABLED='false', DEADLINE_WORKER_ENABLED='false')
    from database import connection, init_db
    from services.local_model_service import LocalModelService, stop_owned_runtime
    records = []
    try:
        with tempfile.TemporaryDirectory() as directory:
            connection._SQLITE_PATH = init_db.SQLITE_PATH = str(Path(directory) / 'live.sqlite3')
            connection.set_engine_mode('sqlite')
            init_db.init_sqlite_fallback()
            from app import app
            from services.project_service import create_project
            from database.connection import query_db
            from services.ai_deadline import phase_budget
            client = app.test_client()
            with client.session_transaction() as session:
                session.update(user_id=2, role='leader')
            ok, message, project_id = create_project(2, 'Live Local Brain', 'Isolated CPU model acceptance',
                                                    project_code='LOCAL-LIVE', initial_member_ids=[3, 4])
            assert ok, message
            task = client.post(f'/api/projects/{project_id}/tasks', json={
                'title': 'Kiểm thử Python SQLite', 'assignee_id': 3, 'estimated_hours': 4,
                'due_date': '2026-10-30', 'priority': 'high', 'labels': 'Python, Testing',
            })
            assert task.status_code == 201, task.get_json()
            task_id = task.get_json()['task_id']

            start = time.monotonic()
            service = LocalModelService()
            assert service.installed, 'Run scripts/setup_local_brain.py first.'
            with phase_budget(120):
                reply = service.generate_content('Chỉ trả lời một câu tiếng Việt ngắn: SQLite dùng để làm gì?', max_output_tokens=160)
            assert reply.strip(), 'The real model produced no answer.'
            records.append({'name': 'Installed Qwen3 CPU model generates text without key', 'passed': True,
                            'seconds': round(time.monotonic() - start, 2), 'reply': reply})
            print(json.dumps(records[-1], ensure_ascii=False), flush=True)

            for task_type, extra in (
                ('weekly_summary', {'week_start': '2026-10-26', 'week_end': '2026-11-01'}),
                ('meeting_minutes', {'raw_notes': 'Thời gian họp: 28/10/2026.\nĐã thống nhất dùng SQLite.\nLong sẽ kiểm thử trước 30/10/2026.\nChưa chốt triển khai.'}),
                ('assignment_suggestion', {'task_id': task_id}),
            ):
                start = time.monotonic()
                response = client.post('/api/ai', json=dict(project_id=project_id, task_type=task_type, **extra))
                data = response.get_json()
                assert response.status_code == 200 and data['success'], data
                assert data['engine']['fallback_used'], data
                draft = query_db('SELECT * FROM ai_drafts WHERE id=%s', (data['draft_id'],), one=True)
                history = query_db('SELECT * FROM ai_history WHERE draft_id=%s', (data['draft_id'],), one=True)
                assert history['model_provider'] == '+'.join(data['engine']['used_providers'])
                assert json.loads(draft['validation_json'])['engine'] == data['engine']
                if task_type == 'meeting_minutes':
                    structured = json.loads(draft['structured_result_json'])
                    assert 'Đã thống nhất dùng SQLite.' in structured['decisions']
                    assert 'Chưa chốt' not in structured['decisions']
                    assert 'Long sẽ kiểm thử' in structured['action_items']
                    assert len(data['source_references']) == 4
                records.append({'name': f'{task_type}: real SQLite pipeline with installed model', 'passed': True,
                                'seconds': round(time.monotonic() - start, 2), 'engine': data['engine'],
                                'status': data['status'], 'draft_id': data['draft_id'], 'result': data['result']})
                print(json.dumps({key: value for key, value in records[-1].items() if key != 'result'}, ensure_ascii=False), flush=True)

            # No model runtime is needed for the last local fallback layer.
            with patch.dict(os.environ, {'LOCAL_AI_MODEL_ENABLED': 'false'}):
                response = client.post('/api/ai', json={'project_id': project_id, 'task_type': 'weekly_summary',
                                                       'week_start': '2026-10-26', 'week_end': '2026-11-01'})
                assert response.status_code == 200 and response.get_json()['engine']['used_providers'] == ['local_rules']
                records.append({'name': 'Model disabled: local domain brain keeps assistant working', 'passed': True})

            if args.probe_primary and key_is_configured(primary_key):
                with patch.dict(os.environ, {key_setting: primary_key, 'AI_PRIMARY_BUDGET_SECONDS': '30'}):
                    for task_type, extra in (
                        ('weekly_summary', {'week_start': '2026-10-26', 'week_end': '2026-11-01'}),
                        ('meeting_minutes', {'raw_notes': 'Cuộc họp kiểm thử.\nĐã thống nhất dùng SQLite.\nLong sẽ kiểm thử trước 30/10/2026.'}),
                        ('assignment_suggestion', {'task_id': task_id}),
                    ):
                        start = time.monotonic()
                        response = client.post('/api/ai', json=dict(project_id=project_id, task_type=task_type, **extra))
                        data = response.get_json()
                        assert response.status_code == 200 and data['success'], data
                        records.append({'name': f'{task_type}: real primary API with synthetic project data',
                                        'passed': True, 'seconds': round(time.monotonic() - start, 2),
                                        'engine': data['engine'], 'status': data['status']})
                        print(json.dumps(records[-1], ensure_ascii=False), flush=True)
    except Exception as error:
        records.append({'name': 'Live local brain acceptance', 'passed': False, 'error': str(error)})
        raise
    finally:
        stop_owned_runtime()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({
            'timestamp': datetime.now(timezone(timedelta(hours=7))).isoformat(),
            'database': 'disposable SQLite', 'primary_provider': primary_provider,
            'real_cloud_api': args.probe_primary and key_is_configured(primary_key), 'real_local_model': True,
            'success': bool(records) and all(row['passed'] for row in records), 'records': records,
        }, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
