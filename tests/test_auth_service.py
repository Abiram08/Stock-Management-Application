"""
Unit tests for services/auth_service.py — login, user CRUD, and password management.
"""
import pytest
from services.auth_service import AuthService
from database.models import User


class TestLogin:
    def test_login_success(self, admin_user):
        service = AuthService()
        result = service.login('admin', 'admin123')
        assert result is not None
        assert result.username == 'admin'

    def test_login_wrong_password(self, admin_user):
        service = AuthService()
        result = service.login('admin', 'wrongpassword')
        assert result is None

    def test_login_nonexistent_user(self):
        service = AuthService()
        result = service.login('ghost', 'password')
        assert result is None

    def test_logout(self, admin_user):
        service = AuthService()
        service.login('admin', 'admin123')
        assert service.is_authenticated()
        service.logout()
        assert not service.is_authenticated()


class TestCreateUser:
    def test_create_user(self):
        user = AuthService.create_user('newuser', 'pass1234', 'SUPERVISOR')
        assert user.username == 'newuser'
        assert user.role == 'SUPERVISOR'
        # Password should be hashed, not plain
        assert user.password != 'pass1234'
        assert user.check_password('pass1234')

    def test_create_duplicate_username(self, admin_user):
        with pytest.raises(ValueError, match="already exists"):
            AuthService.create_user('admin', 'newpassword', 'SUPERVISOR')


class TestUpdatePassword:
    def test_update_password(self, admin_user):
        AuthService.update_password(admin_user.id, 'newpass456')
        user = User.get_by_id(admin_user.id)
        assert user.check_password('newpass456')
        assert not user.check_password('admin123')


class TestUpdateRole:
    def test_update_role(self, admin_user):
        AuthService.update_user_role(admin_user.id, 'STORE_MANAGER')
        user = User.get_by_id(admin_user.id)
        assert user.role == 'STORE_MANAGER'


class TestDeleteUser:
    def test_delete_normal_user(self, supervisor_user):
        AuthService.delete_user(supervisor_user.id)
        assert User.select().where(User.username == 'supervisor').count() == 0

    def test_cannot_delete_admin(self, admin_user):
        with pytest.raises(ValueError, match="Cannot delete"):
            AuthService.delete_user(admin_user.id)


class TestGetAllUsers:
    def test_get_all_users(self, admin_user, supervisor_user):
        users = AuthService.get_all_users()
        assert len(users) == 2
        usernames = [u.username for u in users]
        assert 'admin' in usernames
        assert 'supervisor' in usernames
