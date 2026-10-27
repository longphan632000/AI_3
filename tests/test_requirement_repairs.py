"""Acceptance/regression checks traced to Detai33; all writes isolated."""
import contextlib
import io
import json
import logging
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

class TestRequirementRepairs(unittest.TestCase):
    evidence = {}
    sequence = 0

    @classmethod
    def setUpClass(cls):
        from database import connection, init_db
        if os.getenv('QA_TEST_ENGINE') == 'mysql':
            cls.temp = None
            from app import app
            cls.app = app
            app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
            app.logger.setLevel(logging.CRITICAL)
            return
        cls.previous_database = (connection._SQLITE_PATH, connection._USE_MYSQL, init_db.SQLITE_PATH)
        cls.temp = tempfile.TemporaryDirectory()
        database_path = str(Path(cls.temp.name) / 'requirements.sqlite3')
        connection._SQLITE_PATH = database_path
        connection.set_engine_mode('sqlite')
        init_db.SQLITE_PATH = database_path
        with contextlib.redirect_stdout(io.StringIO()):
            init_db.init_sqlite_fallback()
        from app import app
        cls.app = app
        app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
        app.logger.setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        if cls.temp is None:
            return
        cls.temp.cleanup()
        from database import connection, init_db
        connection._SQLITE_PATH, connection._USE_MYSQL, init_db.SQLITE_PATH = cls.previous_database

    def setUp(self):
        from services.project_service import create_project
        type(self).sequence += 1
        ok, message, self.pid = create_project(2, f'Requirements {self.sequence}', '',
                                              initial_member_ids=[3], project_code=f'DOC{self.sequence}')
        self.assertTrue(ok, message)
        self.leader = self.client(2, 'leader')
        self.member = self.client(3, 'member')
        self.admin = self.client(1, 'admin')

    def client(self, uid, role):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session.update(user_id=uid, role=role)
        return client

    def task(self, **kwargs):
        from services.task_service import create_task
        ok, message, tid = create_task(2, self.pid, kwargs.pop('title', 'Requirement task'), **kwargs)
        self.assertTrue(ok, message)
        return tid

    def save(self, requirements, expected, actual):
        self.evidence[self._testMethodName] = {
            'requirements': requirements, 'expected': expected, 'actual': actual}

    def test_01_leader_delete_preserves_history_by_default(self):
        from database.connection import query_db
        tid = self.task()
        response = self.leader.delete(f'/api/projects/{self.pid}')
        project = query_db('SELECT is_archived FROM projects WHERE id=%s', (self.pid,), one=True)
        task = query_db('SELECT id FROM tasks WHERE id=%s', (tid,), one=True)
        self.save(['FR-03', 'BR-08', 'integrity rule 10'], 'project archived; task history preserved',
                  {'http': response.status_code, 'project': project, 'task': task})
        self.assertIsNotNone(project, 'Default DELETE physically removed project')
        self.assertTrue(project['is_archived'])
        self.assertIsNotNone(task)

    def test_02_leader_cannot_permanently_delete(self):
        response = self.leader.delete(f'/api/projects/{self.pid}?permanent=true')
        self.save(['BR-08', 'integrity rule 10'], '403 for leader permanent delete', response.status_code)
        self.assertEqual(response.status_code, 403)

    def test_03_leader_can_remove_project_member(self):
        from database.connection import query_db
        self.task(assignee_id=3)
        response = self.leader.delete(f'/api/projects/{self.pid}/members/3')
        routes = [str(rule) for rule in self.app.url_map.iter_rules()
                  if 'members' in str(rule) and 'DELETE' in rule.methods]
        self.save(['FR-04', 'UC004'], 'remove member, preserve work history',
                  {'http': response.status_code, 'member_delete_routes': routes})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(query_db('SELECT id FROM project_members WHERE project_id=%s AND user_id=3',
                                  (self.pid,), one=True))

    def test_04_sprint_archive_applies_to_listing(self):
        response = self.leader.post(f'/api/projects/{self.pid}/sprints', json={
            'name': 'Archive sprint', 'start_date': '2026-01-01', 'end_date': '2026-01-10',
            'completion_criteria': 'Done'})
        sid = response.get_json()['sprint_id']
        response = self.leader.put(f'/api/sprints/{sid}', json={
            'name': 'Archive sprint', 'start_date': '2026-01-01', 'end_date': '2026-01-10',
            'status': 'archived', 'completion_criteria': 'Done'})
        listing = self.leader.get(f'/api/projects/{self.pid}/sprints').get_json()['sprints']
        visible = [row['id'] for row in listing]
        self.save(['FR-07', 'UC006'], 'archived sprint absent from active listing',
                  {'update_http': response.status_code, 'still_listed': sid in visible,
                   'delete_http': self.leader.delete(f'/api/sprints/{sid}').status_code})
        self.assertNotIn(sid, visible)

    def test_05_ai_draft_can_be_read_and_edited(self):
        from database.connection import execute_db
        draft = execute_db('''INSERT INTO ai_drafts
            (project_id, task_type, input_params_json, draft_content, source_references_json, created_by)
            VALUES (%s, 'meeting_minutes', '{}', 'Original', '[]', 3)''', (self.pid,))
        read = self.member.get(f'/api/ai/drafts/{draft}')
        edit = self.member.put(f'/api/ai/drafts/{draft}', json={'draft_content': 'Reviewed'})
        supported = [{'path': str(rule), 'methods': sorted(rule.methods)}
                     for rule in self.app.url_map.iter_rules() if '/drafts/' in str(rule)]
        self.save(['FR-12', 'FR-13', 'BR-06', 'UC009', 'UC010'], 'read/edit authorized draft before confirmation',
                  {'get_http': read.status_code, 'put_http': edit.status_code, 'routes': supported})
        self.assertEqual(read.status_code, 200)
        self.assertEqual(edit.status_code, 200)

    def test_06_priority_filter_is_applied(self):
        self.task(priority='high')
        self.task(priority='low')
        rows = self.leader.get(f'/api/projects/{self.pid}/tasks?priority=high').get_json()['tasks']
        self.save(['FR-09'], 'only high priority', [row['priority'] for row in rows])
        self.assertTrue(rows)
        self.assertTrue(all(row['priority'] == 'high' for row in rows))

    def test_07_deadline_filter_is_applied(self):
        self.task(due_date='2026-01-01 12:00:00')
        self.task(due_date='2026-12-01 12:00:00')
        rows = self.leader.get(f'/api/projects/{self.pid}/tasks?due_from=2026-01-01&due_to=2026-01-31').get_json()['tasks']
        self.save(['FR-09'], 'only January deadlines', [row['due_date'] for row in rows])
        self.assertTrue(all('2026-01' in str(row['due_date']) for row in rows))

    def test_08_task_sort_is_applied(self):
        self.task(title='Alpha')
        self.task(title='Zulu')
        rows = self.leader.get(f'/api/projects/{self.pid}/tasks?sort_by=title&sort_order=asc').get_json()['tasks']
        titles = [row['title'] for row in rows]
        self.save(['FR-09'], 'ascending title order; API/UI needs explicit sort contract', titles)
        self.assertEqual(titles, sorted(titles))

    def test_09_false_ai_statistics_cannot_be_confirmed(self):
        tid = self.task(assignee_id=3, due_date='2026-01-10 12:00:00')
        provider = Mock(provider_name='mock')
        provider.generate_response.return_value = f'Tất cả 999 nhiệm vụ đã hoàn thành, tỷ lệ 100%. [Task #{tid}] [User #3]'
        with patch('services.ai_assistant_service.AIProviderService', return_value=provider):
            response = self.leader.post('/api/ai', json={
                'task_type': 'weekly_summary', 'project_id': self.pid,
                'week_start': '2026-01-01', 'week_end': '2026-01-31'})
        body = response.get_json()
        confirmed = self.leader.post(f"/api/ai/drafts/{body['draft_id']}/confirm")
        self.save(['FR-12', 'BR-07', 'NFR-06'], 'unsupported statistics rejected or needs verification',
                  {'source': 'one backlog task; zero done', 'http': response.status_code,
                   'status': body.get('status'), 'warnings': body.get('warnings'),
                   'confirm_http': confirmed.status_code})
        self.assertNotEqual(confirmed.status_code, 200)

    def test_10_assignment_limits_recommendations_to_three(self):
        from database.connection import execute_db
        from services.project_member_service import add_project_member
        add_project_member(2, self.pid, 4)
        uid = execute_db('''INSERT INTO users (username,email,password_hash,full_name,role,status)
                            VALUES (%s,%s,'unused','Audit candidate','member','active')''',
                         (f'cand{self.sequence}', f'cand{self.sequence}@audit.local'))
        add_project_member(2, self.pid, uid)
        tid = self.task()
        provider = Mock(provider_name='mock')
        provider.generate_response.return_value = f'''Đề xuất cho [Task #{tid}]:
1. [User #2] vì có kỹ năng phù hợp, chưa quá tải.
2. [User #3] vì có kỹ năng phù hợp, chưa quá tải.
3. [User #4] vì có kỹ năng phù hợp, chưa quá tải.
4. [User #{uid}] vì có kỹ năng phù hợp, chưa quá tải.'''
        with patch('services.ai_assistant_service.AIProviderService', return_value=provider):
            response = self.leader.post('/api/ai', json={
                'task_type': 'assignment_suggestion', 'project_id': self.pid, 'task_id': tid})
        body = response.get_json()
        self.save(['FR-14', 'UC011'], 'at most 3 recommendations; otherwise reject or flag',
                  {'http': response.status_code, 'status': body.get('status'),
                   'warnings': body.get('warnings'), 'mock_recommendations': 4})
        self.assertTrue(response.status_code != 200 or body.get('status') != 'draft')

    def test_11_overdue_email_has_automatic_trigger(self):
        with patch('services.email_service.send_smtp_email', return_value='MOCKED') as smtp:
            tid = self.task(assignee_id=3, due_date='2020-01-01 12:00:00')
            self.leader.put(f'/api/tasks/{tid}/status', json={'status': 'in_progress'})
        self.save(['FR-17', 'BR-09', 'UC005', 'UC013'], 'automatic overdue processing or queued job',
                  {'smtp_calls_on_create_and_status_update': smtp.call_count,
                   'code_inspection': 'email checker referenced only by manual trigger route; no scheduler/outbox'})
        self.assertGreater(smtp.call_count, 0)

    def test_12_admin_can_update_basic_account_information(self):
        response = self.admin.put('/api/admin/users/3', json={'full_name': 'Updated audit name'})
        self.save(['FR-02', 'UC002'], 'admin can update account information',
                  {'http': response.status_code, 'existing_update_options': 'status and role only'})
        self.assertEqual(response.status_code, 200)

    def test_13_viewer_cannot_change_progress_or_comment(self):
        self.leader.post(f'/api/projects/{self.pid}/members', json={'user_id': 4, 'project_role': 'viewer'})
        viewer = self.client(4, 'member')
        tid = self.task(assignee_id=3)
        progress = viewer.put(f'/api/tasks/{tid}/progress', json={'progress_percent': 100})
        comment = viewer.post(f'/api/tasks/{tid}/comments', json={'content': 'Viewer wrote this'})
        self.save(['FR-02', 'NFR-03'], 'report viewer has no write permission',
                  {'progress_http': progress.status_code, 'comment_http': comment.status_code})
        self.assertEqual(progress.status_code, 403)
        self.assertEqual(comment.status_code, 403)

    def test_14_member_cannot_create_sprint(self):
        sprint = self.member.post(f'/api/projects/{self.pid}/sprints', json={'name': 'Forbidden'})
        self.save(['FR-02', 'FR-07'], 'member only views sprints; cannot create',
                  {'sprint_http': sprint.status_code})
        self.assertEqual(sprint.status_code, 403)

    def test_15_outsider_cannot_read_tasks(self):
        outsider = self.client(4, 'member')
        response = outsider.get(f'/api/projects/{self.pid}/tasks')
        self.save(['FR-02', 'NFR-03'], '403 outside project', response.status_code)
        self.assertEqual(response.status_code, 403)

    def test_16_locked_account_cannot_login(self):
        response = self.app.test_client().post('/api/auth/login', json={
            'username_or_email': 'locked_user', 'password': 'Password123!'})
        self.save(['FR-01'], '401 for locked account', response.status_code)
        self.assertEqual(response.status_code, 401)

    def test_17_reversed_sprint_dates_rejected(self):
        response = self.leader.post(f'/api/projects/{self.pid}/sprints', json={
            'name': 'Invalid', 'start_date': '2026-01-10', 'end_date': '2026-01-01'})
        self.save(['FR-07', 'BR-03'], '400 for reversed sprint dates', response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_18_empty_sprint_completion_is_zero(self):
        from services.sprint_service import create_sprint, calculate_sprint_metrics
        ok, _, sid = create_sprint(2, self.pid, 'Empty', '', '2026-01-01', '2026-01-10', 'Done')
        self.assertTrue(ok)
        metrics = calculate_sprint_metrics(sid)
        self.save(['FR-07', 'BR-04'], 'empty sprint 0%', metrics)
        self.assertEqual(metrics['completion_rate'], 0)

    def test_19_ai_suggestion_does_not_assign_task(self):
        from database.connection import query_db
        tid = self.task()
        provider = Mock(provider_name='mock')
        provider.generate_response.return_value = f'Đề xuất [User #3] cho [Task #{tid}] vì kỹ năng phù hợp. Chưa quá tải.'
        with patch('services.ai_assistant_service.AIProviderService', return_value=provider):
            response = self.leader.post('/api/ai', json={
                'task_type': 'assignment_suggestion', 'project_id': self.pid, 'task_id': tid})
        stored = query_db('SELECT assignee_id FROM tasks WHERE id=%s', (tid,), one=True)
        self.save(['FR-14', 'BR-06'], 'draft only; no automatic assignment',
                  {'http': response.status_code, 'assignee_id': stored['assignee_id']})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(stored['assignee_id'])

    def test_20_logout_invalidates_session(self):
        self.member.post('/logout')
        response = self.member.get(f'/api/projects/{self.pid}/tasks')
        self.save(['FR-01'], '401 after logout', response.status_code)
        self.assertEqual(response.status_code, 401)

    def test_21_attachment_upload_download_and_scope(self):
        from database.connection import query_db
        tid = self.task()
        with tempfile.TemporaryDirectory() as directory, patch.dict(self.app.config, {'UPLOAD_FOLDER':directory}):
            response = self.member.post(f'/api/tasks/{tid}/attachments',data={'file':(io.BytesIO(b'QA attachment'),'bienban.txt')})
            self.assertEqual(response.status_code,201)
            aid=response.get_json()['attachment_id']
            download=self.member.get(f'/api/attachments/{aid}/download')
            self.assertEqual(download.data,b'QA attachment')
            download.close()
            outsider=self.client(4,'member').get(f'/api/attachments/{aid}/download')
            self.assertEqual(outsider.status_code,403)
            stored=query_db('SELECT * FROM attachments WHERE id=%s',(aid,),one=True)
            self.assertNotIn(directory,stored['file_path'])
            self.save(['FR-08','NFR-03'],'upload/download only within project',{'upload':201,'download':200,'outside':403,'bytes_match':True})

    def test_22_attachment_rejects_bad_type_size_and_fake_pdf(self):
        from database.connection import query_db
        tid=self.task()
        statuses=[]
        with tempfile.TemporaryDirectory() as directory, patch.dict(self.app.config,{'UPLOAD_FOLDER':directory}):
            for name,content in [('run.exe',b'executable'),('fake.pdf',b'not pdf'),('large.txt',b'x'*(5*1024*1024+1))]:
                statuses.append(self.member.post(f'/api/tasks/{tid}/attachments',data={'file':(io.BytesIO(content),name)}).status_code)
            self.assertTrue(all(code in (400,413) for code in statuses))
            self.assertEqual(query_db('SELECT COUNT(*) AS n FROM attachments WHERE task_id=%s',(tid,),one=True)['n'],0)
            self.assertEqual(list(Path(directory).iterdir()),[])
        self.save(['FR-08'],'reject invalid files without leftovers',statuses)

    def test_23_failure_rolls_back_task_assignments_and_audit(self):
        from database.connection import query_db
        tid=self.task(assignee_id=2,support_member_ids=[3])
        before=query_db('SELECT * FROM tasks WHERE id=%s',(tid,),one=True)
        audit_before=query_db('SELECT COUNT(*) AS n FROM audit_logs WHERE target_id=%s',(tid,),one=True)['n']
        with patch('services.task_service.sync_task_assignees',side_effect=RuntimeError('Injected transaction failure')):
            response=self.leader.put(f'/api/tasks/{tid}',json={'title':'Must roll back','assignee_id':3,'support_member_ids':[]})
        after=query_db('SELECT * FROM tasks WHERE id=%s',(tid,),one=True)
        self.assertEqual(response.status_code,500)
        self.assertEqual((after['title'],after['assignee_id']),(before['title'],before['assignee_id']))
        self.assertEqual(query_db('SELECT COUNT(*) AS n FROM audit_logs WHERE target_id=%s',(tid,),one=True)['n'],audit_before)
        self.save(['FR-05','NFR-05'],'all changes rolled back on injected failure',{'http':500,'task_unchanged':True,'audit_unchanged':True})

    def test_24_progress_consistent_across_endpoints(self):
        from database.connection import query_db
        tid=self.task()
        self.assertEqual(self.leader.put(f'/api/tasks/{tid}',json={'progress_percent':100}).status_code,200)
        done=query_db('SELECT status,progress_percent FROM tasks WHERE id=%s',(tid,),one=True)
        self.assertEqual(done['status'],'done')
        self.leader.put(f'/api/tasks/{tid}/status',json={'status':'review'})
        opened=query_db('SELECT status,progress_percent FROM tasks WHERE id=%s',(tid,),one=True)
        self.assertEqual(opened['status'],'review')
        self.assertLess(opened['progress_percent'],100)
        self.assertEqual(self.leader.put(f'/api/tasks/{tid}/progress',json={'progress_percent':1.5}).status_code,400)
        self.save(['FR-05','FR-06','FR-10'],'100% means Done; reopened task below 100%; integer input',{'done':done,'reopened':opened,'fraction_rejected':True})

    def test_25_zero_capacity_and_ai_workload_agree(self):
        from services.report_service import get_member_workload_statistics
        from services.project_data_retriever import retrieve_ai_data
        tid=self.task(assignee_id=2,support_member_ids=[3],estimated_hours=10)
        self.leader.put(f'/api/projects/{self.pid}/members/3/capacity',json={'capacity_hours':0,'availability':'100%'})
        report=next(row for row in get_member_workload_statistics(self.pid) if row['user_id']==3)
        data,_=retrieve_ai_data({'task_type':'assignment_suggestion','project_id':self.pid,'task_id':tid})
        candidate=next(row for row in data['candidates'] if row['user_id']==3)
        self.assertEqual(report['capacity_hours'],0)
        self.assertTrue(report['is_overloaded'])
        self.assertEqual(report['current_workload_hours'],candidate['current_workload_hours'])
        self.save(['FR-11','FR-14','BR-05'],'capacity zero preserved; supporter workload consistent',{'capacity':0,'report_hours':report['current_workload_hours'],'ai_hours':candidate['current_workload_hours'],'overloaded':True})

    def test_26_overdue_filter_precedes_pagination(self):
        overdue=self.task(priority='low',due_date='2020-01-01 12:00:00')
        self.task(priority='urgent',due_date='2099-01-01 12:00:00')
        rows=self.leader.get(f'/api/projects/{self.pid}/tasks?overdue_only=true&limit=1').get_json()['tasks']
        self.assertEqual([row['id'] for row in rows],[overdue])
        self.save(['FR-09','BR-02'],'page returns overdue task despite earlier non-overdue priority',{'returned':[row['id'] for row in rows]})

    def test_27_archived_project_and_task_are_readonly_then_restore(self):
        tid=self.task()
        self.leader.delete(f'/api/tasks/{tid}')
        denied=self.leader.put(f'/api/tasks/{tid}/status',json={'status':'done'})
        restored=self.leader.post(f'/api/tasks/{tid}/restore')
        self.assertEqual((denied.status_code,restored.status_code),(409,200))
        self.leader.delete(f'/api/projects/{self.pid}')
        denied=self.leader.post(f'/api/projects/{self.pid}/tasks',json={'title':'Must not create'})
        restored=self.leader.post(f'/api/projects/{self.pid}/restore')
        self.assertEqual((denied.status_code,restored.status_code),(409,200))
        self.save(['FR-03','FR-05','BR-08'],'archived data read-only; explicit restore',{'writes_blocked':409,'restore':200})

    def test_28_custom_and_generated_account_codes_do_not_collide(self):
        from database.connection import query_db
        payload={'username':f'custom{self.sequence}','email':f'custom{self.sequence}@audit.local','password':'Password123!','full_name':'Custom','role':'member','user_code':'NV-005'}
        first=self.admin.post('/api/admin/users',json=payload)
        self.assertEqual(first.status_code,200)
        payload.update(username=f'auto{self.sequence}',email=f'auto{self.sequence}@audit.local')
        payload.pop('user_code')
        second=self.admin.post('/api/admin/users',json=payload)
        self.assertEqual(second.status_code,200)
        codes=[row['user_code'] for row in query_db('SELECT user_code FROM users WHERE username IN (%s,%s)',(f'custom{self.sequence}',f'auto{self.sequence}'))]
        self.assertEqual(len(set(codes)),2)
        self.assertIn('NV-005',codes)
        self.save(['FR-02'],'custom code preserved; automatic code unique',codes)

    def test_29_edit_draft_versions_reject_stale_writes(self):
        from database.connection import execute_db, query_db
        snapshot=json.dumps({'source_refs':{'tasks':[],'members':[]},'data':{'tasks':[]},'warnings':[]})
        did=execute_db("""INSERT INTO ai_drafts(project_id,task_type,input_params_json,draft_content,source_references_json,created_by,validation_json)
            VALUES (%s,'weekly_summary','{}','Original','[]',2,%s)""",(self.pid,snapshot))
        good=self.leader.put(f'/api/ai/drafts/{did}',json={'version':1,'draft_content':'Reviewed'})
        stale=self.leader.put(f'/api/ai/drafts/{did}',json={'version':1,'draft_content':'Overwrite stale'})
        row=query_db('SELECT version,draft_content FROM ai_drafts WHERE id=%s',(did,),one=True)
        self.assertEqual((good.status_code,stale.status_code),(200,400))
        self.assertEqual((row['version'],row['draft_content']),(2,'Reviewed'))
        self.assertEqual(query_db('SELECT COUNT(*) AS n FROM ai_draft_revisions WHERE draft_id=%s',(did,),one=True)['n'],1)
        self.save(['FR-13','FR-15','NFR-09'],'edit version increments; stale writes rejected; prior version retained',row)

    def test_30_confirm_uses_edited_meeting_fields(self):
        from database.connection import execute_db, query_db
        structured=json.dumps({'title':'Original title','decisions':'Old decision','action_items':'Old action'})
        did=execute_db("""INSERT INTO ai_drafts(project_id,task_type,input_params_json,draft_content,source_references_json,structured_result_json,created_by)
            VALUES (%s,'meeting_minutes','{}','Original','[]',%s,3)""",(self.pid,structured))
        edited=self.member.put(f'/api/ai/drafts/{did}',json={'version':1,'draft_content':'Reviewed body','decisions':'Reviewed decision','action_items':'Reviewed action'})
        confirmed=self.leader.post(f'/api/ai/drafts/{did}/confirm')
        self.assertEqual((edited.status_code,confirmed.status_code),(200,200))
        row=query_db('SELECT summary,decisions,action_items FROM meeting_minutes WHERE project_id=%s',(self.pid,),one=True)
        self.assertEqual(row,{'summary':'Reviewed body','decisions':'Reviewed decision','action_items':'Reviewed action'})
        self.save(['FR-13','BR-06'],'confirmed minutes store reviewed fields',row)

    def test_31_admin_cannot_confirm_project_draft(self):
        from database.connection import execute_db
        did=execute_db("""INSERT INTO ai_drafts(project_id,task_type,input_params_json,draft_content,source_references_json,created_by)
            VALUES (%s,'weekly_summary','{}','Draft','[]',2)""",(self.pid,))
        response=self.admin.post(f'/api/ai/drafts/{did}/confirm')
        self.assertEqual(response.status_code,403)
        self.save(['FR-12','FR-13','UC010'],'only project leader confirms',response.status_code)

    def test_32_history_filter_keeps_selected_project(self):
        from database.connection import execute_db
        from services.project_service import create_project
        _,_,other=create_project(2,f'History other {self.sequence}','',project_code=f'HIST{self.sequence}')
        for pid in (self.pid,other):
            execute_db("INSERT INTO ai_history(project_id,requester_id,task_type,result_summary) VALUES (%s,2,'weekly_summary','History')",(pid,))
        rows=self.leader.get(f'/api/ai/history?project_id={self.pid}').get_json()['history']
        self.assertEqual({row['project_id'] for row in rows},{self.pid})
        self.save(['FR-15'],'only selected project history',{'projects':list({row['project_id'] for row in rows})})

    def test_33_javascript_files_and_rendered_scripts_parse(self):
        import re,subprocess
        root=Path(__file__).resolve().parents[1]
        scripts={str(p.name):p.read_text(encoding='utf-8') for p in (root/'static/js').glob('*.js')}
        for path,client in [('/dashboard',self.leader),('/kanban',self.leader),('/sprints',self.leader),('/ai-assistant',self.leader),('/reports',self.leader),('/notifications',self.leader),('/admin',self.admin),('/login',self.app.test_client())]:
            page=client.get(path)
            self.assertEqual(page.status_code,200)
            for index,source in enumerate(re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',page.get_data(as_text=True),re.S)):
                scripts[f'{path}:{index}']=source
        check=subprocess.run(['node','-e',"const vm=require('vm'),fs=require('fs');const scripts=JSON.parse(fs.readFileSync(0,'utf8'));const errors=[];for(const [name,s] of Object.entries(scripts)){try{new vm.Script(s)}catch(e){errors.push({name,error:e.message})}}process.stdout.write(JSON.stringify(errors))"],input=json.dumps(scripts),capture_output=True,encoding='utf-8')
        self.assertEqual(check.returncode,0)
        self.assertEqual(json.loads(check.stdout),[])
        self.save(['FR-06','FR-10','NFR-02'],'all rendered classic scripts parse',{'scripts':len(scripts),'errors':[]})

    def test_34_admin_edit_form_is_in_body_not_title(self):
        html=self.admin.get('/admin').get_data(as_text=True)
        self.assertNotIn('modal-edit-user',html[html.index('<title>'):html.index('</title>')])
        self.assertIn('id="modal-edit-user"',html[html.index('<body'):])
        self.save(['FR-02','NFR-02'],'account editor rendered in page body',True)

    def test_35_overdue_delivery_deduplicates_and_retries_failed(self):
        from database.connection import execute_db, query_db
        from services.email_service import check_and_send_overdue_email_alerts
        from datetime import datetime,timedelta
        with patch('services.email_service.send_smtp_email',return_value='FAILED') as smtp:
            tid=self.task(assignee_id=3,due_date='2020-01-01 12:00:00')
            check_and_send_overdue_email_alerts(project_id=self.pid)
            self.assertEqual(smtp.call_count,1)
        execute_db('UPDATE email_deliveries SET updated_at=%s WHERE task_id=%s',((datetime.now()-timedelta(minutes=10)),tid))
        with patch('services.email_service.send_smtp_email',return_value='SUCCESS') as smtp:
            check_and_send_overdue_email_alerts(project_id=self.pid)
            check_and_send_overdue_email_alerts(project_id=self.pid)
            self.assertEqual(smtp.call_count,1)
        row=query_db('SELECT status,attempts FROM email_deliveries WHERE task_id=%s',(tid,),one=True)
        self.assertEqual(row,{'status':'SENT','attempts':2})
        self.save(['FR-16','FR-17','BR-09'],'failed mail retry bounded; successful mail not duplicated',row)

    def test_36_email_scan_does_not_leak_other_project(self):
        from services.project_service import create_project
        from services.task_service import create_task
        from database.connection import execute_db
        _,_,private=create_project(2,f'Private {self.sequence}','',project_code=f'PRIVATE{self.sequence}')
        _,_,tid=create_task(2,private,'Private task',assignee_id=2,due_date='2020-01-01 12:00:00')
        execute_db('DELETE FROM email_deliveries WHERE task_id=%s',(tid,))
        with patch('services.email_service.send_smtp_email',return_value='MOCKED'):
            denied=self.member.post(f'/api/notifications/trigger-overdue-check?project_id={private}')
            response=self.member.post('/api/notifications/trigger-overdue-check')
        self.assertEqual(denied.status_code,403)
        self.assertNotIn(tid,[a['task_id'] for a in response.get_json()['alerts']])
        self.save(['FR-02','FR-17','NFR-03'],'outside project blocked; no private alert payload',{'specific_project':403,'private_task_leaked':False})

    def test_37_invalid_supporter_rejected_without_partial_task(self):
        from database.connection import query_db
        before=query_db('SELECT COUNT(*) AS n FROM tasks WHERE project_id=%s',(self.pid,),one=True)['n']
        response=self.leader.post(f'/api/projects/{self.pid}/tasks',json={'title':'Bad supporters','support_member_ids':[1,5]})
        self.assertEqual(response.status_code,400)
        self.assertEqual(query_db('SELECT COUNT(*) AS n FROM tasks WHERE project_id=%s',(self.pid,),one=True)['n'],before)
        self.save(['FR-02','FR-05'],'outside/locked supporters rejected before insert',{'http':400,'task_count_unchanged':True})

    def test_38_invalid_inputs_return_4xx(self):
        statuses=[]
        for estimate in ['abc',-99,True,False,float('inf')]:
            statuses.append(self.leader.post(f'/api/projects/{self.pid}/tasks',json={'title':'Invalid estimate','estimated_hours':estimate}).status_code)
        statuses.append(self.leader.post(f'/api/projects/{self.pid}/tasks',json=[1,2]).status_code)
        statuses.append(self.leader.post(f'/api/projects/{self.pid}/sprints',json={'name':'Bad date','start_date':'aaa','end_date':'zzz'}).status_code)
        self.assertTrue(all(code==400 for code in statuses),statuses)
        self.save(['FR-03','FR-05','FR-07'],'wrong types, negative/nonfinite numbers and invalid dates rejected',statuses)

    def test_39_link_attachment_rejects_script_scheme(self):
        tid=self.task()
        good=self.member.post(f'/api/tasks/{tid}/attachments',json={'name':'Tài liệu','url':'https://example.test/document'})
        bad=self.member.post(f'/api/tasks/{tid}/attachments',json={'name':'Bad','url':'javascript:alert(1)'})
        self.assertEqual((good.status_code,bad.status_code),(201,400))
        self.save(['FR-08','NFR-03'],'HTTP link accepted; executable scheme rejected',{'https':201,'javascript':400})

    def test_40_remove_member_preserves_history_and_clears_active_assignment(self):
        from database.connection import query_db
        tid=self.task(assignee_id=3)
        self.member.post(f'/api/tasks/{tid}/comments',json={'content':'Historical comment'})
        response=self.leader.delete(f'/api/projects/{self.pid}/members/3')
        self.assertEqual(response.status_code,200)
        row=query_db('SELECT assignee_id FROM tasks WHERE id=%s',(tid,),one=True)
        self.assertIsNone(row['assignee_id'])
        self.assertIsNotNone(query_db('SELECT id FROM comments WHERE task_id=%s',(tid,),one=True))
        self.assertEqual(self.member.get(f'/api/tasks/{tid}').status_code,403)
        self.save(['FR-04','UC004','NFR-09'],'remove membership, clear active assignment, keep comment history',{'http':200,'history_preserved':True,'departed_access':403})

    def test_41_last_leader_cannot_be_removed(self):
        response=self.leader.delete(f'/api/projects/{self.pid}/members/2')
        self.assertEqual(response.status_code,400)
        self.save(['FR-04','integrity rule 2'],'project keeps an active leader',response.status_code)

    def test_42_ai_deadline_shared_across_retries(self):
        from services.ai_deadline import with_ai_budget, remaining_timeout
        @with_ai_budget
        def call():
            remaining_timeout(20)
            return {'success':True},200
        with patch('services.ai_deadline.time.monotonic',side_effect=[0,31]):
            body,status=call()
        self.assertEqual((status,body['error_code']),(503,'AI_TIMEOUT'))
        self.save(['NFR-01'],'expired total AI budget returns controlled timeout',{'http':503,'error':'AI_TIMEOUT'})

    def test_43_kira_client_initializes_with_installed_sdk(self):
        from services.kira_service import KiraAIService
        with patch.dict(os.environ,{'KIRA_API_KEY':'unit_test_fake_key','KIRA_BASE_URL':'https://example.test/v1'}):
            client=KiraAIService()._get_client()
            self.assertEqual(str(client.base_url),'https://example.test/v1/')
            client.close()
        self.save(['NFR-07','NFR-11'],'declared SDK initializes client without network',True)

    def test_44_dashboard_metrics_use_numeric_counts_and_rate(self):
        from database.connection import execute_db
        ids=[self.task() for _ in range(4)]
        execute_db("UPDATE tasks SET status='done',progress_percent=100 WHERE id=%s",(ids[0],))
        response=self.leader.get(f'/api/projects/{self.pid}/dashboard-metrics')
        self.assertEqual(response.status_code,200)
        metrics=response.get_json()['metrics']
        self.assertEqual((metrics['total_tasks'],metrics['count_done'],metrics['completion_rate']),(4,1,25.0))
        self.assertIsInstance(metrics['count_backlog'],int)
        self.save(['FR-10','BR-04'],'MySQL/SQLite counts numeric, completion 1/4 = 25%',metrics)

    def test_45_long_vietnamese_meeting_note_round_trips(self):
        content='Nội dung cuộc họp tiếng Việt. '*2000
        response=self.member.post(f'/api/projects/{self.pid}/meeting-notes',json={'title':'Ghi chú dài','meeting_date':'2026-01-01T09:00:00','attendees':'Nhóm kiểm thử','content':content})
        self.assertEqual(response.status_code,201)
        notes=self.member.get(f'/api/projects/{self.pid}/meeting-notes').get_json()['meeting_notes']
        self.assertEqual(notes[0]['content'],content.strip())
        self.save(['FR-08','FR-13'],'long UTF-8 note persists without MySQL TEXT truncation',{'http':201,'characters':len(content),'round_trip':True})

    def test_46_disabled_smtp_is_labelled_simulation(self):
        from services.email_service import send_smtp_email
        with patch.dict(os.environ,{'SMTP_ENABLED':'false'}),patch('services.email_service.smtplib.SMTP') as smtp:
            status=send_smtp_email('nobody@example.test','QA','No message should be sent')
        smtp.assert_not_called()
        self.assertEqual(status,'SIMULATED_DEMO_SUCCESS')
        self.save(['FR-17'],'disabled SMTP never sends; explicit simulation status',status)

    def test_47_archived_sprint_tasks_require_restore(self):
        from services.sprint_service import create_sprint
        _,_,sid=create_sprint(2,self.pid,'Sprint','','2026-01-01','2026-01-10','Done')
        tid=self.task(sprint_id=sid)
        self.leader.delete(f'/api/sprints/{sid}')
        denied=self.leader.put(f'/api/tasks/{tid}/progress',json={'progress_percent':30})
        restored=self.leader.post(f'/api/sprints/{sid}/restore')
        updated=self.leader.put(f'/api/tasks/{tid}/progress',json={'progress_percent':30})
        self.assertEqual((denied.status_code,restored.status_code,updated.status_code),(409,200,200))
        self.save(['FR-07','BR-08'],'archived sprint read-only until restore',{'blocked':409,'restored':200,'update_after_restore':200})

    def test_48_pwa_assets_are_served(self):
        manifest=self.leader.get('/static/manifest.json').get_json()
        statuses=[self.leader.get(icon['src']).status_code for icon in manifest['icons']]
        worker=self.leader.get('/sw.js')
        self.assertTrue(all(code==200 for code in statuses))
        self.assertEqual(worker.status_code,200)
        self.assertEqual(worker.headers['Service-Worker-Allowed'],'/')
        self.save(['NFR-02'],'manifest assets and service worker available',{'icons':statuses,'worker':200})

    def test_49_utc_deadline_normalized_to_project_timezone(self):
        tid=self.task(due_date='2030-01-01T00:00:00Z')
        stored=self.leader.get(f'/api/tasks/{tid}').get_json()['task']['due_date']
        self.assertTrue(stored.replace(' ','T').startswith('2030-01-01T07:00:00'))
        self.save(['BR-02','NFR-02'],'UTC timestamp normalized to UTC+7',stored)

    def test_50_kira_sdk_transport_contract(self):
        import httpx
        from openai import OpenAI
        from services.kira_service import KiraAIService
        captured=[]
        def handle(request):
            captured.append(json.loads(request.content))
            return httpx.Response(200,json={'id':'qa','object':'chat.completion','created':0,'model':'qa-model',
                'choices':[{'index':0,'message':{'role':'assistant','content':'{"items": []}'},'finish_reason':'stop'}]})
        with patch.dict(os.environ,{'KIRA_API_KEY':'qa_fake_key','KIRA_MODEL':'qa-model'}):
            client=OpenAI(api_key='qa_fake_key',base_url='https://example.test/v1',max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(handle)))
            provider=KiraAIService()
            with patch.object(provider,'_get_client',return_value=client):
                content=provider.generate_content('Return JSON',json_output=True)
            client.close()
        self.assertEqual(json.loads(content),{'items':[]})
        self.assertEqual(captured[0]['response_format'],{'type':'json_object'})
        self.save(['NFR-07','NFR-11'],'real SDK serializes Kira request with mocked HTTP transport',{'json_response':True,'response_format':'json_object','network':False})

    def test_51_create_project_with_initial_staff(self):
        response=self.leader.post('/api/projects',json={'name':'Dự án có nhân viên','project_code':f'TEAM{self.sequence}','member_ids':[3,4,3]})
        self.assertEqual(response.status_code,201,response.get_json())
        pid=response.get_json()['project_id']
        members=self.leader.get(f'/api/projects/{pid}/members').get_json()['members']
        self.assertEqual({m['user_id'] for m in members},{2,3,4})
        self.assertEqual(self.member.get(f'/api/projects/{pid}').status_code,200)
        self.assertEqual(self.admin.get(f'/api/projects/{pid}').status_code,200)
        self.save(['FR-03','FR-04'],'create project and selected active staff atomically',{'http':201,'members':[2,3,4],'member_read':200,'admin_read':200})

    def test_52_invalid_initial_staff_rolls_back_project(self):
        from database.connection import query_db
        code=f'BADTEAM{self.sequence}'
        response=self.leader.post('/api/projects',json={'name':'Invalid staff','project_code':code,'member_ids':[3,5]})
        self.assertEqual(response.status_code,400)
        self.assertIsNone(query_db('SELECT id FROM projects WHERE project_code=%s',(code,),one=True))
        self.save(['FR-03','FR-04','NFR-05'],'reject whole project when staff is locked',{'http':400,'project_created':False})

    def test_53_mixed_batch_does_not_partially_add_staff(self):
        from database.connection import query_db
        response=self.leader.post(f'/api/projects/{self.pid}/members',json={'user_ids':[4,5]})
        self.assertEqual(response.status_code,400)
        self.assertIsNone(query_db('SELECT id FROM project_members WHERE project_id=%s AND user_id=4',(self.pid,),one=True))
        self.save(['FR-04','NFR-05'],'no partial batch when one account is locked',{'http':400,'partial_membership':False})

    def _registration_approval(self,role):
        from database.connection import query_db
        username=f'pending_{role}_{self.sequence}'
        payload={'username':username,'email':username+'@example.test','password':'QApassword123!','full_name':'Người dùng chờ duyệt','role':role}
        anonymous=self.app.test_client()
        response=anonymous.post('/api/auth/register',json=payload)
        self.assertEqual(response.status_code,202)
        uid=query_db('SELECT id,status FROM users WHERE username=%s',(username,),one=True)['id']
        login={'username_or_email':username,'password':payload['password']}
        self.assertEqual(anonymous.post('/api/auth/login',json=login).status_code,401)
        self.assertEqual(self.member.post(f'/api/admin/users/{uid}/review',json={'decision':'approve'}).status_code,403)
        self.assertEqual(self.admin.post(f'/api/admin/users/{uid}/review',json={'decision':'approve'}).status_code,200)
        self.assertEqual(anonymous.post('/api/auth/login',json=login).status_code,200)
        return {'role':role,'register_http':202,'before_approval':401,'member_approve':403,'admin_approve':200,'after_approval':200}

    def test_54_member_requires_admin_approval(self):
        self.save(['FR-01','FR-02','User requirement: all registrations approved'],'member pending until Admin approval',self._registration_approval('member'))

    def test_55_leader_requires_admin_approval(self):
        self.save(['FR-01','FR-02','User requirement: all registrations approved'],'leader pending until Admin approval',self._registration_approval('leader'))

    def test_56_sync_across_independent_clients(self):
        before=self.member.get('/api/sync').get_json()['revision']
        self.task(title='Shared change')
        after=self.member.get('/api/sync')
        self.assertNotEqual(before,after.get_json()['revision'])
        self.assertEqual(after.headers['Cache-Control'],'no-store')
        data=after.get_json()
        self.assertEqual(set(data),{'success','revision','poll_seconds'})
        self.assertEqual(self.admin.get('/api/sync').status_code,200)
        self.assertEqual(self.app.test_client().get('/api/sync').status_code,401)
        self.save(['FR-10','FR-11','NFR-05'],'separate sessions receive opaque invalidation token; no cached API',{'changed':True,'poll_seconds':5,'anonymous':401,'no_store':True})

    def test_57_lock_invalidates_other_client_session(self):
        from services.account_service import create_user, update_user_status
        from database.connection import query_db
        username=f'sync_lock_{self.sequence}'
        ok,_=create_user(1,username,username+'@example.test','QApassword123!','Nhân viên','member')
        self.assertTrue(ok)
        uid=query_db('SELECT id FROM users WHERE username=%s',(username,),one=True)['id']
        client=self.client(uid,'member')
        self.assertEqual(client.get('/api/sync').status_code,200)
        self.assertTrue(update_user_status(1,uid,'locked')[0])
        self.assertEqual(client.get('/api/sync').status_code,401)
        self.save(['FR-01','FR-02'],'existing browser session rejected after Admin lock',{'before':200,'after':401})

    def test_58_unicode_staff_name_roundtrip(self):
        username=f'vietnamese_{self.sequence}'
        name='Lưu Trà My — Nguyễn Đặng Ánh, tiếng Việt'
        response=self.admin.post('/api/admin/users',json={'username':username,'email':username+'@example.test','password':'QApassword123!','full_name':name,'role':'member'})
        self.assertEqual(response.status_code,200,response.get_json())
        users=self.leader.get('/api/users/assignable').get_json()['users']
        self.assertEqual(next(u for u in users if u['username']==username)['full_name'],name)
        self.save(['FR-02','FR-04','NFR-02'],'Unicode preserved through account creation, database and staff API',{'name':name,'matches':True})

    def test_59_live_file_config_overrides_stale_kira_environment(self):
        from services.ai_provider_service import AIProviderService
        from services.gemini_service import GeminiService
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'.env'
            config='AI_CONFIG_SOURCE=env_file\nAI_PROVIDER=gemini\nGEMINI_MODEL=gemini-3.8-flash\nGEMINI_MEETING_MODEL=gemini-3.8-flash\nGEMINI_API_KEY='
            path.write_text(config+'\n',encoding='utf-8')
            with patch.dict(os.environ,{'AI_CONFIG_SOURCE':'env_file','AI_PROVIDER':'kira','GEMINI_API_KEY':'stale_secret'}),patch('services.ai_config.ENV_FILE',path):
                first=AIProviderService()
                self.assertEqual(first.provider_name,'gemini')
                self.assertIsInstance(first.provider,GeminiService)
                self.assertFalse(first.provider.configured)
                path.write_text(config+'qa_fake_new_key\n',encoding='utf-8')
                second=AIProviderService()
                self.assertTrue(second.provider.configured)
                self.assertEqual(second.provider.meeting_model,second.provider.model)
        self.save(['FR-12','FR-13','FR-14','NFR-11'],'all AI actions use live Gemini config despite stale Kira process settings',{'provider':'gemini','models':'gemini-3.8-flash','blank_key_rejected':True,'reload_key':True})

    def test_60_gemini_wire_contract_and_thought_filter(self):
        from services.gemini_service import GeminiService
        response={'candidates':[{'content':{'parts':[{'thought':True,'text':'Internal thought'},{'text':'{"items":[]}'}]}}]}
        with patch.dict(os.environ,{'AI_CONFIG_SOURCE':'process','GEMINI_API_KEY':'qa_fake_key','GEMINI_MODEL':'gemini-3.8-flash','GEMINI_MEETING_MODEL':'gemini-3.8-flash'}),patch('services.gemini_service.urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as network:
            result=GeminiService().generate_content('Source note',json_output=True)
        self.assertEqual(json.loads(result),{'items':[]})
        request=network.call_args.args[0];payload=json.loads(request.data)
        self.assertIn('/models/gemini-3.8-flash:generateContent',request.full_url)
        self.assertEqual(payload['generationConfig']['responseMimeType'],'application/json')
        self.assertNotIn('temperature',payload['generationConfig'])
        self.save(['FR-13','NFR-06','NFR-11'],'Gemini JSON contract excludes thought text and deprecated sampling field',{'model':'gemini-3.8-flash','json_output':True,'thought_excluded':True})

    def test_61_meeting_pipeline_uses_gemini_and_saves_draft(self):
        import re
        captured=[]
        def respond(request,**kwargs):
            captured.append(request.full_url)
            prompt=json.loads(request.data)['contents'][0]['parts'][0]['text']
            source=prompt.split('NGUỒN:\n')[-1]
            identifiers=re.findall(r'^\[(\d+)\]',source,re.MULTILINE)
            items=[{'id':int(uid),'kinds':['discussion'],'summary':'Trao đổi theo nội dung nguồn.'} for uid in identifiers]
            return io.BytesIO(json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps({'items':items})}]}}]}).encode())
        with patch.dict(os.environ,{'AI_CONFIG_SOURCE':'process','AI_PROVIDER':'gemini','GEMINI_API_KEY':'qa_fake_key','GEMINI_MODEL':'gemini-3.8-flash','GEMINI_MEETING_MODEL':'gemini-3.8-flash'}),patch('services.gemini_service.urllib.request.urlopen',side_effect=respond):
            response=self.member.post('/api/ai',json={'task_type':'meeting_minutes','project_id':self.pid,'raw_notes':'Cuộc họp trao đổi tiến độ.\nCần kiểm tra giao diện điện thoại.'})
        self.assertEqual(response.status_code,200,response.get_json())
        self.assertTrue(captured)
        self.assertTrue(all('generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:' in url for url in captured))
        draft=response.get_json()['draft_id']
        self.assertEqual(self.member.get(f'/api/ai/drafts/{draft}').status_code,200)
        self.save(['FR-13','BR-06','BR-07'],'meeting API routes to Gemini, processes grounded source and persists readable draft',{'http':200,'draft_read':200,'provider':'gemini','network':'mock HTTP transport'})

    def test_62_repair_only_damaged_known_sample_names(self):
        from scripts.repair_sample_names import repair, SAMPLE_NAMES
        from database.connection import execute_db,query_db
        original=query_db('SELECT full_name FROM users WHERE id=3',one=True)['full_name']
        execute_db('UPDATE users SET full_name=%s WHERE id=3',('L?u Tr? My',))
        try:
            self.assertIn('member_my',repair(apply=True))
            restored=query_db('SELECT full_name FROM users WHERE id=3',one=True)['full_name']
            self.assertEqual(restored,SAMPLE_NAMES['member_my'])
            self.assertEqual(repair(apply=True),[])
        finally:
            execute_db('UPDATE users SET full_name=%s WHERE id=3',(original,))
        self.save(['FR-02','NFR-02'],'repair known corrupted names without resetting accounts or passwords',{'restored':restored,'repeat_no_changes':True})

    def test_63_initial_staff_validation_types(self):
        responses=[]
        for index,value in enumerate(['3',True,[True],[None],[1],['abc']]):
            response=self.leader.post('/api/projects',json={'name':'Bad staff type','project_code':f'TYPES{self.sequence}-{index}','member_ids':value})
            responses.append(response.status_code)
            self.assertEqual(response.status_code,400,response.get_json())
        self.save(['FR-03','FR-04','NFR-05'],'invalid staff list types and Admin staff assignment rejected',{'http':responses})

    def test_64_public_development_secret_cannot_forge_admin_session(self):
        from flask import Flask
        fake=Flask('qa-forged-session')
        fake.secret_key='dev_secret_key_ai_sdlc_2026_super_secure'
        serializer=fake.session_interface.get_signing_serializer(fake)
        cookie=serializer.dumps({'user_id':1,'role':'admin'})
        client=self.app.test_client()
        client.set_cookie('session',cookie)
        self.assertEqual(client.get('/api/admin/users').status_code,401)
        self.save(['FR-01','FR-02','NFR-03'],'cookie forged with published sample secret does not grant Admin',{'forged_cookie_http':401})

    def test_65_network_denied_returns_specific_error_without_draft(self):
        from database.connection import query_db
        import errno
        import urllib.error
        before=query_db('SELECT COUNT(*) AS total FROM ai_drafts WHERE project_id=%s',(self.pid,),one=True)['total']
        denied=PermissionError(errno.EACCES,'qa_private_secret')
        denied.winerror=10013
        with patch.dict(os.environ,{'AI_CONFIG_SOURCE':'process','AI_PROVIDER':'gemini','GEMINI_API_KEY':'qa_fake_key'}),patch('services.gemini_service.urllib.request.urlopen',side_effect=urllib.error.URLError(denied)) as network,patch('services.gemini_service.time.sleep') as sleep:
            response=self.leader.post('/api/ai',json={'task_type':'weekly_summary','project_id':self.pid,'week_start':'2026-10-20','week_end':'2026-10-27'})
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.get_json()['error_code'],'AI_NETWORK_DENIED')
        self.assertNotIn('qa_private_secret',response.get_data(as_text=True))
        network.assert_called_once();sleep.assert_not_called()
        after=query_db('SELECT COUNT(*) AS total FROM ai_drafts WHERE project_id=%s',(self.pid,),one=True)['total']
        self.assertEqual(before,after)
        self.save(['FR-12','NFR-01','NFR-03','NFR-06'],'network access denial is explicit; no retry or partial draft',{'http':503,'code':'AI_NETWORK_DENIED','calls':1,'draft_created':False})

    def test_66_admin_probe_exposes_safe_network_diagnostics(self):
        import errno
        import urllib.error
        denied=PermissionError(errno.EACCES,'qa_private_secret')
        denied.winerror=10013
        with patch.dict(os.environ,{'AI_CONFIG_SOURCE':'process','AI_PROVIDER':'gemini','GEMINI_API_KEY':'qa_fake_key','GEMINI_MODEL':'qa-model','GEMINI_MEETING_MODEL':'qa-model'}),patch('services.gemini_service.urllib.request.urlopen',side_effect=urllib.error.URLError(denied)) as network:
            response=self.admin.get('/api/admin/ai-status?probe=1')
        data=response.get_json()
        self.assertEqual(response.status_code,200)
        self.assertFalse(data['api_reachable'])
        self.assertEqual(data['error_code'],'AI_NETWORK_DENIED')
        self.assertEqual(data['checks']['general']['diagnostics']['winerror'],10013)
        self.assertEqual(data['probe_scope'],'model_metadata_only')
        network.assert_called_once()
        self.assertNotIn('qa_private_secret',response.get_data(as_text=True))
        self.assertNotIn('qa_fake_key',response.get_data(as_text=True))
        self.save(['FR-02','NFR-03','NFR-09'],'Admin gets safe error category and OS code; one probe for shared model',{'http':200,'reachable':False,'code':'AI_NETWORK_DENIED','winerror':10013,'probe_calls':1})

    def test_67_meeting_tls_error_preserves_no_partial_result(self):
        import ssl
        import urllib.error
        from database.connection import query_db
        with patch.dict(os.environ,{'AI_CONFIG_SOURCE':'process','AI_PROVIDER':'gemini','GEMINI_API_KEY':'qa_fake_key'}),patch('services.gemini_service.urllib.request.urlopen',side_effect=urllib.error.URLError(ssl.SSLCertVerificationError(1,'private_detail'))) as network,patch('services.gemini_service.time.sleep') as sleep:
            response=self.member.post('/api/ai',json={'task_type':'meeting_minutes','project_id':self.pid,'raw_notes':'Cuộc họp kiểm thử chứng chỉ TLS.'})
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.get_json()['error_code'],'AI_TLS_CERTIFICATE')
        self.assertNotIn('private_detail',response.get_data(as_text=True))
        network.assert_called_once();sleep.assert_not_called()
        self.assertEqual(query_db('SELECT COUNT(*) AS total FROM ai_drafts WHERE project_id=%s',(self.pid,),one=True)['total'],0)
        self.save(['FR-13','NFR-03','NFR-06'],'TLS failure remains verified/explicit and never saves partial meeting',{'http':503,'code':'AI_TLS_CERTIFICATE','draft_created':False,'calls':1})

