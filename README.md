# Work Management System

A comprehensive web-based work management system built with Flask and Bootstrap, designed to help organizations track, manage, and report weekly work activities across different user roles.

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#️-system-architecture)
- [Technologies Used](#-technologies-used)
- [Installation Guide](#-installation-guide)
- [User Manual](#-user-manual)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

## 🚀 Features

### 👥 Multi-Role Support
- **Employees**: Basic task management and personal reporting
- **Leaders**: Team management and comprehensive reporting
- **Admins**: System-wide user and role management

### 📊 Core Functionality
- Task creation, assignment, and tracking
- File upload and management for tasks
- Weekly report generation (PDF/Excel)
- Group/team management
- Real-time notifications
- Advanced search and filtering
- User profile management

### 📈 Reporting & Analytics
- Individual weekly reports
- Team summary reports
- Task completion statistics
- File management statistics
- Export capabilities (PDF/Excel)

## 🏗️ System Architecture

```
Frontend (Web Client)
├── HTML/CSS/JavaScript
├── Bootstrap 5
└── jQuery

Backend (REST API)
├── Flask Application
├── SQLAlchemy ORM
└── Blueprint Architecture

Database
└── MySQL

File Storage
└── Local filesystem
```

## 💻 Technologies Used

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **SQLAlchemy** - ORM
- **MySQL** - Database
- **ReportLab** - PDF generation
- **Pandas** - Excel report generation
- **Flask-CORS** - Cross-origin requests

### Frontend
- **HTML5/CSS3**
- **JavaScript (ES6+)**
- **Bootstrap 5** - UI framework
- **jQuery** - DOM manipulation
- **Font Awesome** - Icons

### Additional Tools
- **Werkzeug** - Password hashing and file handling
- **APScheduler** - Task scheduling
- **Docker** - Containerization support

## 📦 Installation Guide

### Prerequisites

- Python 3.8 or higher
- MySQL 5.7 or higher
- Node.js (optional, for development tools)

### Method 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Duong-Nguyen-Ngoc-Hai/Work_Management_System.git
   cd Work_Management_System
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   
   Create a MySQL database:
   ```sql
   CREATE DATABASE work_management;
   ```

   Create `.env` file in project root:
   ```env
   DATABASE_URL=mysql://username:password@localhost/work_management
   SECRET_KEY=your-secret-key-here
   UPLOAD_FOLDER=uploads
   ```

5. **Initialize database**
   ```bash
   python setup_db.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5000`

### Method 2: Docker Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/Duong-Nguyen-Ngoc-Hai/Work_Management_System.git
   cd Work_Management_System
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   The application will be available at `http://localhost:5000`

## 📖 User Manual

### Initial Setup

1. **Default Admin Account**
   - Email: `admin@company.com`
   - Password: `admin123`
   - Change these credentials after first login

2. **First Time Setup**
   - Login with admin account
   - Create groups for your organization
   - Create user accounts for employees and leaders
   - Assign users to appropriate groups

### 🔐 Authentication & Registration

#### For New Users (Employees)
1. Navigate to `/register`
2. Fill in required information:
   - Full Name
   - Email Address
   - Password
   - Role (Employee/Leader/Admin)
3. System will auto-generate employee code
4. After registration, join a group through the Groups page

#### Login Process
1. Navigate to `/login`
2. Enter email and password
3. System redirects based on user role

### 👤 Employee Functions

#### Task Management
1. **View Tasks**
   - Go to "Tasks" in navigation
   - View assigned tasks in table or card format
   - Use search and filters to find specific tasks

2. **Create New Task**
   ```javascript
   // Click "Add Task" button
   // Fill in task details:
   - Title (required)
   - Description
   - Priority (Low/Medium/High)
   - Deadline
   - Status (Todo/Doing/Done)
   ```

3. **Update Task Status**
   - Click on task to view details
   - Change status using dropdown
   - Add progress notes if needed

4. **File Management**
   - Upload files related to tasks
   - Supported formats: PDF, Images, Documents, Archives
   - Download or delete files as needed

#### Personal Reporting
1. **Generate Weekly Report**
   - Go to "Reports" section
   - Select week range
   - Choose format (PDF/Excel)
   - Download generated report

2. **View Report History**
   - Access previously generated reports
   - Re-download or delete old reports

#### Profile Management
1. **Update Personal Information**
   - Go to "Profile" page
   - Edit name, email, and other details
   - Change password when needed

### 👨‍💼 Leader Functions

#### Team Management
1. **View Group Members**
   - Access "Groups" section
   - View detailed member information
   - Monitor member activities and statistics

2. **Assign Tasks to Team Members**
   ```javascript
   // In Groups page:
   // 1. Select group member
   // 2. Click "Assign Task"
   // 3. Fill task details
   // 4. Set assignee and deadline
   ```

3. **Monitor Team Progress**
   - View team task statistics
   - Filter tasks by member or date range
   - Track completion rates

#### Advanced Reporting
1. **Team Summary Reports**
   - Generate comprehensive team reports
   - Include individual member performance
   - Export in PDF or Excel format

2. **Custom Report Parameters**
   - Select specific team members
   - Choose date ranges
   - Filter by task status or priority

### 🔧 Admin Functions

#### User Management
1. **View All Users**
   - Navigate to "Users" section
   - Search and filter by role, group, or employee code
   - View detailed user statistics

2. **Create New Users**
   ```javascript
   // Click "Add User" button
   // Fill user details:
   - Name, Email, Password
   - Role assignment
   - Group assignment
   - Employee code (auto-generated)
   ```

3. **User Role Management**
   - Promote employees to leaders
   - Demote leaders to employees
   - Deactivate or delete users

4. **Advanced User Operations**
   - Bulk user operations
   - User statistics and analytics
   - System-wide user reports

#### Group Management
1. **Create and Manage Groups**
   - Create new work groups
   - Assign leaders to groups
   - Manage group membership

2. **Group Analytics**
   - View group performance metrics
   - Monitor group task completion
   - Generate group-specific reports

### 📊 Reporting System

#### Report Types
1. **Individual Weekly Reports**
   - Personal task summary
   - Completion statistics
   - File attachments overview

2. **Team Summary Reports**
   - Group performance overview
   - Member-wise breakdowns
   - Comparative analytics

3. **System-wide Reports** (Admin only)
   - Organization-wide statistics
   - User activity reports
   - System usage metrics

#### Report Generation Process
1. Select report type and parameters
2. Choose date range (weekly basis)
3. Select output format (PDF/Excel)
4. Generate and download report
5. Reports are saved for future access

### 🔔 Notifications System

#### Notification Types
- Task assignments
- Task updates and completions
- Report generation alerts
- System announcements

#### Managing Notifications
1. **View Notifications**
   - Click notification bell icon
   - View recent notifications
   - Mark as read/unread

2. **Notification Settings**
   - Configure notification preferences
   - Enable/disable specific notification types

### 🔍 Search and Filtering

#### Task Filtering
- By status (Todo/Doing/Done)
- By priority level
- By date range
- By assignee (for leaders/admins)

#### User Filtering
- By role (Employee/Leader/Admin)
- By group membership
- By activity status
- By employee code

### 📁 File Management

#### File Upload
1. Navigate to specific task
2. Click "Upload File" button
3. Select files (multiple allowed)
4. Files are automatically associated with task

#### File Organization
- Files organized by task
- Version control for file updates
- File type restrictions for security
- File size limitations

#### File Access Control
- Task assignees can upload/download
- Task creators have full access
- Leaders can access team member files
- Admins have system-wide access

### 🎨 Interface Navigation

#### Main Navigation
- **Dashboard**: Overview and quick actions
- **Tasks**: Task management interface
- **Groups**: Team and group management
- **Reports**: Reporting and analytics
- **Users**: User management (Admin/Leader)
- **Profile**: Personal settings
- **Notifications**: System notifications

#### Responsive Design
- Mobile-friendly interface
- Tablet optimization
- Desktop full-feature access
- Touch-friendly controls

### ⚠️ Troubleshooting

#### Common Issues
1. **Login Problems**
   - Verify credentials
   - Check account status
   - Contact admin for password reset

2. **File Upload Issues**
   - Check file size limits
   - Verify file type permissions
   - Ensure stable internet connection

3. **Report Generation Errors**
   - Verify date range selection
   - Check user permissions
   - Ensure sufficient data exists

4. **Performance Issues**
   - Clear browser cache
   - Check network connection
   - Contact system administrator

#### Support Contacts
- System Administrator: admin@company.com
- Technical Support: support@company.com
- User Manual Updates: Available in system help section

### 🔒 Security Best Practices

#### For Users
- Use strong passwords
- Log out when finished
- Don't share login credentials
- Report suspicious activity

#### For Administrators
- Regular password policy enforcement
- Monitor user activity logs
- Keep system updated
- Regular backup procedures
- Access control reviews

### 📈 System Monitoring

#### Performance Metrics
- User activity tracking
- System resource usage
- Report generation statistics
- File storage utilization

#### Maintenance Tasks
- Database optimization
- File cleanup procedures
- User account reviews
- System backup verification

## 🔧 API Documentation

The system provides RESTful APIs for all major functions:

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/change-password` - Password change

### Task Management
- `GET /api/tasks/all` - Get all tasks
- `POST /api/tasks/create` - Create new task
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task

### User Management
- `GET /api/users/all` - Get all users
- `POST /api/users/create` - Create user (Admin only)
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user (Admin only)

### Group Management
- `GET /api/groups/all` - Get all groups
- `POST /api/groups/create` - Create group
- `POST /api/groups/join` - Join group

### Report Generation
- `POST /api/reports/generate-pdf` - Generate PDF report
- `POST /api/reports/summary` - Generate Excel summary
- `GET /api/reports/list` - Get report history

## 📁 Project Structure

```
work_management/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── database.py           # Database connection
├── setup_db.py          # Database initialization
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables
├── models/              # Database models
│   ├── __init__.py
│   ├── user.py
│   ├── task.py
│   ├── group.py
│   ├── file.py
│   ├── report.py
│   ├── join_request.py
│   └── notification.py
├── routes/              # API route handlers
│   ├── __init__.py
│   ├── auth_routes.py
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── group_routes.py
│   ├── file_routes.py
│   ├── report_routes.py
│   └── notification_routes.py
├── templates/           # HTML templates
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   └── employee.html
│   ├── tasks/
│   │   ├── create.html
│   │   ├── detail.html
│   │   └── list.html
│   ├── users/
│   │   ├── list.html
│   │   └── profile.html
│   ├── groups/
│   │   ├── detail.html
│   │   └── list.html
│   ├── reports/
│   │   ├── generate.html
│   │   └── list.html
│   └── notification/
│       └── list.html
├── static/              # Static assets
│   ├── css/
│   │   ├── custom.css
│   │   ├── groups.css
│   │   └── profile.css
│   └── js/
│       ├── app.js
│       ├── groups.js
│       ├── notifications.js
│       └── profile.js
├── uploads/             # File storage
│   └── reports/         # Generated reports
└── utils/               # Utility functions
    ├── __init__.py
    └── notification_scheduler.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For technical support or questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the documentation for common solutions

---

**Version**: 1.0.0  
**Last Updated**: August 2025  
**Developed by**: Work Management Team  
**Repository**: [Work_Management_System](https://github.com/Duong-Nguyen-Ngoc-Hai/Work_Management_System)
