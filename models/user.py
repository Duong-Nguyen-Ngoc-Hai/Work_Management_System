# models/user.py - CẬP NHẬT
from database import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(20), unique=True, nullable=True)  # MÃ NHÂN VIÊN - THÊM MỚI
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('employee', 'leader', 'admin'), default='employee', nullable=False)  # THÊM ADMIN
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)  # THÊM GROUP
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)  # TRẠNG THÁI ACTIVE/INACTIVE

    # Quan hệ
    group = db.relationship('Group', foreign_keys=[group_id], backref='members')
    tasks_assigned = db.relationship('Task', backref='assigner', foreign_keys='Task.assigner_id', lazy=True)
    tasks_received = db.relationship('Task', backref='assignee', foreign_keys='Task.assignee_id', lazy=True)
    uploaded_files = db.relationship('File', backref='uploader', foreign_keys='File.uploaded_by', lazy=True)
    reports = db.relationship('Report', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'