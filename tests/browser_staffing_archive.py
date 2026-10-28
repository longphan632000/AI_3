"""End-to-end current requests using Edge, separate clients and disposable SQLite."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scratch/qa_audit_2026_10_27/browser_deps'))
os.environ.update(AI_CONFIG_SOURCE='process',AI_PROVIDER='gemini',GEMINI_API_KEY='qa_fake',GEMINI_MODEL='gemini-3.6-flash',
    AI_LOCAL_FALLBACK_ENABLED='false',LOCAL_AI_MODEL_ENABLED='false',SMTP_ENABLED='false',DEADLINE_WORKER_ENABLED='false')
from playwright.sync_api import sync_playwright,expect


def main():
    records=[];errors=[];prompts=[];shots=ROOT/'docs/qa-staffing';shots.mkdir(exist_ok=True)
    def record(name,**details):records.append({'name':name,'passed':True,'details':details})
    with tempfile.TemporaryDirectory() as directory:
        from database import connection,init_db
        connection._SQLITE_PATH=init_db.SQLITE_PATH=str(Path(directory)/'browser.sqlite3');connection.set_engine_mode('sqlite');init_db.init_sqlite_fallback()
        from app import app
        from database.connection import query_db,execute_db
        from services.project_service import create_project,archive_project
        from services.task_service import create_task
        from services.member_profile_service import update_professional_profile
        password=query_db('SELECT password_hash FROM users WHERE id=3',one=True)['password_hash']
        ids=[]
        for i in range(15):
            uid=execute_db("INSERT INTO users(username,email,password_hash,full_name,role,status) VALUES (%s,%s,%s,%s,'member','active')",(f'candidate{i}',f'candidate{i}@example.invalid',password,f'Ứng viên {i:02}'))
            ids.append(uid);update_professional_profile(uid,'Python, Flask, backend' if i<7 else 'React, frontend','100%',40)
        pm2=execute_db("INSERT INTO users(username,email,password_hash,full_name,role,status) VALUES ('otherpm','otherpm@example.invalid',%s,'PM khác','leader','active')",(password,))
        _,_,pid=create_project(2,'Dự án kiểm thử nhân sự','Nội dung dự án thử nghiệm',project_code='STAFF-UI',initial_member_ids=[3,4,pm2])
        execute_db("UPDATE project_members SET project_role='leader' WHERE project_id=%s AND user_id=%s",(pid,pm2))
        _,_,tid=create_task(2,pid,'Python API cần phân công',estimated_hours=8,labels='Python, Flask')
        _,_,own=create_task(2,pid,'Nhiệm vụ thực tế của My',assignee_id=3,estimated_hours=5)
        _,_,archived=create_project(2,'Dự án do PM khác lưu trữ','Mô tả cần bảo vệ',project_code='OTHER-ARCH',initial_member_ids=[pm2])
        execute_db("UPDATE project_members SET project_role='leader' WHERE project_id=%s AND user_id=%s",(archived,pm2));archive_project(pm2,archived)
        def gemini(request,timeout=None):
            prompts.append(json.loads(request.data)['contents'][0]['parts'][0]['text'])
            text=f'[Task #{tid}]\n'+'\n'.join(f'[User #{uid}] Lý do phù hợp' for uid in ids[:3])
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':text}]}}]}).encode())
        from werkzeug.serving import make_server
        server=make_server('127.0.0.1',0,app,threaded=True);base=f'http://127.0.0.1:{server.server_port}'
        threading.Thread(target=server.serve_forever,daemon=True).start()
        with patch('services.gemini_service.urllib.request.urlopen',side_effect=gemini),sync_playwright() as pw:
            browser=pw.chromium.launch(channel='msedge',headless=True);contexts=[]
            def login(username,width=1440,height=1000,touch=False):
                ctx=browser.new_context(viewport={'width':width,'height':height},locale='vi-VN',has_touch=touch,is_mobile=touch);contexts.append(ctx)
                ctx.add_init_script(f"localStorage.setItem('active_project_id','{pid}')")
                ctx.route('https://fonts.googleapis.com/**',lambda r:r.abort());ctx.route('https://fonts.gstatic.com/**',lambda r:r.abort())
                page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
                page.goto(base+'/login');page.locator('#login-username').fill(username);page.locator('#login-password').fill('Password123!');page.locator('#btn-submit-login').click()
                page.wait_for_url('**/'+('admin' if username=='admin' else 'dashboard'));page.wait_for_function('currentUser!==null&&currentProjectId!==null')
                return ctx,page
            def assignment(page):
                page.goto(base+'/ai-assistant');expect(page.locator('#btn-generate-ai')).to_be_enabled();page.locator('[data-mode="assignment_suggestion"]').click()
                expect(page.locator('#staffing-candidates-body tr[data-candidate-id]')).to_have_count(12)
            try:
                lc,leader=login('leader_long');assignment(leader)
                expect(leader.locator('#staffing-pool-summary')).to_contain_text('19 người')
                leader.locator('#staffing-next').click();expect(leader.locator('#staffing-page')).to_have_text('Trang 2/2')
                expect(leader.locator('#staffing-candidates-body tr[data-candidate-id]')).to_have_count(7)
                record('All 19 active candidates visible across pages before selecting a member')
                leader.locator('#staffing-prev').click();leader.locator('#ai-task-select').select_option(str(tid))
                leader.locator('#ai-user-prompt').fill('Tôi cần 5 người backend')
                expect(leader.locator('#ai-requested-count')).to_have_value('5');expect(leader.locator('#staffing-pool-summary')).to_contain_text('Đủ điều kiện: 8')
                with leader.expect_response(lambda r:r.url.endswith('/api/ai') and r.request.method=='POST') as response:leader.locator('#btn-generate-ai').click()
                assert response.value.status==200,response.value.text()
                expect(leader.locator('.staffing-recommendation')).to_have_count(5)
                assert '1 đến 3' not in prompts[-1] and '5' in prompts[-1]
                assert lc.request.get(base+f'/api/tasks/{tid}').json()['task']['assignee_id'] is None
                leader.evaluate('window.scrollTo(0,0)');leader.screenshot(path=str(shots/'five-backend-candidates-desktop.png'),full_page=True)
                record('Five requested in natural language; mocked API returns three; five verified suggestions shown without assignment')
                leader.locator('#ai-task-select').select_option('');leader.locator('#ai-staffing-purpose').select_option('recruitment')
                leader.locator('#ai-user-prompt').fill('tôi cần backend')
                expect(leader.locator('#staffing-task-picker')).to_be_hidden()
                leader.locator('#btn-generate-ai').click();expect(leader.locator('.staffing-recommendation')).to_have_count(5)
                leader.locator('[data-recommend-add]').first.click();expect(leader.locator('#staffing-add-selected')).to_be_enabled()
                before=lc.request.get(base+f'/api/projects/{pid}/members').json()['members'];assert len(before)==4
                selected=int(leader.locator('[data-recommend-add]').first.get_attribute('data-recommend-add'))
                leader.locator('#staffing-add-selected').click()
                expect(leader.locator('#staffing-add-selected')).to_have_text('Thêm người đã chọn (0)')
                after=lc.request.get(base+f'/api/projects/{pid}/members').json()['members'];assert len(after)==5
                added=next(m for m in after if m['user_id']==selected);assert added['skills']=='Python, Flask, backend'
                record('Recruitment works without task; selection and explicit add copy real profile without automatic task assignment')
                leader.locator('#ai-staffing-purpose').select_option('assignment');expect(leader.locator('#staffing-task-picker')).to_be_visible()
                leader.locator('#ai-task-select').select_option(str(tid));leader.locator('#ai-candidate-scope').select_option('project')
                row=leader.locator(f'tr[data-candidate-id="{selected}"]');expect(row.get_by_role('button',name='Chọn phân công')).to_be_visible()
                row.get_by_role('button',name='Chọn phân công').click();leader.wait_for_url('**/kanban?**')
                expect(leader.locator('#modal-create-task')).to_be_visible();expect(leader.locator('#new-task-assignee')).to_have_value(str(selected))
                assert lc.request.get(base+f'/api/tasks/{tid}').json()['task']['assignee_id'] is None
                leader.locator('#modal-create-task').get_by_role('button',name='Lưu thay đổi').click()
                expect(leader.locator('#modal-create-task')).not_to_be_visible()
                assert lc.request.get(base+f'/api/tasks/{tid}').json()['task']['assignee_id']==selected
                record('Choose candidate opens normal task editor; only Save assigns')
                mc,member=login('member_my');member.goto(base+'/kanban')
                card=member.locator(f'.task-card[data-task-id="{own}"]');expect(card).to_be_visible()
                member.locator(f'#task-progress-{own}').fill('57');card.get_by_role('button',name='Lưu %',exact=True).click()
                expect(card.locator('[role=progressbar]')).to_have_attribute('aria-valuenow','57')
                member.locator(f'#task-progress-{own}').fill('87');card.locator('.task-status-select').select_option('done')
                assert mc.request.get(base+f'/api/tasks/{own}').json()['task']['progress_percent']==57
                card.get_by_role('button',name='Hủy',exact=True).click();expect(member.locator(f'#task-progress-{own}')).to_have_value('57')
                card.locator('.task-status-select').select_option('done');expect(card.locator('[role=progressbar]')).to_have_attribute('aria-valuenow','100')
                card.locator('.task-status-select').select_option('todo');expect(card.locator('[role=progressbar]')).to_have_attribute('aria-valuenow','0')
                record('Inline percent save/cancel; pending edit protected; Done 100 and reopened Todo 0')
                member.goto(base+'/team');member.get_by_role('button',name='Cập nhật hồ sơ chung để tham gia dự án mới').click()
                member.locator('#professional-skills').fill('Backend Python PROFILE SYNC');member.locator('#professional-availability').fill('70');member.locator('#professional-capacity').fill('30')
                member.locator('#modal-professional-profile button[type=submit]').click();expect(member.locator('#modal-professional-profile')).not_to_be_visible()
                assignment(leader);leader.locator('#staffing-search').fill('member_my');expect(leader.locator('#staffing-candidates-body')).to_contain_text('PROFILE SYNC')
                mc.request.put(base+'/api/me/professional-profile',data={'skills':'Backend Python UPDATED OTHER DEVICE','availability':'60%','capacity_hours':30})
                leader.bring_to_front();expect(leader.locator('#staffing-candidates-body')).to_contain_text('UPDATED OTHER DEVICE',timeout=12000)
                record('Self professional profile updates and reaches PM on another browser automatically')
                ac,admin=login('admin');admin.goto(base+f'/projects/{archived}/archived')
                expect(admin.locator('#archive-name')).to_have_text('Dự án do PM khác lưu trữ');expect(admin.locator('#archive-metadata')).to_contain_text('PM khác')
                admin.evaluate('window.scrollTo(0,0)');admin.screenshot(path=str(shots/'archive-details-admin.png'),full_page=True)
                leader.goto(base+'/dashboard');leader.get_by_role('button',name='Dự án đã lưu trữ',exact=True).click()
                expect(leader.locator('#archived-project-list')).not_to_contain_text('Dự án do PM khác lưu trữ')
                assert lc.request.get(base+f'/api/projects/{archived}/archive-details').status==403
                assert lc.request.post(base+f'/api/projects/{archived}/restore').status==403
                oc,other=login('otherpm');other.goto(base+f'/projects/{archived}/archived');expect(other.locator('#restore-archived-project')).to_be_visible()
                record('Admin sees all archive details; creator PM denied when different PM archived; actual archiver allowed')
                other.locator('#restore-archived-project').click();other.wait_for_url('**/dashboard')
                admin.bring_to_front();expect(admin.locator('#archive-state')).to_contain_text('đã được khôi phục',timeout=12000)
                record('Actual PM restores project; admin detail updates on separate client')
                for label,w,h in [('desktop',1920,1080),('laptop',1366,768),('tablet',768,1024),('phone',390,844),('small-phone',360,740)]:
                    ctx,page=login('leader_long',w,h,w<800);assignment(page)
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1')
                    expect(page.locator('#ai-requested-count')).to_be_visible()
                    page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(shots/f'staffing-{label}.png'),full_page=True)
                    page.goto(base+f'/projects/{archived}/archived') # now active: current project membership still authorizes read.
                    # Creator belongs to restored project; archive-detail remains readable.
                    expect(page.locator('#archive-name')).to_have_text('Dự án do PM khác lưu trữ')
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1')
                    record('Responsive staffing and detail '+label,width=w,touch=w<800)
                assert not errors,errors;record('No browser JavaScript errors',errors=errors)
            except Exception as error:
                records.append({'name':'Staffing acceptance','passed':False,'error':str(error)})
                for i,ctx in enumerate(contexts):
                    if ctx.pages:
                        try:ctx.pages[0].screenshot(path=str(shots/f'failure-{i}.png'),full_page=True)
                        except Exception:pass
                raise
            finally:
                (ROOT/'docs/qa-staffing-results.json').write_text(json.dumps({'database':'disposable SQLite','browser':'Microsoft Edge headless','real_api_calls':False,'real_emails':False,'records':records,'runtime_errors':errors,'success':bool(records) and all(r['passed'] for r in records)},ensure_ascii=False,indent=2),encoding='utf-8')
                browser.close();server.shutdown()
    print('Staffing browser checks:',len(records),'passed:',sum(r['passed'] for r in records))


if __name__=='__main__':main()
