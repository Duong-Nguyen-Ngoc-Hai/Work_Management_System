# models/group.py
from database import db

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Quan hệ
    leader = db.relationship('User', foreign_keys=[leader_id], backref='led_groups')
    
    def __repr__(self):
        return f'<Group {self.name}>'