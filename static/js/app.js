// Main JavaScript for Work Management System

// Global variables
let currentUser = null;
const API_BASE = 'http://localhost:5000/api';

// Initialize app when document is ready
$(document).ready(function() {
    // Check if user is logged in
    checkAuthStatus();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize modals
    initializeModals();
    
    // Set up AJAX error handling
    setupAjaxErrorHandling();
});

// Authentication functions
function checkAuthStatus() {
    const userData = localStorage.getItem('currentUser');
    if (userData) {
        currentUser = JSON.parse(userData);
        updateNavigation();
        // If on login page and already logged in, redirect to dashboard
        if (window.location.pathname === '/login' || window.location.pathname === '/') {
            window.location.href = '/dashboard';
        }
    } else {
        // If not logged in and not on public pages, redirect to login
        const publicPages = ['/login', '/register', '/'];
        if (!publicPages.includes(window.location.pathname)) {
            window.location.href = '/login';
        }
    }
}

function updateNavigation() {
    if (currentUser) {
        // Show user menu and notification menu, hide login button
        $('#user-menu').show();
        $('#notification-menu').show();
        $('#login-btn').hide();
        
        $('#user-name').text(currentUser.name);
        $('#user-full-name').text(currentUser.name);
        $('#user-role').text(currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1));
        
        
        // Show/hide navigation items based on role
        if (currentUser.role === 'admin') {
            $('.admin-only').show();
            $('.admin-leader-only').show();
        } else if (currentUser.role === 'leader') {
            $('.admin-leader-only').show();
        }
        
        // ✅ Groups hiển thị cho tất cả users (không chỉ admin-leader)
        // Groups nav item sẽ luôn hiển thị
        
    } else {
        // Show login button, hide user menu and notifications
        $('#user-menu').hide();
        $('#notification-menu').hide();
        $('#login-btn').show();
        $('.admin-only').hide();
        $('.admin-leader-only').hide();
    }
}

function login(email, password) {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: `${API_BASE}/auth/login`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ email, password }),
            success: function(response) {
                currentUser = response.user;
                localStorage.setItem('currentUser', JSON.stringify(currentUser));
                updateNavigation();
                showAlert('success', 'Login successful!');
                resolve(response);
            },
            error: function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.message : 'Login failed';
                showAlert('danger', error);
                reject(error);
            }
        });
    });
}

function register(userData) {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: `${API_BASE}/auth/register`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(userData),
            success: function(response) {
                showAlert('success', 'Registration successful! Please login.');
                resolve(response);
            },
            error: function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.message : 'Registration failed';
                showAlert('danger', error);
                reject(error);
            }
        });
    });
}

function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    showAlert('info', 'Logged out successfully');
    window.location.href = '/login';
}

// API helper functions
function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return $.ajax({
        url: `${API_BASE}${endpoint}`,
        ...finalOptions
    }).then(response => {
        console.log(`API ${endpoint} response:`, response); // Debug log
        return response;
    });
}

// UI helper functions
function showAlert(type, message, duration = 5000) {
    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas ${getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('#alert-container').append(alertHTML);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        $(`#${alertId}`).alert('close');
    }, duration);
}

function getAlertIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'danger': 'fa-exclamation-triangle',
        'warning': 'fa-exclamation-circle',
        'info': 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

function showLoading() {
    $('.spinner-overlay').css('display', 'flex');
}

function hideLoading() {
    $('.spinner-overlay').hide();
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN') + ' ' + date.toLocaleTimeString('vi-VN', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function formatStatus(status) {
    const statusMap = {
        'todo': '<span class="badge status-badge status-todo">To Do</span>',
        'doing': '<span class="badge status-badge status-doing">In Progress</span>',
        'done': '<span class="badge status-badge status-done">Completed</span>'
    };
    return statusMap[status] || status;
}

function formatPriority(priority) {
    const priorityMap = {
        'high': '<i class="fas fa-exclamation-triangle priority-high"></i> High',
        'medium': '<i class="fas fa-minus-circle priority-medium"></i> Medium',
        'low': '<i class="fas fa-arrow-down priority-low"></i> Low'
    };
    return priorityMap[priority] || priority;
}

// Modal functions
function initializeModals() {
    // Initialize any global modal behaviors
}

function showModal(modalId) {
    $(`#${modalId}`).modal('show');
}

function hideModal(modalId) {
    $(`#${modalId}`).modal('hide');
}

// Form helper functions
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (form.checkValidity()) {
        return true;
    } else {
        form.classList.add('was-validated');
        return false;
    }
}

function resetForm(formId) {
    document.getElementById(formId).reset();
    document.getElementById(formId).classList.remove('was-validated');
}

function getFormData(formId) {
    const formData = new FormData(document.getElementById(formId));
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    return data;
}

// File upload functions
function initializeFileUpload() {
    // Set up drag and drop for file uploads
    $('.file-drop-area').on('dragover dragenter', function(e) {
        e.preventDefault();
        $(this).addClass('dragover');
    });
    
    $('.file-drop-area').on('dragleave dragend drop', function(e) {
        e.preventDefault();
        $(this).removeClass('dragover');
    });
    
    $('.file-drop-area').on('drop', function(e) {
        const files = e.originalEvent.dataTransfer.files;
        handleFileUpload(files[0]);
    });
}

function handleFileUpload(file) {
    if (!file) return;
    
    const allowedTypes = ['image/', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    if (file.size > maxSize) {
        showAlert('danger', 'File size must be less than 10MB');
        return;
    }
    
    const isAllowed = allowedTypes.some(type => file.type.startsWith(type));
    if (!isAllowed) {
        showAlert('danger', 'File type not allowed');
        return;
    }
    
    // Proceed with upload
    uploadFile(file);
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_id', getCurrentTaskId());
    formData.append('uploaded_by', currentUser.id);
    
    showLoading();
    
    $.ajax({
        url: `${API_BASE}/files/upload`,
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            hideLoading();
            showAlert('success', 'File uploaded successfully');
            // Refresh file list if on task detail page
            if (typeof refreshFileList === 'function') {
                refreshFileList();
            }
        },
        error: function(xhr) {
            hideLoading();
            const error = xhr.responseJSON ? xhr.responseJSON.message : 'Upload failed';
            showAlert('danger', error);
        }
    });
}

// Utility functions
function getCurrentTaskId() {
    // Extract task ID from URL or form
    const urlParts = window.location.pathname.split('/');
    const taskIndex = urlParts.indexOf('tasks');
    if (taskIndex !== -1 && urlParts[taskIndex + 1]) {
        return urlParts[taskIndex + 1];
    }
    return null;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// AJAX error handling
function setupAjaxErrorHandling() {
    $(document).ajaxError(function(event, xhr, settings) {
        if (xhr.status === 401) {
            // Unauthorized - redirect to login
            logout();
        } else if (xhr.status === 403) {
            showAlert('danger', 'Access denied');
        } else if (xhr.status >= 500) {
            showAlert('danger', 'Server error. Please try again later.');
        }
    });
}

// Export functions for use in other files
window.WorkManagement = {
    apiCall,
    showAlert,
    showLoading,
    hideLoading,
    formatDate,
    formatStatus,
    formatPriority,
    showModal,
    hideModal,
    validateForm,
    resetForm,
    getFormData,
    currentUser: () => currentUser
};

function timeAgo(dateString) {
    const now = new Date();
    const past = new Date(dateString);
    const diffInSeconds = Math.floor((now - past) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
    if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)} months ago`;
    return `${Math.floor(diffInSeconds / 31536000)} years ago`;
}

// Cập nhật export object
window.WorkManagement = {
    apiCall,
    showAlert,
    showLoading,
    hideLoading,
    formatDate,
    formatStatus,
    formatPriority,
    showModal,
    hideModal,
    validateForm,
    resetForm,
    getFormData,
    timeAgo, // Thêm dòng này
    currentUser: () => currentUser
};