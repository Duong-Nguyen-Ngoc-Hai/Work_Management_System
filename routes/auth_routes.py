from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models.user import User
from models.group import Group
import uuid

auth_bp = Blueprint('auth', __name__)

# Đăng ký
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'employee')
    # ❌ Bỏ: employee_code = data.get('employee_code')

    if not all([name, email, password]):
        return jsonify({'message': 'Missing required fields: name, email, password'}), 400

    # Validate role
    if role not in ['employee', 'leader', 'admin']:
        return jsonify({'message': 'Invalid role. Must be employee, leader, or admin'}), 400

    # Chỉ admin mới có thể tạo tài khoản admin/leader
    if role in ['admin', 'leader']:
        admin_id = data.get('admin_id')
        if not admin_id:
            return jsonify({'message': 'Admin authorization required to create admin/leader account'}), 403
        
        admin = User.query.get(admin_id)
        if not admin or admin.role != 'admin':
            return jsonify({'message': 'Only admins can create admin/leader accounts'}), 403

    # Kiểm tra email đã tồn tại
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'Email already exists'}), 400

    # ✅ Tự động tạo employee_code theo quy tắc
    def generate_employee_code(role, name):
        """Tạo employee code theo quy tắc: ROLE + năm + số thứ tự"""
        from datetime import datetime
        year = datetime.now().year
        
        # Prefix theo role
        prefix_map = {
            'employee': 'EMP',
            'leader': 'LDR', 
            'admin': 'ADM'
        }
        prefix = prefix_map.get(role, 'EMP')
        
        # Đếm số user cùng role trong năm
        count = User.query.filter_by(role=role).filter(
            User.created_at >= datetime(year, 1, 1)
        ).count() + 1
        
        return f"{prefix}{year}{count:03d}"  # VD: EMP2025001, LDR2025001

    employee_code = generate_employee_code(role, name)
    
    # Đảm bảo employee_code unique (tránh conflict)
    counter = 1
    original_code = employee_code
    while User.query.filter_by(employee_code=employee_code).first():
        employee_code = f"{original_code}_{counter}"
        counter += 1

    try:
        hashed_pw = generate_password_hash(password)
        new_user = User(
            name=name, 
            email=email, 
            password_hash=hashed_pw,
            role=role,
            employee_code=employee_code,  # ✅ Tự động sinh
            group_id=None
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': new_user.id,
                'name': new_user.name,
                'email': new_user.email,
                'role': new_user.role,
                'employee_code': new_user.employee_code,  # ✅ Hiển thị mã được tạo
                'group_id': new_user.group_id
            },
            'next_step': 'Join a group using /api/groups/join' if role == 'employee' else 'Contact admin to assign group'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

# Đăng nhập
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing email or password'}), 400

    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.is_active:
        return jsonify({'message': 'Account is deactivated. Please contact admin.'}), 403
    
    if not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid password'}), 401

    # Lấy thông tin group nếu có
    group_info = None
    if user.group_id:
        group = Group.query.get(user.group_id)
        group_info = {
            'id': group.id,
            'name': group.name,
            'description': group.description
        } if group else None

    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'employee_code': user.employee_code,
            'group': group_info,
            'is_active': user.is_active,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200

# Đăng xuất (placeholder - thường dùng cho JWT token invalidation)
@auth_bp.route('/logout', methods=['POST'])
def logout():
    # Trong hệ thống stateless, logout thường được handle ở frontend
    # Hoặc blacklist JWT token nếu sử dụng
    return jsonify({'message': 'Logout successful'}), 200

# Thay đổi password
@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    user_id = data.get('user_id')
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not all([user_id, current_password, new_password]):
        return jsonify({'message': 'Missing required fields'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Verify current password
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({'message': 'Current password is incorrect'}), 401

    # Validate new password
    if len(new_password) < 6:
        return jsonify({'message': 'New password must be at least 6 characters long'}), 400

    # Update password
    try:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error changing password: {str(e)}'}), 500

# Quên mật khẩu (reset password - cần email service)
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # TODO: Implement email service để gửi reset password link
    # Hiện tại chỉ return message
    return jsonify({
        'message': 'Password reset instructions sent to your email',
        'note': 'Email service not implemented yet'
    }), 200

# Validate session/token (placeholder)
@auth_bp.route('/validate', methods=['GET'])
def validate_session():
    # Thường dùng để validate JWT token
    # Hiện tại chỉ return success cho testing
    return jsonify({'message': 'Session valid'}), 200