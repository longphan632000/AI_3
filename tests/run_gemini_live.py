"""Explicit opt-in live Gemini smoke check; synthetic data in disposable SQLite only.

Reads the user's configured Gemini key. Sends three small synthetic AI requests,
never reads project data from the application MySQL database, never confirms drafts.
Not discovered by unittest; run only when real Gemini testing is authorized.
"""
from datetime import date, timedelta, datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['SMTP_ENABLED']='false'
os.environ['DEADLINE_WORKER_ENABLED']='false'


def main():
    from database import connection, init_db
    from services.ai_provider_service import AIProviderService
    provider=AIProviderService()
    if provider.provider_name!='gemini' or not provider.provider.configured:
        raise SystemExit('Live check requires configured Gemini; no request sent.')
    service=provider.provider
    records=[]
    report={'timestamp':datetime.now(timezone.utc).isoformat(),'provider':'gemini',
            'model':service.model,'meeting_model':service.meeting_model,
            'database':'disposable SQLite; application MySQL never used',
            'input':'synthetic QA data only','records':records}
    ok,message=service.probe_model()
    report['metadata_probe']={'passed':ok,'code':service.last_probe_error_code,'message':message}
    print('Metadata:',ok,service.last_probe_error_code,flush=True)
    with tempfile.TemporaryDirectory() as directory:
        connection._USE_MYSQL=False
        connection._SQLITE_PATH=init_db.SQLITE_PATH=str(Path(directory)/'live_gemini.sqlite3')
        init_db.init_sqlite_fallback()
        from app import app
        from database.connection import query_db,execute_db
        from services.project_service import create_project
        from services.project_member_service import update_member_capacity
        from services.task_service import create_task,update_task_status
        app.config.update(TESTING=False,PROPAGATE_EXCEPTIONS=False)
        for uid in range(1,6):
            execute_db('UPDATE users SET full_name=%s,username=%s,email=%s WHERE id=%s',
                       (f'QA User {uid}',f'qa_user_{uid}',f'qa{uid}@example.test',uid))
        success,_,pid=create_project(2,'Synthetic Gemini QA','Temporary QA fixture',
                                     initial_member_ids=[3,4],project_code='QA-LIVE-GEMINI')
        assert success
        update_member_capacity(2,pid,3,'Python, testing','100%',40)
        update_member_capacity(2,pid,4,'Documentation, frontend','80%',32)
        success,_,done=create_task(2,pid,'Verify test data',assignee_id=3,estimated_hours=1)
        assert success
        assert update_task_status(2,done,'done')[0]
        success,_,tid=create_task(2,pid,'Write Python unit tests',description='Test login validation using synthetic data.',estimated_hours=2,labels='Python, testing')
        assert success
        leader=app.test_client();member=app.test_client()
        for client,uid,role in [(leader,2,'leader'),(member,3,'member')]:
            with client.session_transaction() as session:session.update(user_id=uid,role=role)
        today=date.today()
        cases=[('weekly_summary',leader,{'week_start':(today-timedelta(days=6)).isoformat(),'week_end':today.isoformat()}),
               ('meeting_minutes',member,{'raw_notes':'Cuộc họp kiểm thử hệ thống.\nQA User 3 kiểm tra chức năng đăng nhập.\nNhóm thống nhất rà soát kết quả kiểm thử trước khi phát hành.'}),
               ('assignment_suggestion',leader,{'task_id':tid})]
        for kind,client,fields in cases:
            started=time.monotonic()
            if not ok:
                record={'task_type':kind,'passed':False,'code':service.last_probe_error_code,'skipped':'metadata connection failed'}
            else:
                response=client.post('/api/ai',json={'task_type':kind,'project_id':pid,**fields})
                data=response.get_json() or {}
                draft=None
                if data.get('draft_id'):
                    draft=query_db('SELECT status FROM ai_drafts WHERE id=%s',(data['draft_id'],),one=True)
                record={'task_type':kind,'http':response.status_code,
                        'passed':response.status_code==200 and data.get('success') is True and bool(draft),
                        'status':data.get('status'),'error_code':data.get('error_code'),
                        'message':data.get('error'),'warnings':data.get('warnings',[]),
                        'result_chars':len(data.get('result','')),'draft_saved':bool(draft),
                        'seconds':round(time.monotonic()-started,3)}
            records.append(record)
            print(json.dumps({k:record.get(k) for k in ['task_type','http','passed','status','error_code','seconds']},ensure_ascii=True),flush=True)
        assignee=query_db('SELECT assignee_id FROM tasks WHERE id=%s',(tid,),one=True)['assignee_id']
        official=query_db('SELECT COUNT(*) AS total FROM meeting_minutes WHERE project_id=%s',(pid,),one=True)['total']
        confirmed=query_db("SELECT COUNT(*) AS total FROM ai_drafts WHERE project_id=%s AND status='confirmed'",(pid,),one=True)['total']
        report['safety']={'task_still_unassigned':assignee is None,'official_meeting_count':official,'confirmed_draft_count':confirmed}
        assert assignee is None and official==0 and confirmed==0
    report['success']=ok and all(record['passed'] for record in records)
    output=ROOT/'docs/qa-gemini-live-results.json'
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Live Gemini result:',report['success'],'written to docs/qa-gemini-live-results.json',flush=True)
    return 0 if report['success'] else 1


if __name__=='__main__':raise SystemExit(main())
