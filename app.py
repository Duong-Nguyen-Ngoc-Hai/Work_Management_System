from flask import Flask, render_template, jsonify
from flask_cors import CORS
from database import db
from config import Config
from sqlalchemy import text
import os
import time

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)
    
    # Wait for database connection before creating tables
    with app.app_context():
        wait_for_db()
        
        from models import user, task, file, report, group, notification, join_request
        db.create_all()
        
        # Initialize default admin and data
        init_default_data()
    
    @app.route('/')
    def index():
        return render_template('auth/login.html')
    
    @app.route('/login')
    def login_page():
        return render_template('auth/login.html')
    
    @app.route('/register')
    def register_page():
        return render_template('auth/register.html')
    
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard/employee.html')
    
    @app.route('/tasks')
    def tasks():
        return render_template('tasks/list.html')
    
    @app.route('/reports')
    def reports():
        return render_template('reports/list.html')
    
    @app.route('/users')
    def users():
        return render_template('users/list.html')
    
    @app.route('/groups')
    def groups():
        return render_template('groups/list.html')
    
    @app.route('/profile')
    def profile():
        return render_template('users/profile.html')
    
    @app.route('/notifications')
    def notifications():
        return render_template('notifications/list.html')
    
    @app.route('/test-db')
    def test_db_connection():
        try:
            db.session.execute(text('SELECT 1'))
            return jsonify({'status': 'success', 'message': 'Database connected successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup notification scheduler
    setup_scheduler(app)

    return app

def wait_for_db():
    """Wait for database to be ready"""
    for i in range(30):  # Wait up to 30 seconds
        try:
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"⏳ Waiting for database... ({i+1}/30): {e}")
            time.sleep(1)
    
    print("❌ Could not connect to database after 30 seconds")
    return False

def register_blueprints(app):
    """Register all blueprints"""
    try:
        from routes.auth_routes import auth_bp
        from routes.task_routes import task_bp
        from routes.file_routes import file_bp
        from routes.user_routes import user_bp
        from routes.report_routes import report_bp
        from routes.group_routes import group_bp
        from routes.notification_routes import notification_bp

        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(task_bp, url_prefix='/api/tasks')
        app.register_blueprint(file_bp, url_prefix='/api/files')
        app.register_blueprint(user_bp, url_prefix='/api/users')
        app.register_blueprint(report_bp, url_prefix='/api/reports')
        app.register_blueprint(group_bp, url_prefix='/api/groups')
        app.register_blueprint(notification_bp)
        
        print("✅ All blueprints registered successfully")
    except Exception as e:
        print(f"⚠️ Warning: Failed to register some blueprints: {e}")

def setup_scheduler(app):
    """Setup notification scheduler"""
    try:
        from utils.notification_scheduler import setup_notification_scheduler
        setup_notification_scheduler(app)
        print("✅ Notification scheduler started successfully")
    except Exception as e:
        print(f"⚠️ Warning: Notification scheduler setup failed: {e}")

def init_default_data():
    """Initialize default admin and group data"""
    try:
        from models.user import User
        from models.group import Group
        from werkzeug.security import generate_password_hash
        
        # Create admin if not exists
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
            
        # Create default group if not exists
        default_group = Group.query.filter_by(name='Default Group').first()
        if not default_group:
            default_group = Group(
                name='Default Group',
                description='Default group for new employees'
            )
            db.session.add(default_group)
        
        db.session.commit()
        print("✅ Default data initialized successfully")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Warning: Failed to initialize default data: {e}")

if __name__ == '__main__':
    app = create_app()
    
    # Create uploads directory if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'reports'), exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run application
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Work Management System on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)