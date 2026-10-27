import unittest
from app import app
from database.connection import query_db

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_login_success(self):
        """Kiểm thử đăng nhập thành công với tài khoản active (FR-01)."""
        res = self.client.post('/api/auth/login', json={
            'username_or_email': 'leader_long',
            'password': 'Password123!'
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['username'], 'leader_long')
        self.assertEqual(data['user']['role'], 'leader')

    def test_login_locked_account(self):
        """Kiểm thử từ chối tài khoản bị khóa theo FR-01."""
        res = self.client.post('/api/auth/login', json={
            'username_or_email': 'locked_user',
            'password': 'Password123!'
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])
        self.assertIn('khóa', data['error'].lower())

    def test_login_wrong_password(self):
        """Kiểm thử từ chối mật khẩu sai."""
        res = self.client.post('/api/auth/login', json={
            'username_or_email': 'leader_long',
            'password': 'WrongPassword999'
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])

    def test_admin_redirect_to_admin_page(self):
        """Kiểm thử Admin đăng nhập thì chuyển hướng vào /admin chứ không vào dashboard dự án."""
        res = self.client.post('/api/auth/login', json={
            'username_or_email': 'admin',
            'password': 'Password123!'
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['user']['role'], 'admin')
        self.assertIn('/admin', data['redirect_url'])

    def test_register_new_user_success(self):
        """Kiểm thử đăng ký tài khoản mới thành công."""
        import time
        ts = int(time.time())
        res = self.client.post('/api/auth/register', json={
            'full_name': 'Test New Member',
            'username': f'test_user_{ts}',
            'email': f'test_{ts}@example.com',
            'password': 'Password123!',
            'role': 'member'
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 202)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'member')
        self.assertEqual(data['user']['status'], 'pending')

    def test_register_duplicate_username(self):
        """Kiểm thử đăng ký trùng tên đăng nhập bị từ chối."""
        res = self.client.post('/api/auth/register', json={
            'full_name': 'Trùng Tên',
            'username': 'leader_long',
            'email': 'unique_email_123@example.com',
            'password': 'Password123!',
            'role': 'member'
        })
        data = res.get_json()
        self.assertEqual(res.status_code, 400)
        self.assertFalse(data['success'])
        self.assertIn('sử dụng', data['error'].lower())

if __name__ == '__main__':
    unittest.main()

