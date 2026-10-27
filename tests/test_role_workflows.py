import unittest
from uuid import uuid4

from app import app
from database.init_db import init_sqlite_fallback
from database.connection import query_db


class TestRoleWorkflows(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def login(self, username):
        return self.client.post('/api/auth/login', json={
            'username_or_email': username, 'password': 'Password123!'
        })

    def register_leader(self):
        username = 'leader_' + uuid4().hex[:12]
        response = self.client.post('/api/auth/register', json={
            'username': username, 'email': username + '@example.test',
            'password': 'Password123!', 'full_name': 'New Leader', 'role': 'leader'
        })
        self.assertEqual(response.status_code, 202)
        return username, response.get_json()['user']

    def test_leader_requires_admin_approval_and_project_assignment(self):
        username, user = self.register_leader()
        self.assertEqual(user['status'], 'pending')
        self.assertEqual(self.login(username).status_code, 401)

        self.assertEqual(self.login('admin').status_code, 200)
        response = self.client.post(f"/api/admin/users/{user['id']}/review", json={'decision': 'approve'})
        self.assertEqual(response.status_code, 200)
        self.client.post('/logout')

        self.assertEqual(self.login(username).status_code, 200)
        sprint_data = {'name': 'New Sprint', 'start_date': '2026-09-01', 'end_date': '2026-09-02'}
        self.assertEqual(self.client.post('/api/projects/1/sprints', json=sprint_data).status_code, 403)
        project = self.client.post('/api/projects', json={'name': 'New project'})
        self.assertEqual(project.status_code, 201)
        project_id = project.get_json()['project_id']
        self.assertEqual(self.client.post(f'/api/projects/{project_id}/sprints', json=sprint_data).status_code, 201)

    def test_rejected_leader_cannot_log_in(self):
        username, user = self.register_leader()
        self.login('admin')
        response = self.client.post(f"/api/admin/users/{user['id']}/review", json={'decision': 'reject'})
        self.assertEqual(response.status_code, 200)
        self.client.post('/logout')
        self.assertEqual(self.login(username).status_code, 401)

    def test_admin_can_assign_approved_leader_to_existing_project(self):
        username, user = self.register_leader()
        self.login('admin')
        self.assertEqual(self.client.post(f"/api/admin/users/{user['id']}/review", json={
            'decision': 'approve'
        }).status_code, 200)
        membership = self.client.post('/api/projects/1/members', json={
            'user_id': user['id'], 'project_role': 'member'
        })
        self.assertEqual(membership.status_code, 200)
        assignment = self.client.post('/api/admin/projects/1/leaders', json={
            'user_id': user['id']
        })
        self.assertEqual(assignment.status_code, 200)
        leaders = self.client.get('/api/admin/projects/1/leaders').get_json()['leaders']
        self.assertTrue(any(leader['user_id'] == user['id'] for leader in leaders))
        self.client.post('/logout')
        self.assertEqual(self.login(username).status_code, 200)
        response = self.client.post('/api/projects/1/sprints', json={
            'name': 'Assigned leader sprint', 'start_date': '2026-09-01', 'end_date': '2026-09-02'
        })
        self.assertEqual(response.status_code, 201)
        admin = app.test_client()
        admin.post('/api/auth/login', json={
            'username_or_email': 'admin', 'password': 'Password123!'
        })
        self.assertEqual(admin.delete(f"/api/admin/projects/1/leaders/{user['id']}").status_code, 200)
        self.assertEqual(self.client.post('/api/projects/1/sprints', json={
            'name': 'No longer leader', 'start_date': '2026-09-03', 'end_date': '2026-09-04'
        }).status_code, 403)

    def test_admin_can_reopen_rejected_request(self):
        username, user = self.register_leader()
        self.login('admin')
        url = f"/api/admin/users/{user['id']}/review"
        self.assertEqual(self.client.post(url, json={'decision': 'reject'}).status_code, 200)
        self.assertEqual(self.client.post(url, json={'decision': 'reopen'}).status_code, 200)
        self.assertEqual(self.client.post(url, json={'decision': 'approve'}).status_code, 200)
        self.client.post('/logout')
        self.assertEqual(self.login(username).status_code, 200)

    def test_admin_page_and_account_validation(self):
        self.assertEqual(self.client.get('/api/system/db-status').status_code, 403)
        self.login('admin')
        page = self.client.get('/admin')
        self.assertEqual(page.status_code, 200)
        self.assertIn('pending-requests-list', page.get_data(as_text=True))
        self.assertEqual(self.client.post('/api/admin/users', json={
            'username': 'x', 'email': 'invalid', 'password': '1',
            'full_name': '', 'role': 'invalid'
        }).status_code, 400)
        self.assertEqual(self.client.post('/api/admin/users/1/role', json={'role': 'member'}).status_code, 400)

    def test_member_cannot_manage_tasks_or_sprints(self):
        self.assertEqual(self.login('member_my').status_code, 200)
        html = self.client.get('/kanban').get_data(as_text=True)
        self.assertIn('id="create-task-button"', html)
        self.assertIn('style="display:none;"', html)
        self.assertEqual(self.client.post('/api/projects/1/tasks', json={'title': 'No'}).status_code, 403)
        self.assertEqual(self.client.put('/api/tasks/1', json={'title': 'No'}).status_code, 403)
        self.assertEqual(self.client.post('/api/tasks/1/assign-sprint', json={'sprint_id': 2}).status_code, 403)
        self.assertEqual(self.client.get('/api/projects/1/eligible-users').status_code, 403)
        self.assertEqual(self.client.put('/api/tasks/3/status', json={'status': 'review'}).status_code, 200)

    def test_task_references_must_belong_to_project(self):
        self.assertEqual(self.login('leader_long').status_code, 200)
        project = self.client.post('/api/projects', json={'name': 'Isolated project'})
        self.assertEqual(project.status_code, 201)
        project_id = project.get_json()['project_id']
        url = f'/api/projects/{project_id}/tasks'
        self.assertEqual(self.client.post(url, json={'title': 'Bad sprint', 'sprint_id': 1}).status_code, 400)
        self.assertEqual(self.client.post(url, json={'title': 'Bad assignee', 'assignee_id': 3}).status_code, 400)
        eligible = self.client.get(f'/api/projects/{project_id}/eligible-users')
        self.assertEqual(eligible.status_code, 200)
        self.assertTrue(any(user['id'] == 3 for user in eligible.get_json()['users']))
        self.assertEqual(self.client.post(f'/api/projects/{project_id}/members', json={
            'user_id': 3, 'project_role': 'member'
        }).status_code, 200)
        self.assertEqual(self.client.post(url, json={'title': 'Assigned task', 'assignee_id': 3}).status_code, 201)
        task = self.client.post(url, json={'title': 'Good task'})
        self.assertEqual(task.status_code, 201)
        task_id = task.get_json()['task_id']
        self.assertEqual(self.client.post(f'/api/tasks/{task_id}/assign-sprint', json={'sprint_id': 1}).status_code, 400)
        self.assertEqual(self.client.post(f'/api/projects/{project_id}/members', json={
            'user_id': 4, 'project_role': 'leader'
        }).status_code, 400)

    def test_locked_user_session_is_revoked(self):
        member = app.test_client()
        admin = app.test_client()
        member.post('/api/auth/login', json={'username_or_email': 'member_khanh', 'password': 'Password123!'})
        admin.post('/api/auth/login', json={'username_or_email': 'admin', 'password': 'Password123!'})
        self.assertEqual(admin.post('/api/admin/users/4/status', json={'status': 'locked'}).status_code, 200)
        self.assertEqual(member.get('/api/projects').status_code, 401)
        admin.post('/api/admin/users/4/status', json={'status': 'active'})

    def test_role_demotion_takes_effect_in_existing_session(self):
        username, user = self.register_leader()
        admin = app.test_client()
        admin.post('/api/auth/login', json={
            'username_or_email': 'admin', 'password': 'Password123!'
        })
        admin.post(f"/api/admin/users/{user['id']}/review", json={'decision': 'approve'})
        self.assertEqual(self.login(username).status_code, 200)
        project = self.client.post('/api/projects', json={'name': 'Role change project'})
        project_id = project.get_json()['project_id']
        self.assertEqual(admin.post(f"/api/admin/users/{user['id']}/role", json={
            'role': 'member'
        }).status_code, 200)
        self.assertEqual(self.client.post(f'/api/projects/{project_id}/sprints', json={
            'name': 'Denied sprint', 'start_date': '2026-09-01', 'end_date': '2026-09-02'
        }).status_code, 403)

    def test_sqlite_initialization_preserves_existing_accounts(self):
        username = 'persist_' + uuid4().hex[:12]
        response = self.client.post('/api/auth/register', json={
            'username': username, 'email': username + '@example.test',
            'password': 'Password123!', 'full_name': 'Persistent Member', 'role': 'member'
        })
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()['user']['status'], 'pending')
        init_sqlite_fallback()
        self.assertIsNotNone(query_db('SELECT id FROM users WHERE username = %s;', (username,), one=True))

    def test_admin_delete_user_workflow(self):
        # 1. Non-admin cannot delete user
        self.login('member_my')
        self.assertEqual(self.client.delete('/api/admin/users/4').status_code, 403)

        # 2. Login admin
        self.login('admin')

        # 3. Admin cannot delete self
        self.assertEqual(self.client.delete('/api/admin/users/1').status_code, 400)

        # 4. Cannot delete non-existent user
        self.assertEqual(self.client.delete('/api/admin/users/999999').status_code, 400)

        # 5. Create a temporary user to delete
        temp_username = 'delete_me_' + uuid4().hex[:8]
        reg = self.client.post('/api/admin/users', json={
            'username': temp_username,
            'email': f'{temp_username}@example.com',
            'password': 'Password123!',
            'full_name': 'To Be Deleted',
            'role': 'member'
        })
        self.assertEqual(reg.status_code, 200)
        target = query_db('SELECT id FROM users WHERE username = %s;', (temp_username,), one=True)
        self.assertIsNotNone(target)
        target_id = target['id']

        # 6. Delete user successfully
        del_res = self.client.delete(f'/api/admin/users/{target_id}')
        self.assertEqual(del_res.status_code, 200)
        self.assertIn('Đã xóa vĩnh viễn', del_res.get_json()['message'])

        # 7. Verify user removed from DB
        after = query_db('SELECT id FROM users WHERE id = %s;', (target_id,), one=True)
        self.assertIsNone(after)

        # 8. Verify audit log entry
        audit = query_db("SELECT action, target_type, target_id FROM audit_logs WHERE action = 'DELETE_USER' AND target_id = %s;", (target_id,), one=True)
        self.assertIsNotNone(audit)
        self.assertEqual(audit['action'], 'DELETE_USER')


if __name__ == '__main__':
    unittest.main()


