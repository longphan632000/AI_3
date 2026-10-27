import unittest
from unittest.mock import patch
from app import app
from database.connection import query_db

class TestIntegrationE2E(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_e2e_full_flow(self):
        """
        Kiểm thử tích hợp luồng hoàn chỉnh E2E:
        Đăng nhập Trưởng nhóm ➔ Tạo nhiệm vụ ➔ Kéo thả Kanban ➔ Cập nhật tiến độ ➔ Gọi Trợ lý AI ➔ Xác nhận bản nháp.
        """
        # 1. Đăng nhập Leader
        res = self.client.post('/api/auth/login', json={
            'username_or_email': 'leader_long',
            'password': 'Password123!'
        })
        self.assertEqual(res.status_code, 200)

        # 2. Tạo nhiệm vụ mới gán cho member_my (user_id=3)
        res = self.client.post('/api/projects/1/tasks', json={
            'title': 'E2E Test Task: Tích hợp hoàn tất',
            'description': 'Kiểm thử toàn diện luồng nghiệp vụ',
            'sprint_id': 2,
            'assignee_id': 3,
            'priority': 'high',
            'due_date': '2026-10-01 17:00:00',
            'estimated_hours': 10.0,
            'labels': 'E2E, Test'
        })
        self.assertEqual(res.status_code, 201)
        task_id = res.get_json()['task_id']
        self.assertTrue(task_id > 0)

        # 3. Kéo thả Kanban: Đổi trạng thái sang in_progress
        res = self.client.put(f'/api/tasks/{task_id}/status', json={'status': 'in_progress'})
        self.assertEqual(res.status_code, 200)

        # 4. Kéo thả Kanban: Đổi trạng thái sang done
        res = self.client.put(f'/api/tasks/{task_id}/status', json={'status': 'done'})
        self.assertEqual(res.status_code, 200)

        # 5. Kiểm tra thông báo FR-16 đã được tạo cho thành viên
        notis = query_db("SELECT * FROM notifications WHERE user_id = 3 AND task_id = %s;", (task_id,))
        self.assertGreater(len(notis), 0)

        # 6. Gọi Trợ lý AI tóm tắt tiến độ tuần (FR-12)
        with patch('services.ai_provider_service.AIProviderService.generate_response',
                   return_value=f'Tiến độ tuần: [Task #{task_id}] đã được cập nhật.'):
            res = self.client.post('/api/ai', json={
                'task_type': 'weekly_summary',
                'project_id': 1,
                'week_start': '2026-09-01',
                'week_end': '2026-10-01'
            })
        self.assertEqual(res.status_code, 200)
        ai_data = res.get_json()
        self.assertTrue(ai_data['success'])
        self.assertEqual(ai_data['status'], 'draft')
        draft_id = ai_data['draft_id']

        # 7. Trưởng nhóm xác nhận bản nháp chính thức (UC010)
        res = self.client.post(f'/api/ai/drafts/{draft_id}/confirm')
        self.assertEqual(res.status_code, 200)

        # Kiểm tra draft đã chuyển sang confirmed
        draft_row = query_db("SELECT status FROM ai_drafts WHERE id = %s;", (draft_id,), one=True)
        self.assertEqual(draft_row['status'], 'confirmed')

    def test_admin_blocked_from_creating_task_and_sprint(self):
        """
        Kiểm thử logic chuẩn theo tài liệu: Quản trị viên KHÔNG được tạo nhiệm vụ hay sprint (chỉ quản lý user/audit).
        """
        # Đăng nhập Admin
        self.client.post('/api/auth/login', json={'username_or_email': 'admin', 'password': 'Password123!'})

        # Thử tạo nhiệm vụ -> phải bị 403 Forbidden
        res = self.client.post('/api/projects/1/tasks', json={'title': 'Admin test task', 'priority': 'low'})
        self.assertEqual(res.status_code, 403)
        self.assertIn('không có quyền', res.get_json()['error'].lower())

        # Thử tạo sprint -> phải bị 403 Forbidden
        res = self.client.post('/api/projects/1/sprints', json={
            'name': 'Admin test sprint', 'start_date': '2026-09-01', 'end_date': '2026-09-10'
        })
        self.assertEqual(res.status_code, 403)

    def test_upload_meeting_file_and_extract_text(self):
        """
        Kiểm thử tính năng tải lên tệp biên bản cuộc họp (.txt / .docx) trích xuất nội dung (FR-13).
        """
        import io
        # Đăng nhập Leader
        self.client.post('/api/auth/login', json={'username_or_email': 'leader_long', 'password': 'Password123!'})

        # Giả lập tải lên file .txt ghi chú cuộc họp
        file_content = b"Bien ban cuoc hop nhom 33 luc 9h sang ngay 24/09. Thanh vien co mat day du. Chot xong kien truc SDLC."
        data = {
            'file': (io.BytesIO(file_content), 'meeting_notes_2409.txt')
        }
        res = self.client.post('/api/ai/upload-meeting-file', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])
        self.assertIn('nhom 33', json_data['extracted_text'])
        self.assertGreater(json_data['word_count'], 5)

if __name__ == '__main__':
    unittest.main()

