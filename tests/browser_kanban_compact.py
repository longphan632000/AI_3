"""Exercise a crowded Kanban with real mouse/touch events and disposable SQLite."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scratch/qa_audit_2026_10_27/browser_deps'))
os.environ.update(AI_CONFIG_SOURCE='process',AI_PROVIDER='gemini',GEMINI_API_KEY='qa_fake_key',
                  AI_LOCAL_FALLBACK_ENABLED='false',LOCAL_AI_MODEL_ENABLED='false',
                  SMTP_ENABLED='false',DEADLINE_WORKER_ENABLED='false',FLASK_DEBUG='false')
from playwright.sync_api import expect, sync_playwright


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--legacy-template',action='store_true',help='Reproduce a running server that still renders the cached previous Kanban template.')
    parser.add_argument('--output',type=Path,default=ROOT/'logstest/kanban-compact')
    args=parser.parse_args()
    expect.set_options(timeout=15000)
    output=args.output
    output.mkdir(parents=True,exist_ok=True)
    records,errors,contexts=[],[],[]
    started=datetime.now(timezone.utc).isoformat()
    def record(name,**details):
        records.append({'name':name,'passed':True,'details':details})
        print('PASS:',name,flush=True)
    with tempfile.TemporaryDirectory() as directory:
        from database import connection,init_db
        connection._SQLITE_PATH=init_db.SQLITE_PATH=str(Path(directory)/'crowded-kanban.sqlite3')
        connection.set_engine_mode('sqlite')
        init_db.init_sqlite_fallback()
        from services.project_service import create_project
        from services.task_service import create_task,update_task_status
        ok,message,pid=create_project(2,'Kanban nhiều nhiệm vụ','',project_code='COMPACT',initial_member_ids=[3,4])
        assert ok,message
        for index in range(54):
            ok,message,tid=create_task(2,pid,f'Nhiệm vụ {index:03d}: Kiểm tra giao diện và xử lý dữ liệu',
                assignee_id=3,estimated_hours=2,labels='Backend, Python, Flask, SQL, Kiểm thử')
            assert ok,message
            assert update_task_status(2,tid,'todo' if index%2 else 'in_progress')[0]
        ok,message,readonly=create_task(2,pid,'Nhiệm vụ của Khánh',assignee_id=4,priority='high')
        assert ok,message
        ok,message,primary=create_task(2,pid,('Nhiệm vụ ưu tiên: '+('Đối chiếu thông tin dài và đầy đủ. '*8))[:200],
            description='Giữ đầy đủ mô tả; thẻ chỉ hiển thị phần tóm tắt.',assignee_id=3,priority='urgent',
            labels='Backend, Python, Flask, SQL, Kiểm thử',estimated_hours=8)
        assert ok,message
        from app import app
        if args.legacy_template:
            from jinja2 import ChoiceLoader,DictLoader
            app.jinja_env.loader=ChoiceLoader([DictLoader({'kanban.html':(ROOT/'tests/fixtures/kanban_cached_v1.html').read_text(encoding='utf-8')}),app.jinja_env.loader])
            app.jinja_env.cache.clear()
        from werkzeug.serving import make_server
        server=make_server('127.0.0.1',0,app,threaded=True)
        base=f'http://127.0.0.1:{server.server_port}'
        threading.Thread(target=server.serve_forever,daemon=True).start()
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='msedge',headless=True)
            def login(username,width=1366,height=900,touch=False):
                ctx=browser.new_context(viewport={'width':width,'height':height},has_touch=touch,is_mobile=touch,locale='vi-VN')
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
                page.wait_for_url('**/dashboard')
                page.goto(base+'/kanban')
                expect(page.locator('.task-card')).to_have_count(50)
                return ctx,page
            def card(page,tid):
                return page.locator(f'.task-card[data-task-id="{tid}"]')
            try:
                member_ctx,member=login('member_my')
                leader_ctx,leader=login('leader_long')
                for width,height,label in ((1920,1080,'desktop'),(1366,900,'laptop'),(768,1024,'tablet'),(390,844,'phone'),(320,740,'small-phone')):
                    member.set_viewport_size({'width':width,'height':height})
                    member.wait_for_function('document.querySelector(".kanban-workspace").getBoundingClientRect().bottom<=innerHeight+2')
                    sizes=member.evaluate('''() => ({
                        width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                        pageHeight:document.documentElement.scrollHeight,height:innerHeight,
                        columnHeights:[...document.querySelectorAll('.kanban-column')].map(el=>el.getBoundingClientRect().height),
                        bodyHeights:[...document.querySelectorAll('.column-body')].map(el=>el.clientHeight),
                        cardHeight:Math.max(...[...document.querySelectorAll('.task-card')].map(el=>el.getBoundingClientRect().height))
                    })''')
                    assert sizes['scrollWidth']<=width+2,sizes
                    assert sizes['pageHeight']<=height+4,sizes
                    assert max(sizes['columnHeights'])-min(sizes['columnHeights'])<2,sizes
                    assert sizes['cardHeight']<=310,sizes
                    assert sizes['cardHeight']+24<=min(sizes['bodyHeights'])+2,sizes
                    assert member.locator('.task-card input,.task-card select,.inline-task-progress').count()==0
                    assert member.locator('.column-body').evaluate_all('elements=>elements.some(el=>el.scrollHeight>el.clientHeight+500)')
                    member.screenshot(path=str(output/f'board-{label}.png'),full_page=True)
                    record('Crowded board stays inside viewport with compact cards and equal columns',viewport=[width,height],**sizes)

                leader.set_viewport_size({'width':320,'height':740})
                expect(leader.locator('#create-task-button')).to_be_visible()
                leader.wait_for_function('document.querySelector(".kanban-workspace").getBoundingClientRect().bottom<=innerHeight+2')
                assert card(leader,primary).bounding_box()['height']+24<=leader.locator('#col-body-backlog').evaluate('el=>el.clientHeight')+2
                leader.locator('#kanban-project-panel summary').click()
                expect(leader.get_by_role('button',name='+ Tạo dự án',exact=True)).to_be_visible()
                expect(leader.locator('#add-project-member-button')).to_be_visible()
                expect(leader.locator('#archived-projects-button')).to_be_visible()
                leader.keyboard.press('Escape')
                leader.locator('#kanban-filter-panel summary').click()
                leader.get_by_role('button',name='Nhiệm vụ đã lưu trữ',exact=True).click()
                expect(leader.locator('#modal-archived-projects')).to_be_visible()
                expect(leader.locator('#archived-project-list')).to_have_text('Chưa có nhiệm vụ lưu trữ.')
                leader.locator('#modal-archived-projects .modal-header button').click()
                leader.screenshot(path=str(output/'board-pm-small-phone.png'),full_page=True)
                leader.set_viewport_size({'width':1366,'height':900})
                record('PM create control and archive access also fit a small phone without clipping the first card')

                member.set_viewport_size({'width':1366,'height':900})
                member.wait_for_function('innerWidth===1366')
                expect(card(member,readonly).locator('.task-progress-edit')).to_have_count(0)
                expect(card(member,readonly)).to_have_attribute('draggable','false')
                assert member_ctx.request.put(base+f'/api/tasks/{readonly}/progress',data={'progress_percent':80}).status==403
                assert member_ctx.request.put(base+f'/api/tasks/{readonly}/status',data={'status':'done'}).status==403
                expect(card(leader,readonly).locator('.task-progress-edit')).to_be_visible()
                record('Compact controls respect member ownership and PM permissions; server rejects unauthorized writes')

                member.locator('#kanban-filter-panel summary').click()
                member.locator('#filter-status').select_option('todo')
                expect(member.locator('.task-card')).to_have_count(27)
                expect(member.locator('#kanban-filter-count')).to_have_text('1')
                member.keyboard.press('Escape')
                assert not member.locator('#kanban-filter-panel').evaluate('el=>el.open')
                member.locator('#kanban-filter-panel summary').click()
                member.locator('#filter-status').select_option('')
                expect(member.locator('.task-card')).to_have_count(50)
                member.locator('#filter-sort').select_option('title')
                member.locator('#filter-order').select_option('asc')
                member.locator('#filter-sort').select_option('priority')
                member.locator('#filter-order').select_option('desc')
                member.keyboard.press('Escape')
                expect(card(member,primary)).to_be_visible()
                member.locator('#tasks-next').click()
                expect(member.locator('.task-card')).to_have_count(6)
                expect(member.locator('#tasks-next')).to_be_disabled()
                expect(member.locator('#tasks-page')).to_have_text('Trang 2')
                member.locator('#tasks-prev').click()
                expect(member.locator('.task-card')).to_have_count(50)
                member.locator('#filter-keyword').fill('Nhiệm vụ 005:')
                expect(member.locator('.task-card')).to_have_count(1)
                expect(member.locator('.task-title')).to_contain_text('Nhiệm vụ 005:')
                member.locator('#filter-keyword').fill('')
                expect(member.locator('.task-card')).to_have_count(50)
                record('Collapsed filters, active filter count, search, sorting and pagination remain usable with 56 tasks')

                body=member.locator('#col-body-in_progress')
                header=member.locator('.kanban-column[data-status="in_progress"] .column-header')
                before=header.bounding_box()['y']
                body.evaluate('el=>el.scrollTop=400')
                assert abs(header.bounding_box()['y']-before)<1
                assert member.locator('#col-body-todo').evaluate('el=>el.scrollTop')==0
                assert leader_ctx.request.put(base+f'/api/tasks/{primary}/progress',data={'progress_percent':45}).status==200
                expect(card(member,primary).locator('[role=progressbar]')).to_have_attribute('aria-valuenow','45',timeout=15000)
                assert abs(body.evaluate('el=>el.scrollTop')-400)<2
                record('Columns scroll independently; headers and scroll position survive automatic updates')

                card(member,primary).locator('.task-progress-edit').click()
                expect(member.locator('#detail-progress')).to_be_focused()
                member.locator('#detail-progress').fill('73')
                assert leader_ctx.request.put(base+f'/api/tasks/{primary}/progress',data={'progress_percent':55}).status==200
                expect(member.locator('#sync-banner')).to_be_visible(timeout=15000)
                expect(member.locator('#detail-progress')).to_have_value('73')
                member.screenshot(path=str(output/'progress-editor.png'))
                member.keyboard.press('Escape')
                expect(member.locator('#modal-task-detail')).to_be_hidden()
                expect(card(member,primary).locator('[role=progressbar]')).to_have_attribute('aria-valuenow','55',timeout=15000)
                assert member_ctx.request.get(base+f'/api/tasks/{primary}').json()['task']['progress_percent']==55
                record('Popup keeps unsaved percentage during concurrent changes; Escape cancels without writing')

                member.locator('.kanban-board').evaluate('el=>el.scrollLeft=0')
                member.locator('#col-body-todo').evaluate('el=>el.scrollTop=0')
                source=member.locator('#col-body-todo .task-card').first
                dragged_id=int(source.get_attribute('data-task-id'))
                start=source.locator('.task-title').bounding_box()
                bounds=member.locator('#col-body-todo').bounding_box()
                sx,sy=start['x']+start['width']/2,start['y']+start['height']/2
                member.mouse.move(sx,sy);member.mouse.down()
                member.mouse.move(sx+10,sy+10,steps=5)
                member.mouse.move(bounds['x']+bounds['width']/2,bounds['y']+bounds['height']-12,steps=12)
                member.wait_for_function('document.getElementById("col-body-todo").scrollTop>200')
                board=member.locator('.kanban-board').bounding_box()
                member.mouse.move(board['x']+board['width']-10,board['y']+100,steps=12)
                member.wait_for_function('document.querySelector(".kanban-board").scrollLeft>60')
                target=member.locator('.kanban-column[data-status="done"] .column-header')
                target.scroll_into_view_if_needed()
                box=target.bounding_box()
                with member.expect_response(lambda response:response.url.endswith(f'/tasks/{dragged_id}/status') and response.request.method=='PUT') as moved:
                    member.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2,steps=15)
                    member.mouse.up()
                assert moved.value.status==200
                assert member_ctx.request.get(base+f'/api/tasks/{dragged_id}').json()['task']['status']=='done'
                member.wait_for_function('window.taskDragActive===false')
                assert member.locator('.drag-over,.is-task-dragging').count()==0
                record('Real mouse drag auto-scrolls vertically and horizontally; dropping saves Done and cleans drag state')

                assert leader_ctx.request.put(base+f'/api/tasks/{primary}/status',data={'status':'backlog'}).status==200
                touch_ctx,touch=login('member_my',390,844,True)
                touch.locator('.kanban-board').evaluate('el=>el.scrollLeft=0')
                handle=card(touch,primary).locator('.task-drag-handle')
                box=handle.bounding_box()
                cdp=touch_ctx.new_cdp_session(touch)
                sx,sy=box['x']+box['width']/2,box['y']+box['height']/2
                board=touch.locator('.kanban-board').bounding_box()
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx,'y':sy}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':380,'y':board['y']+90}]})
                touch.wait_for_function('document.querySelector(".kanban-board").scrollLeft>310')
                bounds=touch.locator('#col-body-todo').bounding_box()
                tx=min(350,max(45,bounds['x']+bounds['width']/2))
                ty=bounds['y']+bounds['height']-12
                cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':tx,'y':ty}]})
                touch.wait_for_function('document.getElementById("col-body-todo").scrollTop>120')
                with touch.expect_response(lambda response:response.url.endswith(f'/tasks/{primary}/status') and response.request.method=='PUT') as moved:
                    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                assert moved.value.status==200
                assert touch_ctx.request.get(base+f'/api/tasks/{primary}').json()['task']['status']=='todo'
                assert touch_ctx.request.get(base+f'/api/tasks/{primary}').json()['task']['progress_percent']==55
                touch.wait_for_function('window.taskDragActive===false')
                record('Real touch drag auto-scrolls across columns and down a long column before saving the selected status')

                touch.locator('#col-body-todo').evaluate('el=>el.scrollTop=0')
                touch.locator('.kanban-board').evaluate('el=>{const col=el.querySelector("[data-status=todo]");el.scrollLeft+=col.getBoundingClientRect().left-el.getBoundingClientRect().left;}')
                card(touch,primary).locator('.task-progress-edit').click()
                expect(touch.locator('#detail-progress')).to_have_value('55')
                touch.locator('#detail-progress').fill('101')
                touch.get_by_role('button',name='Lưu tiến độ',exact=True).click()
                assert not touch.locator('#detail-progress').evaluate('el=>el.checkValidity()')
                assert touch_ctx.request.get(base+f'/api/tasks/{primary}').json()['task']['progress_percent']==55
                touch.locator('#detail-progress').fill('100')
                touch.get_by_role('button',name='Lưu tiến độ',exact=True).click()
                expect(touch.locator('#detail-progress')).to_have_value('100')
                expect(touch.locator('#detail-task-status')).to_have_text('DONE')
                touch.screenshot(path=str(output/'progress-editor-phone.png'))
                touch.locator('#task-detail-actions').get_by_role('button',name='Hủy',exact=True).click()
                assert touch_ctx.request.get(base+f'/api/tasks/{primary}').json()['task']['progress_percent']==100
                record('Touch popup saves actual progress; 100 percent still marks the task Done')
                assert not errors,errors
            except Exception as error:
                records.append({'name':'Failure','passed':False,'error':str(error)})
                for index,ctx in enumerate(contexts):
                    if ctx.pages:
                        try:ctx.pages[0].screenshot(path=str(output/f'failure-{index}.png'),full_page=True)
                        except Exception:pass
                raise
            finally:
                payload={'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),'legacy_template':args.legacy_template,
                    'database':'disposable SQLite','fixture_task_count':56,'browser':'Microsoft Edge headless',
                    'real_api_calls':False,'real_emails':False,'records':records,'runtime_errors':errors,
                    'success':bool(records) and all(row['passed'] for row in records)}
                (output/'browser-results.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
                browser.close();server.shutdown()
    print('Compact Kanban checks:',len(records),'passed:',sum(row['passed'] for row in records))


if __name__=='__main__':
    main()
