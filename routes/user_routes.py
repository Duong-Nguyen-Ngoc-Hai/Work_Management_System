from flask import Blueprint, request, jsonify
from database import db
from models.user import User
from models.task import Task
from models.file import File
from models.report import Report
from models.group import Group
from werkzeug.security import generate_password_hash
import uuid

user_bp = Blueprint('user', __name__)

# Lấy danh sách tất cả users với tìm kiếm/lọc
@user_bp.route('/all', methods=['GET'])
def get_all_users():
    # Lấy tham số tìm kiếm
    role = request.args.get('role')  # employee, leader, admin
    group_id = request.args.get('group_id')
    employee_code = request.args.get('employee_code')
    name = request.args.get('name')
    
    # Tạo query cơ bản
    query = User.query
    
    # Áp dụng filters
    if role:
        query = query.filter_by(role=role)
    if group_id:
        query = query.filter_by(group_id=group_id)
    if employee_code:
        query = query.filter(User.employee_code.like(f'%{employee_code}%'))
    if name:
        query = query.filter(User.name.like(f'%{name}%'))
    
    users = query.all()
    result = []
    
    for user in users:
        # Thống kê tasks của user
        total_tasks = Task.query.filter_by(assignee_id=user.id).count()
        completed_tasks = Task.query.filter_by(assignee_id=user.id, status='done').count()
        
        # Lấy thông tin group
        group_info = None
        if user.group_id:
            group = Group.query.get(user.group_id)
            group_info = {
                'id': group.id,
                'name': group.name
            } if group else None
        
        result.append({
            'id': user.id,
            'employee_code': user.employee_code,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'group': group_info,
            'is_active': user.is_active,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(result)

# Phân quyền: nâng user thành leader (chỉ admin)
@user_bp.route('/promote/<int:user_id>', methods=['PUT'])
def promote_to_leader(user_id):
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Kiểm tra quyền admin
    if admin_id:
        admin = User.query.get(admin_id)
        if not admin or admin.role != 'admin':
            return jsonify({'message': 'Access denied. Only admins can promote users'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.role == 'leader':
        return jsonify({'message': 'User is already a leader'}), 400

    user.role = 'leader'
    db.session.commit()

    return jsonify({'message': f'User {user.name} promoted to leader successfully'})

# Phân quyền: hạ leader xuống employee (chỉ admin)
@user_bp.route('/demote/<int:user_id>', methods=['PUT'])
def demote_to_employee(user_id):
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Kiểm tra quyền admin
    if admin_id:
        admin = User.query.get(admin_id)
        if not admin or admin.role != 'admin':
            return jsonify({'message': 'Access denied. Only admins can demote users'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.role == 'employee':
        return jsonify({'message': 'User is already an employee'}), 400

    user.role = 'employee'
    db.session.commit()

    return jsonify({'message': f'User {user.name} demoted to employee successfully'})

# Cập nhật thông tin user
@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Kiểm tra quyền (chỉ admin hoặc chính user đó mới được update)
    if admin_id:
        admin = User.query.get(admin_id)
        if not admin or (admin.role != 'admin' and admin.id != user_id):
            return jsonify({'message': 'Access denied'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Cập nhật thông tin
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.employee_code = data.get('employee_code', user.employee_code)
    user.group_id = data.get('group_id', user.group_id)
    user.is_active = data.get('is_active', user.is_active)
    
    # Chỉ admin mới được thay đổi role
    if admin_id:
        admin = User.query.get(admin_id)
        if admin and admin.role == 'admin' and admin.id != user_id:
            new_role = data.get('role')
            if new_role in ['employee', 'leader', 'admin']:
                user.role = new_role

    # Cập nhật password nếu có
    new_password = data.get('password')
    if new_password:
        user.password_hash = generate_password_hash(new_password)

    try:
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating user: {str(e)}'}), 500

# Tạo user mới (chỉ admin)
@user_bp.route('/create', methods=['POST'])
def create_user():
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Kiểm tra quyền admin
    if admin_id:
        admin = User.query.get(admin_id)
        if not admin or admin.role != 'admin':
            return jsonify({'message': 'Access denied. Only admins can create users'}), 403

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'employee')
    employee_code = data.get('employee_code')
    group_id = data.get('group_id')

    if not all([name, email, password]):
        return jsonify({'message': 'Missing required fields: name, email, password'}), 400

    if role not in ['employee', 'leader', 'admin']:
        return jsonify({'message': 'Invalid role. Must be employee, leader, or admin'}), 400

    # Tạo employee_code tự động nếu không có
    if not employee_code:
        employee_code = f"EMP{str(uuid.uuid4())[:8].upper()}"

    # Kiểm tra email và employee_code đã tồn tại
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    if User.query.filter_by(employee_code=employee_code).first():
        return jsonify({'message': 'Employee code already exists'}), 400

    try:
        hashed_pw = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_pw,
            role=role,
            employee_code=employee_code,
            group_id=group_id
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': new_user.id,
                'name': new_user.name,
                'email': new_user.email,
                'role': new_user.role,
                'employee_code': new_user.employee_code,
                'group_id': new_user.group_id
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

# Xóa user (chỉ admin)
@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Kiểm tra quyền admin
    if admin_id:
        admin = User.query.get(admin_id)
        if not admin or admin.role != 'admin':
            return jsonify({'message': 'Access denied. Only admins can delete users'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Không cho phép xóa chính mình
    if admin_id == user_id:
        return jsonify({'message': 'Cannot delete yourself'}), 400

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': f'User {user.name} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting user: {str(e)}'}), 500

# Thống kê tổng quan hệ thống (chỉ admin)
@user_bp.route('/system-stats', methods=['GET'])
def get_system_stats():
    total_users = User.query.count()
    total_employees = User.query.filter_by(role='employee').count()
    total_leaders = User.query.filter_by(role='leader').count()
    total_admins = User.query.filter_by(role='admin').count()
    
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='done').count()
    active_tasks = Task.query.filter(Task.status.in_(['todo', 'doing'])).count()
    
    total_files = File.query.count()
    total_reports = Report.query.count()
    total_groups = Group.query.count()

    return jsonify({
        'users': {
            'total': total_users,
            'employees': total_employees,
            'leaders': total_leaders,
            'admins': total_admins
        },
        'tasks': {
            'total': total_tasks,
            'completed': completed_tasks,
            'active': active_tasks,
            'completion_rate': f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
        },
        'files': {
            'total': total_files
        },
        'reports': {
            'total': total_reports
        },
        'groups': {
            'total': total_groups
        }
    })

# Lấy danh sách employees (để leader gán task)
@user_bp.route('/employees', methods=['GET'])
def get_employees():
    employees = User.query.filter_by(role='employee').all()
    result = []
    
    for emp in employees:
        # Lấy thông tin group
        group_info = None
        if emp.group_id:
            group = Group.query.get(emp.group_id)
            group_info = {
                'id': group.id,
                'name': group.name
            } if group else None
        
        result.append({
            'id': emp.id,
            'employee_code': emp.employee_code,
            'name': emp.name,
            'email': emp.email,
            'group': group_info,  # Thông tin group nếu có
            'is_active': emp.is_active
        })
    
    return jsonify(result)

@user_bp.route('/available-leaders', methods=['GET'])
def get_available_leaders():
    """Lấy danh sách leaders có thể gán làm leader cho group"""
    leaders = User.query.filter(User.role.in_(['leader', 'admin'])).all()
    result = []
    
    for leader in leaders:
        # Kiểm tra xem có đang lead group nào không
        led_group = Group.query.filter_by(leader_id=leader.id).first()
        is_leading = led_group is not None
        
        # Thông tin group hiện tại
        current_group_info = None
        if leader.group_id:
            current_group = Group.query.get(leader.group_id)
            current_group_info = {
                'id': current_group.id,
                'name': current_group.name
            } if current_group else None
        
        result.append({
            'id': leader.id,
            'employee_code': leader.employee_code,
            'name': leader.name,
            'email': leader.email,
            'role': leader.role,
            'is_leading': is_leading,
            'led_group': {'id': led_group.id, 'name': led_group.name} if led_group else None,
            'current_group': current_group_info,
            'can_be_leader': not is_leading,  # Chỉ có thể gán làm leader nếu chưa lead group nào
            'is_active': leader.is_active
        })
    
    return jsonify(result)

# Lấy danh sách leaders
@user_bp.route('/leaders', methods=['GET'])
def get_leaders():
    leaders = User.query.filter_by(role='leader').all()
    result = []
    for leader in leaders:
        # Thống kê
        tasks_assigned = Task.query.filter_by(assigner_id=leader.id).count()
        reports_created = Report.query.filter_by(user_id=leader.id).count()
        
        result.append({
            'id': leader.id,
            'name': leader.name,
            'email': leader.email,
            'employee_code': leader.employee_code,
            'tasks_assigned': tasks_assigned,
            'reports_created': reports_created
        })
    return jsonify(result)

# Lấy thông tin chi tiết 1 user
@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user_detail(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Thống kê chi tiết
    total_tasks = Task.query.filter_by(assignee_id=user.id).count()
    completed_tasks = Task.query.filter_by(assignee_id=user.id, status='done').count()
    in_progress_tasks = Task.query.filter_by(assignee_id=user.id, status='doing').count()
    todo_tasks = Task.query.filter_by(assignee_id=user.id, status='todo').count()
    
    # Thống kê files
    uploaded_files = File.query.filter_by(uploaded_by=user.id).count()
    
    # Thống kê reports
    reports_created = Report.query.filter_by(user_id=user.id).count()
    
    # Thông tin group
    group_info = None
    if user.group_id:
        group = Group.query.get(user.group_id)
        group_info = {
            'id': group.id,
            'name': group.name,
            'description': group.description
        } if group else None

    return jsonify({
        'id': user.id,
        'employee_code': user.employee_code,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'group': group_info,
        'is_active': user.is_active,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'statistics': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'todo_tasks': todo_tasks,
            'uploaded_files': uploaded_files,
            'reports_created': reports_created,
            'completion_rate': f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
        }
    })
    
@user_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Lấy thông tin profile đầy đủ của user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Thống kê chi tiết
    total_tasks = Task.query.filter_by(assignee_id=user.id).count()
    completed_tasks = Task.query.filter_by(assignee_id=user.id, status='done').count()
    in_progress_tasks = Task.query.filter_by(assignee_id=user.id, status='doing').count()
    todo_tasks = Task.query.filter_by(assignee_id=user.id, status='todo').count()
    
    # Thống kê files
    uploaded_files = File.query.filter_by(uploaded_by=user.id).count()
    
    # Thống kê reports
    reports_created = Report.query.filter_by(user_id=user.id).count()
    
    # Tasks gần đây
    recent_tasks = Task.query.filter_by(assignee_id=user.id).order_by(Task.updated_at.desc()).limit(5).all()
    recent_tasks_data = []
    for task in recent_tasks:
        recent_tasks_data.append({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'priority': getattr(task, 'priority', 'medium'),
            'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else None,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else None
        })
    
    # Thông tin group
    group_info = None
    if user.group_id:
        group = Group.query.get(user.group_id)
        if group:
            group_leader = User.query.get(group.leader_id) if group.leader_id else None
            group_info = {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'leader': {
                    'id': group_leader.id,
                    'name': group_leader.name,
                    'email': group_leader.email
                } if group_leader else None,
                'member_count': User.query.filter_by(group_id=group.id).count()
            }

    result = {
        'id': user.id,
        'employee_code': user.employee_code,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'group': group_info,
        'statistics': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'todo_tasks': todo_tasks,
            'completion_rate': f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",
            'uploaded_files': uploaded_files,
            'reports_created': reports_created
        },
        'recent_tasks': recent_tasks_data
    }
    
    return jsonify(result)