# setup_db.py - CẬP NHẬT
from app import create_app
from database import db
from models.user import User
from models.group import Group
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Tạo bảng
    db.create_all()
    
    # Tạo admin mặc định nếu chưa có
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            employee_code='ADMIN001',
            name='System Administrator',
            email='admin@company.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin account created: admin@company.com / admin123")
        
    # ✅ Tạo group mặc định nếu chưa có
    default_group = Group.query.filter_by(name='Default Group').first()
    if not default_group:
        default_group = Group(
            name='Default Group',
            description='Default group for new employees',
            leader_id=None
        )
        db.session.add(default_group)
        db.session.commit()
        print("✅ Default group created")
    
    print("✅ Database & tables created successfully!")