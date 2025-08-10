from app import create_app
from database import db
from models.user import User
from models.group import Group
from werkzeug.security import generate_password_hash
from sqlalchemy import text
import time

def wait_for_db():
    """Wait for database to be ready"""
    for i in range(30):  # Wait up to 30 seconds
        try:
            app = create_app()
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                print("✅ Database connection established")
                return True
        except Exception as e:
            print(f"⏳ Waiting for database... ({i+1}/30)")
            time.sleep(1)
    
    print("❌ Could not connect to database after 30 seconds")
    return False

def init_default_data():
    if not wait_for_db():
        return
    
    app = create_app()
    
    with app.app_context():
        try:
            # Tạo tất cả tables
            db.create_all()
            print("✅ Database tables created")
            
            # Tạo admin mặc định
            admin = User.query.filter_by(email='admin@company.com').first()
            if not admin:
                admin = User(
                    employee_code='ADMIN001',
                    name='System Administrator',
                    email='admin@company.com',
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    is_active=True
                )
                db.session.add(admin)
                print("✅ Admin user created")
            
            # Tạo nhóm mặc định
            default_group = Group.query.filter_by(name='Default Group').first()
            if not default_group:
                default_group = Group(
                    name='Default Group',
                    description='Default group for new employees'
                )
                db.session.add(default_group)
                print("✅ Default group created")
            
            # Tạo một số user mẫu
            if not User.query.filter_by(email='leader@company.com').first():
                leader = User(
                    employee_code='LEAD001',
                    name='Team Leader',
                    email='leader@company.com',
                    password_hash=generate_password_hash('leader123'),
                    role='leader',
                    is_active=True
                )
                db.session.add(leader)
                print("✅ Leader user created")
            
            if not User.query.filter_by(email='employee@company.com').first():
                employee = User(
                    employee_code='EMP001',
                    name='John Employee',
                    email='employee@company.com',
                    password_hash=generate_password_hash('employee123'),
                    role='employee',
                    is_active=True
                )
                db.session.add(employee)
                print("✅ Employee user created")
            
            db.session.commit()
            print("✅ All data initialized successfully!")
            
            # Hiển thị thông tin đăng nhập
            print("\n🔑 Default Login Accounts:")
            print("Admin: admin@company.com / admin123")
            print("Leader: leader@company.com / leader123") 
            print("Employee: employee@company.com / employee123")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error initializing data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    init_default_data()