"""Real Edge UI checks for deletion, cancel and draft review on disposable SQLite."""

import json
import os
from pathlib import Path
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scratch/qa_audit_2026_10_27/browser_deps'))
os.environ.update(AI_CONFIG_SOURCE='process', AI_PROVIDER='gemini', GEMINI_API_KEY='your_gemini_api_key',
                  LOCAL_AI_MODEL_ENABLED='false', SMTP_ENABLED='false', DEADLINE_WORKER_ENABLED='false')

from playwright.sync_api import sync_playwright, expect


def main():
    from database import connection, init_db
    out = ROOT / 'docs'
    shots = out / 'qa-ui-repairs'
    shots.mkdir(exist_ok=True)
    records, errors = [], []
    def record(name, **details):
        records.append({'name': name, 'passed': True, 'details': details})
    with tempfile.TemporaryDirectory() as directory:
        connection._SQLITE_PATH = init_db.SQLITE_PATH = str(Path(directory) / 'ui.sqlite3')
        connection.set_engine_mode('sqlite')
        init_db.init_sqlite_fallback()
        from app import app
        from database.connection import query_db
        from services.project_service import create_project
        from services.account_service import create_user
        from tests.test_ui_actions import insert_draft
        ok, message, pid = create_project(2, 'UI repair acceptance', '', project_code='UI-BROWSER', initial_member_ids=[3, 4])
        assert ok, message
        content = '\n'.join(f'- Đoạn nguồn {index}: Nội dung để kiểm tra cuộn và đối chiếu.' for index in range(1, 151))
        warning_draft = insert_draft(pid, needs_review=True, content=content)
        clean_draft = insert_draft(pid)
        member_draft = insert_draft(pid, created_by=3, needs_review=True)
        assert create_user(1, 'ui_delete_target', 'ui_delete_target@example.test', 'Password123!', 'QA Xóa tài khoản')[0]
        target = query_db('SELECT id FROM users WHERE username=%s', ('ui_delete_target',), one=True)['id']
        from werkzeug.serving import make_server
        server = make_server('127.0.0.1', 0, app, threaded=True)
        base = f'http://127.0.0.1:{server.server_port}'
        threading.Thread(target=server.serve_forever, daemon=True).start()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge', headless=True)
            def login(username):
                context = browser.new_context(viewport={'width': 1366, 'height': 768}, locale='vi-VN')
                context.route('https://fonts.googleapis.com/**', lambda route: route.abort())
                context.route('https://fonts.gstatic.com/**', lambda route: route.abort())
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(base + '/login')
                page.locator('#login-username').fill(username)
                page.locator('#login-password').fill('Password123!')
                page.locator('#btn-submit-login').click()
                page.wait_for_url('**/' + ('admin' if username == 'admin' else 'dashboard'))
                page.wait_for_function('typeof currentUser !== "undefined" && currentUser !== null')
                return context, page
            def read_draft(identifier, context):
                return context.request.get(base + f'/api/ai/drafts/{identifier}').json()['draft']
            try:
                admin_context, admin = login('admin')
                expect(admin.locator('#users-table-body tr').filter(has_text='admin (')).to_have_count(1)
                own_row = admin.locator('#users-table-body tr').filter(has_text='admin (')
                expect(own_row.get_by_role('button', name='Xóa tài khoản', exact=True)).to_be_disabled()
                record('Admin sees delete control; own account is protected')
                admin.locator('#admin-user-search').fill('ui_delete_target')
                button = admin.locator('#users-table-body').get_by_role('button', name='Xóa tài khoản', exact=True)
                admin.once('dialog', lambda dialog: dialog.dismiss())
                button.click()
                assert query_db('SELECT id FROM users WHERE id=%s', (target,), one=True)
                record('Cancel account deletion keeps account')
                admin.once('dialog', lambda dialog: dialog.accept())
                with admin.expect_response(lambda response: response.request.method == 'DELETE' and response.url.endswith(f'/users/{target}')) as deleted:
                    button.click()
                assert deleted.value.status == 200, deleted.value.text()
                expect(admin.locator('#users-table-body')).to_contain_text('Không có tài khoản phù hợp')
                assert query_db('SELECT id FROM users WHERE id=%s', (target,), one=True) is None
                record('Confirm deletion removes fixture account and updates table')
                admin.locator('#admin-user-search').fill('leader_long')
                admin.once('dialog', lambda dialog: dialog.accept())
                with admin.expect_response(lambda response: response.request.method == 'DELETE' and response.url.endswith('/users/2')) as blocked:
                    admin.locator('#users-table-body').get_by_role('button', name='Xóa tài khoản', exact=True).click()
                assert blocked.value.status == 400
                expect(admin.locator('#toast-container')).to_contain_text('Trưởng nhóm thay thế')
                record('Deletion of last project leader is blocked')
                admin.screenshot(path=str(shots / 'admin-delete-control.png'))

                leader_context, leader = login('leader_long')
                leader.goto(base + '/ai-assistant')
                leader.wait_for_function(f'typeof currentProjectId !== "undefined" && String(currentProjectId)==="{pid}"')
                leader.get_by_role('button', name='📜 Lịch sử AI (FR-15)', exact=True).click()
                leader.locator(f'button[onclick="displayDraft({warning_draft})"]').click()
                confirm = leader.locator('#btn-confirm-draft')
                expect(confirm).to_be_visible()
                expect(confirm).to_be_disabled()
                expect(leader.locator('#ai-confirmation-hint')).to_contain_text('còn cảnh báo')
                record('Warning draft shows disabled confirm plus review explanation')
                modal = leader.locator('#modal-draft-editor')
                mutations = []
                leader.on('request', lambda request: mutations.append((request.method, request.url))
                          if '/api/ai/drafts/' in request.url and request.method in ('PUT', 'POST') else None)
                for width, height, label in ((1366, 600, 'laptop'), (768, 700, 'tablet'), (390, 640, 'phone'), (320, 560, 'small-phone')):
                    leader.set_viewport_size({'width': width, 'height': height})
                    leader.locator('#btn-edit-draft').click()
                    expect(modal).to_have_class('modal-overlay active')
                    body = modal.locator('.draft-editor-body')
                    body.evaluate('element => element.scrollTop=element.scrollHeight')
                    for locator in (modal.get_by_role('button', name='Đóng cửa sổ chỉnh sửa bản nháp', exact=True),
                                    modal.get_by_role('button', name='Hủy thay đổi', exact=True),
                                    modal.get_by_role('button', name='Lưu và xác nhận', exact=True)):
                        expect(locator).to_be_visible()
                        box = locator.bounding_box()
                        assert box and box['y'] >= -1 and box['y'] + box['height'] <= height + 1, (label, box)
                    assert modal.locator('.modal-box').evaluate('el=>el.scrollWidth<=el.clientWidth+2')
                    leader.screenshot(path=str(shots / f'draft-editor-{label}.png'))
                    modal.get_by_role('button', name='Hủy thay đổi', exact=True).click()
                    expect(modal).not_to_have_class('modal-overlay active')
                    record(f'Header and footer stay visible while scrolling: {label}', width=width, height=height)

                leader.set_viewport_size({'width': 1366, 'height': 768})
                for action in ('cancel', 'escape', 'close', 'backdrop'):
                    before = read_draft(warning_draft, leader_context)
                    before_mutations = len(mutations)
                    leader.locator('#btn-edit-draft').click()
                    modal.locator('#draft-edit-content').fill('Thay đổi chưa lưu cần được hủy')
                    if action == 'cancel':
                        modal.get_by_role('button', name='Hủy thay đổi', exact=True).click()
                    elif action == 'escape':
                        leader.keyboard.press('Escape')
                    elif action == 'close':
                        modal.get_by_role('button', name='Đóng cửa sổ chỉnh sửa bản nháp', exact=True).click()
                    else:
                        modal.click(position={'x': 3, 'y': 3})
                    expect(modal).not_to_have_class('modal-overlay active')
                    after = read_draft(warning_draft, leader_context)
                    assert (after['version'], after['draft_content']) == (before['version'], before['draft_content'])
                    assert len(mutations) == before_mutations
                    record(f'Close without saving keeps database unchanged: {action}')

                leader.locator('#btn-edit-draft').click()
                before_mutations = len(mutations)
                modal.locator('#btn-save-confirm-draft').click()
                expect(modal).to_have_class('modal-overlay active')
                assert len(mutations) == before_mutations
                record('Save and confirm requires explicit source review')
                modal.locator('#draft-edit-verified').check()
                modal.locator('#draft-edit-review-note').fill('Đã đối chiếu người phụ trách và hạn với tài liệu nguồn.')
                modal.locator('#draft-edit-decisions').fill('Quyết định đã được kiểm tra')
                modal.locator('#draft-edit-actions').fill('Long kiểm thử SQLite theo ghi chú gốc')
                with leader.expect_response(lambda response: response.request.method == 'POST' and response.url.endswith(f'/drafts/{warning_draft}/confirm')) as confirmed:
                    modal.locator('#btn-save-confirm-draft').click()
                assert confirmed.value.status == 200, confirmed.value.text()
                expect(modal).not_to_have_class('modal-overlay active')
                expect(leader.locator('#ai-status-text')).to_have_text('ĐÃ XÁC NHẬN')
                saved = read_draft(warning_draft, leader_context)
                assert saved['status'] == 'confirmed'
                snapshot = json.loads(saved['validation_json'])
                assert snapshot['reviewed_by'] == 2 and snapshot['warnings'] == []
                record('Leader reviews, saves and confirms exact version through UI', version=saved['version'])

                leader.get_by_role('button', name='📜 Lịch sử AI (FR-15)', exact=True).click()
                leader.locator(f'button[onclick="displayDraft({clean_draft})"]').click()
                leader.locator('#btn-edit-draft').click()
                modal.locator('#draft-edit-content').fill('Chỉ lưu bản nháp, chưa xác nhận')
                with leader.expect_response(lambda response: response.request.method == 'PUT' and response.url.endswith(f'/drafts/{clean_draft}')) as saved_response:
                    modal.locator('#btn-save-draft-edit').click()
                assert saved_response.value.status == 200
                expect(modal).not_to_have_class('modal-overlay active')
                assert read_draft(clean_draft, leader_context)['status'] == 'draft'
                expect(leader.locator('#btn-confirm-draft')).to_be_enabled()
                with leader.expect_response(lambda response: response.request.method == 'POST' and response.url.endswith(f'/drafts/{clean_draft}/confirm')) as confirmed_clean:
                    leader.locator('#btn-confirm-draft').click()
                assert confirmed_clean.value.status == 200
                record('Save alone stays draft; main confirm control then works')

                member_context, member = login('member_my')
                member.goto(base + '/ai-assistant')
                member.wait_for_function('typeof currentProjectRole !== "undefined" && currentProjectRole === "member"')
                # Fixture reproduces the result card a member receives after generation.
                member.evaluate('(identifier)=>displayDraft(identifier)', member_draft)
                expect(member.locator('#btn-confirm-draft')).to_be_hidden()
                member.locator('#btn-edit-draft').click()
                expect(member.locator('#btn-save-confirm-draft')).to_be_hidden()
                expect(member.locator('#draft-review-fields')).to_be_hidden()
                result = member_context.request.post(base + f'/api/ai/drafts/{member_draft}/confirm', data={'version': 1})
                assert result.status == 403
                record('Member can edit own draft but cannot review away warnings or confirm')
                assert not errors, errors
                record('No JavaScript runtime errors', errors=errors)
            except Exception as error:
                records.append({'name': 'UI repairs acceptance', 'passed': False, 'error': str(error)})
                raise
            finally:
                (out / 'qa-ui-repairs.json').write_text(json.dumps({
                    'database': 'disposable SQLite', 'browser': 'Microsoft Edge headless',
                    'real_api_calls': False, 'records': records, 'runtime_errors': errors,
                    'success': bool(records) and all(record['passed'] for record in records),
                }, ensure_ascii=False, indent=2), encoding='utf-8')
                browser.close()
                server.shutdown()
    print('UI repair checks:', len(records), 'passed:', sum(record['passed'] for record in records))


if __name__ == '__main__':
    main()
