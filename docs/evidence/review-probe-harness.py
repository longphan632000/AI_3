"""Reproduce review observations on SQLite only; never patch the application."""
import contextlib
from datetime import datetime,timezone,timedelta
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(r'D:\UNG DUNG AL_NAM3\Code Chuan');WORK=Path(__file__).parent/'skill-docs';sys.path.insert(0,str(ROOT))
os.environ.update(AI_CONFIG_SOURCE='process',AI_PROVIDER='gemini',GEMINI_API_KEY='qa_fake',AI_LOCAL_FALLBACK_ENABLED='false',LOCAL_AI_MODEL_ENABLED='false',SMTP_ENABLED='false',DEADLINE_WORKER_ENABLED='false')

def main():
    records=[]
    with tempfile.TemporaryDirectory() as directory:
        from database import connection,init_db
        connection._SQLITE_PATH=init_db.SQLITE_PATH=str(Path(directory)/'review.sqlite3');connection.set_engine_mode('sqlite')
        with contextlib.redirect_stdout(io.StringIO()):init_db.init_sqlite_fallback()
        from app import app
        from database.connection import execute_db,query_db
        from services.project_service import create_project
        from services.task_service import create_task
        from services.member_profile_service import update_professional_profile
        _,_,pid=create_project(2,'Dự án QA hồ sơ','',project_code='SKILL-PROBE')
        _,_,tid=create_task(2,pid,'Backend QA',estimated_hours=6,labels='backend')
        ids=[]
        for i in range(5):
            uid=execute_db("INSERT INTO users(username,email,password_hash,full_name,role,status) VALUES (%s,%s,'qa',%s,'member','active')",(f'profile_{i}',f'profile_{i}@example.invalid',f'Ứng viên QA {i}'))
            ids.append(uid);update_professional_profile(uid,'Python Flask backend','100%',40)
        leader=app.test_client()
        with leader.session_transaction() as session:session.update(user_id=2,role='leader')
        with patch('services.ai_provider_service.AIProviderService.generate_response',return_value='\n'.join(f'[User #{uid}]' for uid in ids)):
            generated=leader.post('/api/ai',json={'task_type':'assignment_suggestion','project_id':pid,'task_id':tid,'staffing_version':2,'requested_count':5,'user_note':'Cần 5 người backend'}).get_json()
        assert generated['success'] and generated['status']=='draft' and len(generated['structured_result']['recommendations'])==5
        saved=leader.put(f"/api/ai/drafts/{generated['draft_id']}",json={'version':1,'draft_content':generated['result']})
        after=leader.get(f"/api/ai/drafts/{generated['draft_id']}").get_json()['draft']
        records.append({'id':'PROBE-01','issue':'REQ-11','expected':'Saving unchanged valid five-candidate draft preserves valid draft state',
            'observed':{'http':saved.status_code,'before':generated['status'],'after':after['status'],'warnings':after['warnings']},
            'defect_reproduced':after['status']=='needs_verification','application_changed':False})
        admin=app.test_client()
        with admin.session_transaction() as session:session.update(user_id=1,role='admin')
        comment=admin.post(f'/api/tasks/{tid}/comments',json={'content':'QA policy observation'})
        note=admin.post(f'/api/projects/{pid}/meeting-notes',json={'title':'QA note','meeting_date':'2026-10-28','content':'QA source'})
        attachment=admin.post(f'/api/tasks/{tid}/attachments',json={'name':'QA link','url':'https://example.invalid/qa'})
        records.append({'id':'PROBE-02','issue':'REQ-02','expected':'Observe actual Admin collaboration policy; no authorization decision is fabricated',
            'observed':{'comment_http':comment.status_code,'note_http':note.status_code,'attachment_http':attachment.status_code},'defect_reproduced':False,'application_changed':False})
        _,_,empty=create_task(2,pid,'Thiếu dữ liệu QA',estimated_hours=0)
        row=query_db('SELECT due_date,estimated_hours FROM tasks WHERE id=%s',(empty,),one=True)
        records.append({'id':'PROBE-03','issue':'REQ-04','expected':'Observe current nullable date and zero-estimate rule',
            'observed':dict(row),'defect_reproduced':False,'application_changed':False})
    result={'timestamp':datetime.now(timezone(timedelta(hours=7))).isoformat(),'database':'disposable SQLite','real_api_calls':False,'real_emails':False,'records':records,'completed':True}
    (WORK/'review-probes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({'probes_completed':len(records),'defects_reproduced':sum(r['defect_reproduced'] for r in records),'live_database_writes':False}))

if __name__=='__main__':main()
