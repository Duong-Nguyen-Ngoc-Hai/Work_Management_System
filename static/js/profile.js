$(document).ready(function() {
    // Lấy thông tin user hiện tại từ WorkManagement global object
    const currentUser = WorkManagement.currentUser();
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }

    // Load profile data
    loadProfileData();
    loadWorkStatistics();
    loadRecentActivity();

    // Event listeners
    $('#btn-edit-profile').click(openEditProfileModal);
    $('#edit-profile-form').submit(handleProfileUpdate);
    $('#change-password-form').submit(handlePasswordChange);
});

// Load profile information
function loadProfileData() {
    const currentUser = WorkManagement.currentUser();
    WorkManagement.showLoading();
    
    WorkManagement.apiCall(`/users/${currentUser.id}`)
        .then(user => {
            displayProfileInfo(user);
            WorkManagement.hideLoading();
        })
        .catch(error => {
            console.error('Error loading profile:', error);
            WorkManagement.hideLoading();
            WorkManagement.showAlert('danger', 'Failed to load profile information');
        });
}

// Display profile information
function displayProfileInfo(user) {
    const avatar = user.name.charAt(0).toUpperCase();
    const joinDate = WorkManagement.formatDate(user.created_at);
    const groupName = user.group ? user.group.name : 'No group assigned';
    
    const profileHtml = `
        <div class="row">
            <div class="col-md-4 text-center">
                <div class="profile-avatar">
                    ${avatar}
                </div>
                <h4 class="mb-2">${user.name}</h4>
                <div class="mb-3">
                    <span class="role-badge ${user.role}">
                        ${user.role}
                    </span>
                </div>
                <div class="mb-2">
                    <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
            </div>
            <div class="col-md-8">
                <table class="table profile-info-table">
                    <tbody>
                        <tr>
                            <td><i class="fas fa-id-card me-2 text-primary"></i>Employee Code</td>
                            <td>${user.employee_code || 'Not assigned'}</td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-envelope me-2 text-primary"></i>Email</td>
                            <td>${user.email}</td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-users me-2 text-primary"></i>Group</td>
                            <td>${groupName}</td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-calendar-alt me-2 text-primary"></i>Join Date</td>
                            <td>${joinDate}</td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-user-tag me-2 text-primary"></i>Account Status</td>
                            <td>
                                <span class="badge ${user.is_active ? 'bg-success' : 'bg-danger'}">
                                    ${user.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    $('#profile-info').html(profileHtml);
}

// Load work statistics
function loadWorkStatistics() {
    const currentUser = WorkManagement.currentUser();
    Promise.all([
        WorkManagement.apiCall(`/tasks/user/${currentUser.id}`),
        WorkManagement.apiCall(`/reports/list?user_id=${currentUser.id}`),
        WorkManagement.apiCall(`/files/user/${currentUser.id}`)
    ])
    .then(([tasks, reports, files]) => {
        displayWorkStatistics(tasks, reports, files);
    })
    .catch(error => {
        console.error('Error loading work statistics:', error);
        $('#work-stats').html(`
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Unable to load work statistics
            </div>
        `);
    });
}

// Display work statistics
function displayWorkStatistics(tasks, reports, files) {
    const tasksData = Array.isArray(tasks) ? tasks : [];
    const reportsData = Array.isArray(reports) ? reports : [];
    const filesData = Array.isArray(files) ? files : [];
    
    const totalTasks = tasksData.length;
    const completedTasks = tasksData.filter(task => task.status === 'done').length;
    const totalReports = reportsData.length;
    const totalFiles = filesData.length;
    
    const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    
    const statsHtml = `
        <div class="row">
            <div class="col-lg-3 col-md-6">
                <div class="profile-stat-card tasks">
                    <div class="stat-number">${totalTasks}</div>
                    <div class="stat-label">Total Tasks</div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="profile-stat-card completed">
                    <div class="stat-number">${completedTasks}</div>
                    <div class="stat-label">Completed Tasks</div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="profile-stat-card reports">
                    <div class="stat-number">${totalReports}</div>
                    <div class="stat-label">Reports Generated</div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="profile-stat-card files">
                    <div class="stat-number">${totalFiles}</div>
                    <div class="stat-label">Files Uploaded</div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Task Completion Rate</h6>
                        <div class="progress mb-2" style="height: 10px;">
                            <div class="progress-bar bg-success" 
                                 style="width: ${completionRate}%" 
                                 role="progressbar" 
                                 aria-valuenow="${completionRate}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                            </div>
                        </div>
                        <small class="text-muted">${completionRate}% completion rate</small>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('#work-stats').html(statsHtml);
}

// Load recent activity
function loadRecentActivity() {
    const currentUser = WorkManagement.currentUser();
    // Get recent tasks, reports, and files
    Promise.all([
        WorkManagement.apiCall(`/tasks/user/${currentUser.id}?limit=5`),
        WorkManagement.apiCall(`/reports/list?user_id=${currentUser.id}`),
        WorkManagement.apiCall(`/files/user/${currentUser.id}?limit=3`)
    ])
    .then(([tasks, reports, files]) => {
        displayRecentActivity(tasks, reports, files);
    })
    .catch(error => {
        console.error('Error loading recent activity:', error);
        $('#recent-activity').html(`
            <div class="text-center text-muted">
                <i class="fas fa-exclamation-triangle"></i>
                <p class="mt-2">Unable to load recent activity</p>
            </div>
        `);
    });
}

// Display recent activity
function displayRecentActivity(tasks, reports, files) {
    const tasksData = Array.isArray(tasks) ? tasks.slice(0, 3) : [];
    const reportsData = Array.isArray(reports) ? reports.slice(0, 2) : [];
    const filesData = Array.isArray(files) ? files.slice(0, 2) : [];
    
    let activityHtml = '';
    
    // Recent tasks
    tasksData.forEach(task => {
        const timeAgo = WorkManagement.timeAgo(task.updated_at || task.created_at);
        activityHtml += `
            <div class="activity-item">
                <div class="activity-icon task">
                    <i class="fas fa-tasks"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">Task: ${task.title}</div>
                    <div class="activity-time">
                        Status: <span class="badge bg-${getStatusColor(task.status)}">${task.status}</span>
                        • ${timeAgo}
                    </div>
                </div>
            </div>
        `;
    });
    
    // Recent reports
    reportsData.forEach(report => {
        const timeAgo = WorkManagement.timeAgo(report.created_at);
        activityHtml += `
            <div class="activity-item">
                <div class="activity-icon report">
                    <i class="fas fa-file-alt"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">Generated ${report.report_type} report</div>
                    <div class="activity-time">${timeAgo}</div>
                </div>
            </div>
        `;
    });
    
    // Recent files
    filesData.forEach(file => {
        const timeAgo = WorkManagement.timeAgo(file.upload_date);
        activityHtml += `
            <div class="activity-item">
                <div class="activity-icon file">
                    <i class="fas fa-file"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">Uploaded ${file.filename}</div>
                    <div class="activity-time">${timeAgo}</div>
                </div>
            </div>
        `;
    });
    
    if (!activityHtml) {
        activityHtml = `
            <div class="text-center text-muted">
                <i class="fas fa-inbox"></i>
                <p class="mt-2">No recent activity</p>
            </div>
        `;
    }
    
    $('#recent-activity').html(activityHtml);
}

// Open edit profile modal
function openEditProfileModal() {
    const currentUser = WorkManagement.currentUser();
    WorkManagement.apiCall(`/users/${currentUser.id}`)
        .then(user => {
            $('#edit-name').val(user.name);
            $('#edit-email').val(user.email);
            $('#edit-employee-code').val(user.employee_code || '');
            $('#edit-role').val(user.role);
            $('#edit-group').val(user.group ? user.group.name : 'No group');
            
            $('#editProfileModal').modal('show');
        })
        .catch(error => {
            console.error('Error loading user data:', error);
            WorkManagement.showAlert('danger', 'Failed to load user data');
        });
}

// Handle profile update
function handleProfileUpdate(e) {
    e.preventDefault();
    const currentUser = WorkManagement.currentUser();
    
    const formData = {
        name: $('#edit-name').val(),
        email: $('#edit-email').val(),
        admin_id: currentUser.id // User updating their own profile
    };
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall(`/users/${currentUser.id}`, {
        method: 'PUT',
        data: JSON.stringify(formData)
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', 'Profile updated successfully');
        $('#editProfileModal').modal('hide');
        
        // Update current user data in localStorage
        const updatedUser = WorkManagement.currentUser();
        updatedUser.name = formData.name;
        updatedUser.email = formData.email;
        localStorage.setItem('currentUser', JSON.stringify(updatedUser));
        
        // Update navigation
        $('#user-name').text(updatedUser.name);
        
        // Reload profile data
        loadProfileData();
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to update profile';
        WorkManagement.showAlert('danger', message);
    });
}

// Change password
function changePassword() {
    $('#changePasswordModal').modal('show');
}

// Handle password change
function handlePasswordChange(e) {
    e.preventDefault();
    const currentUser = WorkManagement.currentUser();
    
    const formData = {
        user_id: currentUser.id,
        current_password: $('input[name="current_password"]').val(),
        new_password: $('input[name="new_password"]').val(),
        confirm_password: $('input[name="confirm_password"]').val()
    };
    
    // Validate passwords match
    if (formData.new_password !== formData.confirm_password) {
        WorkManagement.showAlert('danger', 'New passwords do not match');
        return;
    }
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall('/auth/change-password', {
        method: 'POST',
        data: JSON.stringify(formData)
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', 'Password changed successfully');
        $('#changePasswordModal').modal('hide');
        $('#change-password-form')[0].reset();
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to change password';
        WorkManagement.showAlert('danger', message);
    });
}

// Quick action functions
function generateWeeklyReport() {
    window.location.href = '/reports';
}

function viewMyTasks() {
    window.location.href = '/tasks';
}

// Helper functions
function getStatusColor(status) {
    switch(status) {
        case 'done': return 'success';
        case 'doing': return 'primary';
        case 'todo': return 'secondary';
        default: return 'secondary';
    }
}