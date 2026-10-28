"""Two real Gemini checks with synthetic staffing data in disposable SQLite."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    values=dotenv_values(ROOT/'.env')
    key=values.get('GEMINI_API_KEY')
    assert key,'Gemini key is required; never print it.'
    os.environ.update(AI_CONFIG_SOURCE='process',AI_PROVIDER='gemini',GEMINI_API_KEY=key,
        GEMINI_MODEL=values.get('GEMINI_MODEL') or 'gemini-3.6-flash',AI_LOCAL_FALLBACK_ENABLED='true',
        LOCAL_AI_MODEL_ENABLED='false',SMTP_ENABLED='false',DEADLINE_WORKER_ENABLED='false')
    records=[]
    with tempfile.TemporaryDirectory() as directory:
        from database import connection,init_db
        connection._SQLITE_PATH=init_db.SQLITE_PATH=str(Path(directory)/'live.sqlite3');connection.set_engine_mode('sqlite')
        with contextlib.redirect_stdout(io.StringIO()):init_db.init_sqlite_fallback()
        from app import app
        from database.connection import execute_db
        from services.project_service import create_project
        from services.task_service import create_task
        from services.member_profile_service import update_professional_profile
        _,_,pid=create_project(2,'Dự án QA tổng hợp','','',project_code='QA-REAL-STAFF')
        _,_,tid=create_task(2,pid,'QA Backend Flask',estimated_hours=6,labels='Python Flask')
        for i in range(8):
            uid=execute_db("INSERT INTO users(username,email,password_hash,full_name,role,status) VALUES (%s,%s,'qa',%s,'member','active')",(f'qa_live_{i}',f'qa_live_{i}@example.invalid',f'Ứng viên QA {i}'))
            update_professional_profile(uid,'Python, Flask, backend','100%',40)
        client=app.test_client()
        with client.session_transaction() as session:session.update(user_id=2,role='leader')
        for purpose in ('assignment','recruitment'):
            r=client.post('/api/ai',json={'task_type':'assignment_suggestion','staffing_version':2,'project_id':pid,
                'task_id':tid if purpose=='assignment' else None,'purpose':purpose,'candidate_scope':'system','user_note':'Tôi cần 5 người backend'})
            data=r.get_json();structured=data.get('structured_result') or {};engine=data.get('engine') or {}
            count=len(structured.get('recommendations',[]));success=r.status_code==200 and count==5
            records.append({'purpose':purpose,'passed':success,'http':r.status_code,'requested_count':5,'actual_count':count,
                'status':data.get('status'),'engine':engine,'real_api_succeeded':'gemini' in engine.get('used_providers',[]),
                'error_code':data.get('error_code')})
    result={'database':'disposable SQLite','data':'synthetic QA profiles only','real_api_calls':True,'real_emails':False,
        'success':all(r['passed'] for r in records),'records':records}
    (ROOT/'docs/qa-staffing-gemini-live.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'live_staffing_checks':len(records),'passed':sum(r['passed'] for r in records),'gemini_succeeded':sum(r['real_api_succeeded'] for r in records)}))
    return 0 if result['success'] else 1

if __name__=='__main__':raise SystemExit(main())
