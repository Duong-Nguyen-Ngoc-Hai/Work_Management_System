# models/task.py - CẬP NHẬT
from database import db

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum('todo', 'doing', 'done'), default='todo', nullable=False)
    priority = db.Column(db.Enum('low', 'medium', 'high'), default='medium', nullable=False)  # THÊM PRIORITY
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Foreign keys
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    assigner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)  # THÊM GROUP_ID

    # Quan hệ
    group = db.relationship('Group', backref='tasks')
    subtasks = db.relationship('Task', backref=db.backref('parent_task', remote_side=[id]), lazy=True)
    files = db.relationship('File', backref='task', lazy=True)

    def __repr__(self):
        return f'<Task {self.title}>'