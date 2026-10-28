"""Authorization and persistence behind the repaired account/draft controls."""

import json
import unittest
from uuid import uuid4


def insert_draft(project_id, created_by=2, needs_review=False, content=None):
    from database.connection import execute_db
    from services.ai_history_service import save_ai_history
    body = content or 'Biên bản kiểm thử: quyết định và công việc theo nguồn.'
    structured = {'title': 'Họp kiểm thử thao tác', 'meeting_note_id': None,
                  'decisions': 'Giữ dữ liệu nguồn', 'action_items': 'Long kiểm thử SQLite'}
    status = 'needs_verification' if needs_review else 'draft'
    snapshot = {'warnings': ['Người phụ trách cần được đối chiếu với nguồn.'] if needs_review else [],
                'source_refs': {'tasks': [], 'members': [2, 3]}, 'data': {}, 'original_status': status}
    draft_id = execute_db('''INSERT INTO ai_drafts(project_id,task_type,input_params_json,draft_content,
        source_references_json,structured_result_json,status,created_by,validation_json)
        VALUES (%s,'meeting_minutes','{}',%s,'[]',%s,%s,%s,%s)''',
        (project_id, body, json.dumps(structured, ensure_ascii=False), status, created_by,
         json.dumps(snapshot, ensure_ascii=False)))
    save_ai_history(project_id, created_by, 'meeting_minutes', 'qa-fixture', 'ui-repair-test', [],
                    'Bản nháp kiểm thử thao tác', status, draft_id)
    return draft_id


class TestUIActions(unittest.TestCase):
    def setUp(self):
        from app import app
        from services.project_service import create_project
        self.leader = app.test_client()
        self.member = app.test_client()
        self.admin = app.test_client()
        for client, uid, role in ((self.leader, 2, 'leader'), (self.member, 3, 'member'), (self.admin, 1, 'admin')):
            with client.session_transaction() as session:
                session.update(user_id=uid, role=role)
        ok, message, self.project_id = create_project(2, 'UI action fixture', '',
            project_code='UI-' + uuid4().hex[:10], initial_member_ids=[3, 4])
        self.assertTrue(ok, message)

    def test_delete_button_is_rendered_but_self_deletion_remains_blocked(self):
        html = self.admin.get('/admin').get_data(as_text=True)
        self.assertIn('Xóa tài khoản', html)
        self.assertIn('deleteUserAccount(', html)
        self.assertIn('currentAdminId', html)
        self.assertEqual(self.admin.delete('/api/admin/users/1').status_code, 400)
        self.assertEqual(self.member.delete('/api/admin/users/2').status_code, 403)

    def test_last_project_leader_cannot_be_deleted(self):
        from database.connection import query_db
        result = self.admin.delete('/api/admin/users/2')
        self.assertEqual(result.status_code, 400)
        self.assertIn('Trưởng nhóm thay thế', result.get_json()['error'])
        self.assertIsNotNone(query_db('SELECT id FROM users WHERE id=2', one=True))
        self.assertIsNotNone(query_db('SELECT id FROM project_members WHERE project_id=%s AND user_id=2',
                                     (self.project_id,), one=True))

    def test_delete_with_replacement_keeps_business_records_and_revisions(self):
        from database.connection import query_db
        from services.account_service import create_user
        from services.project_service import create_project
        from services.project_member_service import assign_project_leader
        from services.task_service import create_task
        name = 'delete_' + uuid4().hex[:8]
        self.assertTrue(create_user(1, name, name + '@example.test', 'Password123!', 'Temporary Leader', 'leader')[0])
        target = query_db('SELECT id FROM users WHERE username=%s', (name,), one=True)['id']
        ok, message, project = create_project(target, 'Delete with replacement', '', project_code='DEL-' + uuid4().hex[:8])
        self.assertTrue(ok, message)
        self.assertTrue(assign_project_leader(1, project, 2)[0])
        ok, message, task = create_task(target, project, 'Preserved task', assignee_id=target, estimated_hours=1)
        self.assertTrue(ok, message)
        draft = insert_draft(project, target)
        from services.ai_draft_service import edit_ai_draft
        self.assertTrue(edit_ai_draft(draft, target, 'leader', {'version': 1, 'draft_content': 'Nội dung đã chỉnh'})[0])
        result = self.admin.delete(f'/api/admin/users/{target}')
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertIsNone(query_db('SELECT id FROM users WHERE id=%s', (target,), one=True))
        preserved = query_db('SELECT reporter_id,assignee_id FROM tasks WHERE id=%s', (task,), one=True)
        self.assertEqual(preserved, {'reporter_id': 1, 'assignee_id': None})
        revision = query_db('SELECT edited_by FROM ai_draft_revisions WHERE draft_id=%s', (draft,), one=True)
        self.assertIsNotNone(revision)
        self.assertIsNone(revision['edited_by'])
        self.assertIsNotNone(query_db('SELECT id FROM audit_logs WHERE action=%s AND target_id=%s',
                                     ('DELETE_USER', target), one=True))

    def test_review_requires_leader_and_explicit_note_before_confirmation(self):
        draft = insert_draft(self.project_id, needs_review=True)
        result = self.leader.put(f'/api/ai/drafts/{draft}', json={'version': 1, 'draft_content': 'Nội dung chỉnh sửa'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()['version'], 2)
        self.assertEqual(result.get_json()['status'], 'needs_verification')
        self.assertEqual(self.leader.post(f'/api/ai/drafts/{draft}/confirm', json={'version': 2}).status_code, 403)
        missing_note = self.leader.put(f'/api/ai/drafts/{draft}', json={'version': 2, 'verified': True, 'review_note': ''})
        self.assertEqual(missing_note.status_code, 400)
        reviewed = self.leader.put(f'/api/ai/drafts/{draft}', json={
            'version': 2, 'verified': True, 'review_note': 'Đã đối chiếu từng người và hạn với nguồn.',
            'decisions': 'Quyết định đã đối chiếu', 'action_items': 'Công việc đã đối chiếu',
        })
        self.assertEqual(reviewed.status_code, 200, reviewed.get_json())
        self.assertEqual(reviewed.get_json()['status'], 'draft')
        confirmed = self.leader.post(f'/api/ai/drafts/{draft}/confirm', json={'version': 3})
        self.assertEqual(confirmed.status_code, 200, confirmed.get_json())
        from database.connection import query_db
        official = query_db('SELECT decisions,action_items FROM meeting_minutes WHERE project_id=%s', (self.project_id,), one=True)
        self.assertEqual(official['decisions'], 'Quyết định đã đối chiếu')
        self.assertEqual(official['action_items'], 'Công việc đã đối chiếu')

    def test_member_cannot_clear_warnings_or_confirm_own_draft(self):
        draft = insert_draft(self.project_id, created_by=3, needs_review=True)
        result = self.member.put(f'/api/ai/drafts/{draft}', json={
            'version': 1, 'verified': True, 'review_note': 'Tự xác minh'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()['status'], 'needs_verification')
        self.assertEqual(self.member.post(f'/api/ai/drafts/{draft}/confirm', json={'version': 2}).status_code, 403)

    def test_stale_confirmation_does_not_confirm_a_newer_unreviewed_version(self):
        draft = insert_draft(self.project_id)
        saved = self.leader.put(f'/api/ai/drafts/{draft}', json={'version': 1, 'draft_content': 'Phiên bản mới'})
        self.assertEqual(saved.get_json()['version'], 2)
        rejected = self.leader.post(f'/api/ai/drafts/{draft}/confirm', json={'version': 1})
        self.assertEqual(rejected.status_code, 409)
        from database.connection import query_db
        self.assertEqual(query_db('SELECT status FROM ai_drafts WHERE id=%s', (draft,), one=True)['status'], 'draft')
        self.assertEqual(self.leader.post(f'/api/ai/drafts/{draft}/confirm', json={'version': 2}).status_code, 200)

    def test_invalid_confirmation_version_is_rejected_without_writes(self):
        draft = insert_draft(self.project_id)
        for version in (0, -1, True, 'wrong'):
            with self.subTest(version=version):
                self.assertEqual(self.leader.post(f'/api/ai/drafts/{draft}/confirm', json={'version': version}).status_code, 400)
        from database.connection import query_db
        self.assertEqual(query_db('SELECT status FROM ai_drafts WHERE id=%s', (draft,), one=True)['status'], 'draft')

    def test_save_alone_keeps_draft_and_returns_version_for_later_confirmation(self):
        draft = insert_draft(self.project_id)
        result = self.leader.put(f'/api/ai/drafts/{draft}', json={'version': 1, 'draft_content': 'Chỉ lưu, chưa xác nhận'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual((result.get_json()['version'], result.get_json()['status']), (2, 'draft'))
        from database.connection import query_db
        self.assertEqual(query_db('SELECT COUNT(*) AS n FROM meeting_minutes WHERE project_id=%s', (self.project_id,), one=True)['n'], 0)
        stale = self.leader.put(f'/api/ai/drafts/{draft}', json={'version': 1, 'draft_content': 'Không được ghi đè'})
        self.assertEqual(stale.status_code, 400)

    def test_confirmed_draft_cannot_be_edited(self):
        draft = insert_draft(self.project_id)
        self.assertEqual(self.leader.post(f'/api/ai/drafts/{draft}/confirm', json={'version': 1}).status_code, 200)
        result = self.leader.put(f'/api/ai/drafts/{draft}', json={'version': 1, 'draft_content': 'Không được ghi đè bản chính thức'})
        self.assertEqual(result.status_code, 403)


if __name__ == '__main__':
    unittest.main()
