from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from database import db
from models.file import File
from models.task import Task
from models.user import User
from config import Config

file_bp = Blueprint('file', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(filepath):
    """Lấy kích thước file in bytes"""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0

# Upload file cho task
@file_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    task_id = request.form.get('task_id')
    uploaded_by = request.form.get('uploaded_by')  # user_id

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if not task_id or not uploaded_by:
        return jsonify({'message': 'Missing task_id or uploaded_by'}), 400

    # Validate file type
    if not allowed_file(file.filename):
        return jsonify({'message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Validate task_id exists
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': f'Task with ID {task_id} not found'}), 404

    # Validate uploaded_by exists
    user = User.query.get(uploaded_by)
    if not user:
        return jsonify({'message': f'User with ID {uploaded_by} not found'}), 404

    # Kiểm tra quyền: user phải là assignee hoặc assigner của task
    if task.assignee_id != int(uploaded_by) and task.assigner_id != int(uploaded_by):
        return jsonify({'message': 'You do not have permission to upload files to this task'}), 403

    # Tạo thư mục upload nếu chưa tồn tại
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)

    # Tạo filename unique để tránh trùng lặp
    filename = secure_filename(file.filename)
    base_name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(Config.UPLOAD_FOLDER, filename)):
        filename = f"{base_name}_{counter}{ext}"
        counter += 1

    save_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    
    try:
        file.save(save_path)
        
        new_file = File(
            task_id=task_id,
            filename=filename,
            filepath=save_path,
            uploaded_by=uploaded_by
        )
        db.session.add(new_file)
        db.session.commit()

        return jsonify({
            'message': 'File uploaded successfully',
            'file': {
                'id': new_file.id,
                'filename': new_file.filename,
                'task_id': new_file.task_id,
                'uploaded_by': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email
                },
                'file_size': get_file_size(save_path),
                'upload_date': new_file.upload_date.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error uploading file: {str(e)}'}), 500

# Lấy danh sách file của 1 task
@file_bp.route('/task/<int:task_id>', methods=['GET'])
def get_files(task_id):
    # Validate task exists
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': f'Task with ID {task_id} not found'}), 404

    files = File.query.filter_by(task_id=task_id).order_by(File.upload_date.desc()).all()
    result = []
    for f in files:
        uploader = User.query.get(f.uploaded_by)
        result.append({
            'id': f.id,
            'filename': f.filename,
            'filepath': f.filepath,
            'uploaded_by': {
                'id': uploader.id,
                'name': uploader.name,
                'email': uploader.email
            } if uploader else None,
            'file_size': get_file_size(f.filepath),
            'upload_date': f.upload_date.strftime('%Y-%m-%d %H:%M:%S') if f.upload_date else None
        })
    return jsonify({
        'files': result,
        'total_files': len(result),
        'total_size': sum([get_file_size(f.filepath) for f in files])
    })

# Download file
@file_bp.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    file_record = File.query.get(file_id)
    if not file_record:
        return jsonify({'message': 'File not found'}), 404

    if not os.path.exists(file_record.filepath):
        return jsonify({'message': 'File does not exist on server'}), 404

    try:
        return send_file(file_record.filepath, as_attachment=True, download_name=file_record.filename)
    except Exception as e:
        return jsonify({'message': f'Error downloading file: {str(e)}'}), 500

# Xóa file
@file_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    file_record = File.query.get(file_id)
    if not file_record:
        return jsonify({'message': 'File not found'}), 404

    # Kiểm tra quyền: chỉ người upload hoặc admin/leader có thể xóa
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.role not in ['admin', 'leader'] and file_record.uploaded_by != user_id:
            return jsonify({'message': 'You do not have permission to delete this file'}), 403

    try:
        # Xóa file trong filesystem
        if os.path.exists(file_record.filepath):
            os.remove(file_record.filepath)
        
        # Xóa record trong database
        db.session.delete(file_record)
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting file: {str(e)}'}), 500

# Lấy thông tin chi tiết 1 file
@file_bp.route('/<int:file_id>', methods=['GET'])
def get_file_detail(file_id):
    file_record = File.query.get(file_id)
    if not file_record:
        return jsonify({'message': 'File not found'}), 404

    uploader = User.query.get(file_record.uploaded_by)
    task = Task.query.get(file_record.task_id)

    return jsonify({
        'id': file_record.id,
        'filename': file_record.filename,
        'filepath': file_record.filepath,
        'file_size': get_file_size(file_record.filepath),
        'task': {
            'id': task.id,
            'title': task.title,
            'status': task.status
        } if task else None,
        'uploaded_by': {
            'id': uploader.id,
            'name': uploader.name,
            'email': uploader.email,
            'employee_code': uploader.employee_code
        } if uploader else None,
        'upload_date': file_record.upload_date.strftime('%Y-%m-%d %H:%M:%S') if file_record.upload_date else None
    })

# Lấy tất cả files (cho admin/leader)
@file_bp.route('/all', methods=['GET'])
def get_all_files():
    user_id = request.args.get('user_id')
    
    # Kiểm tra quyền (admin/leader)
    if user_id:
        user = User.query.get(user_id)
        if not user or user.role not in ['admin', 'leader']:
            return jsonify({'message': 'Access denied. Only admins or leaders can view all files'}), 403

    files = File.query.order_by(File.upload_date.desc()).all()
    result = []
    
    for f in files:
        uploader = User.query.get(f.uploaded_by)
        task = Task.query.get(f.task_id)
        
        result.append({
            'id': f.id,
            'filename': f.filename,
            'file_size': get_file_size(f.filepath),
            'task': {
                'id': task.id,
                'title': task.title,
                'status': task.status
            } if task else None,
            'uploaded_by': {
                'id': uploader.id,
                'name': uploader.name,
                'employee_code': uploader.employee_code
            } if uploader else None,
            'upload_date': f.upload_date.strftime('%Y-%m-%d %H:%M:%S') if f.upload_date else None
        })
    
    return jsonify({
        'files': result,
        'total_files': len(result),
        'total_size': sum([get_file_size(f.filepath) for f in files])
    })

# Lấy files của 1 user
@file_bp.route('/user/<int:user_id>', methods=['GET'])
def get_files_by_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    files = File.query.filter_by(uploaded_by=user_id).order_by(File.upload_date.desc()).all()
    result = []
    
    for f in files:
        task = Task.query.get(f.task_id)
        result.append({
            'id': f.id,
            'filename': f.filename,
            'file_size': get_file_size(f.filepath),
            'task': {
                'id': task.id,
                'title': task.title,
                'status': task.status
            } if task else None,
            'upload_date': f.upload_date.strftime('%Y-%m-%d %H:%M:%S') if f.upload_date else None
        })
    
    return jsonify({
        'user': {
            'id': user.id,
            'name': user.name,
            'employee_code': user.employee_code
        },
        'files': result,
        'total_files': len(result),
        'total_size': sum([get_file_size(f.filepath) for f in files])
    })

# Thống kê files
@file_bp.route('/stats', methods=['GET'])
def get_file_stats():
    user_id = request.args.get('user_id')
    
    # Kiểm tra quyền
    if user_id:
        user = User.query.get(user_id)
        if not user or user.role not in ['admin', 'leader']:
            return jsonify({'message': 'Access denied'}), 403

    all_files = File.query.all()
    total_files = len(all_files)
    total_size = sum([get_file_size(f.filepath) for f in all_files])
    
    # Thống kê theo file type
    file_types = {}
    for f in all_files:
        ext = f.filename.split('.')[-1].lower() if '.' in f.filename else 'unknown'
        file_types[ext] = file_types.get(ext, 0) + 1
    
    # Thống kê theo user
    user_stats = {}
    for f in all_files:
        user_id = f.uploaded_by
        if user_id:
            user = User.query.get(user_id)
            if user:
                user_stats[user.name] = user_stats.get(user.name, 0) + 1

    return jsonify({
        'total_files': total_files,
        'total_size': total_size,
        'file_types': file_types,
        'top_uploaders': dict(sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:10])
    })