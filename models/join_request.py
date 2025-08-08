from database import db
from datetime import datetime
from enum import Enum

class JoinRequestStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class JoinRequest(db.Model):
    __tablename__ = 'join_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    status = db.Column(db.Enum(JoinRequestStatus), default=JoinRequestStatus.PENDING, nullable=False)
    message = db.Column(db.Text, nullable=True)  # Message from user
    admin_message = db.Column(db.Text, nullable=True)  # Response from admin/leader
    
    # Who processed the request
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='join_requests')
    group = db.relationship('Group', backref='join_requests')
    processed_by = db.relationship('User', foreign_keys=[processed_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': {
                'id': self.user.id,
                'name': self.user.name,
                'email': self.user.email,
                'employee_code': self.user.employee_code,
                'role': self.user.role
            } if self.user else None,
            'group': {
                'id': self.group.id,
                'name': self.group.name,
                'description': self.group.description
            } if self.group else None,
            'status': self.status.value,
            'message': self.message,
            'admin_message': self.admin_message,
            'processed_by': {
                'id': self.processed_by.id,
                'name': self.processed_by.name
            } if self.processed_by else None,
            'processed_at': self.processed_at.strftime('%Y-%m-%d %H:%M:%S') if self.processed_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }