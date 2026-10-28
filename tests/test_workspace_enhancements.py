"""Permissions, report data and sync contracts for the shared workspace."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4


class TestWorkspaceEnhancements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from database import connection, init_db
        cls.previous = connection._SQLITE_PATH, connection._USE_MYSQL, init_db.SQLITE_PATH
        cls.temp = None
        if os.getenv('QA_TEST_ENGINE') != 'mysql':
            cls.temp = tempfile.TemporaryDirectory()
            connection._SQLITE_PATH = init_db.SQLITE_PATH = str(Path(cls.temp.name) / 'workspace.sqlite3')
            connection.set_engine_mode('sqlite')
            with contextlib.redirect_stdout(io.StringIO()):
                init_db.init_sqlite_fallback()
        from app import app
        cls.app = app

    @classmethod
    def tearDownClass(cls):
        if cls.temp:
            from database import connection, init_db
            connection._SQLITE_PATH, connection._USE_MYSQL, init_db.SQLITE_PATH = cls.previous
            cls.temp.cleanup()

    def setUp(self):
        from services.project_service import create_project
        ok, message, self.pid = create_project(2, 'Shared workspace', '', project_code='WS-' + uuid4().hex[:10], initial_member_ids=[3,4])
        self.assertTrue(ok, message)
        self.leader = self.client(2, 'leader')
        self.member = self.client(3, 'member')
        self.supporter = self.client(4, 'member')
        self.admin = self.client(1, 'admin')

    def client(self, uid, role):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session.update(user_id=uid, role=role)
        return client

    def task(self, **fields):
        from services.task_service import create_task
        ok, message, task = create_task(2, self.pid, fields.pop('title', 'Python Flask API'), **fields)
        self.assertTrue(ok, message)
        return task

    def test_assignee_and_supporter_receive_server_permissions_and_can_update(self):
        tid = self.task(assignee_id=3, support_member_ids=[4], estimated_hours=4)
        for client in (self.member, self.supporter):
            task = client.get(f'/api/tasks/{tid}').get_json()['task']
            self.assertTrue(task['can_update_status'])
            self.assertTrue(task['can_update_progress'])
            self.assertEqual(client.put(f'/api/tasks/{tid}/status', json={'status':'review'}).status_code, 200)
            self.assertEqual(client.put(f'/api/tasks/{tid}/progress', json={'progress_percent':37}).status_code, 200)
        self.assertEqual(self.member.get(f'/api/tasks/{tid}').get_json()['task']['progress_percent'], 37)

    def test_unassigned_member_cannot_update_another_members_task(self):
        tid = self.task(assignee_id=4)
        task = self.member.get(f'/api/tasks/{tid}').get_json()['task']
        self.assertFalse(task['can_update_status'])
        self.assertFalse(task['can_update_progress'])
        self.assertEqual(self.member.put(f'/api/tasks/{tid}/status', json={'status':'done'}).status_code, 403)
        self.assertEqual(self.member.put(f'/api/tasks/{tid}/progress', json={'progress_percent':100}).status_code, 403)

    def test_progress_validation_and_hundred_percent_completion(self):
        tid = self.task(assignee_id=3)
        for value in (-1, 101, True, 12.5, 'bad'):
            self.assertEqual(self.member.put(f'/api/tasks/{tid}/progress', json={'progress_percent':value}).status_code, 400)
        self.assertEqual(self.member.put(f'/api/tasks/{tid}/progress', json={'progress_percent':100}).status_code, 200)
        task = self.leader.get(f'/api/tasks/{tid}').get_json()['task']
        self.assertEqual((task['status'], task['progress_percent']), ('done',100))

    def test_member_can_edit_only_own_capacity(self):
        result = self.member.put(f'/api/projects/{self.pid}/members/3/capacity', json={'skills':'Python, Flask', 'availability':'50%', 'capacity_hours':12})
        self.assertEqual(result.status_code, 200, result.get_json())
        denied = self.member.put(f'/api/projects/{self.pid}/members/4/capacity', json={'skills':'forged', 'availability':'100%', 'capacity_hours':999})
        self.assertEqual(denied.status_code, 403)
        members = self.member.get(f'/api/projects/{self.pid}/members').get_json()['members']
        self.assertEqual(next(m for m in members if m['user_id']==3)['availability_percent'], 50)

    def test_leader_edits_member_and_ai_retrieval_uses_current_saved_data(self):
        tid = self.task(estimated_hours=5, description='Build a Python API', labels='Python, Flask')
        self.task(assignee_id=3, estimated_hours=4)
        response = self.leader.put(f'/api/projects/{self.pid}/members/3/capacity', json={'skills':'Python, Flask', 'availability':'50%', 'capacity_hours':6})
        self.assertEqual(response.status_code, 200)
        from services.project_data_retriever import retrieve_ai_data
        data, refs = retrieve_ai_data({'task_type':'assignment_suggestion', 'project_id':self.pid, 'task_id':tid, 'requester_id':2})
        candidate = next(c for c in data['candidates'] if c['user_id']==3)
        self.assertEqual((candidate['skills'], candidate['capacity_hours'], candidate['current_workload_hours']), ('Python, Flask',3,4))
        self.assertTrue(candidate['is_currently_overloaded'])
        self.assertIn(3, refs['members'])
        self.assertEqual(data['task']['labels'], 'Python, Flask')

    def test_invalid_capacity_does_not_change_saved_data(self):
        from database.connection import query_db
        before = query_db('SELECT skills,availability,capacity_hours FROM project_members WHERE project_id=%s AND user_id=3', (self.pid,), one=True)
        for data in ({'skills':'bad', 'availability':'101%', 'capacity_hours':4}, {'skills':'bad', 'availability':'50%', 'capacity_hours':-1}):
            self.assertEqual(self.member.put(f'/api/projects/{self.pid}/members/3/capacity', json=data).status_code, 400)
        after = query_db('SELECT skills,availability,capacity_hours FROM project_members WHERE project_id=%s AND user_id=3', (self.pid,), one=True)
        self.assertEqual(before, after)

    def test_capacity_is_project_specific_and_viewer_cannot_edit(self):
        from services.project_service import create_project
        from database.connection import execute_db
        _, _, other = create_project(2, 'Other project', '', initial_member_ids=[3])
        self.assertEqual(self.member.put(f'/api/projects/{self.pid}/members/3/capacity', json={'skills':'Project one', 'availability':'0%', 'capacity_hours':0}).status_code, 200)
        members = self.member.get(f'/api/projects/{other}/members').get_json()['members']
        self.assertNotEqual(next(m for m in members if m['user_id']==3)['skills'], 'Project one')
        execute_db("UPDATE project_members SET project_role='viewer' WHERE project_id=%s AND user_id=3", (self.pid,))
        self.assertEqual(self.member.put(f'/api/projects/{self.pid}/members/3/capacity', json={'skills':'bad'}).status_code, 403)

    def test_report_distinguishes_actual_progress_from_done_ratio(self):
        self.task(assignee_id=3, estimated_hours=2)
        tid = self.task(assignee_id=3, estimated_hours=3)
        self.member.put(f'/api/tasks/{tid}/progress', json={'progress_percent':25})
        done = self.task(assignee_id=3, estimated_hours=6)
        self.member.put(f'/api/tasks/{done}/progress', json={'progress_percent':100})
        result = self.member.get(f'/api/projects/{self.pid}/report').get_json()
        self.assertTrue(result['success'])
        self.assertEqual(result['metrics']['total_tasks'], 3)
        self.assertEqual(result['metrics']['average_progress'], 41.7)
        self.assertEqual(result['metrics']['completion_rate'], 33.3)
        member = next(m for m in result['workload'] if m['user_id']==3)
        self.assertEqual(member['current_workload_hours'], 5)

    def test_empty_report_has_zero_values_and_no_nonfinite_numbers(self):
        result = self.member.get(f'/api/projects/{self.pid}/report')
        self.assertEqual(result.status_code, 200)
        metrics = result.get_json()['metrics']
        self.assertEqual((metrics['total_tasks'],metrics['average_progress'],metrics['completion_rate']), (0,0,0))
        self.assertNotIn('NaN', result.get_data(as_text=True))

    def test_report_filter_checks_sprint_scope_and_outsider_permissions(self):
        from services.sprint_service import create_sprint
        from services.project_service import create_project
        _, _, sid = create_sprint(2, self.pid, 'Report filter', '', '2026-10-01','2026-10-30','done')
        self.task(sprint_id=sid)
        self.task()
        result = self.member.get(f'/api/projects/{self.pid}/report?sprint_id={sid}')
        self.assertEqual(result.get_json()['metrics']['total_tasks'], 1)
        ok, message, other = create_project(2,'Outsider project','',project_code='OUT-'+uuid4().hex[:10])
        self.assertTrue(ok, message)
        self.assertEqual(self.member.get(f'/api/projects/{other}/report').status_code, 403)
        self.assertEqual(self.member.get(f'/api/projects/{other}/members').status_code, 403)
        self.assertEqual(self.leader.get(f'/api/projects/{other}/report?sprint_id={sid}').status_code, 404)
        self.assertEqual(self.member.get(f'/api/projects/{self.pid}/report?sprint_id=bad').status_code, 400)

    def test_profile_is_current_session_account_without_secrets(self):
        result = self.member.get('/api/auth/me?user_id=1').get_json()
        self.assertEqual(result['user']['id'], 3)
        self.assertNotIn('password', json.dumps(result).lower())
        self.assertNotIn('api_key', json.dumps(result).lower())
        for client in (self.member,self.leader,self.admin):
            page = client.get('/team')
            self.assertEqual(page.status_code, 200)
            self.assertIn('account-profile-button', page.get_data(as_text=True))
            self.assertIn('Thành viên & Năng lực', page.get_data(as_text=True))

    def test_sync_changes_on_capacity_and_notification_read_but_not_app_version(self):
        first = self.member.get('/api/sync').get_json()
        self.member.put(f'/api/projects/{self.pid}/members/3/capacity', json={'skills':'Sync skill','availability':'75%','capacity_hours':10})
        second = self.member.get('/api/sync').get_json()
        self.assertNotEqual(first['revision'], second['revision'])
        self.assertEqual(first['app_version'], second['app_version'])
        from services.notification_service import create_notification
        nid = create_notification(3,self.pid,None,'qa','Read sync','Read sync')
        before = self.member.get('/api/sync').get_json()['revision']
        self.member.post(f'/api/notifications/{nid}/read')
        self.assertNotEqual(before, self.member.get('/api/sync').get_json()['revision'])

    def test_shared_pages_have_version_and_no_store_cache_policy(self):
        for route in ('/kanban','/reports','/team','/api/auth/me','/api/sync'):
            response = self.member.get(route)
            self.assertIn('no-store', response.headers['Cache-Control'])
            self.assertEqual(len(response.headers['X-App-Version']), 20)
        with patch('routes.sync_routes.get_app_version', return_value='next-build'):
            self.assertEqual(self.member.get('/api/sync').get_json()['app_version'],'next-build')

    def test_archived_task_is_readonly_in_returned_capabilities(self):
        tid = self.task(assignee_id=3)
        self.assertEqual(self.leader.delete(f'/api/tasks/{tid}').status_code, 200)
        task = self.member.get(f'/api/tasks/{tid}').get_json()['task']
        self.assertFalse(task['can_update_progress'])
        self.assertEqual(self.member.put(f'/api/tasks/{tid}/progress',json={'progress_percent':20}).status_code,409)
