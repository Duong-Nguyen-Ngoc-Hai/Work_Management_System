# Thêm vào models/notification.py
from database import db
from datetime import datetime
from enum import Enum

class NotificationType(Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_OVERDUE = "task_overdue"
    TASK_DEADLINE_SOON = "task_deadline_soon"
    GROUP_JOINED = "group_joined"
    GROUP_REMOVED = "group_removed"
    GROUP_JOIN_REQUEST = "group_join_request"
    GROUP_JOIN_APPROVED = "group_join_approved"
    GROUP_JOIN_REJECTED = "group_join_rejected"
    ROLE_CHANGED = "role_changed"
    REPORT_GENERATED = "report_generated"
    SYSTEM_ANNOUNCEMENT = "system_announcement"

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    # Related entity IDs (optional)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=True)
    
    # Notification state
    is_read = db.Column(db.Boolean, default=False)
    is_important = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    task = db.relationship('Task', backref='notifications')
    group = db.relationship('Group', backref='notifications')
    report = db.relationship('Report', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'is_read': self.is_read,
            'is_important': self.is_important,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M:%S') if self.read_at else None,
            'task_id': self.task_id,
            'group_id': self.group_id,
            'report_id': self.report_id
        }