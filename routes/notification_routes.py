from flask import Blueprint, request, jsonify
from models.notification import Notification, NotificationType
from models.user import User
from models.task import Task
from models.group import Group
from models.report import Report
from database import db
from datetime import datetime, timedelta

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notification_bp.route('/list', methods=['GET'])
def get_notifications():
    """Lấy danh sách notifications cho user"""
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    
    if not user_id:
        return jsonify({'message': 'Missing user_id'}), 400
    
    query = Notification.query.filter_by(user_id=user_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'total': total,
        'unread_count': Notification.query.filter_by(user_id=user_id, is_read=False).count()
    })

@notification_bp.route('/mark-read/<int:notification_id>', methods=['PUT'])
def mark_as_read(notification_id):
    """Đánh dấu notification là đã đọc"""
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'message': 'Notification not found'}), 404
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Notification marked as read'})

@notification_bp.route('/mark-all-read', methods=['PUT'])
def mark_all_as_read():
    """Đánh dấu tất cả notifications của user là đã đọc"""
    user_id = request.json.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'Missing user_id'}), 400
    
    notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
    
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': f'{len(notifications)} notifications marked as read'})

@notification_bp.route('/delete/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Xóa notification"""
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'message': 'Notification not found'}), 404
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'})

@notification_bp.route('/clear-all', methods=['DELETE'])
def clear_all_notifications():
    """Xóa tất cả notifications của user"""
    user_id = request.json.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'Missing user_id'}), 400
    
    count = Notification.query.filter_by(user_id=user_id).count()
    Notification.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return jsonify({'message': f'{count} notifications cleared'})

# ✅ Utility function để tạo notifications
def create_notification(user_id, title, message, notification_type, **kwargs):
    """Helper function để tạo notification mới"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        task_id=kwargs.get('task_id'),
        group_id=kwargs.get('group_id'),
        report_id=kwargs.get('report_id'),
        is_important=kwargs.get('is_important', False)
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return notification