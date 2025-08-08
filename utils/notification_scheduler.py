# Tạo utils/notification_scheduler.py
from datetime import datetime, timedelta
from models.task import Task
from models.user import User
from routes.notification_routes import create_notification, NotificationType
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

def setup_notification_scheduler(app):
    """Setup background scheduler for notifications"""
    try:
        scheduler = BackgroundScheduler()
        
        # Check deadlines every hour
        scheduler.add_job(
            func=check_task_deadlines,
            trigger="interval",
            hours=1,
            id='deadline_notifications',
            replace_existing=True
        )
        
        # Daily cleanup of old notifications (keep last 30 days)
        scheduler.add_job(
            func=cleanup_old_notifications,
            trigger="cron", 
            hour=2,  # Run at 2 AM daily
            id='notification_cleanup',
            replace_existing=True
        )
        
        scheduler.start()
        print("🚀 Notification scheduler started successfully")
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
        
    except Exception as e:
        print(f"❌ Failed to setup notification scheduler: {e}")
        raise e

def cleanup_old_notifications():
    """Clean up notifications older than 30 days"""
    try:
        from models.notification import Notification
        from database import db
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_notifications = Notification.query.filter(
            Notification.created_at < cutoff_date
        ).all()
        
        count = len(old_notifications)
        
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        print(f"🧹 Cleaned up {count} old notifications")
        
    except Exception as e:
        print(f"❌ Error cleaning up notifications: {e}")

def check_task_deadlines():
    """Check for tasks approaching deadline and overdue tasks"""
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    
    # Tasks due within 24 hours
    upcoming_tasks = Task.query.filter(
        Task.deadline <= tomorrow,
        Task.deadline > now,
        Task.status.in_(['todo', 'doing'])
    ).all()
    
    for task in upcoming_tasks:
        if task.assignee_id:
            create_notification(
                user_id=task.assignee_id,
                title=f"Task deadline approaching: {task.title}",
                message=f"Task '{task.title}' is due within 24 hours",
                notification_type=NotificationType.TASK_DEADLINE_SOON,
                task_id=task.id,
                is_important=True
            )
    
    # Overdue tasks
    overdue_tasks = Task.query.filter(
        Task.deadline < now,
        Task.status.in_(['todo', 'doing'])
    ).all()
    
    for task in overdue_tasks:
        if task.assignee_id:
            # Check if we haven't already sent overdue notification today
            from models.notification import Notification
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            existing_notification = Notification.query.filter(
                Notification.user_id == task.assignee_id,
                Notification.task_id == task.id,
                Notification.type == NotificationType.TASK_OVERDUE,
                Notification.created_at >= today_start
            ).first()
            
            if not existing_notification:
                create_notification(
                    user_id=task.assignee_id,
                    title=f"Task overdue: {task.title}",
                    message=f"Task '{task.title}' is overdue",
                    notification_type=NotificationType.TASK_OVERDUE,
                    task_id=task.id,
                    is_important=True
                )