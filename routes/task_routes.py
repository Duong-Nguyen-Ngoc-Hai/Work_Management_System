from flask import Blueprint, request, jsonify
from database import db
from models.task import Task
from models.user import User
from models.group import Group
from datetime import datetime, timedelta
from routes.notification_routes import create_notification, NotificationType

task_bp = Blueprint('task', __name__)

# Thêm task mới
@task_bp.route('/create', methods=['POST'])
def create_task():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    status = data.get('status', 'todo')
    priority = data.get('priority', 'medium')  # Thêm priority
    deadline = data.get('deadline')
    assigner_id = data.get('assigner_id')
    assignee_id = data.get('assignee_id')
    parent_task_id = data.get('parent_task_id')
    group_id = data.get('group_id')  # Thêm group_id

    if not title:
        return jsonify({'message': 'Missing title'}), 400
    
    if priority not in ['low', 'medium', 'high']:
        return jsonify({'message': 'Invalid priority. Must be low, medium, or high'}), 400
    
    # Kiểm tra assigner_id có tồn tại không
    if assigner_id:
        assigner = User.query.get(assigner_id)
        if not assigner:
            return jsonify({'message': f'Assigner with ID {assigner_id} not found'}), 400

    # Kiểm tra assignee_id có tồn tại không
    if assignee_id:
        assignee = User.query.get(assignee_id)
        if not assignee:
            return jsonify({'message': f'Assignee with ID {assignee_id} not found'}), 400

    # Kiểm tra parent_task_id có tồn tại không
    if parent_task_id:
        parent_task = Task.query.get(parent_task_id)
        if not parent_task:
            return jsonify({'message': f'Parent task with ID {parent_task_id} not found'}), 400

    # Kiểm tra group_id có tồn tại không
    if group_id:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'message': f'Group with ID {group_id} not found'}), 400

    # Chuyển đổi deadline từ string sang datetime nếu có
    deadline_obj = None
    if deadline:
        try:
            deadline_obj = datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                deadline_obj = datetime.strptime(deadline, '%Y-%m-%d')
            except ValueError:
                return jsonify({'message': 'Invalid deadline format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS'}), 400

    new_task = Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        deadline=deadline_obj,
        assigner_id=assigner_id,
        assignee_id=assignee_id,
        parent_task_id=parent_task_id,
        group_id=group_id
    )
    
    try:
        db.session.add(new_task)
        db.session.commit()
        
        if assignee_id and assignee_id != assigner_id:
            assigner = User.query.get(assigner_id)
            create_notification(
                user_id=assignee_id,
                title=f"New task assigned: {title}",
                message=f"You have been assigned a new task '{title}' by {assigner.name if assigner else 'System'}",
                notification_type=NotificationType.TASK_ASSIGNED,
                task_id=new_task.id,
                is_important=priority == 'high'
            )
        
        return jsonify({
            'message': 'Task created successfully',
            'task': {
                'id': new_task.id,
                'title': new_task.title,
                'status': new_task.status,
                'priority': new_task.priority,
                'group_id': new_task.group_id,
                'created_at': new_task.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating task: {str(e)}'}), 500

# Lấy danh sách task với tìm kiếm/lọc
@task_bp.route('/search', methods=['GET'])
def search_tasks():
    # Lấy các tham số tìm kiếm
    assignee_id = request.args.get('assignee_id')
    assigner_id = request.args.get('assigner_id')
    group_id = request.args.get('group_id')
    status = request.args.get('status')
    priority = request.args.get('priority')
    date_from = request.args.get('date_from')  # YYYY-MM-DD
    date_to = request.args.get('date_to')     # YYYY-MM-DD
    week = request.args.get('week')           # YYYY-WXX
    title = request.args.get('title')
    
    # Tạo query cơ bản
    query = Task.query
    
    # Áp dụng filters
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)
    if assigner_id:
        query = query.filter_by(assigner_id=assigner_id)
    if group_id:
        query = query.filter_by(group_id=group_id)
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if title:
        query = query.filter(Task.title.like(f'%{title}%'))
    
    # Lọc theo ngày
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Task.created_at >= date_from_obj)
        except ValueError:
            return jsonify({'message': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Task.created_at <= date_to_obj)
        except ValueError:
            return jsonify({'message': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
    
    # Lọc theo tuần
    if week:
        try:
            year, week_num = week.split('-W')
            year = int(year)
            week_num = int(week_num)
            
            # Tính toán ngày bắt đầu và kết thúc tuần
            jan1 = datetime(year, 1, 1)
            start_date = jan1 + timedelta(weeks=week_num-1) - timedelta(days=jan1.weekday())
            end_date = start_date + timedelta(days=6)
            
            query = query.filter(
                Task.created_at >= start_date,
                Task.created_at <= end_date + timedelta(days=1)
            )
        except ValueError:
            return jsonify({'message': 'Invalid week format. Use YYYY-WXX (e.g., 2025-W28)'}), 400
    
    # Thực hiện query
    tasks = query.order_by(Task.created_at.desc()).all()
    result = []
    
    for task in tasks:
        # Lấy thông tin liên quan
        assigner = User.query.get(task.assigner_id) if task.assigner_id else None
        assignee = User.query.get(task.assignee_id) if task.assignee_id else None
        group = Group.query.get(task.group_id) if task.group_id else None
        
        result.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'deadline': task.deadline.strftime('%Y-%m-%d %H:%M:%S') if task.deadline else None,
            'parent_task_id': task.parent_task_id,
            'assigner': {
                'id': assigner.id,
                'name': assigner.name,
                'email': assigner.email
            } if assigner else None,
            'assignee': {
                'id': assignee.id,
                'name': assignee.name,
                'email': assignee.email,
                'employee_code': assignee.employee_code
            } if assignee else None,
            'group': {
                'id': group.id,
                'name': group.name
            } if group else None,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else None,
            'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else None
        })
    
    return jsonify({
        'tasks': result,
        'total_count': len(result),
        'filters_applied': {
            'assignee_id': assignee_id,
            'assigner_id': assigner_id,
            'group_id': group_id,
            'status': status,
            'priority': priority,
            'date_from': date_from,
            'date_to': date_to,
            'week': week,
            'title': title
        }
    })

# Lấy danh sách task của 1 user
@task_bp.route('/user/<int:user_id>', methods=['GET'])
def get_tasks_by_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    tasks = Task.query.filter_by(assignee_id=user_id).order_by(Task.created_at.desc()).all()
    result = []
    for task in tasks:
        assigner = User.query.get(task.assigner_id) if task.assigner_id else None
        group = Group.query.get(task.group_id) if task.group_id else None
        
        result.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'deadline': task.deadline.strftime('%Y-%m-%d %H:%M:%S') if task.deadline else None,
            'parent_task_id': task.parent_task_id,
            'assigner': {
                'id': assigner.id,
                'name': assigner.name
            } if assigner else None,
            'group': {
                'id': group.id,
                'name': group.name
            } if group else None,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else None
        })
    return jsonify(result)

# Lấy tất cả tasks
@task_bp.route('/all', methods=['GET'])
def get_all_tasks():
    """Lấy tất cả tasks theo quyền user"""
    # Lấy user_id từ query params để xác định quyền
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'Missing user_id parameter'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Base query
    query = Task.query
    
    # ✅ Apply role-based filtering
    if user.role == 'admin':
        # Admin xem tất cả tasks
        tasks = query.order_by(Task.created_at.desc()).all()
        
    elif user.role == 'leader':
        # ✅ Leader chỉ xem tasks trong nhóm của mình + tasks của chính mình
        if user.group_id:
            # Lấy tất cả user IDs trong nhóm (bao gồm cả leader)
            group_users = User.query.filter_by(group_id=user.group_id).all()
            user_ids = [u.id for u in group_users]
            
            # Lấy tasks được assign cho members trong nhóm HOẶC tasks mà leader tạo
            tasks = query.filter(
                db.or_(
                    Task.assignee_id.in_(user_ids),  # Tasks assigned to group members
                    Task.assigner_id == user.id      # Tasks created by leader
                )
            ).order_by(Task.created_at.desc()).all()
        else:
            # Leader không có nhóm chỉ xem tasks của chính mình
            tasks = query.filter(
                db.or_(
                    Task.assignee_id == user.id,
                    Task.assigner_id == user.id
                )
            ).order_by(Task.created_at.desc()).all()
            
    else:  # employee
        # Employee chỉ xem tasks của chính mình
        tasks = query.filter(
            db.or_(
                Task.assignee_id == user.id,
                Task.assigner_id == user.id
            )
        ).order_by(Task.created_at.desc()).all()

    # Format response
    result = []
    for task in tasks:
        # Lấy thông tin liên quan
        assigner = User.query.get(task.assigner_id) if task.assigner_id else None
        assignee = User.query.get(task.assignee_id) if task.assignee_id else None
        group = Group.query.get(task.group_id) if task.group_id else None
        parent_task = Task.query.get(task.parent_task_id) if task.parent_task_id else None
        
        # Count subtasks
        subtasks_count = Task.query.filter_by(parent_task_id=task.id).count()
        
        result.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': getattr(task, 'priority', 'medium'),
            'deadline': task.deadline.strftime('%Y-%m-%d %H:%M:%S') if task.deadline else None,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else None,
            'assigner': {
                'id': assigner.id,
                'name': assigner.name,
                'employee_code': assigner.employee_code
            } if assigner else None,
            'assignee': {
                'id': assignee.id,
                'name': assignee.name,
                'employee_code': assignee.employee_code,
                'role': assignee.role
            } if assignee else None,
            'group': {
                'id': group.id,
                'name': group.name
            } if group else None,
            'parent_task': {
                'id': parent_task.id,
                'title': parent_task.title
            } if parent_task else None,
            'subtasks_count': subtasks_count,
            'progress': calculate_task_progress(task)
        })
    
    return jsonify(result)

# Helper function để tính progress
def calculate_task_progress(task):
    """Calculate task progress based on status and subtasks"""
    if task.status == 'done':
        return 100
    elif task.status == 'doing':
        # Check if has subtasks
        subtasks = Task.query.filter_by(parent_task_id=task.id).all()
        if subtasks:
            completed_subtasks = len([st for st in subtasks if st.status == 'done'])
            return int((completed_subtasks / len(subtasks)) * 100) if len(subtasks) > 0 else 25
        else:
            return 50  # Default for "doing" without subtasks
    else:  # todo
        return 0

# Lấy tasks theo group
@task_bp.route('/group/<int:group_id>', methods=['GET'])
def get_tasks_by_group(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404

    tasks = Task.query.filter_by(group_id=group_id).order_by(Task.created_at.desc()).all()
    result = []
    for task in tasks:
        assigner = User.query.get(task.assigner_id) if task.assigner_id else None
        assignee = User.query.get(task.assignee_id) if task.assignee_id else None
        
        result.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'deadline': task.deadline.strftime('%Y-%m-%d %H:%M:%S') if task.deadline else None,
            'parent_task_id': task.parent_task_id,
            'assigner': {
                'id': assigner.id,
                'name': assigner.name
            } if assigner else None,
            'assignee': {
                'id': assignee.id,
                'name': assignee.name,
                'employee_code': assignee.employee_code
            } if assignee else None,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else None
        })
    return jsonify(result)

# Lấy subtasks của 1 task
@task_bp.route('/<int:task_id>/subtasks', methods=['GET'])
def get_subtasks(task_id):
    parent_task = Task.query.get(task_id)
    if not parent_task:
        return jsonify({'message': 'Parent task not found'}), 404

    subtasks = Task.query.filter_by(parent_task_id=task_id).all()
    result = []
    for subtask in subtasks:
        assignee = User.query.get(subtask.assignee_id) if subtask.assignee_id else None
        
        result.append({
            'id': subtask.id,
            'title': subtask.title,
            'description': subtask.description,
            'status': subtask.status,
            'priority': subtask.priority,
            'deadline': subtask.deadline.strftime('%Y-%m-%d %H:%M:%S') if subtask.deadline else None,
            'assignee': {
                'id': assignee.id,
                'name': assignee.name
            } if assignee else None,
            'created_at': subtask.created_at.strftime('%Y-%m-%d %H:%M:%S') if subtask.created_at else None
        })
    return jsonify(result)

# Cập nhật task
@task_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    # Cập nhật deadline nếu có
    if 'deadline' in data and data['deadline']:
        try:
            task.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                task.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'message': 'Invalid deadline format'}), 400

    # Cập nhật priority nếu có
    if 'priority' in data:
        if data['priority'] not in ['low', 'medium', 'high']:
            return jsonify({'message': 'Invalid priority. Must be low, medium, or high'}), 400
        task.priority = data['priority']

    # Cập nhật các trường khác
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.status = data.get('status', task.status)
    task.assignee_id = data.get('assignee_id', task.assignee_id)
    task.group_id = data.get('group_id', task.group_id)
    
    try:
        old_status = task.status
        db.session.commit()
        
        if old_status != 'done' and task.status == 'done':
            if task.assigner_id and task.assigner_id != task.assignee_id:
                assignee = User.query.get(task.assignee_id)
                create_notification(
                    user_id=task.assigner_id,
                    title=f"Task completed: {task.title}",
                    message=f"Task '{task.title}' has been completed by {assignee.name if assignee else 'assignee'}",
                    notification_type=NotificationType.TASK_COMPLETED,
                    task_id=task.id
                )
        
        # ✅ THÊM: Notification for task updates
        elif old_status != task.status:
            if task.assigner_id and task.assigner_id != task.assignee_id:
                assignee = User.query.get(task.assignee_id)
                create_notification(
                    user_id=task.assigner_id,
                    title=f"Task updated: {task.title}",
                    message=f"Task '{task.title}' status changed from {old_status} to {task.status} by {assignee.name if assignee else 'assignee'}",
                    notification_type=NotificationType.TASK_UPDATED,
                    task_id=task.id
                )
        
        return jsonify({'message': 'Task updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating task: {str(e)}'}), 500

# Xóa task
@task_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting task: {str(e)}'}), 500

# Lấy thông tin chi tiết 1 task
@task_bp.route('/<int:task_id>', methods=['GET'])
def get_task_detail(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    # Lấy thông tin liên quan
    assigner = User.query.get(task.assigner_id) if task.assigner_id else None
    assignee = User.query.get(task.assignee_id) if task.assignee_id else None
    group = Group.query.get(task.group_id) if task.group_id else None
    parent_task = Task.query.get(task.parent_task_id) if task.parent_task_id else None
    
    # Lấy subtasks
    subtasks = Task.query.filter_by(parent_task_id=task_id).all()
    subtask_list = []
    for subtask in subtasks:
        subtask_assignee = User.query.get(subtask.assignee_id) if subtask.assignee_id else None
        subtask_list.append({
            'id': subtask.id,
            'title': subtask.title,
            'status': subtask.status,
            'priority': subtask.priority,
            'assignee': {
                'id': subtask_assignee.id,
                'name': subtask_assignee.name
            } if subtask_assignee else None
        })

    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'deadline': task.deadline.strftime('%Y-%m-%d %H:%M:%S') if task.deadline else None,
        'assigner': {
            'id': assigner.id,
            'name': assigner.name,
            'email': assigner.email
        } if assigner else None,
        'assignee': {
            'id': assignee.id,
            'name': assignee.name,
            'email': assignee.email,
            'employee_code': assignee.employee_code
        } if assignee else None,
        'group': {
            'id': group.id,
            'name': group.name,
            'description': group.description
        } if group else None,
        'parent_task': {
            'id': parent_task.id,
            'title': parent_task.title
        } if parent_task else None,
        'subtasks': subtask_list,
        'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else None,
        'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else None
    })

# Dashboard - Thống kê tasks
@task_bp.route('/dashboard', methods=['GET'])
def get_dashboard_stats():
    user_id = request.args.get('user_id')
    group_id = request.args.get('group_id')
    
    # Tạo query cơ bản
    query = Task.query
    
    if user_id:
        query = query.filter_by(assignee_id=user_id)
    if group_id:
        query = query.filter_by(group_id=group_id)
    
    tasks = query.all()
    
    # Thống kê
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == 'done'])
    in_progress_tasks = len([t for t in tasks if t.status == 'doing'])
    todo_tasks = len([t for t in tasks if t.status == 'todo'])
    
    high_priority_tasks = len([t for t in tasks if t.priority == 'high'])
    medium_priority_tasks = len([t for t in tasks if t.priority == 'medium'])
    low_priority_tasks = len([t for t in tasks if t.priority == 'low'])
    
    # Tasks sắp hết hạn (trong vòng 3 ngày)
    upcoming_deadline = datetime.now() + timedelta(days=3)
    overdue_tasks = len([t for t in tasks if t.deadline and t.deadline < datetime.now() and t.status != 'done'])
    upcoming_tasks = len([t for t in tasks if t.deadline and t.deadline <= upcoming_deadline and t.deadline > datetime.now()])
    
    return jsonify({
        'total_tasks': total_tasks,
        'status_breakdown': {
            'completed': completed_tasks,
            'in_progress': in_progress_tasks,
            'todo': todo_tasks
        },
        'priority_breakdown': {
            'high': high_priority_tasks,
            'medium': medium_priority_tasks,
            'low': low_priority_tasks
        },
        'deadline_status': {
            'overdue': overdue_tasks,
            'upcoming': upcoming_tasks
        },
        'completion_rate': f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
    })

@task_bp.route('/bulk-create', methods=['POST'])
def bulk_create_tasks():
    """Tạo task cho nhiều assignees cùng lúc"""
    data = request.get_json()
    assigner_id = data.get('assigner_id')
    assignee_ids = data.get('assignee_ids', [])
    
    if not assignee_ids:
        return jsonify({'message': 'No assignees specified'}), 400
    
    # Kiểm tra quyền của assigner
    assigner = User.query.get(assigner_id)
    if not assigner:
        return jsonify({'message': 'Assigner not found'}), 404
    
    if assigner.role not in ['admin', 'leader']:
        return jsonify({'message': 'Only admin and leaders can assign tasks'}), 403
    
    # Nếu là leader, kiểm tra xem có phải leader của group không
    group_id = data.get('group_id')
    if assigner.role == 'leader':
        led_group = Group.query.filter_by(leader_id=assigner_id).first()
        if not led_group:
            return jsonify({'message': 'You are not leading any group'}), 403
        if group_id and group_id != led_group.id:
            return jsonify({'message': 'You can only assign tasks within your group'}), 403
    
    # Validate assignees
    assignees = User.query.filter(User.id.in_(assignee_ids)).all()
    if len(assignees) != len(assignee_ids):
        return jsonify({'message': 'Some assignees not found'}), 404
    
    # Nếu là leader, kiểm tra tất cả assignees có trong group không
    if assigner.role == 'leader':
        for assignee in assignees:
            if assignee.group_id != led_group.id:
                return jsonify({'message': f'User {assignee.name} is not in your group'}), 403
    
    try:
        created_tasks = []
        
        for assignee_id in assignee_ids:
            task = Task(
                title=data.get('title'),
                description=data.get('description', ''),
                status=data.get('status', 'todo'),
                priority=data.get('priority', 'medium'),
                deadline=datetime.strptime(data['deadline'], '%Y-%m-%d').date() if data.get('deadline') else None,
                assignee_id=assignee_id,
                assigner_id=assigner_id,
                group_id=group_id,
                created_at=datetime.utcnow()
            )
            db.session.add(task)
            created_tasks.append(task)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully created {len(created_tasks)} tasks',
            'tasks_created': len(created_tasks)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating tasks: {str(e)}'}), 500

@task_bp.route('/parent-options', methods=['GET'])
def get_parent_task_options():
    """Lấy danh sách tasks có thể làm parent task"""
    group_id = request.args.get('group_id')
    status = request.args.get('status', 'todo,doing')  # Default chỉ lấy tasks chưa hoàn thành
    assignee_id = request.args.get('assignee_id')
    limit = request.args.get('limit', 50, type=int)
    
    query = Task.query
    
    # Filters
    if group_id:
        query = query.filter_by(group_id=int(group_id))
    
    if status:
        status_list = status.split(',')
        query = query.filter(Task.status.in_(status_list))
    
    if assignee_id:
        query = query.filter_by(assignee_id=int(assignee_id))
    
    # Chỉ lấy main tasks (không phải subtasks)
    query = query.filter(Task.parent_task_id.is_(None))
    
    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
    
    result = []
    for task in tasks:
        assignee = User.query.get(task.assignee_id) if task.assignee_id else None
        
        result.append({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'priority': task.priority,
            'assignee': assignee.name if assignee else 'Unassigned',
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(result)