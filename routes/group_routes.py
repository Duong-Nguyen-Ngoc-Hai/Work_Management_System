from flask import Blueprint, request, jsonify
from database import db
from models.group import Group
from models.user import User
from models.task import Task
from routes.notification_routes import create_notification, NotificationType
from models.join_request import JoinRequest, JoinRequestStatus
from datetime import datetime

group_bp = Blueprint('group', __name__)

# Tạo nhóm mới (chỉ admin)
@group_bp.route('/create', methods=['POST'])
def create_group():
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Kiểm tra quyền (chỉ admin)
    admin = User.query.get(admin_id)
    if not admin or admin.role != 'admin':
        return jsonify({'message': 'Access denied. Only admins can create groups'}), 403
    
    name = data.get('name')
    description = data.get('description', '')
    leader_id = data.get('leader_id')
    
    if not name:
        return jsonify({'message': 'Group name is required'}), 400
    
    # Kiểm tra tên nhóm đã tồn tại
    existing_group = Group.query.filter_by(name=name).first()
    if existing_group:
        return jsonify({'message': 'Group name already exists'}), 400
    
    # Validate leader_id nếu có
    if leader_id:
        leader = User.query.get(leader_id)
        if not leader:
            return jsonify({'message': 'Leader not found'}), 404
        if leader.role not in ['leader', 'admin']:
            return jsonify({'message': 'Leader must have leader or admin role'}), 400
        
        # Kiểm tra leader đã lead group khác chưa
        existing_led_group = Group.query.filter_by(leader_id=leader_id).first()
        if existing_led_group:
            return jsonify({'message': f'User is already leading group "{existing_led_group.name}". A user can only lead one group at a time.'}), 400
        
        # Kiểm tra leader có đang ở group khác không
        if leader.group_id:
            current_group = Group.query.get(leader.group_id)
            return jsonify({'message': f'User is currently a member of group "{current_group.name}". Remove from current group first.'}), 400
    
    try:
        new_group = Group(
            name=name,
            description=description,
            leader_id=leader_id
        )
        db.session.add(new_group)
        db.session.commit()
        
        # Tự động thêm leader vào group
        if leader_id:
            leader = User.query.get(leader_id)
            leader.group_id = new_group.id
            db.session.commit()
        
        return jsonify({
            'message': 'Group created successfully',
            'group': {
                'id': new_group.id,
                'name': new_group.name,
                'description': new_group.description,
                'leader_id': new_group.leader_id,
                'created_at': new_group.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating group: {str(e)}'}), 500

# Lấy danh sách tất cả nhóm
@group_bp.route('/all', methods=['GET'])
def get_all_groups():
    groups = Group.query.all()
    result = []
    for group in groups:
        leader = User.query.get(group.leader_id)
        member_count = User.query.filter_by(group_id=group.id).count()
        
        # Thống kê tasks của nhóm
        group_tasks = Task.query.filter_by(group_id=group.id).count()
        completed_tasks = Task.query.filter_by(group_id=group.id, status='done').count()
        
        result.append({
            'id': group.id,
            'name': group.name,
            'description': group.description,
            'leader_name': leader.name if leader else 'No leader',
            'leader_id': group.leader_id,
            'member_count': member_count,
            'total_tasks': group_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': f"{(completed_tasks/group_tasks*100):.1f}%" if group_tasks > 0 else "0%",
            'created_at': group.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(result)

# Gán leader cho group (chỉ admin)
@group_bp.route('/assign-leader', methods=['POST'])
def assign_leader():
    data = request.get_json()
    admin_id = data.get('admin_id')
    group_id = data.get('group_id')
    leader_id = data.get('leader_id')
    
    # Kiểm tra quyền admin
    admin = User.query.get(admin_id)
    if not admin or admin.role != 'admin':
        return jsonify({'message': 'Access denied. Only admins can assign leaders'}), 403
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    leader = User.query.get(leader_id)
    if not leader:
        return jsonify({'message': 'Leader not found'}), 404
    
    if leader.role not in ['leader', 'admin']:
        return jsonify({'message': 'User must have leader or admin role'}), 400
    
    # Kiểm tra leader đã lead group khác chưa
    existing_led_group = Group.query.filter_by(leader_id=leader_id).first()
    if existing_led_group and existing_led_group.id != group_id:
        return jsonify({'message': f'User is already leading group "{existing_led_group.name}". A user can only lead one group at a time.'}), 400
    
    try:
        # Gỡ leader cũ ra khỏi group (nhưng không xóa khỏi group_id)
        if group.leader_id and group.leader_id != leader_id:
            old_leader = User.query.get(group.leader_id)
            # Old leader vẫn ở trong group nhưng không còn là leader
        
        # Gán leader mới
        group.leader_id = leader_id
        
        # Nếu leader chưa ở trong group này, thêm vào group
        if leader.group_id != group_id:
            # Nếu leader đang ở group khác, remove khỏi group cũ
            if leader.group_id:
                old_group = Group.query.get(leader.group_id)
                # Nếu leader đang lead group cũ, không cho phép
                if old_group and old_group.leader_id == leader_id:
                    return jsonify({'message': f'Cannot assign leader. User is currently leading group "{old_group.name}". Remove as leader from that group first.'}), 400
            
            leader.group_id = group_id
        
        db.session.commit()
        
        return jsonify({'message': f'Leader {leader.name} assigned to group {group.name} successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error assigning leader: {str(e)}'}), 500

# Employee join group (tự nguyện)
@group_bp.route('/join', methods=['POST'])
def join_group():
    data = request.get_json()
    user_id = data.get('user_id')
    group_id = data.get('group_id')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Chỉ employee mới có thể join
    if user.role != 'employee':
        return jsonify({'message': 'Only employees can join groups'}), 403
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    # Kiểm tra user đã trong group khác chưa
    if user.group_id:
        current_group = Group.query.get(user.group_id)
        return jsonify({'message': f'You are already in group "{current_group.name}". Leave current group first.'}), 400
    
    # Kiểm tra group có leader không
    if not group.leader_id:
        return jsonify({'message': 'This group has no leader. Cannot join.'}), 400
    
    try:
        user.group_id = group_id
        db.session.commit()
        return jsonify({'message': f'Successfully joined group {group.name}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error joining group: {str(e)}'}), 500

# Employee leave group
@group_bp.route('/leave', methods=['POST'])
def leave_group():
    data = request.get_json()
    user_id = data.get('user_id')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.group_id:
        return jsonify({'message': 'You are not in any group'}), 400
    
    try:
        old_group = Group.query.get(user.group_id)
        user.group_id = None
        db.session.commit()
        return jsonify({'message': f'Successfully left group {old_group.name}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error leaving group: {str(e)}'}), 500

# Leader/Admin thêm member vào group
@group_bp.route('/add-member', methods=['POST'])
def add_member_to_group():
    data = request.get_json()
    admin_id = data.get('admin_id')  # Có thể là admin hoặc leader
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    
    # Kiểm tra quyền
    admin = User.query.get(admin_id)
    if not admin or admin.role not in ['admin', 'leader']:
        return jsonify({'message': 'Access denied. Only admins or leaders can add members'}), 403
    
    # Nếu là leader, chỉ có thể add vào group mà mình lead
    if admin.role == 'leader':
        led_group = Group.query.filter_by(leader_id=admin_id).first()
        if not led_group:
            return jsonify({'message': 'You are not leading any group'}), 403
        if led_group.id != group_id:
            return jsonify({'message': 'You can only add members to your own group'}), 403
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user.role != 'employee':
        return jsonify({'message': 'Only employees can be added to groups'}), 400
    
    # Kiểm tra user đã trong group khác chưa
    if user.group_id:
        if user.group_id == group_id:
            return jsonify({'message': 'User is already in this group'}), 400
        else:
            current_group = Group.query.get(user.group_id)
            return jsonify({'message': f'User is already in group "{current_group.name}"'}), 400
    
    try:
        user.group_id = group_id
        db.session.commit()
        
         # ✅ THÊM: Notification for user joining group
        group = Group.query.get(group_id)
        create_notification(
            user_id=user.id,
            title=f"Added to group: {group.name}",
            message=f"You have been added to the group '{group.name}'",
            notification_type=NotificationType.GROUP_JOINED,
            group_id=group_id
        )
        
        # ✅ Notify group leader
        if group.leader_id and group.leader_id != user.id:
            create_notification(
                user_id=group.leader_id,
                title=f"New member joined: {group.name}",
                message=f"{user.name} has joined your group '{group.name}'",
                notification_type=NotificationType.GROUP_JOINED,
                group_id=group_id
            )
        
        return jsonify({'message': f'User {user.name} added to group {group.name} successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error adding user to group: {str(e)}'}), 500

# Lấy thông tin chi tiết 1 nhóm
@group_bp.route('/<int:group_id>', methods=['GET'])
def get_group_detail(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    leader = User.query.get(group.leader_id)
    members = User.query.filter_by(group_id=group_id).all()
    
    # Thống kê tasks
    group_tasks = Task.query.filter_by(group_id=group_id).all()
    total_tasks = len(group_tasks)
    completed_tasks = len([t for t in group_tasks if t.status == 'done'])
    in_progress_tasks = len([t for t in group_tasks if t.status == 'doing'])
    todo_tasks = len([t for t in group_tasks if t.status == 'todo'])
    
    # Thông tin members
    member_list = []
    for member in members:
        member_tasks = Task.query.filter_by(assignee_id=member.id, group_id=group_id).count()
        member_completed = Task.query.filter_by(assignee_id=member.id, group_id=group_id, status='done').count()
        
        member_list.append({
            'id': member.id,
            'name': member.name,
            'email': member.email,
            'role': member.role,
            'employee_code': member.employee_code,
            'tasks_assigned': member_tasks,
            'tasks_completed': member_completed,
            'completion_rate': f"{(member_completed/member_tasks*100):.1f}%" if member_tasks > 0 else "0%"
        })
    
    return jsonify({
        'id': group.id,
        'name': group.name,
        'description': group.description,
        'leader': {
            'id': leader.id,
            'name': leader.name,
            'email': leader.email
        } if leader else None,
        'created_at': group.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'statistics': {
            'total_members': len(members),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'todo_tasks': todo_tasks,
            'completion_rate': f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
        },
        'members': member_list
    })

# Xóa user khỏi nhóm
@group_bp.route('/remove-member', methods=['POST'])
def remove_member_from_group():
    data = request.get_json()
    admin_id = data.get('admin_id')
    user_id = data.get('user_id')
    
    # Kiểm tra quyền
    admin = User.query.get(admin_id)
    if not admin or admin.role not in ['admin', 'leader']:
        return jsonify({'message': 'Access denied. Only admins or leaders can remove members'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.group_id:
        return jsonify({'message': 'User is not in any group'}), 400
    
    # Lấy thông tin group
    group = Group.query.get(user.group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    # Nếu là leader, chỉ có thể remove từ group mà mình lead
    if admin.role == 'leader':
        led_group = Group.query.filter_by(leader_id=admin_id).first()
        if not led_group or led_group.id != user.group_id:
            return jsonify({'message': 'You can only remove members from your own group'}), 403
        
        # Leader không thể remove chính mình
        if admin_id == user_id:
            return jsonify({'message': 'You cannot remove yourself from the group'}), 403
    
    # Kiểm tra nếu user đang là leader của group
    is_leader = (group.leader_id == user_id)
    
    try:
        # Remove user khỏi group
        old_group = Group.query.get(user.group_id)
        user.group_id = None
        
        # Nếu user đang là leader, set group leader thành None
        if is_leader:
            group.leader_id = None
            
        db.session.commit()
        
        create_notification(
            user_id=user.id,
            title=f"Removed from group: {old_group.name}",
            message=f"You have been removed from the group '{old_group.name}'",
            notification_type=NotificationType.GROUP_REMOVED,
            group_id=old_group.id
        )
        
        message = f'User {user.name} removed from group {group.name} successfully'
        if is_leader:
            message += '. Group now has no leader.'
        
        return jsonify({'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error removing member: {str(e)}'}), 500
    
# Cập nhật thông tin nhóm
@group_bp.route('/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Kiểm tra quyền
    admin = User.query.get(admin_id)
    if not admin or admin.role not in ['admin', 'leader']:
        return jsonify({'message': 'Access denied. Only admins or leaders can update groups'}), 403
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    # Nếu là leader, chỉ có thể update group mà mình lead
    if admin.role == 'leader' and group.leader_id != admin.id:
        return jsonify({'message': 'You can only update your own group'}), 403
    
    # Cập nhật thông tin cơ bản
    group.name = data.get('name', group.name)
    group.description = data.get('description', group.description)
    
    # Cập nhật leader nếu có (chỉ admin)
    if admin.role == 'admin':
        new_leader_id = data.get('leader_id')
        
        # Xử lý trường hợp set leader thành None (No Leader)
        if new_leader_id == '' or new_leader_id is None:
            # Remove leader hiện tại
            if group.leader_id:
                old_leader = User.query.get(group.leader_id)
                # Old leader vẫn ở trong group nhưng không còn là leader
            group.leader_id = None
            
        # Xử lý trường hợp gán leader mới
        elif new_leader_id and str(new_leader_id) != str(group.leader_id):
            new_leader = User.query.get(new_leader_id)
            if not new_leader:
                return jsonify({'message': 'New leader not found'}), 404
            if new_leader.role not in ['leader', 'admin']:
                return jsonify({'message': 'New leader must have leader or admin role'}), 400
            
            # Kiểm tra leader mới có đang lead group khác không
            existing_led_group = Group.query.filter_by(leader_id=new_leader_id).first()
            if existing_led_group and existing_led_group.id != group_id:
                return jsonify({'message': f'User is already leading group "{existing_led_group.name}". A user can only lead one group at a time.'}), 400
            
            # Gỡ leader cũ (nhưng vẫn giữ trong group)
            old_leader_id = group.leader_id
            
            # Gán leader mới
            group.leader_id = new_leader_id
            
            # Chuyển leader mới vào group này nếu chưa có
            if new_leader.group_id != group_id:
                # Nếu leader mới đang ở group khác, remove khỏi group cũ
                if new_leader.group_id:
                    # Kiểm tra xem có đang lead group cũ không
                    old_group = Group.query.get(new_leader.group_id)
                    if old_group and old_group.leader_id == new_leader_id:
                        return jsonify({'message': f'Cannot change leader. User is currently leading group "{old_group.name}". Remove as leader from that group first.'}), 400
                
                new_leader.group_id = group_id
    
    try:
        db.session.commit()
        return jsonify({'message': 'Group updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating group: {str(e)}'}), 500

# Xóa nhóm
@group_bp.route('/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Kiểm tra quyền (chỉ admin)
    admin = User.query.get(admin_id)
    if not admin or admin.role != 'admin':
        return jsonify({'message': 'Access denied. Only admins can delete groups'}), 403
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    # Kiểm tra nhóm còn members không
    members = User.query.filter_by(group_id=group_id).all()
    if members:
        return jsonify({'message': f'Cannot delete group. It has {len(members)} member(s). Remove all members first.'}), 400
    
    try:
        db.session.delete(group)
        db.session.commit()
        return jsonify({'message': f'Group {group.name} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting group: {str(e)}'}), 500

# Lấy danh sách nhóm mà user có thể join (cho employee)
@group_bp.route('/available', methods=['GET'])
def get_available_groups():
    groups = Group.query.all()
    result = []
    for group in groups:
        leader = User.query.get(group.leader_id)
        member_count = User.query.filter_by(group_id=group.id).count()
        
        result.append({
            'id': group.id,
            'name': group.name,
            'description': group.description,
            'leader_name': leader.name if leader else 'No leader',
            'member_count': member_count,
            'can_join': member_count < 10 and group.leader_id is not None  # Có leader và chưa đầy
        })
    return jsonify(result)

# Promote member thành leader của group hiện tại
@group_bp.route('/promote-member', methods=['POST'])
def promote_member_to_leader():
    data = request.get_json()
    admin_id = data.get('admin_id')
    user_id = data.get('user_id')
    group_id = data.get('group_id')
    
    # Kiểm tra quyền (chỉ admin)
    admin = User.query.get(admin_id)
    if not admin or admin.role != 'admin':
        return jsonify({'message': 'Access denied. Only admins can promote members to leader'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    # Kiểm tra user có trong group này không
    if user.group_id != group_id:
        return jsonify({'message': 'User is not a member of this group'}), 400
    
    # Kiểm tra user có đang lead group khác không
    existing_led_group = Group.query.filter_by(leader_id=user_id).first()
    if existing_led_group:
        return jsonify({'message': f'User is already leading group "{existing_led_group.name}". A user can only lead one group at a time.'}), 400
    
    try:
        # Nâng cấp role thành leader
        if user.role == 'employee':
            user.role = 'leader'
        
        # Gán làm leader của group
        group.leader_id = user_id
        
        db.session.commit()
        
        return jsonify({'message': f'User {user.name} has been promoted to leader of group {group.name} successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error promoting member: {str(e)}'}), 500

# Chuyển member sang group khác
@group_bp.route('/transfer-member', methods=['POST'])
@group_bp.route('/transfer-member', methods=['POST'])
def transfer_member_to_group():
    data = request.get_json()
    admin_id = data.get('admin_id')
    user_id = data.get('user_id')
    target_group_id = data.get('target_group_id')
    
    # Kiểm tra quyền (admin hoặc leader)
    admin = User.query.get(admin_id)
    if not admin or admin.role not in ['admin', 'leader']:
        return jsonify({'message': 'Access denied. Only admins or leaders can transfer members'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.group_id:
        return jsonify({'message': 'User is not in any group'}), 400
    
    # Lấy thông tin group hiện tại
    current_group = Group.query.get(user.group_id)
    
    # Nếu là leader, chỉ có thể transfer từ group mà mình lead
    if admin.role == 'leader':
        led_group = Group.query.filter_by(leader_id=admin_id).first()
        if not led_group:
            return jsonify({'message': 'You are not leading any group'}), 403
        if led_group.id != user.group_id:
            return jsonify({'message': 'You can only transfer members from your own group'}), 403
        
        # Leader không thể transfer chính mình
        if admin_id == user_id:
            return jsonify({'message': 'You cannot transfer yourself'}), 403
    
    target_group = Group.query.get(target_group_id)
    if not target_group:
        return jsonify({'message': 'Target group not found'}), 404
    
    # Kiểm tra user có phải leader của group hiện tại không
    is_current_leader = (current_group.leader_id == user_id)
    
    if is_current_leader:
        return jsonify({'message': f'Cannot transfer group leader. Remove as leader first or promote another member to leader.'}), 400
    
    try:
        # Chuyển sang group mới
        user.group_id = target_group_id
        
        db.session.commit()
        
        return jsonify({'message': f'User {user.name} transferred from "{current_group.name}" to "{target_group.name}" successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error transferring member: {str(e)}'}), 500

# Lấy danh sách groups để transfer
@group_bp.route('/transfer-options/<int:current_group_id>', methods=['GET'])
def get_transfer_options(current_group_id):
    # Lấy tất cả groups trừ group hiện tại
    groups = Group.query.filter(Group.id != current_group_id).all()
    result = []
    
    for group in groups:
        leader = User.query.get(group.leader_id)
        member_count = User.query.filter_by(group_id=group.id).count()
        
        result.append({
            'id': group.id,
            'name': group.name,
            'leader_name': leader.name if leader else 'No leader',
            'member_count': member_count,
            'can_join': group.leader_id is not None  # Chỉ có thể join group có leader
        })
    
    return jsonify(result)

@group_bp.route('/join-request', methods=['POST'])
def create_join_request():
    """Employee tạo request join group"""
    data = request.get_json()
    user_id = data.get('user_id')
    group_id = data.get('group_id')
    message = data.get('message', '')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Chỉ employee mới có thể request
    if user.role != 'employee':
        return jsonify({'message': 'Only employees can request to join groups'}), 403
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'message': 'Group not found'}), 404
    
    # Kiểm tra user đã trong group nào chưa
    if user.group_id:
        current_group = Group.query.get(user.group_id)
        return jsonify({'message': f'You are already in group "{current_group.name}". Leave current group first.'}), 400
    
    # Kiểm tra đã có pending request chưa
    existing_request = JoinRequest.query.filter_by(
        user_id=user_id,
        group_id=group_id,
        status=JoinRequestStatus.PENDING
    ).first()
    
    if existing_request:
        return jsonify({'message': 'You already have a pending request for this group'}), 400
    
    # Kiểm tra group có leader không
    if not group.leader_id:
        return jsonify({'message': 'This group has no leader. Cannot submit join request.'}), 400
    
    try:
        # Tạo join request
        join_request = JoinRequest(
            user_id=user_id,
            group_id=group_id,
            message=message,
            status=JoinRequestStatus.PENDING
        )
        
        db.session.add(join_request)
        db.session.commit()
        
        # ✅ Gửi notification cho admin và leader
        # Notification cho admin
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            create_notification(
                user_id=admin.id,
                title=f"New join request: {group.name}",
                message=f"{user.name} ({user.employee_code}) wants to join group '{group.name}'",
                notification_type=NotificationType.GROUP_JOIN_REQUEST,
                group_id=group_id,
                is_important=True
            )
        
        # Notification cho leader của group (nếu khác admin)
        if group.leader_id:
            leader = User.query.get(group.leader_id)
            if leader and leader.role != 'admin':
                create_notification(
                    user_id=leader.id,
                    title=f"New join request: {group.name}",
                    message=f"{user.name} ({user.employee_code}) wants to join your group '{group.name}'",
                    notification_type=NotificationType.GROUP_JOIN_REQUEST,
                    group_id=group_id,
                    is_important=True
                )
        
        return jsonify({
            'message': 'Join request submitted successfully',
            'request': join_request.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating join request: {str(e)}'}), 500

@group_bp.route('/join-requests', methods=['GET'])
def get_join_requests():
    """Lấy danh sách join requests (cho admin/leader)"""
    user_id = request.args.get('user_id')
    group_id = request.args.get('group_id')  # Optional filter
    status = request.args.get('status', 'pending')  # pending, approved, rejected, all
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Base query
    query = JoinRequest.query
    
    if user.role == 'admin':
        # Admin xem tất cả requests
        pass
    elif user.role == 'leader':
        # Leader chỉ xem requests cho group mà mình lead
        led_group = Group.query.filter_by(leader_id=user_id).first()
        if not led_group:
            return jsonify([])  # Không lead group nào
        query = query.filter_by(group_id=led_group.id)
    else:
        return jsonify({'message': 'Access denied. Only admin and leaders can view join requests'}), 403
    
    # Apply filters
    if group_id:
        query = query.filter_by(group_id=group_id)
    
    if status != 'all':
        query = query.filter_by(status=JoinRequestStatus(status))
    
    requests = query.order_by(JoinRequest.created_at.desc()).all()
    
    return jsonify([req.to_dict() for req in requests])

@group_bp.route('/join-requests/<int:request_id>/approve', methods=['POST'])
def approve_join_request(request_id):
    """Admin/Leader approve join request"""
    data = request.get_json()
    admin_id = data.get('admin_id')
    admin_message = data.get('admin_message', '')
    
    admin = User.query.get(admin_id)
    if not admin or admin.role not in ['admin', 'leader']:
        return jsonify({'message': 'Access denied. Only admin and leaders can approve requests'}), 403
    
    join_request = JoinRequest.query.get(request_id)
    if not join_request:
        return jsonify({'message': 'Join request not found'}), 404
    
    if join_request.status != JoinRequestStatus.PENDING:
        return jsonify({'message': 'Request is no longer pending'}), 400
    
    # Nếu là leader, chỉ có thể approve requests cho group mình lead
    if admin.role == 'leader':
        led_group = Group.query.filter_by(leader_id=admin_id).first()
        if not led_group or led_group.id != join_request.group_id:
            return jsonify({'message': 'You can only approve requests for your own group'}), 403
    
    # Kiểm tra user còn available không
    user = User.query.get(join_request.user_id)
    if user.group_id:
        return jsonify({'message': 'User has already joined another group'}), 400
    
    try:
        # Approve request
        join_request.status = JoinRequestStatus.APPROVED
        join_request.admin_message = admin_message
        join_request.processed_by_id = admin_id
        join_request.processed_at = datetime.utcnow()
        
        # Add user to group
        user.group_id = join_request.group_id
        
        db.session.commit()
        
        # ✅ Gửi notification cho user
        create_notification(
            user_id=user.id,
            title=f"Join request approved: {join_request.group.name}",
            message=f"Your request to join '{join_request.group.name}' has been approved by {admin.name}",
            notification_type=NotificationType.GROUP_JOINED,
            group_id=join_request.group_id,
            is_important=True
        )
        
        return jsonify({
            'message': 'Join request approved successfully',
            'request': join_request.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error approving request: {str(e)}'}), 500

@group_bp.route('/join-requests/<int:request_id>/reject', methods=['POST'])
def reject_join_request(request_id):
    """Admin/Leader reject join request"""
    data = request.get_json()
    admin_id = data.get('admin_id')
    admin_message = data.get('admin_message', '')
    
    admin = User.query.get(admin_id)
    if not admin or admin.role not in ['admin', 'leader']:
        return jsonify({'message': 'Access denied. Only admin and leaders can reject requests'}), 403
    
    join_request = JoinRequest.query.get(request_id)
    if not join_request:
        return jsonify({'message': 'Join request not found'}), 404
    
    if join_request.status != JoinRequestStatus.PENDING:
        return jsonify({'message': 'Request is no longer pending'}), 400
    
    # Nếu là leader, chỉ có thể reject requests cho group mình lead
    if admin.role == 'leader':
        led_group = Group.query.filter_by(leader_id=admin_id).first()
        if not led_group or led_group.id != join_request.group_id:
            return jsonify({'message': 'You can only reject requests for your own group'}), 403
    
    try:
        # Reject request
        join_request.status = JoinRequestStatus.REJECTED
        join_request.admin_message = admin_message
        join_request.processed_by_id = admin_id
        join_request.processed_at = datetime.utcnow()
        
        db.session.commit()
        
        # ✅ Gửi notification cho user
        create_notification(
            user_id=join_request.user_id,
            title=f"Join request rejected: {join_request.group.name}",
            message=f"Your request to join '{join_request.group.name}' has been rejected by {admin.name}",
            notification_type=NotificationType.GROUP_JOIN_REJECTED,
            group_id=join_request.group_id,
            is_important=True
        )
        
        return jsonify({
            'message': 'Join request rejected',
            'request': join_request.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error rejecting request: {str(e)}'}), 500

@group_bp.route('/my-join-requests', methods=['GET'])
def get_my_join_requests():
    """Lấy danh sách join requests của user hiện tại"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'Missing user_id'}), 400
    
    requests = JoinRequest.query.filter_by(user_id=user_id).order_by(JoinRequest.created_at.desc()).all()
    
    return jsonify([req.to_dict() for req in requests])