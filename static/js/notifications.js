class NotificationManager {
    constructor() {
        this.notifications = [];
        this.unreadCount = 0;
        this.updateInterval = null;
        this.isDropdownOpen = false;
    }

    // Initialize notification system
    init() {
        this.setupEventListeners();
        this.startPeriodicUpdates();
        this.loadNotifications();
    }

    setupEventListeners() {
        // Dropdown toggle
        $('#notification-menu .dropdown-toggle').on('click', (e) => {
            e.preventDefault();
            this.toggleDropdown();
        });

        // Close dropdown when clicking outside
        $(document).on('click', (e) => {
            if (!$(e.target).closest('#notification-menu').length && this.isDropdownOpen) {
                this.closeDropdown();
            }
        });

        // Mark notification as read when clicked
        $(document).on('click', '.notification-item', (e) => {
            const notificationId = $(e.currentTarget).data('id');
            if (notificationId) {
                this.markAsRead(notificationId);
            }
        });
    }

    // Start periodic updates every 30 seconds
    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => {
            this.loadNotifications(true); // Silent update
        }, 30000);
    }

    // Load notifications from server
    async loadNotifications(silent = false) {
        try {
            const currentUser = WorkManagement.currentUser();
            if (!currentUser) return;

            const response = await WorkManagement.apiCall(`/notifications/list?user_id=${currentUser.id}&limit=10`);
            
            this.notifications = response.notifications || [];
            this.unreadCount = response.unread_count || 0;
            
            this.updateUI();
            
            if (!silent) {
                this.showNewNotificationsToast();
            }
            
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    // Update UI elements
    updateUI() {
        this.updateNotificationCount();
        this.updateNotificationList();
    }

    // Update notification count badge
    updateNotificationCount() {
        const badge = $('#notification-count');
        
        if (this.unreadCount > 0) {
            badge.text(this.unreadCount > 99 ? '99+' : this.unreadCount).show();
        } else {
            badge.hide();
        }
    }

    // Update notification list in dropdown
    updateNotificationList() {
        const container = $('#notification-list');
        
        if (this.notifications.length === 0) {
            container.html(`
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-bell-slash fa-2x mb-2"></i>
                    <p>No notifications</p>
                </div>
            `);
            return;
        }

        const notificationsHtml = this.notifications.map(notification => 
            this.createNotificationHTML(notification)
        ).join('');

        container.html(notificationsHtml);
    }

    // Create HTML for single notification
    createNotificationHTML(notification) {
        const timeAgo = this.getTimeAgo(notification.created_at);
        const isUnread = !notification.is_read;
        const typeIcon = this.getNotificationIcon(notification.type);
        const typeColor = this.getNotificationColor(notification.type);

        return `
            <div class="notification-item dropdown-item-text p-3 ${isUnread ? 'bg-light border-start border-primary border-3' : ''}" 
                 data-id="${notification.id}" 
                 style="cursor: pointer; border-bottom: 1px solid #f0f0f0;">
                <div class="d-flex">
                    <div class="me-3">
                        <div class="bg-${typeColor} text-white rounded-circle d-flex align-items-center justify-content-center" 
                             style="width: 40px; height: 40px;">
                            <i class="fas ${typeIcon}"></i>
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-start">
                            <h6 class="mb-1 ${isUnread ? 'fw-bold' : ''}">${notification.title}</h6>
                            ${isUnread ? '<span class="badge bg-primary rounded-pill">New</span>' : ''}
                        </div>
                        <p class="mb-1 text-muted small">${notification.message}</p>
                        <small class="text-muted">${timeAgo}</small>
                        ${notification.task_id ? `<a href="/tasks?highlight=${notification.task_id}" class="btn btn-sm btn-outline-primary mt-1">View Task</a>` : ''}
                        ${notification.group_id ? `<a href="/groups?highlight=${notification.group_id}" class="btn btn-sm btn-outline-info mt-1">View Group</a>` : ''}
                        ${notification.report_id ? `<a href="/reports?highlight=${notification.report_id}" class="btn btn-sm btn-outline-success mt-1">View Report</a>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    // Get notification icon based on type
    getNotificationIcon(type) {
        const icons = {
            'task_assigned': 'fa-tasks',
            'task_updated': 'fa-edit',
            'task_completed': 'fa-check-circle',
            'task_overdue': 'fa-exclamation-triangle',
            'task_deadline_soon': 'fa-clock',
            'group_joined': 'fa-users',
            'group_removed': 'fa-user-times',
            'group_join_request': 'fa-paper-plane',
            'group_join_approved': 'fa-check-circle',
            'group_join_rejected': 'fa-times-circle',
            'role_changed': 'fa-user-tag',
            'report_generated': 'fa-chart-bar',
            'system_announcement': 'fa-bullhorn'
        };
        return icons[type] || 'fa-bell';
    }

    // Get notification color based on type
    getNotificationColor(type) {
        const colors = {
            'task_assigned': 'primary',
            'task_updated': 'info',
            'task_completed': 'success',
            'task_overdue': 'danger',
            'task_deadline_soon': 'warning',
            'group_joined': 'success',
            'group_removed': 'secondary',
            'group_join_request': 'warning',
            'group_join_approved': 'success',
            'group_join_rejected': 'danger',
            'role_changed': 'warning',
            'report_generated': 'success',
            'system_announcement': 'primary'
        };
        return colors[type] || 'secondary';
    }

    // Calculate time ago
    getTimeAgo(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
        
        return date.toLocaleDateString();
    }

    // Toggle dropdown
    toggleDropdown() {
        const dropdown = $('#notification-menu .dropdown-menu');
        
        if (this.isDropdownOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        const dropdown = $('#notification-menu .dropdown-menu');
        dropdown.addClass('show');
        this.isDropdownOpen = true;
        
        // Load latest notifications when opening
        this.loadNotifications();
    }

    closeDropdown() {
        const dropdown = $('#notification-menu .dropdown-menu');
        dropdown.removeClass('show');
        this.isDropdownOpen = false;
    }

    // Mark notification as read
    async markAsRead(notificationId) {
        try {
            await WorkManagement.apiCall(`/notifications/mark-read/${notificationId}`, {
                method: 'PUT'
            });

            // Update local state
            const notification = this.notifications.find(n => n.id === notificationId);
            if (notification && !notification.is_read) {
                notification.is_read = true;
                this.unreadCount = Math.max(0, this.unreadCount - 1);
                this.updateUI();
            }

        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    // Mark all notifications as read
    async markAllAsRead() {
        try {
            const currentUser = WorkManagement.currentUser();
            await WorkManagement.apiCall('/notifications/mark-all-read', {
                method: 'PUT',
                data: JSON.stringify({ user_id: currentUser.id })
            });

            // Update local state
            this.notifications.forEach(n => n.is_read = true);
            this.unreadCount = 0;
            this.updateUI();

            WorkManagement.showAlert('success', 'All notifications marked as read');

        } catch (error) {
            console.error('Error marking all notifications as read:', error);
            WorkManagement.showAlert('danger', 'Error marking notifications as read');
        }
    }

    // Clear all notifications
    async clearAllNotifications() {
        if (!confirm('Are you sure you want to clear all notifications? This cannot be undone.')) {
            return;
        }

        try {
            const currentUser = WorkManagement.currentUser();
            await WorkManagement.apiCall('/notifications/clear-all', {
                method: 'DELETE',
                data: JSON.stringify({ user_id: currentUser.id })
            });

            // Update local state
            this.notifications = [];
            this.unreadCount = 0;
            this.updateUI();

            WorkManagement.showAlert('success', 'All notifications cleared');

        } catch (error) {
            console.error('Error clearing notifications:', error);
            WorkManagement.showAlert('danger', 'Error clearing notifications');
        }
    }

    // Show toast for new notifications
    showNewNotificationsToast() {
        // Only show toast if there are new unread notifications
        // Implementation depends on your toast system
    }

    // Create notification (called from other parts of the app)
    static async createNotification(userId, title, message, type, options = {}) {
        try {
            const notification = await WorkManagement.apiCall('/notifications/create', {
                method: 'POST',
                data: JSON.stringify({
                    user_id: userId,
                    title: title,
                    message: message,
                    type: type,
                    ...options
                })
            });

            // Trigger update for current user if it's their notification
            const currentUser = WorkManagement.currentUser();
            if (currentUser && currentUser.id === userId) {
                window.notificationManager?.loadNotifications();
            }

            return notification;

        } catch (error) {
            console.error('Error creating notification:', error);
        }
    }

    // Cleanup
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Global notification functions
window.markAllAsRead = function() {
    window.notificationManager?.markAllAsRead();
};

window.clearAllNotifications = function() {
    window.notificationManager?.clearAllNotifications();
};

// Initialize when document is ready
$(document).ready(function() {
    const currentUser = WorkManagement.currentUser();
    if (currentUser) {
        window.notificationManager = new NotificationManager();
        window.notificationManager.init();
    }
});