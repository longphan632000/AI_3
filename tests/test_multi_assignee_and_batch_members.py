import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest
from datetime import datetime, timedelta
from app import app
from database.connection import get_db_connection, query_db
from services.project_service import create_project
from services.project_member_service import add_project_members, get_project_members
from services.task_service import create_task, update_task_details, get_task_by_id

class TestMultiAssigneeAndBatchMembers(unittest.TestCase):
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

    def test_01_create_project_with_initial_members(self):
        """Kiểm tra tạo dự án mới kèm danh sách nhiều thành viên ban đầu."""
        # Leader user_id = 2 (leader_long), thêm member 3 (member_my) và member 4 (member_khanh)
        success, msg, project_id = create_project(
            creator_id=2,
            name="Dự án Test Multi-Members",
            description="Kiểm tra gán nhiều thành viên cùng lúc",
            initial_member_ids=[3, 4]
        )
        self.assertTrue(success, f"Tạo dự án thất bại: {msg}")
        self.assertIsNotNone(project_id)

        # Kiểm tra danh sách thành viên dự án
        members = get_project_members(project_id)
        member_user_ids = [m['user_id'] for m in members]
        self.assertIn(2, member_user_ids, "Leader phải có trong dự án")
        self.assertIn(3, member_user_ids, "Thành viên 3 phải có trong dự án")
        self.assertIn(4, member_user_ids, "Thành viên 4 phải có trong dự án")

    def test_02_batch_add_project_members(self):
        """Kiểm tra thêm hàng loạt thành viên vào dự án hiện có."""
        # Tạo dự án chỉ có Leader
        success, msg, project_id = create_project(
            creator_id=2,
            name="Dự án Test Batch Add",
            description="Test thêm nhiều thành viên một lần",
            initial_member_ids=[]
        )
        self.assertTrue(success)

        # Batch add user 3 và user 4
        success, msg, added_count = add_project_members(
            leader_id=2,
            project_id=project_id,
            user_ids=[3, 4],
            project_role='member'
        )
        self.assertTrue(success, f"Thêm hàng loạt thất bại: {msg}")
        self.assertEqual(added_count, 2)

        members = get_project_members(project_id)
        current_ids = [m['user_id'] for m in members]
        self.assertIn(3, current_ids)
        self.assertIn(4, current_ids)

    def test_03_create_task_with_multi_assignees(self):
        """Kiểm tra tạo nhiệm vụ với 1 người phụ trách chính + nhiều người hỗ trợ."""
        _, _, project_id = create_project(
            creator_id=2,
            name="Dự án Test Task Multi Assignee",
            description="Testing",
            initial_member_ids=[3, 4]
        )

        # Tạo task: assignee chính = 3, hỗ trợ = [4]
        success, msg, task_id = create_task(
            user_id=2,
            project_id=project_id,
            title="Nhiệm vụ kiểm thử đa thành viên",
            description="Phân công 1 chính, 1 hỗ trợ",
            assignee_id=3,
            support_member_ids=[4],
            priority='high',
            estimated_hours=12.0
        )
        self.assertTrue(success, f"Tạo task thất bại: {msg}")

        # Lấy thông tin task
        task = get_task_by_id(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task['assignee_id'], 3)
        self.assertEqual(task['support_count'], 1)
        
        support_ids = task['support_member_ids']
        self.assertIn(4, support_ids)

        # Kiểm tra trực tiếp bảng task_assignees trong CSDL qua query_db
        rows = query_db("SELECT * FROM task_assignees WHERE task_id = %s", (task_id,))
        self.assertEqual(len(rows), 2)
        primary_row = [r for r in rows if r['is_primary'] == 1]
        support_rows = [r for r in rows if r['is_primary'] == 0]
        self.assertEqual(len(primary_row), 1)
        self.assertEqual(primary_row[0]['user_id'], 3)
        self.assertEqual(len(support_rows), 1)
        self.assertEqual(support_rows[0]['user_id'], 4)

    def test_04_leader_rescue_overdue_task(self):
        """Kiểm tra Leader điều phối, bổ sung hỗ trợ cứu viện task trễ hạn (BR-02)."""
        _, _, project_id = create_project(
            creator_id=2,
            name="Dự án Test Rescue Overdue",
            description="Testing BR-02 rescue",
            initial_member_ids=[3, 4]
        )

        # Tạo task trễ hạn (due_date trong quá khứ)
        past_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        success, msg, task_id = create_task(
            user_id=2,
            project_id=project_id,
            title="Task trễ hạn cần cứu viện khẩn cấp",
            description="Quá hạn cần thêm người gấp",
            assignee_id=3,
            due_date=past_date,
            support_member_ids=[]
        )
        self.assertTrue(success)

        # Leader bổ sung thành viên 4 vào hỗ trợ cứu viện và gia hạn due_date
        new_due_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
        old_task = get_task_by_id(task_id)
        ok, update_msg = update_task_details(
            user_id=2,
            task_id=task_id,
            title=old_task['title'],
            description=old_task['description'],
            sprint_id=old_task['sprint_id'],
            assignee_id=3,
            priority=old_task['priority'],
            due_date=new_due_date,
            estimated_hours=old_task['estimated_hours'],
            labels=old_task['labels'],
            blockers=old_task['blockers'],
            support_member_ids=[4]
        )
        self.assertTrue(ok, f"Cứu viện task thất bại: {update_msg}")

        # Kiểm tra thông tin cập nhật
        task = get_task_by_id(task_id)
        self.assertEqual(task['support_count'], 1)
        self.assertIn(4, task['support_member_ids'])

        # Kiểm tra thông báo cứu viện trễ hạn đã được gửi đến thành viên hỗ trợ (FR-16)
        rescue_notif = query_db(
            "SELECT * FROM notifications WHERE user_id = 4 AND (message LIKE %s OR title LIKE %s) ORDER BY id DESC LIMIT 1",
            ('%cứu viện%', '%cứu viện%'),
            one=True
        )
        self.assertIsNotNone(rescue_notif, "Phải có thông báo cứu viện trễ hạn gửi tới thành viên hỗ trợ")

    def test_05_api_rbac_member_cannot_reassign_or_rescue(self):
        """Kiểm tra quyền hạn (RBAC) qua API: Member không được quyền điều phối/cứu viện task."""
        _, _, project_id = create_project(
            creator_id=2,
            name="Dự án Test RBAC API Rescue",
            description="Testing RBAC",
            initial_member_ids=[3, 4]
        )

        _, _, task_id = create_task(
            user_id=2,
            project_id=project_id,
            title="Task bảo vệ RBAC",
            description="Test RBAC",
            assignee_id=3,
            support_member_ids=[]
        )

        # Đăng nhập bằng Member (member_my)
        self.login('member_my')
        res = self.client.put(f'/api/tasks/{task_id}', json={
            'assignee_id': 4,
            'support_member_ids': [3]
        })
        self.assertEqual(res.status_code, 403, "Thành viên thường không được phép gọi API cập nhật phân công nhiệm vụ")

        # Đăng nhập bằng Leader (leader_long)
        self.login('leader_long')
        res_leader = self.client.put(f'/api/tasks/{task_id}', json={
            'assignee_id': 4,
            'support_member_ids': [3]
        })
        self.assertEqual(res_leader.status_code, 200, "Trưởng nhóm phải cập nhật phân công nhiệm vụ thành công")

if __name__ == '__main__':
    unittest.main()
