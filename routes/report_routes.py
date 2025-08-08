from flask import Blueprint, request, jsonify, send_file
from database import db
from models.report import Report
from models.task import Task
from models.user import User
from models.group import Group
import os
from config import Config
from datetime import datetime, timedelta
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import re
from routes.notification_routes import create_notification, NotificationType

report_bp = Blueprint('report', __name__)

# 1. Tạo báo cáo tuần cho nhân viên (Excel)
@report_bp.route('/generate', methods=['POST'])
def generate_weekly_report():
    """Tạo báo cáo tuần cho nhân viên"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        week = data.get('week')  # Format: 2025-W01

        if not user_id or not week:
            return jsonify({'message': 'Missing user_id or week'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Parse week to get date range
        try:
            year, week_num = week.split('-W')
            year = int(year)
            week_num = int(week_num)
            
            jan1 = datetime(year, 1, 1)
            start_date = jan1 + timedelta(weeks=week_num-1) - timedelta(days=jan1.weekday())
            end_date = start_date + timedelta(days=6)
        except ValueError:
            return jsonify({'message': 'Invalid week format. Use YYYY-WXX'}), 400

        # Get tasks for the week
        tasks = Task.query.filter(
            Task.assignee_id == user_id,
            Task.created_at >= start_date,
            Task.created_at <= end_date + timedelta(days=1)
        ).all()

        # ✅ Tạo báo cáo ngay cả khi không có tasks
        # Create reports folder
        reports_folder = os.path.join(Config.UPLOAD_FOLDER, 'reports')
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Prepare data for Excel
        task_data = []
        if tasks:
            for task in tasks:
                assigner = User.query.get(task.assigner_id) if task.assigner_id else None
                
                task_data.append({
                    'Task ID': task.id,
                    'Title': task.title,
                    'Description': task.description or '',
                    'Status': task.status,
                    'Priority': getattr(task, 'priority', 'medium'),
                    'Deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else '',
                    'Assigner': assigner.name if assigner else '',
                    'Created Date': task.created_at.strftime('%Y-%m-%d') if task.created_at else '',
                    'Updated Date': task.updated_at.strftime('%Y-%m-%d') if task.updated_at else ''
                })
        else:
            # ✅ Thêm dòng thông báo không có tasks
            task_data.append({
                'Task ID': 'N/A',
                'Title': 'No tasks found for this week',
                'Description': f'No tasks assigned to {user.name} for week {week}',
                'Status': 'N/A',
                'Priority': 'N/A',
                'Deadline': 'N/A',
                'Assigner': 'N/A',
                'Created Date': 'N/A',
                'Updated Date': 'N/A'
            })

        # Create Excel file
        df = pd.DataFrame(task_data)
        filename = f"weekly_report_{user.name.replace(' ', '_')}_{week}.xlsx"
        file_path = os.path.join(reports_folder, filename)

        # Statistics
        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.status == 'done']) if tasks else 0
        in_progress = len([t for t in tasks if t.status == 'doing']) if tasks else 0
        todo = len([t for t in tasks if t.status == 'todo']) if tasks else 0

        stats_data = [
            ['Metric', 'Value'],
            ['Total Tasks', total_tasks],
            ['Completed', completed],
            ['In Progress', in_progress],
            ['To Do', todo],
            ['Completion Rate', f"{(completed/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"]
        ]
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Summary sheet
            pd.DataFrame(stats_data[1:], columns=stats_data[0]).to_excel(writer, sheet_name='Summary', index=False)
            # Tasks sheet
            df.to_excel(writer, sheet_name='Tasks', index=False)

        # Save to database
        new_report = Report(
            user_id=user_id,
            week=week,
            file_path=file_path
        )
        db.session.add(new_report)
        db.session.commit()
        
        create_notification(
            user_id=user_id,
            title="Weekly report generated",
            message=f"Your weekly report for {week} has been generated successfully",
            notification_type=NotificationType.REPORT_GENERATED,
            report_id=new_report.id
        )

        return jsonify({
            'message': 'Weekly report generated successfully',
            'report': {
                'id': new_report.id,
                'filename': filename,
                'week': week,
                'tasks_count': total_tasks,
                'created_at': new_report.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error generating report: {str(e)}'}), 500

# 2. Tạo báo cáo tuần cho nhân viên (PDF)
@report_bp.route('/generate-pdf', methods=['POST'])
def generate_weekly_report_pdf():
    """Tạo báo cáo tuần PDF cho nhân viên"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        week = data.get('week')

        if not user_id or not week:
            return jsonify({'message': 'Missing user_id or week'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Parse week
        try:
            year, week_num = week.split('-W')
            year = int(year)
            week_num = int(week_num)
            
            jan1 = datetime(year, 1, 1)
            start_date = jan1 + timedelta(weeks=week_num-1) - timedelta(days=jan1.weekday())
            end_date = start_date + timedelta(days=6)
        except ValueError:
            return jsonify({'message': 'Invalid week format'}), 400

        # Get tasks
        tasks = Task.query.filter(
            Task.assignee_id == user_id,
            Task.created_at >= start_date,
            Task.created_at <= end_date + timedelta(days=1)
        ).all()

        # Create reports folder
        reports_folder = os.path.join(Config.UPLOAD_FOLDER, 'reports')
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Create PDF
        filename = f"weekly_report_{user.name.replace(' ', '_')}_{week}.pdf"
        file_path = os.path.join(reports_folder, filename)

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph(f"Weekly Report - {week}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # User info
        user_info = Paragraph(f"<b>Employee:</b> {user.name}<br/><b>Email:</b> {user.email}", styles['Normal'])
        story.append(user_info)
        story.append(Spacer(1, 12))

        # Statistics
        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.status == 'done']) if tasks else 0
        
        stats_data = [
            ['Metric', 'Value'],
            ['Total Tasks', str(total_tasks)],
            ['Completed', str(completed)],
            ['Completion Rate', f"{(completed/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 12))

        # Tasks table
        if tasks:
            task_data = [['ID', 'Title', 'Status', 'Priority', 'Deadline']]
            for task in tasks:
                task_data.append([
                    str(task.id),
                    task.title[:25] + '...' if len(task.title) > 25 else task.title,
                    task.status,
                    getattr(task, 'priority', 'medium'),
                    task.deadline.strftime('%Y-%m-%d') if task.deadline else 'N/A'
                ])
        else:
            # ✅ Thông báo không có tasks
            task_data = [['Message'], ['No tasks found for this week']]

        tasks_table = Table(task_data, colWidths=[0.5*inch, 2*inch, 1*inch, 1*inch, 1.5*inch] if tasks else [6*inch])
        tasks_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tasks_table)
        doc.build(story)

        # Save to database
        new_report = Report(
            user_id=user_id,
            week=f"PDF_{week}",
            file_path=file_path
        )
        db.session.add(new_report)
        db.session.commit()
        
        create_notification(
            user_id=user_id,
            title="Weekly report generated",
            message=f"Your weekly report for {week} has been generated successfully",
            notification_type=NotificationType.REPORT_GENERATED,
            report_id=new_report.id
        )

        return jsonify({
            'message': 'PDF report generated successfully',
            'report': {
                'id': new_report.id,
                'filename': filename,
                'week': week,
                'format': 'PDF',
                'created_at': new_report.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error generating PDF: {str(e)}'}), 500

# 3. Tạo báo cáo tổng hợp cho admin/leader (Excel)
@report_bp.route('/summary', methods=['POST'])
def generate_summary_report():
    """Tạo báo cáo tổng hợp cho admin/leader"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        week = data.get('week')
        group_id = data.get('group_id')  # Optional, for filtering

        if not admin_id or not week:
            return jsonify({'message': 'Missing admin_id or week'}), 400

        admin = User.query.get(admin_id)
        if not admin or admin.role not in ['admin', 'leader']:
            return jsonify({'message': 'Access denied. Only admin/leader can generate summary reports'}), 403

        # Parse week
        try:
            year, week_num = week.split('-W')
            year = int(year)
            week_num = int(week_num)
            
            jan1 = datetime(year, 1, 1)
            start_date = jan1 + timedelta(weeks=week_num-1) - timedelta(days=jan1.weekday())
            end_date = start_date + timedelta(days=6)
        except ValueError:
            return jsonify({'message': 'Invalid week format'}), 400

        # ✅ Build query based on role - SỬA LẠI LOGIC
        query = Task.query.filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date + timedelta(days=1)
        )

        if admin.role == 'leader':
            # ✅ Leader chỉ xem tasks trong nhóm của mình
            if not admin.group_id:
                # ✅ Tạo báo cáo trống cho leader không có nhóm
                tasks = []
                report_scope = f"Leader {admin.name} (No group assigned)"
            else:
                # Lấy tất cả users trong nhóm của leader
                group_users = User.query.filter_by(group_id=admin.group_id).all()
                if group_users:
                    user_ids = [u.id for u in group_users]
                    query = query.filter(Task.assignee_id.in_(user_ids))
                    tasks = query.all()
                else:
                    tasks = []
                
                group = Group.query.get(admin.group_id)
                group_name = group.name if group else f"Group {admin.group_id}"
                report_scope = f"Group: {group_name}"
                
        elif admin.role == 'admin':
            if group_id:
                # ✅ Admin chọn group cụ thể
                group = Group.query.get(group_id)
                if not group:
                    return jsonify({'message': 'Group not found'}), 404
                
                group_users = User.query.filter_by(group_id=group_id).all()
                if group_users:
                    user_ids = [u.id for u in group_users]
                    query = query.filter(Task.assignee_id.in_(user_ids))
                    tasks = query.all()
                else:
                    tasks = []
                
                report_scope = f"Group: {group.name}"
            else:
                # ✅ Admin xem tất cả
                tasks = query.all()
                report_scope = "All Groups"

        # ✅ Tạo báo cáo ngay cả khi không có tasks
        # Create reports folder
        reports_folder = os.path.join(Config.UPLOAD_FOLDER, 'reports')
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Prepare summary data
        summary_data = []
        if tasks:
            for task in tasks:
                assignee = User.query.get(task.assignee_id) if task.assignee_id else None
                assigner = User.query.get(task.assigner_id) if task.assigner_id else None
                task_group = Group.query.get(task.group_id) if task.group_id else None
                
                summary_data.append({
                    'Task ID': task.id,
                    'Title': task.title,
                    'Status': task.status,
                    'Priority': getattr(task, 'priority', 'medium'),
                    'Assignee': assignee.name if assignee else 'Unassigned',
                    'Assignee Email': assignee.email if assignee else '',
                    'Assignee Code': getattr(assignee, 'employee_code', '') if assignee else '',
                    'Assigner': assigner.name if assigner else '',
                    'Group': task_group.name if task_group else 'No Group',
                    'Created Date': task.created_at.strftime('%Y-%m-%d') if task.created_at else '',
                    'Deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else ''
                })
        else:
            # ✅ Thêm dòng thông báo không có tasks
            summary_data.append({
                'Task ID': 'N/A',
                'Title': 'No tasks found for this week',
                'Status': 'N/A',
                'Priority': 'N/A',
                'Assignee': 'N/A',
                'Assignee Email': 'N/A',
                'Assignee Code': 'N/A',
                'Assigner': 'N/A',
                'Group': report_scope,
                'Created Date': 'N/A',
                'Deadline': 'N/A'
            })

        # Statistics
        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.status == 'done']) if tasks else 0
        in_progress = len([t for t in tasks if t.status == 'doing']) if tasks else 0
        todo = len([t for t in tasks if t.status == 'todo']) if tasks else 0

        stats_data = [
            ['Total Tasks', total_tasks],
            ['Completed', completed],
            ['In Progress', in_progress],
            ['To Do', todo],
            ['Completion Rate', f"{(completed/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"],
            ['Report Scope', report_scope],
            ['Generated By', f"{admin.name} ({admin.role})"],
            ['Week Period', f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"]
        ]

        # Create Excel file
        role_prefix = "A" if admin.role == 'admin' else "L"
        group_suffix = f"_group_{group_id}" if group_id else ""
        filename = f"{role_prefix.lower()}_summary_{week}{group_suffix}.xlsx"
        file_path = os.path.join(reports_folder, filename)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Summary statistics
            pd.DataFrame(stats_data, columns=['Metric', 'Value']).to_excel(writer, sheet_name='Statistics', index=False)
            
            # All tasks
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='All Tasks', index=False)
            
            # ✅ Tasks by user - chỉ tạo khi có tasks
            if tasks:
                user_tasks = {}
                for task in tasks:
                    if task.assignee_id:
                        if task.assignee_id not in user_tasks:
                            user_tasks[task.assignee_id] = []
                        user_tasks[task.assignee_id].append(task)
                
                for user_id, user_task_list in user_tasks.items():
                    user = User.query.get(user_id)
                    if user:
                        user_data = []
                        for task in user_task_list:
                            user_data.append({
                                'Task ID': task.id,
                                'Title': task.title,
                                'Status': task.status,
                                'Priority': getattr(task, 'priority', 'medium'),
                                'Deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else ''
                            })
                        
                        sheet_name = re.sub(r'[^\w\s-]', '', user.name)[:30]
                        if user_data:  # Chỉ tạo sheet khi có data
                            pd.DataFrame(user_data).to_excel(writer, sheet_name=sheet_name, index=False)

        # Save to database
        new_report = Report(
            user_id=admin_id,
            week=f"{role_prefix}_SUM_{week}",
            file_path=file_path
        )
        db.session.add(new_report)
        db.session.commit()

        return jsonify({
            'message': 'Summary report generated successfully',
            'report': {
                'id': new_report.id,
                'filename': filename,
                'week': week,
                'scope': report_scope,
                'created_at': new_report.created_at.strftime('%Y-%m-%d %H:%M:%S')
            },
            'statistics': {
                'total_tasks': total_tasks,
                'completed': completed,
                'in_progress': in_progress,
                'todo': todo
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error generating summary: {str(e)}'}), 500

# 4. Tạo báo cáo tổng hợp PDF cho admin/leader
@report_bp.route('/summary-pdf', methods=['POST'])
def generate_summary_report_pdf():
    """Tạo báo cáo tổng hợp PDF cho admin/leader"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        week = data.get('week')
        group_id = data.get('group_id')

        if not admin_id or not week:
            return jsonify({'message': 'Missing admin_id or week'}), 400

        admin = User.query.get(admin_id)
        if not admin or admin.role not in ['admin', 'leader']:
            return jsonify({'message': 'Access denied'}), 403

        # Parse week
        try:
            year, week_num = week.split('-W')
            year = int(year)
            week_num = int(week_num)
            
            jan1 = datetime(year, 1, 1)
            start_date = jan1 + timedelta(weeks=week_num-1) - timedelta(days=jan1.weekday())
            end_date = start_date + timedelta(days=6)
        except ValueError:
            return jsonify({'message': 'Invalid week format'}), 400

        # ✅ Get tasks based on role - logic giống Excel
        query = Task.query.filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date + timedelta(days=1)
        )

        if admin.role == 'leader':
            if not admin.group_id:
                tasks = []
                report_scope = f"Leader {admin.name} (No group assigned)"
            else:
                group_users = User.query.filter_by(group_id=admin.group_id).all()
                if group_users:
                    user_ids = [u.id for u in group_users]
                    query = query.filter(Task.assignee_id.in_(user_ids))
                    tasks = query.all()
                else:
                    tasks = []
                
                group = Group.query.get(admin.group_id)
                group_name = group.name if group else f"Group {admin.group_id}"
                report_scope = f"Group: {group_name}"
                
        elif admin.role == 'admin':
            if group_id:
                group = Group.query.get(group_id)
                if not group:
                    return jsonify({'message': 'Group not found'}), 404
                
                group_users = User.query.filter_by(group_id=group_id).all()
                if group_users:
                    user_ids = [u.id for u in group_users]
                    query = query.filter(Task.assignee_id.in_(user_ids))
                    tasks = query.all()
                else:
                    tasks = []
                
                report_scope = f"Group: {group.name}"
            else:
                tasks = query.all()
                report_scope = "All Groups"

        # Create PDF
        reports_folder = os.path.join(Config.UPLOAD_FOLDER, 'reports')
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        role_prefix = "A" if admin.role == 'admin' else "L"
        group_suffix = f"_group_{group_id}" if group_id else ""
        filename = f"{role_prefix.lower()}_summary_{week}{group_suffix}.pdf"
        file_path = os.path.join(reports_folder, filename)

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph(f"Summary Report - {week}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Admin info
        admin_info = Paragraph(f"<b>Generated by:</b> {admin.name} ({admin.role})<br/><b>Scope:</b> {report_scope}", styles['Normal'])
        story.append(admin_info)
        story.append(Spacer(1, 12))

        # Statistics
        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.status == 'done']) if tasks else 0
        
        stats_data = [
            ['Metric', 'Value'],
            ['Total Tasks', str(total_tasks)],
            ['Completed', str(completed)],
            ['Completion Rate', f"{(completed/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 12))

        # ✅ Tasks by user - xử lý khi không có tasks
        if tasks:
            user_tasks = {}
            for task in tasks:
                if task.assignee_id:
                    if task.assignee_id not in user_tasks:
                        user_tasks[task.assignee_id] = []
                    user_tasks[task.assignee_id].append(task)

            if user_tasks:
                for user_id, user_task_list in user_tasks.items():
                    user = User.query.get(user_id)
                    if user:
                        user_title = Paragraph(f"Tasks for {user.name}", styles['Heading2'])
                        story.append(user_title)
                        
                        task_data = [['ID', 'Title', 'Status', 'Priority']]
                        for task in user_task_list:
                            task_data.append([
                                str(task.id),
                                task.title[:30] + '...' if len(task.title) > 30 else task.title,
                                task.status,
                                getattr(task, 'priority', 'medium')
                            ])
                        
                        tasks_table = Table(task_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch])
                        tasks_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        story.append(tasks_table)
                        story.append(Spacer(1, 12))
            else:
                # Có tasks nhưng không có assignee
                no_assignee = Paragraph("No assigned tasks found", styles['Normal'])
                story.append(no_assignee)
        else:
            # ✅ Thông báo không có tasks
            no_tasks = Paragraph(f"No tasks found for {report_scope} in week {week}", styles['Normal'])
            story.append(no_tasks)

        doc.build(story)

        # Save to database
        role_prefix = "A" if admin.role == 'admin' else "L"  # ✅ Rút ngắn
        new_report = Report(
            user_id=admin_id,
            week=f"PDF_{role_prefix}_SUM_{week}",
            file_path=file_path
        )
        db.session.add(new_report)
        db.session.commit()

        return jsonify({
            'message': 'Summary PDF generated successfully',
            'report': {
                'id': new_report.id,
                'filename': filename,
                'week': week,
                'format': 'PDF',
                'scope': report_scope,
                'created_at': new_report.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error generating PDF: {str(e)}'}), 500

# 5. Lấy danh sách reports
@report_bp.route('/list', methods=['GET'])
def get_reports():
    """Lấy danh sách reports theo quyền"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'Missing user_id'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Build query based on role
    if user.role == 'employee':
        reports = Report.query.filter_by(user_id=user_id).order_by(Report.created_at.desc()).all()
    elif user.role == 'leader':
        if user.group_id:
            group_users = User.query.filter_by(group_id=user.group_id).all()
            user_ids = [u.id for u in group_users]
            reports = Report.query.filter(Report.user_id.in_(user_ids)).order_by(Report.created_at.desc()).all()
        else:
            reports = Report.query.filter_by(user_id=user_id).order_by(Report.created_at.desc()).all()
    else:  # admin
        reports = Report.query.order_by(Report.created_at.desc()).all()

    result = []
    for report in reports:
        creator = User.query.get(report.user_id)
        
        filename = os.path.basename(report.file_path) if report.file_path else 'unknown.xlsx'
        file_size = os.path.getsize(report.file_path) if report.file_path and os.path.exists(report.file_path) else 0
        
        # Determine report type and format
        week_str = report.week
        if 'SUM' in week_str or 'SUMMARY' in week_str:
            report_type = 'summary'
        else:
            report_type = 'weekly'
            
        if 'PDF' in week_str:
            format_type = 'pdf'
        else:
            format_type = 'excel'
        
        # Extract week period
        week_match = re.search(r'(\d{4}-W\d{2})', report.week)
        week_period = week_match.group(1) if week_match else 'Custom'
        
        result.append({
            'id': report.id,
            'filename': filename,
            'report_type': report_type,
            'format': format_type,
            'week_period': week_period,
            'file_size': file_size,
            # ✅ XÓA download_count
            'created_by': creator.name if creator else 'Unknown',
            'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify(result)

# 6. Download report
@report_bp.route('/download/<int:report_id>', methods=['GET'])
def download_report(report_id):
    """Download report file"""
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    if not report.file_path or not os.path.exists(report.file_path):
        return jsonify({'message': 'File not found'}), 404
    
    return send_file(report.file_path, as_attachment=True)

# 7. Delete report
@report_bp.route('/delete/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Delete report"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'Missing user_id'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    # Check permissions
    if user.role == 'employee' and report.user_id != user.id:
        return jsonify({'message': 'Access denied'}), 403
    elif user.role == 'leader':
        creator = User.query.get(report.user_id)
        if not creator or (creator.group_id != user.group_id and report.user_id != user.id):
            return jsonify({'message': 'Access denied'}), 403
    # Admin can delete any report
    
    try:
        # Delete file
        if report.file_path and os.path.exists(report.file_path):
            os.remove(report.file_path)
        
        # Delete record
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({'message': 'Report deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting report: {str(e)}'}), 500

# 8. Get statistics
@report_bp.route('/stats', methods=['GET'])
def get_statistics():
    """Get report statistics"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'Missing user_id'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Build query based on role
    if user.role == 'employee':
        reports = Report.query.filter_by(user_id=user_id).all()
    elif user.role == 'leader':
        if user.group_id:
            group_users = User.query.filter_by(group_id=user.group_id).all()
            user_ids = [u.id for u in group_users]
            reports = Report.query.filter(Report.user_id.in_(user_ids)).all()
        else:
            reports = Report.query.filter_by(user_id=user_id).all()
    else:  # admin
        reports = Report.query.all()
    
    # Calculate statistics
    total = len(reports)
    
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    this_week = len([r for r in reports if r.created_at >= start_of_week])
    
    start_of_month = now.replace(day=1)
    this_month = len([r for r in reports if r.created_at >= start_of_month])
    
    # ✅ XÓA downloads count
    return jsonify({
        'total': total,
        'this_week': this_week,
        'this_month': this_month
    })