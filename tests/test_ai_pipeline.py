import unittest
import json
from app import app
from services.ai_request_analyzer import analyze_ai_request
from services.ai_response_validator import validate_ai_response
from services.ai_confirmation_service import confirm_ai_draft
from database.connection import execute_db

class TestAIPipeline(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_request_analyzer_rbac_d06(self):
        """Kiểm thử phân quyền riêng từng chức năng AI theo D06."""
        # Weekly summary: Thành viên thường (user_id=3) cố gọi -> Phải bị từ chối
        valid, msg, _ = analyze_ai_request({
            'task_type': 'weekly_summary',
            'project_id': 1,
            'week_start': '2026-09-01',
            'week_end': '2026-09-10'
        }, session_user_id=3, session_system_role='member')
        self.assertFalse(valid)
        self.assertIn('Trưởng nhóm', msg)

        # Weekly summary: Trưởng nhóm (user_id=2) gọi -> Hợp lệ
        valid, msg, req = analyze_ai_request({
            'task_type': 'weekly_summary',
            'project_id': 1,
            'week_start': '2026-09-01',
            'week_end': '2026-09-10'
        }, session_user_id=2, session_system_role='leader')
        self.assertTrue(valid)
        self.assertEqual(req['requester_id'], 2)

    def test_response_validator_hallucination_detection(self):
        """Kiểm thử Response Validator phát hiện ID ảo giác ngoài CSDL."""
        source_refs = {
            'tasks': [1, 2, 3],
            'members': [2, 3]
        }

        # Phản hồi chỉ chứa ID hợp lệ
        valid_response = "Tóm tắt: Đã hoàn thành [Task #1] và [Task #2] do [User #2] phụ trách."
        val = validate_ai_response(valid_response, {'task_type': 'weekly_summary'}, source_refs)
        self.assertEqual(val['status'], 'draft')
        self.assertEqual(len(val['warnings']), 0)

        # Phản hồi chứa ID ảo giác không tồn tại trong source_refs (Ví dụ [Task #999] hoặc [User #888])
        hallucinated_response = "AI bịa đặt: Đã giao việc [Task #999] cho [User #888]."
        val_bad = validate_ai_response(hallucinated_response, {'task_type': 'weekly_summary'}, source_refs)
        self.assertEqual(val_bad['status'], 'needs_verification')
        self.assertGreater(len(val_bad['warnings']), 0)
        self.assertIn('999', str(val_bad['warnings']))

    def test_confirmation_service_leader_only_uc010(self):
        """Kiểm thử chỉ Trưởng nhóm mới có quyền xác nhận bản nháp chính thức (UC010, D05)."""
        # Tạo 1 bản nháp test
        draft_id = execute_db("""
            INSERT INTO ai_drafts (project_id, task_type, input_params_json, draft_content,
                                   source_references_json, structured_result_json, status, created_by)
            VALUES (1, 'meeting_minutes', '{}', 'Nội dung biên bản test', '[]', %s, 'draft', 3);
        """, (json.dumps({'title': 'Họp kiểm thử', 'meeting_note_id': None,
                          'decisions': 'Chọn phương án A', 'action_items': 'Lan kiểm thử'}),))

        # Thành viên thường (user_id=3) cố xác nhận -> Phải bị từ chối
        ok, msg = confirm_ai_draft(draft_id, user_id=3, user_system_role='member')
        self.assertFalse(ok)
        self.assertIn('Trưởng nhóm', msg)

        # Trưởng nhóm (user_id=2) xác nhận -> Thành công
        ok, msg = confirm_ai_draft(draft_id, user_id=2, user_system_role='leader')
        self.assertTrue(ok)
        from database.connection import query_db
        minute = query_db('SELECT decisions, action_items FROM meeting_minutes WHERE title = %s',
                          ('Họp kiểm thử',), one=True)
        self.assertEqual(minute['decisions'], 'Chọn phương án A')
        self.assertEqual(minute['action_items'], 'Lan kiểm thử')

if __name__ == '__main__':
    unittest.main()
