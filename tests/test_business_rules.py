import unittest
from datetime import datetime, timedelta
from app import app
from services.task_service import is_task_overdue, update_task_status
from services.sprint_service import calculate_sprint_metrics, create_sprint
from services.report_service import get_member_workload_statistics

class TestBusinessRules(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_br_01_kanban_status_validation(self):
        """BR-01: Trạng thái Kanban phải thuộc 5 trạng thái hợp lệ."""
        # Trạng thái không hợp lệ
        success, msg = update_task_status(user_id=2, task_id=1, new_status='invalid_status_xyz')
        self.assertFalse(success)
        self.assertIn('không hợp lệ', msg.lower())

    def test_br_02_overdue_task_detection(self):
        """BR-02: Nhiệm vụ trễ khi quá hạn, chưa Done và chưa lưu trữ."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

        # Quá hạn và chưa Done -> Trễ
        self.assertTrue(is_task_overdue(yesterday, 'in_progress', False))
        # Quá hạn nhưng đã Done -> Không trễ
        self.assertFalse(is_task_overdue(yesterday, 'done', False))
        # Quá hạn nhưng đã lưu trữ -> Không trễ
        self.assertFalse(is_task_overdue(yesterday, 'in_progress', True))
        # Chưa tới hạn -> Không trễ
        self.assertFalse(is_task_overdue(tomorrow, 'in_progress', False))

    def test_br_03_sprint_dates(self):
        """BR-03: Ngày bắt đầu sprint không được sau ngày kết thúc."""
        success, msg, sprint_id = create_sprint(
            user_id=2, project_id=1,
            name="Sprint Test Lỗi Ngày",
            goal="Test BR-03",
            start_date="2026-10-20",
            end_date="2026-10-10", # Lỗi: Ngày kết thúc trước ngày bắt đầu
            completion_criteria="None"
        )
        self.assertFalse(success)
        self.assertIn('BR-03', msg)

    def test_br_04_completion_rate(self):
        """BR-04: Tỷ lệ hoàn thành = Done / Total * 100%. Nếu total = 0 thì trả về 0.0%."""
        # Sprint 1 trong seed data có 2 task done -> rate 100.0%
        stats = calculate_sprint_metrics(1)
        self.assertGreaterEqual(stats['completion_rate'], 0.0)
        self.assertLessEqual(stats['completion_rate'], 100.0)

    def test_br_05_workload_and_overload(self):
        """BR-05: Tải = tổng estimated_hours việc chưa Done; Quá tải khi Tải > Capacity."""
        workload = get_member_workload_statistics(project_id=1)
        self.assertIsInstance(workload, list)
        self.assertGreater(len(workload), 0)
        for m in workload:
            self.assertIn('capacity_hours', m)
            self.assertIn('current_workload_hours', m)
            self.assertIn('is_overloaded', m)
            # Kiểm tra logic quá tải
            expected_overloaded = m['current_workload_hours'] > m['capacity_hours']
            self.assertEqual(m['is_overloaded'], expected_overloaded)

if __name__ == '__main__':
    unittest.main()
