"""Current staffing, actual progress and archive actor contracts on isolated data."""
import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4


class TestStaffingArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from database import connection, init_db
        cls.previous=connection._SQLITE_PATH,connection._USE_MYSQL,init_db.SQLITE_PATH
        cls.temp=None
        if os.getenv('QA_TEST_ENGINE')!='mysql':
            cls.temp=tempfile.TemporaryDirectory()
            connection._SQLITE_PATH=init_db.SQLITE_PATH=str(Path(cls.temp.name)/'staffing.sqlite3')
            connection.set_engine_mode('sqlite')
            with contextlib.redirect_stdout(io.StringIO()):init_db.init_sqlite_fallback()
        from app import app
        cls.app=app

    @classmethod
    def tearDownClass(cls):
        if cls.temp:
            from database import connection,init_db
            connection._SQLITE_PATH,connection._USE_MYSQL,init_db.SQLITE_PATH=cls.previous
            cls.temp.cleanup()

    def client(self,uid,role):
        c=self.app.test_client()
        with c.session_transaction() as s:s.update(user_id=uid,role=role)
        return c

    def setUp(self):
        from services.project_service import create_project
        from database.connection import execute_db,query_db
        from services.member_profile_service import update_professional_profile
        suffix=uuid4().hex[:10]
        self.extra=[]
        for i in range(8):
            uid=execute_db('''INSERT INTO users(username,email,password_hash,full_name,role,status)
                VALUES (%s,%s,%s,%s,'member','active')''',(f'{suffix}-{i}',f'{suffix}-{i}@example.invalid','qa',f'Backend {suffix} {i}'))
            self.extra.append(uid)
            update_professional_profile(uid,'Python, Flask, backend','100%',40)
        self.pm2=execute_db('''INSERT INTO users(username,email,password_hash,full_name,role,status)
            VALUES (%s,%s,'qa','Other PM','leader','active')''',(suffix+'pm',suffix+'pm@example.invalid'))
        ok,msg,self.pid=create_project(2,'Staffing '+suffix,'Private project description',project_code=suffix,initial_member_ids=[3,4,self.pm2])
        self.assertTrue(ok,msg)
        execute_db("UPDATE project_members SET project_role='leader' WHERE project_id=%s AND user_id=%s",(self.pid,self.pm2))
        self.leader=self.client(2,'leader');self.admin=self.client(1,'admin');self.member=self.client(3,'member');self.other=self.client(self.pm2,'leader')
        self.before_count=query_db('SELECT COUNT(*) AS n FROM project_members WHERE project_id=%s',(self.pid,),one=True)['n']

    def task(self,**kwargs):
        from services.task_service import create_task
        ok,msg,tid=create_task(2,self.pid,kwargs.pop('title','Build Python API'),**kwargs)
        self.assertTrue(ok,msg);return tid

    def preview(self,**kwargs):
        return self.leader.post(f'/api/projects/{self.pid}/staffing-preview',json={'staffing_version':2,**kwargs})

    def test_01_count_five_and_all_candidates_before_member_selection(self):
        tid=self.task(estimated_hours=8)
        r=self.preview(task_id=tid,user_note='Tôi cần 5 người backend')
        self.assertEqual(r.status_code,200,r.get_json());d=r.get_json()
        self.assertEqual(d['requested_count'],5);self.assertEqual(len(d['recommendations']),5)
        self.assertTrue(set(self.extra)<=set(c['user_id'] for c in d['candidates']))
        self.assertTrue(all(not c['in_project'] for c in d['recommendations']))

    def test_02_recruitment_without_task_filters_skills_not_people(self):
        from services.member_profile_service import update_professional_profile
        update_professional_profile(self.extra[0],'React, frontend','100%',40)
        d=self.preview(user_note='tôi cần backend',purpose='recruitment',requested_count=5).get_json()
        self.assertIsNone(d['task']);self.assertEqual(len(d['recommendations']),5)
        excluded=next(c for c in d['candidates'] if c['user_id']==self.extra[0])
        self.assertFalse(excluded['eligible']);self.assertIn(self.extra[0],[c['user_id'] for c in d['candidates']])

    def test_03_count_validation_and_vietnamese_words(self):
        from services.staffing_service import parse_staffing_requirements
        self.assertEqual(parse_staffing_requirements('cần năm người backend')['requested_count'],5)
        for value in (0,101,True,'1.5',-1):
            self.assertEqual(self.preview(requested_count=value).status_code,400)
        self.assertEqual(self.preview(user_note='cần 101 người').status_code,400)

    def test_04_pages_cover_entire_pool_and_search_does_not_limit_ranking(self):
        first=self.preview(limit=3).get_json();ids=[]
        for offset in range(0,first['total_candidates'],3):
            ids.extend(c['user_id'] for c in self.preview(limit=3,offset=offset).get_json()['candidates'])
        self.assertEqual(len(ids),len(set(ids)));self.assertEqual(len(ids),first['total_candidates'])
        d=self.preview(user_note='cần 5 người backend',search='No such name').get_json()
        self.assertEqual(d['total_visible'],0);self.assertEqual(len(d['recommendations']),5)

    def test_05_global_load_deduplicates_and_never_leaks_private_task_text(self):
        from services.project_service import create_project
        from services.task_service import create_task
        from services.project_member_service import add_project_members
        ok,msg,pid=create_project(2,'Secret other project','',project_code=uuid4().hex[:10],initial_member_ids=[self.extra[0]])
        self.assertTrue(ok,msg)
        _,_,tid=create_task(2,pid,'DO NOT EXPOSE PRIVATE TASK TITLE',assignee_id=self.extra[0],estimated_hours=43,due_date='2020-01-01')
        add_project_members(2,self.pid,[self.extra[0]],use_profiles=True)
        d=self.preview(task_id=self.task(estimated_hours=6)).get_json()
        c=next(c for c in d['candidates'] if c['user_id']==self.extra[0])
        self.assertEqual(c['current_workload_hours'],43);self.assertEqual(c['overdue_task_count'],1)
        self.assertTrue(c['is_projected_overloaded']);self.assertNotIn('DO NOT EXPOSE',json.dumps(d))
        self.assertNotIn('task_id',c);self.assertNotIn('email',c);self.assertNotIn('password_hash',c)
        self.assertIsInstance(tid,int)

    def test_06_profile_ownership_validation_and_sync_revision(self):
        before=self.leader.get('/api/sync').get_json()['revision']
        r=self.member.put('/api/me/professional-profile',json={'user_id':self.extra[0],'skills':'Python owner only','availability':'50%','capacity_hours':20})
        self.assertEqual(r.status_code,200);self.assertEqual(r.get_json()['profile']['user_id'],3)
        self.assertEqual(r.get_json()['profile']['capacity_hours'],10)
        self.assertNotEqual(before,self.leader.get('/api/sync').get_json()['revision'])
        self.assertEqual(self.admin.get('/api/me/professional-profile').status_code,403)
        self.assertEqual(self.member.put('/api/me/professional-profile',json={'availability':'101%'}).status_code,400)

    def test_07_add_selected_uses_fresh_profile_and_does_not_assign(self):
        from services.member_profile_service import update_professional_profile
        from database.connection import query_db
        tid=self.task(estimated_hours=5)
        self.preview(task_id=tid,user_note='cần 5 người backend')
        self.assertEqual(query_db('SELECT COUNT(*) AS n FROM project_members WHERE project_id=%s',(self.pid,),one=True)['n'],self.before_count)
        update_professional_profile(self.extra[0],'Python latest','60%',20)
        r=self.leader.post(f'/api/projects/{self.pid}/members',json={'user_ids':self.extra[:2],'use_professional_profile':True})
        self.assertEqual(r.status_code,200,r.get_json());self.assertEqual(r.get_json()['added_count'],2)
        member=query_db('SELECT * FROM project_members WHERE project_id=%s AND user_id=%s',(self.pid,self.extra[0]),one=True)
        self.assertEqual((member['skills'],member['availability'],float(member['capacity_hours'])),('Python latest','60%',20))
        self.assertIsNone(query_db('SELECT assignee_id FROM tasks WHERE id=%s',(tid,),one=True)['assignee_id'])

    def test_08_locked_viewer_and_admin_are_not_candidates(self):
        from database.connection import execute_db
        execute_db("UPDATE users SET status='locked' WHERE id=%s",(self.extra[0],))
        execute_db("UPDATE project_members SET project_role='viewer' WHERE project_id=%s AND user_id=4",(self.pid,))
        ids={c['user_id'] for c in self.preview().get_json()['candidates']}
        self.assertFalse(ids&{1,4,self.extra[0]})
        self.assertEqual(self.member.post(f'/api/projects/{self.pid}/staffing-preview',json={}).status_code,403)
        outsider=self.client(self.extra[1],'member')
        self.assertEqual(outsider.post(f'/api/projects/{self.pid}/staffing-preview',json={}).status_code,403)

    def test_09_insufficient_skills_and_zero_capacity_explained(self):
        from services.member_profile_service import update_professional_profile
        update_professional_profile(self.extra[0],'Rust','0%',40)
        d=self.preview(user_note='cần 5 người Rust',purpose='recruitment').get_json()
        # Every other test member has Python skills; no invented Rust candidate.
        self.assertEqual(d['eligible_count'],0);self.assertEqual(d['missing_count'],5)
        self.assertEqual(d['recommendations'],[])

    def test_10_api_first_incorrect_three_normalized_to_five_and_saved(self):
        from database.connection import query_db
        tid=self.task(estimated_hours=6)
        raw='\n'.join(f'[User #{uid}] Lý do phù hợp' for uid in self.extra[:3])
        env={'AI_CONFIG_SOURCE':'process','AI_PROVIDER':'gemini','GEMINI_API_KEY':'qa_fake','AI_LOCAL_FALLBACK_ENABLED':'true','LOCAL_AI_MODEL_ENABLED':'false'}
        response=io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':raw}]}}]}).encode())
        with patch.dict(os.environ,env),patch('services.gemini_service.urllib.request.urlopen',return_value=response) as http:
            r=self.leader.post('/api/ai',json={'task_type':'assignment_suggestion','project_id':self.pid,'task_id':tid,'user_note':'cần 5 người backend','staffing_version':2})
        self.assertEqual(r.status_code,200,r.get_json());http.assert_called_once()
        d=r.get_json();self.assertEqual(d['status'],'draft');self.assertEqual(len(d['structured_result']['recommendations']),5)
        self.assertIn('gemini',d['engine']['used_providers'])
        self.assertTrue(d['structured_result']['count_normalized'])
        draft=self.leader.get(f"/api/ai/drafts/{d['draft_id']}").get_json()['draft']
        self.assertEqual(len(draft['structured_result']['recommendations']),5)
        self.assertEqual(query_db('SELECT COUNT(*) AS n FROM project_members WHERE project_id=%s',(self.pid,),one=True)['n'],self.before_count)

    def test_11_zero_eligible_saves_honest_draft_without_provider_call(self):
        with patch('services.ai_provider_service.AIProviderService.generate_response') as generate:
            r=self.leader.post('/api/ai',json={'task_type':'assignment_suggestion','project_id':self.pid,'user_note':'cần 5 người Swift','purpose':'recruitment','staffing_version':2})
        self.assertEqual(r.status_code,200,r.get_json());generate.assert_not_called()
        self.assertIn('Thiếu 5',r.get_json()['result']);self.assertEqual(r.get_json()['status'],'draft')

    def test_12_archive_rights_follow_actual_archiver_even_when_creator_differs(self):
        from services.project_service import archive_project
        self.assertTrue(archive_project(self.pm2,self.pid)[0])
        p=self.admin.get(f'/api/projects/{self.pid}/archive-details').get_json()['project']
        self.assertEqual((p['created_by'],p['archived_by']),(2,self.pm2));self.assertTrue(p['archived_at'])
        self.assertEqual(self.leader.get(f'/api/projects/{self.pid}/archive-details').status_code,403)
        self.assertEqual(self.leader.get(f'/api/projects/{self.pid}').status_code,404)
        self.assertEqual(self.leader.get(f'/api/projects/{self.pid}/members').status_code,403)
        self.assertEqual(self.leader.post(f'/api/projects/{self.pid}/restore').status_code,403)
        self.assertEqual(self.member.get(f'/api/projects/{self.pid}/archive-details').status_code,403)
        self.assertNotIn(self.pid,[p['id'] for p in self.leader.get('/api/projects?archived=true').get_json()['projects']])
        self.assertIn(self.pid,[p['id'] for p in self.other.get('/api/projects?archived=true').get_json()['projects']])
        self.assertEqual(self.other.get(f'/projects/{self.pid}/archived').status_code,200)
        self.assertEqual(self.other.post(f'/api/projects/{self.pid}/restore').status_code,200)

    def test_13_archived_detail_is_readonly_and_admin_restores_prior_status(self):
        from database.connection import execute_db
        tid=self.task(assignee_id=3,estimated_hours=4)
        execute_db("UPDATE projects SET status='completed' WHERE id=%s",(self.pid,))
        self.assertEqual(self.leader.delete(f'/api/projects/{self.pid}').status_code,200)
        self.assertEqual(self.admin.get(f'/api/projects/{self.pid}/archive-details').get_json()['tasks'][0]['id'],tid)
        self.assertEqual(self.leader.put(f'/api/tasks/{tid}/progress',json={'progress_percent':80}).status_code,409)
        self.assertEqual(self.admin.post(f'/api/projects/{self.pid}/restore').status_code,200)
        self.assertEqual(self.admin.get(f'/api/projects/{self.pid}').get_json()['project']['status'],'completed')

    def test_14_unknown_legacy_archiver_only_admin_and_service_enforces(self):
        from database.connection import execute_db
        from services.project_service import restore_project
        execute_db("UPDATE projects SET is_archived=TRUE,status='archived',archived_by=NULL,archived_at=NULL WHERE id=%s",(self.pid,))
        self.assertEqual(self.leader.get(f'/api/projects/{self.pid}/archive-details').status_code,403)
        self.assertFalse(restore_project(2,self.pid)[0]);self.assertTrue(restore_project(1,self.pid)[0])

    def test_15_member_moves_all_columns_and_sets_actual_percentage(self):
        tid=self.task(assignee_id=3)
        self.assertEqual(self.member.put(f'/api/tasks/{tid}/progress',json={'progress_percent':47}).status_code,200)
        for state,percent in [('in_progress',47),('todo',47),('review',47),('done',100),('todo',0)]:
            r=self.member.put(f'/api/tasks/{tid}/status',json={'status':state})
            self.assertEqual(r.status_code,200,r.get_json())
            t=self.leader.get(f'/api/tasks/{tid}').get_json()['task'];self.assertEqual((t['status'],t['progress_percent']),(state,percent))
        self.member.put(f'/api/tasks/{tid}/progress',json={'progress_percent':73})
        self.assertEqual(self.leader.get(f'/api/tasks/{tid}').get_json()['task']['progress_percent'],73)

    def test_16_supporter_allowed_other_member_denied_and_progress_bounds(self):
        tid=self.task(assignee_id=4,support_member_ids=[3])
        self.assertEqual(self.member.put(f'/api/tasks/{tid}/progress',json={'progress_percent':64}).status_code,200)
        for value in (-1,101,'NaN',True):self.assertEqual(self.member.put(f'/api/tasks/{tid}/progress',json={'progress_percent':value}).status_code,400)
        other=self.task(assignee_id=4)
        self.assertEqual(self.member.put(f'/api/tasks/{other}/status',json={'status':'done'}).status_code,403)

    def test_17_history_and_notifications_cannot_bypass_archive_actor_permission(self):
        from database.connection import execute_db
        from services.project_service import archive_project,restore_project
        from services.ai_history_service import save_ai_history
        save_ai_history(self.pid,2,'assignment_suggestion','qa','v2',[],'SECRET ARCHIVED HISTORY')
        notification_ids=[]
        for uid in (2,3,self.pm2,1):
            notification_ids.append(execute_db('''INSERT INTO notifications(user_id,project_id,event_type,title,message)
                VALUES (%s,%s,'task_assigned','SECRET ARCHIVED NOTICE','Private text')''',(uid,self.pid)))
        self.assertTrue(archive_project(self.pm2,self.pid)[0])
        self.assertEqual(self.leader.get(f'/api/ai/history?project_id={self.pid}').get_json()['history'],[])
        self.assertTrue(self.other.get(f'/api/ai/history?project_id={self.pid}').get_json()['history'])
        self.assertTrue(self.admin.get(f'/api/ai/history?project_id={self.pid}').get_json()['history'])
        for c,denied in ((self.leader,True),(self.member,True),(self.other,False),(self.admin,False)):
            notices=c.get('/api/notifications').get_json()['notifications']
            self.assertEqual(any(n['project_id']==self.pid for n in notices),not denied)
        self.assertTrue(restore_project(self.pm2,self.pid)[0])
        self.assertTrue(self.leader.get(f'/api/ai/history?project_id={self.pid}').get_json()['history'])


class TestArchiveMigration(unittest.TestCase):
    def test_actor_backfill_is_evidenced_idempotent_and_never_creator_guess(self):
        from database.archive_schema import ensure_archive_schema
        db=sqlite3.connect(':memory:')
        db.executescript('''CREATE TABLE projects(id INTEGER PRIMARY KEY,is_archived INTEGER);
            CREATE TABLE users(id INTEGER PRIMARY KEY); INSERT INTO users VALUES(7);
            CREATE TABLE audit_logs(id INTEGER PRIMARY KEY,user_id INTEGER,target_type TEXT,target_id INTEGER,action TEXT,created_at TEXT);
            INSERT INTO projects VALUES(1,1),(2,1),(3,0);
            INSERT INTO audit_logs VALUES(1,7,'PROJECT',1,'ARCHIVE_PROJECT','2026-01-01'),(2,7,'PROJECT',1,'ARCHIVE_PROJECT','2026-02-01');''')
        ensure_archive_schema(db,'sqlite');ensure_archive_schema(db,'sqlite')
        self.assertEqual(db.execute('SELECT archived_by,archived_at FROM projects WHERE id=1').fetchone(),(7,'2026-02-01'))
        self.assertEqual(db.execute('SELECT archived_by,archived_at FROM projects WHERE id=2').fetchone(),(None,None))
        db.close()
