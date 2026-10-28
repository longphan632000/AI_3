"""Edge acceptance checks: member actions, charts, profile, capacity and sync.

Disposable SQLite and mocked Gemini transport; no real emails or API keys.
"""
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scratch/qa_audit_2026_10_27/browser_deps'))
os.environ.update(AI_CONFIG_SOURCE='process', AI_PROVIDER='gemini', GEMINI_API_KEY='qa_fake_key',
                  GEMINI_MODEL='gemini-3.6-flash', GEMINI_MEETING_MODEL='gemini-3.6-flash',
                  AI_LOCAL_FALLBACK_ENABLED='false', LOCAL_AI_MODEL_ENABLED='false',
                  SMTP_ENABLED='false', DEADLINE_WORKER_ENABLED='false')
from playwright.sync_api import sync_playwright, expect


def main():
    records, errors, prompts = [], [], []
    out = ROOT / 'logstest'
    shots = out / 'qa-workspace'
    shots.mkdir(exist_ok=True)
    def record(name, **details):
        records.append({'name':name, 'passed':True, 'details':details})
    with tempfile.TemporaryDirectory() as directory:
        from database import connection, init_db
        connection._SQLITE_PATH = init_db.SQLITE_PATH = str(Path(directory) / 'workspace.sqlite3')
        connection.set_engine_mode('sqlite')
        init_db.init_sqlite_fallback()
        from app import app
        from services.project_service import create_project
        from services.task_service import create_task, update_task_status, update_task_progress
        from services.sprint_service import create_sprint
        ok, message, pid = create_project(2,'Đội ngũ phát triển Atlas','',project_code='WORKSPACE-UI',initial_member_ids=[3,4])
        assert ok, message
        _, _, sid = create_sprint(2,pid,'Sprint kiểm thử giao diện','','2026-10-01','2026-10-31','Hoàn tất kiểm thử')
        _, _, primary = create_task(2,pid,'Python API do My phụ trách',assignee_id=3,estimated_hours=4,sprint_id=sid)
        _, _, support = create_task(2,pid,'Kiểm thử tích hợp My hỗ trợ',assignee_id=2,support_member_ids=[3],estimated_hours=8,sprint_id=sid)
        update_task_status(2,support,'todo')
        _, _, other = create_task(2,pid,'Nhiệm vụ riêng của Khánh',assignee_id=4,estimated_hours=2)
        _, _, finished = create_task(2,pid,'Tài liệu đã hoàn thành',assignee_id=4,estimated_hours=3)
        update_task_progress(2,finished,100)
        _, _, ai_task = create_task(2,pid,'Xây dựng API Flask cần phân công',description='Triển khai Python Flask API và kiểm thử.',estimated_hours=6,labels='Python, Flask',sprint_id=sid)

        def gemini_http(request, timeout=None):
            payload = json.loads(request.data)
            prompts.append(payload['contents'][0]['parts'][0]['text'])
            from services.project_data_retriever import retrieve_ai_data
            from services.local_brain_service import LocalBrainService
            req = {'task_type':'assignment_suggestion','project_id':pid,'task_id':ai_task,'requester_id':2}
            data, _ = retrieve_ai_data(req)
            text = LocalBrainService(req,data).assignment_suggestion()
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':text}]}}]}).encode('utf-8'))

        from werkzeug.serving import make_server
        server = make_server('127.0.0.1',0,app,threaded=True)
        base = f'http://127.0.0.1:{server.server_port}'
        threading.Thread(target=server.serve_forever,daemon=True).start()
        with patch('services.gemini_service.urllib.request.urlopen',side_effect=gemini_http), sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge',headless=True)
            contexts = []
            def login(username, width=1366, height=900, touch=False):
                ctx = browser.new_context(viewport={'width':width,'height':height},locale='vi-VN',has_touch=touch,is_mobile=touch)
                contexts.append(ctx)
                ctx.add_init_script(f"localStorage.setItem('active_project_id','{pid}')")
                ctx.route('https://fonts.googleapis.com/**',lambda route:route.abort())
                ctx.route('https://fonts.gstatic.com/**',lambda route:route.abort())
                page=ctx.new_page()
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(base+'/login')
                page.locator('#login-username').fill(username)
                page.locator('#login-password').fill('Password123!')
                page.locator('#btn-submit-login').click()
                page.wait_for_url('**/'+('admin' if username=='admin' else 'dashboard'))
                page.wait_for_function('currentUser !== null && currentProjectId !== null')
                return ctx,page
            def task_card(page, tid):
                return page.locator(f'.task-card[data-task-id="{tid}"]')
            def api_task(ctx, tid):
                return ctx.request.get(base+f'/api/tasks/{tid}').json()['task']
            def open_kanban(page):
                page.goto(base+'/kanban')
                expect(task_card(page,primary)).to_be_visible()
            def edit_capacity(page, skills, availability, capacity):
                modal=page.locator('#modal-member-capacity')
                expect(modal).to_be_visible()
                modal.locator('#member-edit-skills').fill(skills)
                modal.locator('#member-edit-availability').fill(str(availability))
                modal.locator('#member-edit-capacity').fill(str(capacity))
                with page.expect_response(lambda r:'/capacity' in r.url and r.request.method=='PUT') as response:
                    modal.get_by_role('button',name='Lưu thay đổi',exact=True).click()
                assert response.value.status==200,response.value.text()
                expect(modal).not_to_be_visible()
            try:
                member_ctx,member=login('member_my')
                open_kanban(member)
                expect(task_card(member,primary)).to_have_attribute('draggable','true')
                expect(task_card(member,support)).to_have_attribute('draggable','true')
                expect(task_card(member,other)).to_have_attribute('draggable','false')
                expect(task_card(member,other).locator('.task-progress-edit')).to_have_count(0)
                record('Server permissions shown consistently for assignee, supporter and read-only tasks')
                member.bring_to_front()
                member.evaluate("window.qaDragEvents=[]; for(const name of ['dragstart','dragover','drop','dragend'])document.addEventListener(name,event=>{if(window.qaDragEvents.length<40)window.qaDragEvents.push({type:event.type,target:event.target.tagName,task:event.target.closest('.task-card')?.dataset.taskId,column:event.target.closest('.kanban-column')?.dataset.status,active:window.taskDragActive});})")

                with member.expect_response(lambda r:r.url.endswith(f'/tasks/{primary}/status') and r.request.method=='PUT',timeout=10000) as dragged:
                    source=task_card(member,primary).locator('.task-title')
                    source.evaluate('el=>el.scrollIntoView({block:"center",inline:"nearest"})')
                    start=source.bounding_box()
                    target=member.locator('.kanban-column[data-status="todo"]').bounding_box()
                    sx,sy=start['x']+start['width']/2,start['y']+start['height']/2
                    header=member.locator('.app-header').bounding_box()
                    tx,ty=target['x']+100,max(target['y'],header['y']+header['height'])+24
                    member.mouse.move(sx,sy);member.mouse.down()
                    member.mouse.move(sx+6,sy+6,steps=3)
                    member.mouse.move(tx,ty,steps=15)
                    member.mouse.move(tx+1,ty+1)
                    member.mouse.up()
                assert dragged.value.status==200
                expect(member.locator(f'#col-body-todo .task-card[data-task-id="{primary}"]')).to_be_visible()
                record('Member moves assigned task with native drag and drop',http=200,status='todo')

                leader_ctx,leader=login('leader_long')
                leader.goto(base+'/reports')
                expect(leader.locator('#report-total')).to_have_text('5')
                task_card(member,primary).locator('.task-progress-edit').click()
                member.locator('#detail-progress').fill('45')
                member.get_by_role('button',name='Lưu tiến độ',exact=True).click()
                expect(member.locator('#detail-progress')).to_have_value('45')
                member.locator('#modal-task-detail .modal-header .btn-icon').click()
                expect(task_card(member,primary).locator('[role="progressbar"]')).to_have_attribute('aria-valuenow','45')
                leader.bring_to_front()
                expected=leader_ctx.request.get(base+f'/api/projects/{pid}/report').json()['metrics']['average_progress']
                expect(leader.locator('#report-average')).to_have_text(f'{expected:g}%',timeout=12000)
                record('Member saves actual progress; PM report updates automatically',progress=45,average=expected)

                task_card(member,support).locator('.task-status-select').select_option('in_progress')
                expect(member.locator(f'#col-body-in_progress .task-card[data-task-id="{support}"]')).to_be_visible()
                task_card(member,support).locator('.task-progress-edit').click()
                member.locator('#detail-progress').fill('60')
                with member.expect_response(lambda r:r.url.endswith(f'/tasks/{support}/progress') and r.request.method=='PUT') as saved:
                    member.get_by_role('button',name='Lưu tiến độ',exact=True).click()
                assert saved.value.status==200
                expect(member.locator('#detail-progress')).to_have_value('60')
                member.locator('#modal-task-detail .modal-header .btn-icon').click()
                assert api_task(member_ctx,support)['progress_percent']==60
                record('Supporter changes status and actual progress through visible controls')

                task_card(member,primary).locator('.task-progress-edit').click()
                member.locator('#detail-progress').fill('73')
                assert leader_ctx.request.put(base+f'/api/tasks/{primary}/status',data={'status':'review'}).status==200
                member.bring_to_front()
                expect(member.locator('#sync-banner')).to_be_visible(timeout=12000)
                expect(member.locator('#detail-progress')).to_have_value('73')
                member.locator('#modal-task-detail .modal-header .btn-icon').click()
                expect(member.locator(f'#col-body-review .task-card[data-task-id="{primary}"]')).to_be_visible(timeout=12000)
                expect(member.locator('#sync-banner')).to_be_hidden(timeout=12000)
                assert api_task(member_ctx,primary)['progress_percent']==45
                record('Concurrent update keeps unsaved progress; closing applies pending revision without another server change')

                task_card(member,primary).locator('.task-progress-edit').click()
                assert leader_ctx.request.put(base+f'/api/tasks/{primary}/progress',data={'progress_percent':55}).status==200
                expect(member.locator('#detail-progress')).to_have_value('55',timeout=12000)
                member.locator('#modal-task-detail .modal-header .btn-icon').click()
                record('Unedited task detail refreshes automatically from another client')

                for page,uid,name in ((member,3,'Lưu Trà My'),(leader,2,'Phan Chân Long')):
                    page.locator('#account-profile-button').click()
                    expect(page.locator('#account-profile-info')).to_contain_text(name)
                    assert page.context.request.get(base+'/api/auth/me').json()['user']['id']==uid
                    assert 'password_hash' not in page.locator('#account-profile-info').inner_text()
                    page.keyboard.press('Escape')
                    expect(page.locator('#modal-account-profile')).to_be_hidden()
                record('Avatar opens the current session account; Escape closes safely')

                leader.goto(base+'/team')
                member.goto(base+'/team')
                expect(member.locator('#edit-my-capacity')).to_be_visible()
                expect(member.locator('.capacity-edit-button')).to_have_count(1)
                member.locator('#edit-my-capacity').click()
                edit_capacity(member,'Python, Flask',50,10)
                expect(member.locator('.member-card[data-user-id="3"]')).to_contain_text('5 giờ')
                leader.bring_to_front()
                expect(leader.locator('.member-card[data-user-id="3"] .member-skills')).to_have_text('Python, Flask',timeout=12000)
                leader.locator('.capacity-edit-button[data-user-id="3"]').click()
                edit_capacity(leader,'Python, Flask, API QA',50,6)
                member.bring_to_front()
                expect(member.locator('.member-card[data-user-id="3"] .member-skills')).to_have_text('Python, Flask, API QA',timeout=12000)
                expect(member.locator('.member-card[data-user-id="3"] .member-effective')).to_have_text('3 giờ')
                record('Member edits own capacity; PM edits team capacity; both clients receive the changes')

                leader.goto(base+'/reports')
                expect(leader.locator('#report-status-chart circle')).to_have_count(6)
                expect(leader.locator('.workload-chart-row[data-user-id="3"]')).to_contain_text('Quá tải')
                report=leader_ctx.request.get(base+f'/api/projects/{pid}/report').json()
                row=next(m for m in report['workload'] if m['user_id']==3)
                assert (row['effective_capacity_hours'],row['current_workload_hours'])==(3,12)
                leader.locator('#report-sprint').select_option(str(sid))
                expect(leader.locator('#report-total')).to_have_text('3')
                leader.locator('#report-sprint').select_option('')
                expect(leader.locator('#report-total')).to_have_text('5')
                leader.screenshot(path=str(shots/'reports-desktop.png'),full_page=True)
                record('Charts and sprint filters match backend totals, workload and overload',effective=3,workload=12)

                member.goto(base+'/reports')
                expect(member.locator('#report-total')).to_have_text('5')
                response=leader_ctx.request.post(base+f'/api/projects/{pid}/sprints',data={'name':'Sprint mới đồng bộ','goal':'Bổ sung bộ lọc','start_date':'2026-11-01','end_date':'2026-11-15','completion_criteria':'Hoàn tất','sprint_code':'SYNC-REPORT'})
                assert response.status==201,response.text()
                new_sprint=response.json()['sprint_id']
                member.bring_to_front()
                expect(member.locator(f'#report-sprint option[value="{new_sprint}"]')).to_have_count(1,timeout=12000)
                record('New sprint filter appears automatically on another device')

                leader.goto(base+'/ai-assistant')
                expect(leader.locator('#btn-generate-ai')).to_be_enabled()
                leader.locator('[data-mode="assignment_suggestion"]').click()
                leader.locator('#ai-task-select').select_option(str(ai_task))
                expect(leader.locator('#staffing-candidates-body')).to_contain_text('API QA')
                before=api_task(leader_ctx,ai_task)['assignee_id']
                with leader.expect_response(lambda r:r.url.endswith('/api/ai') and r.request.method=='POST') as generated:
                    leader.locator('#btn-generate-ai').click()
                assert generated.value.status==200,generated.value.text()
                expect(leader.locator('#ai-output-content')).to_contain_text('Gợi ý phân công')
                assert prompts and 'API QA' in prompts[-1]
                assert api_task(leader_ctx,ai_task)['assignee_id']==before
                record('AI adapter receives current skills/capacity/workload; proposal does not assign task',transport='mock Gemini HTTP')

                member_ctx.set_offline(True)
                member.bring_to_front()
                expect(member.locator('#sync-connection-status')).to_have_text('Mất kết nối máy chủ',timeout=12000)
                member_ctx.set_offline(False)
                expect(member.locator('#sync-connection-status')).to_have_text('Đã đồng bộ',timeout=12000)
                record('Lost connection is visible; reconnection refreshes shared data')

                # Real touch events, rather than calling the app's drag functions.
                for touch_width,touch_height in ((768,1024),(390,844)):
                    touch_ctx,touch=login('member_my',touch_width,touch_height,True)
                    assert leader_ctx.request.put(base+f'/api/tasks/{primary}/status',data={'status':'backlog'}).status==200
                    open_kanban(touch)
                    handle=task_card(touch,primary).locator('.task-drag-handle')
                    handle.evaluate('el=>el.scrollIntoView({block:"center",inline:"nearest"})')
                    touch.evaluate('window.scrollTo(0,0)')
                    handle.evaluate('el=>{const body=el.closest(".column-body");body.scrollTop=body.scrollHeight;}')
                    start=handle.bounding_box()
                    target=touch.locator('.kanban-column[data-status="todo"]').bounding_box()
                    cdp=touch_ctx.new_cdp_session(touch)
                    sx,sy=start['x']+start['width']/2,start['y']+start['height']/2
                    assert 0<sy<touch_height,(start,touch_height)
                    header=touch.locator('.app-header').bounding_box()
                    tx,ty=min(touch_width-24,target['x']+min(100,target['width']/2)),max(0,target['y'],header['y']+header['height'])+40
                    touch.evaluate("window.qaTouchEvents=[];for(const name of ['pointerdown','pointermove','pointerup','pointercancel'])document.addEventListener(name,e=>{if(window.qaTouchEvents.length<25)window.qaTouchEvents.push({type:e.type,tag:e.target.tagName,pointer:e.pointerType,active:window.taskDragActive,x:e.clientX,y:e.clientY});})")
                    with touch.expect_response(lambda r:r.url.endswith(f'/tasks/{primary}/status') and r.request.method=='PUT',timeout=10000) as moved:
                        cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx,'y':sy}]})
                        for step in range(1,11):
                            cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sx+(tx-sx)*step/10,'y':sy+(ty-sy)*step/10}]})
                        touch.wait_for_timeout(250)
                        cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                    assert moved.value.status==200
                    expect(touch.locator(f'#col-body-todo .task-card[data-task-id="{primary}"]')).to_be_visible()
                    record('Touch drag with browser events', width=touch_width)
                for width,height,label in ((1366,900,'desktop'),(1024,768,'small-desktop'),(768,1024,'tablet'),(390,844,'phone'),(320,740,'small-phone')):
                    member.set_viewport_size({'width':width,'height':height})
                    for path in ('/kanban','/team','/reports'):
                        member.goto(base+path)
                        member.wait_for_function('currentUser !== null && currentProjectId !== null')
                        if path=='/kanban':expect(task_card(member,primary).locator('.task-progress-edit')).to_be_visible()
                        if path=='/team':expect(member.locator('#edit-my-capacity')).to_be_visible()
                        if path=='/reports':expect(member.locator('#report-total')).to_have_text('5')
                        assert member.evaluate('document.documentElement.scrollWidth<=innerWidth+2'),(label,path)
                    member.screenshot(path=str(shots/f'reports-{label}.png'),full_page=True)
                    member.goto(base+'/team')
                    expect(member.locator('.member-card[data-user-id="3"]')).to_contain_text('API QA')
                    member.screenshot(path=str(shots/f'team-{label}.png'),full_page=True)
                    member.locator('#account-profile-button').click()
                    expect(member.locator('#account-profile-info')).to_contain_text('Lưu Trà My')
                    assert member.locator('#modal-account-profile .modal-box').evaluate('el=>el.scrollWidth<=el.clientWidth+2')
                    member.screenshot(path=str(shots/f'profile-{label}.png'))
                    member.keyboard.press('Escape')
                    record(f'Feature parity and layout: {label}',width=width,pages=3,profile=True)

                # Simulate a new server build without editing source files during QA.
                member.set_viewport_size({'width':1366,'height':900})
                member.goto(base+'/team')
                member.wait_for_function('syncRevision !== null')
                member.locator('#edit-my-capacity').click()
                member.locator('#member-edit-skills').fill('Nội dung chưa lưu cần được giữ')
                next_version='qa-next-workspace-build'
                def new_sync(route):
                    response=route.fetch()
                    data=response.json();data['app_version']=next_version
                    route.fulfill(response=response,json=data)
                def new_page(route):
                    response=route.fetch()
                    html=re.sub(r'name="app-version" content="[^"]+"',f'name="app-version" content="{next_version}"',response.text())
                    route.fulfill(response=response,body=html)
                member_ctx.route('**/api/sync',new_sync)
                member_ctx.route('**/team',new_page)
                expect(member.locator('#sync-banner')).to_contain_text('phiên bản mới',timeout=12000)
                expect(member.locator('#member-edit-skills')).to_have_value('Nội dung chưa lưu cần được giữ')
                member.locator('#modal-member-capacity').get_by_role('button',name='Hủy',exact=True).click()
                member.wait_for_function('document.querySelector(\'meta[name="app-version"]\').content === "qa-next-workspace-build"',timeout=15000)
                expect(member.locator('.member-card[data-user-id="3"] .member-skills')).to_have_text('Python, Flask, API QA')
                record('Build upgrade preserves unsaved form and loads new UI after cancel/finish')
                assert not errors,errors
                record('No JavaScript runtime errors',errors=errors)
            except Exception as error:
                records.append({'name':'Workspace acceptance','passed':False,'error':str(error)})
                if 'member' in locals():
                    records[-1]['drag_events']=member.evaluate('window.qaDragEvents||[]')
                if 'touch' in locals():
                    records[-1]['touch_events']=touch.evaluate('window.qaTouchEvents||[]')
                for index,ctx in enumerate(contexts):
                    if ctx.pages:
                        try:ctx.pages[0].screenshot(path=str(shots/f'failure-{index}.png'),full_page=True)
                        except Exception:pass
                raise
            finally:
                (out/'qa-workspace-results.json').write_text(json.dumps({'database':'disposable SQLite','browser':'Microsoft Edge headless','real_api_calls':False,'real_emails':False,'records':records,'runtime_errors':errors,'success':bool(records) and all(r['passed'] for r in records)},ensure_ascii=False,indent=2),encoding='utf-8')
                browser.close();server.shutdown()
    print('Workspace browser checks:',len(records),'passed:',sum(r['passed'] for r in records))


if __name__=='__main__':
    main()
