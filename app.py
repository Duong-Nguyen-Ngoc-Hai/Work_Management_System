from flask import Flask, render_template
from flask_cors import CORS
from config import Config
from database import db
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)
    
    with app.app_context():
        from models import user, task, file, report, group, notification, join_request
        db.create_all()
    
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
        return render_template('notification/list.html')

    @app.route('/test-db')
    def test_db_connection():
        try:
            db.session.execute(text('SELECT 1'))
            return "Kết nối cơ sở dữ liệu thành công!"
        except Exception as e:
            return f"Lỗi kết nối cơ sở dữ liệu: {str(e)}"
        
        

    # Import & đăng ký blueprint
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
    
    # ✅ Setup notification scheduler sau khi app được tạo
    try:
        from utils.notification_scheduler import setup_notification_scheduler
        setup_notification_scheduler(app)
        print("✅ Notification scheduler started successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not start notification scheduler: {e}")
    except Exception as e:
        print(f"⚠️ Warning: Notification scheduler setup failed: {e}")
    

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)