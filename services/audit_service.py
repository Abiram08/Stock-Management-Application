from database.models import AuditLog, User, db
from peewee import JOIN
import json
import datetime


class AuditService:
    """Central service for audit logging and retrieval."""

    @staticmethod
    def log(action, user=None, details=None):
        """
        Log an action to the audit trail.
        
        Args:
            action: Action type string (e.g., 'MATERIAL_CREATED', 'MRS_ISSUED')
            user: User model instance (optional)
            details: Dict of additional context (will be JSON serialized)
        """
        try:
            AuditLog.create(
                action=action,
                user=user,
                details=json.dumps(details) if details else None
            )
        except Exception as e:
            print(f"Audit log error: {e}")

    @staticmethod
    def get_logs(action_filter=None, user_filter=None, date_from=None, date_to=None, limit=200):
        """
        Get audit logs with optional filters.
        
        Returns list of AuditLog records.
        """
        query = (AuditLog
                 .select(AuditLog, User)
                 .join(User, on=(AuditLog.user == User.id), join_type=JOIN.LEFT_OUTER)
                 .order_by(AuditLog.timestamp.desc()))

        if action_filter and action_filter != 'ALL':
            query = query.where(AuditLog.action == action_filter)

        if user_filter and user_filter != 'ALL':
            query = query.where(User.username == user_filter)

        if date_from:
            query = query.where(AuditLog.timestamp >= date_from)

        if date_to:
            # Include the full end day
            end = datetime.datetime.combine(date_to, datetime.time.max)
            query = query.where(AuditLog.timestamp <= end)

        return list(query.limit(limit))

    @staticmethod
    def get_action_types():
        """Get all distinct action types for filter dropdowns."""
        actions = (AuditLog
                   .select(AuditLog.action)
                   .distinct()
                   .order_by(AuditLog.action))
        return [a.action for a in actions]
