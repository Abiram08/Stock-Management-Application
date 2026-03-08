from database.models import User, AuditLog, db
import bcrypt
import json
import datetime


class AuthService:
    def __init__(self):
        self.current_user = None

    def login(self, username, password):
        try:
            user = User.get(User.username == username)
            if user.check_password(password):
                self.current_user = user
                # Log the login
                AuditLog.create(
                    action='USER_LOGIN',
                    user=user,
                    details=json.dumps({'username': username})
                )
                return user
            else:
                return None
        except User.DoesNotExist:
            return None

    def logout(self):
        if self.current_user:
            AuditLog.create(
                action='USER_LOGOUT',
                user=self.current_user,
                details=json.dumps({'username': self.current_user.username})
            )
        self.current_user = None

    def is_authenticated(self):
        return self.current_user is not None

    @staticmethod
    def create_user(username, password, role):
        """Create a new user with hashed password."""
        if User.select().where(User.username == username).exists():
            raise ValueError(f"Username '{username}' already exists.")
        user = User(username=username, role=role)
        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def update_password(user_id, new_password):
        """Update a user's password."""
        user = User.get_by_id(user_id)
        user.set_password(new_password)
        user.save()
        return user

    @staticmethod
    def get_all_users():
        """Get all users."""
        return list(User.select().order_by(User.created_at.desc()))

    @staticmethod
    def update_user_role(user_id, new_role):
        """Update user role."""
        user = User.get_by_id(user_id)
        user.role = new_role
        user.save()
        return user

    @staticmethod
    def delete_user(user_id):
        """Delete a user (cannot delete admin)."""
        user = User.get_by_id(user_id)
        if user.username == 'admin':
            raise ValueError("Cannot delete the default admin account.")
        user.delete_instance()
        return True
