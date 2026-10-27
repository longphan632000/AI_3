import unittest
from datetime import datetime, timedelta
from app import app
from database.connection import query_db, execute_db
from services.project_service import create_project
from services.task_service import create_task, get_task_by_id, archive_task
from services.report_service import get_member_workload_statistics
from services.notification_service import scan_and_create_deadline_notifications, get_user_notifications

class TestFiveImprovements(unittest.TestCase):
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

    def test_01_supporter_workload_and_overdue_included(self):
        """Lỗi 1: Kiểm tra thành viên hỗ trợ (My - user 3) được tính đúng số việc và việc trễ hạn."""
        # Tạo dự án với Leader (user 2), Thành viên 1 (Long - user 2 hoặc user 4), My (user 3)
        success, msg, project_id = create_project(
            creator_id=2,
            name="Dự án Kiểm Thử Tải Việc Hỗ Trợ",
            description="Test BR-05 multi-assignee workload",
            initial_member_ids=[3, 4]
        )
        self.assertTrue(success)

        # Tạo một task trễ hạn, phụ trách chính = 4, người cùng hỗ trợ = 3 (Lưu Trà My)
        yesterday = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        ok, _, task_id = create_task(
            user_id=2,
            project_id=project_id,
            title="Task trễ hạn cần hỗ trợ khẩn cấp",
            description="Test workload attribution",
            assignee_id=4,
            support_member_ids=[3],
            priority='high',
            due_date=yesterday,
            estimated_hours=8.0
        )
        self.assertTrue(ok)

        # Lấy báo cáo phân bổ tải công việc
        workload = get_member_workload_statistics(project_id)
        my_stats = next((w for w in workload if w['user_id'] == 3), None)
        self.assertIsNotNone(my_stats, "Lưu Trà My phải có trong báo cáo thành viên")

        # Kiểm tra: My phải có 1 việc đang làm, 1 việc trễ hạn và 8.0 giờ tải
        self.assertEqual(my_stats['active_task_count'], 1, "My phải được tính 1 active task do tham gia hỗ trợ")
        self.assertEqual(my_stats['overdue_task_count'], 1, "My phải được tính 1 task trễ hạn do task tham gia bị quá hạn")
        self.assertEqual(my_stats['current_workload_hours'], 8.0, "My phải được ghi nhận 8 giờ tải của task hỗ trợ")

    def test_02_delete_task_api_and_rbac(self):
        """Lỗi 2: Kiểm tra chức năng xóa nhiệm vụ và bảo vệ quyền Leader."""
        _, _, project_id = create_project(
            creator_id=2,
            name="Dự án Test Delete Task",
            description="Test delete",
            initial_member_ids=[3]
        )
        _, _, task_id = create_task(
            user_id=2,
            project_id=project_id,
            title="Task chuẩn bị xóa",
            assignee_id=3
        )

        # Thành viên thường (user 3) cố xóa -> 403 Forbidden
        self.login('member_my')
        res_member = self.client.delete(f'/api/tasks/{task_id}')
        self.assertEqual(res_member.status_code, 403)

        # Leader (user 2) xóa task -> 200 OK
        self.login('leader_long')
        res_leader = self.client.delete(f'/api/tasks/{task_id}')
        self.assertEqual(res_leader.status_code, 200)

        # Task đã bị lưu trữ / xóa khỏi board
        task = get_task_by_id(task_id)
        self.assertTrue(task['is_archived'])

    def test_03_automated_overdue_and_due_soon_notifications(self):
        """Lỗi 4: Kiểm tra tự động phát thông báo nhiệm vụ trễ hạn & sắp trễ hạn cho cả chính và hỗ trợ."""
        _, _, project_id = create_project(
            creator_id=2,
            name="Dự án Test Deadline Notifications",
            description="Test FR-16 automated reminders",
            initial_member_ids=[3, 4]
        )

        # 1. Task trễ hạn (due_date quá khứ)
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        _, _, overdue_task_id = create_task(
            user_id=2,
            project_id=project_id,
            title="Task đã trễ hạn hôm qua",
            assignee_id=3,
            support_member_ids=[4],
            due_date=past_date
        )

        # 2. Task sắp trễ hạn (due_date trong vòng 12 tiếng tới)
        soon_date = (datetime.now() + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
        _, _, soon_task_id = create_task(
            user_id=2,
            project_id=project_id,
            title="Task sắp đến hạn tối nay",
            assignee_id=4,
            support_member_ids=[3],
            due_date=soon_date
        )

        # One overdue notice may already exist from the post-commit email scan.
        before = query_db("SELECT COUNT(*) AS n FROM notifications WHERE project_id=%s AND event_type IN ('task_overdue','due_soon_reminder')", (project_id,), one=True)['n']
        # Quét thông báo tự động
        new_count = scan_and_create_deadline_notifications(target_project_id=project_id)
        self.assertGreaterEqual(before + new_count, 4, "Phải tạo ít nhất 4 thông báo (2 cho task trễ + 2 cho task sắp trễ)")

        # Kiểm tra thông báo của User 3 (My): phải nhận được cả 2 loại thông báo
        my_notifs = get_user_notifications(user_id=3, limit=10)
        events = [n['event_type'] for n in my_notifs]
        self.assertIn('task_overdue', events, "My phải nhận được thông báo task_overdue")
        self.assertIn('due_soon_reminder', events, "My phải nhận được thông báo due_soon_reminder")

        # Quét lần 2 ngay lập tức -> Không tạo trùng (anti-spam 24h)
        repeat_count = scan_and_create_deadline_notifications(target_project_id=project_id)
        self.assertEqual(repeat_count, 0, "Không được tạo trùng lặp thông báo trong vòng 24 giờ")

if __name__ == '__main__':
    unittest.main()
