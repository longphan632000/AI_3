import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest
from app import app
from database.connection import query_db
from services.project_service import create_project, get_project_by_id
from services.sprint_service import create_sprint
from services.task_service import create_task

class TestProjectLifecycle(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def login(self, username):
        return self.client.post('/api/auth/login', json={
            'username_or_email': username,
            'password': 'Password123!'
        })

    def test_leader_can_edit_project(self):
        """Kiểm tra Leader có thể cập nhật tên, mô tả, mốc thời gian dự án thành công."""
        # Tạo dự án bởi Leader (user_id = 2)
        success, msg, project_id = create_project(
            creator_id=2,
            name="Dự án Ban Đầu",
            description="Mô tả ban đầu",
            start_date="2026-10-01",
            end_date="2026-10-15"
        )
        self.assertTrue(success)

        # Đăng nhập leader_long
        login_res = self.login('leader_long')
        self.assertEqual(login_res.status_code, 200)

        # Gửi yêu cầu cập nhật dự án
        put_res = self.client.put(f'/api/projects/{project_id}', json={
            'name': 'Dự án Đã Được Sửa Tên Hoàn Chỉnh',
            'description': 'Mô tả mục tiêu mới cập nhật',
            'start_date': '2026-10-05',
            'end_date': '2026-10-25',
            'status': 'active'
        })
        self.assertEqual(put_res.status_code, 200)
        data = put_res.get_json()
        self.assertTrue(data.get('success'))

        # Kiểm tra CSDL xem dữ liệu đã được cập nhật chính xác chưa
        updated_proj = query_db("SELECT * FROM projects WHERE id = %s", (project_id,), one=True)
        self.assertIsNotNone(updated_proj)
        self.assertEqual(updated_proj['name'], 'Dự án Đã Được Sửa Tên Hoàn Chỉnh')
        self.assertEqual(updated_proj['description'], 'Mô tả mục tiêu mới cập nhật')

    def test_empty_project_name_rejected(self):
        """Kiểm tra hệ thống chặn lỗi nếu Leader để trống tên dự án (HTTP 400)."""
        success, _, project_id = create_project(2, "Dự án Hợp Lệ", "Mô tả")
        self.assertTrue(success)

        self.login('leader_long')
        put_res = self.client.put(f'/api/projects/{project_id}', json={
            'name': '   ',  # Tên rỗng toàn khoảng trắng
            'description': 'Mô tả'
        })
        self.assertEqual(put_res.status_code, 400)
        data = put_res.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('không được để trống', data.get('error', ''))

    def test_invalid_date_range_rejected(self):
        """Kiểm tra hệ thống chặn lỗi nếu ngày bắt đầu sau ngày kết thúc (HTTP 400)."""
        success, _, project_id = create_project(2, "Dự án Ngày Sai", "Mô tả")
        self.assertTrue(success)

        self.login('leader_long')
        put_res = self.client.put(f'/api/projects/{project_id}', json={
            'name': 'Dự án Ngày Sai',
            'start_date': '2026-10-20',
            'end_date': '2026-10-10'  # Ngày kết thúc trước ngày bắt đầu!
        })
        self.assertEqual(put_res.status_code, 400)
        data = put_res.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('không được sau ngày kết thúc', data.get('error', ''))

    def test_member_cannot_edit_or_delete_project(self):
        """Kiểm tra quyền RBAC: Thành viên thường (Member) bị cấm sửa hoặc xóa dự án (HTTP 403)."""
        # Tạo dự án với leader_long (2) và thêm member_my (3)
        success, _, project_id = create_project(2, "Dự án Bảo Mật RBAC", "Mô tả", initial_member_ids=[3])
        self.assertTrue(success)

        # Đăng nhập member_my
        self.login('member_my')

        # Thử sửa dự án
        put_res = self.client.put(f'/api/projects/{project_id}', json={
            'name': 'Member cố tình đổi tên'
        })
        self.assertEqual(put_res.status_code, 403)

        # Thử xóa dự án
        del_res = self.client.delete(f'/api/projects/{project_id}')
        self.assertEqual(del_res.status_code, 403)

    def test_admin_delete_wrong_project_cascade(self):
        """BR-08: Leader bị chặn xóa vĩnh viễn; Admin được xóa và dọn dữ liệu phụ thuộc."""
        # Tạo dự án tạo sai
        success, _, project_id = create_project(2, "Dự án Nhầm Lẫn Cần Xóa", "Tạo sai cần xóa")
        self.assertTrue(success)

        # Tạo thêm 1 sprint và 1 task phụ thuộc vào dự án này
        sp_ok, _, sprint_id = create_sprint(2, project_id, "Sprint Test", "Mục tiêu", "2026-10-01", "2026-10-10", "Tiêu chuẩn hoàn thành")
        self.assertTrue(sp_ok)
        task_ok, _, task_id = create_task(2, project_id, "Task Test", "Mô tả", sprint_id=sprint_id)
        self.assertTrue(task_ok)

        # Kiểm tra trước khi xóa: các bản ghi đều tồn tại
        self.assertIsNotNone(query_db("SELECT id FROM projects WHERE id = %s", (project_id,), one=True))
        self.assertIsNotNone(query_db("SELECT id FROM sprints WHERE id = %s", (sprint_id,), one=True))
        self.assertIsNotNone(query_db("SELECT id FROM tasks WHERE id = %s", (task_id,), one=True))

        # Đăng nhập Leader và thực hiện xóa vĩnh viễn dự án
        self.login('leader_long')
        denied = self.client.delete(f'/api/projects/{project_id}?permanent=true')
        self.assertEqual(denied.status_code, 403)
        self.login('admin')
        del_res = self.client.delete(f'/api/projects/{project_id}?permanent=true')
        self.assertEqual(del_res.status_code, 200)
        data = del_res.get_json()
        self.assertTrue(data.get('success'))

        # Kiểm tra CSDL sau khi xóa: Dự án và mọi dữ liệu phụ thuộc đều đã bị xóa sạch (Cascade)
        self.assertIsNone(query_db("SELECT id FROM projects WHERE id = %s", (project_id,), one=True))
        self.assertIsNone(query_db("SELECT id FROM sprints WHERE id = %s", (sprint_id,), one=True))
        self.assertIsNone(query_db("SELECT id FROM tasks WHERE id = %s", (task_id,), one=True))
        self.assertEqual(len(query_db("SELECT id FROM project_members WHERE project_id = %s", (project_id,))), 0)

    def test_custom_project_code_and_duplicate_check(self):
        """Kiểm tra tạo dự án với mã định danh tùy chọn và ngăn chặn mã trùng lặp."""
        self.login('leader_long')
        # Tạo dự án 1 với mã JIRA-01
        res1 = self.client.post('/api/projects', json={
            'project_code': 'JIRA-01',
            'name': 'Dự án Jira Test 1',
            'start_date': '2026-10-01',
            'end_date': '2026-10-20'
        })
        self.assertEqual(res1.status_code, 201)
        data1 = res1.get_json()
        self.assertTrue(data1.get('success'))
        pid1 = data1.get('project_id')

        proj1 = query_db("SELECT project_code FROM projects WHERE id = %s", (pid1,), one=True)
        self.assertEqual(proj1['project_code'], 'JIRA-01')

        # Thử tạo dự án 2 trùng mã JIRA-01
        res2 = self.client.post('/api/projects', json={
            'project_code': 'jira-01', # Thử viết thường
            'name': 'Dự án Trùng Mã'
        })
        self.assertEqual(res2.status_code, 400)
        self.assertIn('đã tồn tại', res2.get_json().get('error', ''))

    def test_sprint_and_task_codes(self):
        """Kiểm tra mã sprint tùy chọn và mã task Jira-style tự động gắn tiền tố mã dự án."""
        success, _, project_id = create_project(2, "Dự án Auto Task", "Mô tả", project_code="AUTO")
        self.assertTrue(success)

        # Tạo sprint với mã tùy chọn SP-99
        s_ok, _, sprint_id = create_sprint(2, project_id, "Sprint 99", "Mục tiêu", "2026-10-01", "2026-10-10", "DOD", sprint_code="SP-99")
        self.assertTrue(s_ok)
        sprint_row = query_db("SELECT sprint_code FROM sprints WHERE id = %s", (sprint_id,), one=True)
        self.assertEqual(sprint_row['sprint_code'], 'SP-99')

        # Tạo task, kiểm tra task_code Jira-style tự động
        t_ok, _, task_id = create_task(2, project_id, "Nhiệm vụ Test Auto Code", sprint_id=sprint_id)
        self.assertTrue(t_ok)
        task_row = query_db("SELECT task_code FROM tasks WHERE id = %s", (task_id,), one=True)
        self.assertEqual(task_row['task_code'], f"AUTO-{task_id}")

    def test_admin_create_user_with_user_code(self):
        """Kiểm tra Admin tạo tài khoản với mã thành viên tùy chọn và kiểm tra trùng lặp."""
        from services.account_service import create_user
        # Admin tạo tài khoản mới với mã DEV-99
        u_ok, msg = create_user(1, "dev_test_99", "dev99@test.local", "Password123!", "Lập trình viên 99", role="member", user_code="DEV-99")
        self.assertTrue(u_ok)

        user_row = query_db("SELECT user_code FROM users WHERE username = 'dev_test_99'", one=True)
        self.assertEqual(user_row['user_code'], 'DEV-99')

        # Thử tạo tài khoản khác trùng mã DEV-99
        u_dup, dup_msg = create_user(1, "dev_test_100", "dev100@test.local", "Password123!", "Lập trình viên 100", role="member", user_code="dev-99")
        self.assertFalse(u_dup)
        self.assertIn("đã tồn tại", dup_msg)

if __name__ == '__main__':
    unittest.main()
