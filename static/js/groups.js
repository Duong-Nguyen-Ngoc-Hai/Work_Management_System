// Groups Management JavaScript

let selectedGroupId = null;
let allGroups = [];
let availableLeaders = [];

$(document).ready(function() {
    const currentUser = WorkManagement.currentUser();
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }

    initializeGroupsPage();
    loadGroups();
    
    // ✅ Chỉ admin/leader mới cần load available leaders
    if (currentUser.role === 'admin' || currentUser.role === 'leader') {
        loadAvailableLeaders();
    }
    
    // ✅ Employee: Load join requests của mình
    if (currentUser.role === 'employee') {
        loadMyJoinRequests();
    }
    
    // ✅ Admin/Leader: Load pending join requests
    if (currentUser.role === 'admin' || currentUser.role === 'leader') {
        loadPendingJoinRequests();
    }
    
    // Event listeners
    $('#btn-create-group').click(function() {
        openGroupModal();
    });
    
    $('#btn-refresh').click(function() {
        loadGroups();
        
        // Refresh additional data based on role
        if (currentUser.role === 'employee') {
            loadMyJoinRequests();
        } else if (currentUser.role === 'admin' || currentUser.role === 'leader') {
            loadPendingJoinRequests();
        }
    });
    
    $('#search-name, #filter-leader, #sort-by').on('input change', function() {
        filterAndDisplayGroups();
    });
    
    $('#group-form').submit(function(e) {
        e.preventDefault();
        saveGroup();
    });
    
    $('#btn-confirm-join').click(function() {
        joinGroup(selectedGroupId);
    });
    
    $('#btn-edit-group').click(function() {
        editCurrentGroup();
    });
});

function initializeGroupsPage() {
    const currentUser = WorkManagement.currentUser();
    console.log('Initializing groups page for user role:', currentUser.role);
    
    // Show/hide elements based on user role
    if (currentUser.role === 'admin') {
        $('.admin-only').show();
        $('.admin-leader-only').show();
        console.log('Admin UI elements shown');
    } else if (currentUser.role === 'leader') {
        $('.admin-leader-only').show();
        console.log('Leader UI elements shown');
    }
}

function loadMyJoinRequests() {
    const currentUser = WorkManagement.currentUser();
    
    WorkManagement.apiCall(`/groups/my-join-requests?user_id=${currentUser.id}`)
        .then(requests => {
            displayMyJoinRequests(requests);
        })
        .catch(error => {
            console.error('Error loading join requests:', error);
        });
}

// ✅ THÊM: Display join requests của employee
function displayMyJoinRequests(requests) {
    if (requests.length === 0) return;
    
    const requestsHtml = requests.map(req => {
        let statusBadge = '';
        let statusClass = '';
        
        switch(req.status) {
            case 'pending':
                statusBadge = '<span class="badge bg-warning">Pending</span>';
                statusClass = 'border-warning';
                break;
            case 'approved':
                statusBadge = '<span class="badge bg-success">Approved</span>';
                statusClass = 'border-success';
                break;
            case 'rejected':
                statusBadge = '<span class="badge bg-danger">Rejected</span>';
                statusClass = 'border-danger';
                break;
        }
        
        return `
            <div class="card mb-2 ${statusClass}">
                <div class="card-body py-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${req.group.name}</strong>
                            ${req.admin_message ? `<br><small class="text-muted">${req.admin_message}</small>` : ''}
                        </div>
                        <div class="text-end">
                            ${statusBadge}
                            <br><small class="text-muted">${WorkManagement.formatDate(req.created_at)}</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    const myRequestsPanel = `
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-paper-plane me-2"></i>My Join Requests
                        </h6>
                    </div>
                    <div class="card-body">
                        ${requestsHtml}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('#groups-container').before(myRequestsPanel);
}

// ✅ THÊM: Load pending join requests cho admin/leader
function loadPendingJoinRequests() {
    const currentUser = WorkManagement.currentUser();
    
    WorkManagement.apiCall(`/groups/join-requests?user_id=${currentUser.id}&status=pending`)
        .then(requests => {
            if (requests.length > 0) {
                displayPendingJoinRequests(requests);
            }
        })
        .catch(error => {
            console.error('Error loading pending requests:', error);
        });
}

// ✅ THÊM: Display pending join requests
function displayPendingJoinRequests(requests) {
    const requestsHtml = requests.map(req => `
        <div class="card mb-2">
            <div class="card-body py-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${req.user.name}</strong> wants to join <strong>${req.group.name}</strong>
                        <br><small class="text-muted">${req.user.employee_code} • ${WorkManagement.formatDate(req.created_at)}</small>
                        ${req.message ? `<br><small class="text-info">"${req.message}"</small>` : ''}
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-success" onclick="approveJoinRequest(${req.id}, '${req.user.name}', '${req.group.name}')">
                            <i class="fas fa-check"></i> Approve
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="rejectJoinRequest(${req.id}, '${req.user.name}', '${req.group.name}')">
                            <i class="fas fa-times"></i> Reject
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    const pendingRequestsPanel = `
        <div class="row mb-4">
            <div class="col-12">
                <div class="card border-warning">
                    <div class="card-header bg-warning text-white">
                        <h6 class="mb-0">
                            <i class="fas fa-clock me-2";"></i>Pending Join Requests (${requests.length})
                        </h6>
                    </div>
                    <div class="card-body">
                        ${requestsHtml}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('#groups-container').before(pendingRequestsPanel);
}

// ✅ THÊM: Approve join request
function approveJoinRequest(requestId, userName, groupName) {
    const message = prompt(`Approve ${userName}'s request to join ${groupName}?\n\nOptional message:`);
    
    if (message === null) return; // User cancelled
    
    const currentUser = WorkManagement.currentUser();
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall(`/groups/join-requests/${requestId}/approve`, {
        method: 'POST',
        data: JSON.stringify({
            admin_id: currentUser.id,
            admin_message: message
        })
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', `${userName}'s request approved successfully`);
        
        // Refresh data
        loadGroups();
        loadPendingJoinRequests();
        location.reload();
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to approve request';
        WorkManagement.showAlert('danger', message);
    });
}

// ✅ THÊM: Reject join request
function rejectJoinRequest(requestId, userName, groupName) {
    const message = prompt(`Reject ${userName}'s request to join ${groupName}?\n\nReason (optional):`);
    
    if (message === null) return; // User cancelled
    
    const currentUser = WorkManagement.currentUser();
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall(`/groups/join-requests/${requestId}/reject`, {
        method: 'POST',
        data: JSON.stringify({
            admin_id: currentUser.id,
            admin_message: message
        })
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('info', `${userName}'s request rejected`);
        
        // Refresh data
        loadPendingJoinRequests();
        location.reload();
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to reject request';
        WorkManagement.showAlert('danger', message);
    });
}

function loadGroups() {
    console.log('Loading groups...');
    WorkManagement.showLoading();
    
    WorkManagement.apiCall('/groups/all')
        .then(response => {
            console.log('Groups loaded successfully:', response);
            allGroups = response;
            displayGroups(allGroups);
            WorkManagement.hideLoading();
        })
        .catch(error => {
            console.error('Error loading groups:', error);
            WorkManagement.showAlert('danger', 'Failed to load groups');
            WorkManagement.hideLoading();
        });
}

function loadAvailableLeaders() {
    WorkManagement.apiCall('/users/available-leaders')
        .then(response => {
            availableLeaders = response;
            updateLeaderDropdown();
        })
        .catch(error => {
            console.error('Error loading leaders:', error);
        });
}

function updateLeaderDropdown() {
    const leaderSelect = $('#group-leader');
    const filterSelect = $('#filter-leader');
    
    // Clear existing options (except default)
    leaderSelect.find('option:not(:first)').remove();
    filterSelect.find('option:gt(1)').remove();
    
    availableLeaders.forEach(leader => {
        const displayText = leader.can_be_leader ? 
            `${leader.name} (${leader.employee_code})` : 
            `${leader.name} (${leader.employee_code}) - Leading: ${leader.led_group.name}`;
        
        const option = `<option value="${leader.id}" ${!leader.can_be_leader ? 'disabled' : ''}>${displayText}</option>`;
        
        leaderSelect.append(option);
        
        // Filter dropdown chỉ hiển thị leaders đang active
        if (leader.can_be_leader || leader.is_leading) {
            filterSelect.append(`<option value="${leader.id}">${leader.name}</option>`);
        }
    });
}

function displayGroups(groups) {
    console.log('Displaying groups:', groups);
    const container = $('#groups-container');
    container.empty();
    
    if (!groups || groups.length === 0) {
        container.html(`
            <div class="col-12">
                <div class="text-center py-5">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">No groups found</h5>
                    <p class="text-muted">Create your first group to get started</p>
                </div>
            </div>
        `);
        return;
    }
    
    groups.forEach(group => {
        const card = createGroupCard(group);
        container.append(card);
    });
}

function createGroupCard(group) {
    const currentUser = WorkManagement.currentUser();
    const isAdmin = currentUser.role === 'admin';
    const isLeader = currentUser.role === 'leader';
    const isEmployee = currentUser.role === 'employee';
    
    // Check if user can join this group
    const canRequestJoin = isEmployee && !currentUser.group && group.leader_name !== 'No leader';
    
    // Check if user already has pending request for this group
    // This will be checked via existing requests loaded separately
    
    return `
        <div class="col-lg-4 col-md-6 mb-4">
            <div class="card group-card h-100 shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h5 class="card-title mb-0">${group.name}</h5>
                        <span class="badge bg-primary">${group.member_count} members</span>
                    </div>
                    
                    <p class="card-text text-muted">${group.description || 'No description'}</p>
                    
                    <div class="mb-3">
                        <div class="row text-center">
                            <div class="col-4">
                                <div class="fw-bold text-primary">${group.total_tasks}</div>
                                <small class="text-muted">Tasks</small>
                            </div>
                            <div class="col-4">
                                <div class="fw-bold text-success">${group.completed_tasks}</div>
                                <small class="text-muted">Done</small>
                            </div>
                            <div class="col-4">
                                <div class="fw-bold text-info">${group.completion_rate}</div>
                                <small class="text-muted">Rate</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-crown me-1"></i>
                                Leader: ${group.leader_name}
                            </small>
                            <small class="text-muted">${WorkManagement.formatDate(group.created_at)}</small>
                        </div>
                    </div>
                </div>
                
                <div class="card-footer bg-transparent">
                    <div class="d-flex gap-2">
                        <!-- View Details - Available for all -->
                        <button class="btn btn-outline-info btn-sm flex-fill" onclick="viewGroupDetails(${group.id})">
                            <i class="fas fa-eye me-1"></i>Details
                        </button>
                        
                        ${/* Admin Actions */ ''}
                        ${isAdmin ? `
                            <button class="btn btn-outline-warning btn-sm" onclick="editGroup(${group.id})" title="Edit Group">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="deleteGroup(${group.id})" title="Delete Group">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                        
                        ${/* Employee Actions */ ''}
                        ${canRequestJoin ? `
                            <button class="btn btn-success btn-sm" onclick="showRequestJoinModal(${group.id}, '${group.name}')" title="Request to Join">
                                <i class="fas fa-paper-plane me-1"></i>Request Join
                            </button>
                        ` : ''}
                        
                        ${/* Show status for employee if in group */ ''}
                        ${isEmployee && currentUser.group && currentUser.group.id === group.id ? `
                            <span class="btn btn-outline-success btn-sm disabled">
                                <i class="fas fa-check me-1"></i>Joined
                            </span>
                        ` : ''}
                        
                        ${/* Show disabled if no leader */ ''}
                        ${isEmployee && !currentUser.group && group.leader_name === 'No leader' ? `
                            <span class="btn btn-outline-secondary btn-sm disabled" title="No leader available">
                                <i class="fas fa-ban me-1"></i>No Leader
                            </span>
                        ` : ''}
                        
                        ${/* Show disabled if user already in group */ ''}
                        ${isEmployee && currentUser.group && currentUser.group.id !== group.id ? `
                            <span class="btn btn-outline-secondary btn-sm disabled" title="Leave current group first">
                                <i class="fas fa-ban me-1"></i>In Another Group
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ✅ THÊM: Show Request Join Modal
function showRequestJoinModal(groupId, groupName) {
    const modalHtml = `
        <div class="modal fade" id="requestJoinModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-paper-plane me-2"></i>Request to Join "${groupName}"
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <form id="requestJoinForm">
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                Your request will be sent to the group leader and administrators for approval.
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Message (Optional)</label>
                                <textarea class="form-control" name="message" rows="3" 
                                         placeholder="Why do you want to join this group? (optional)"></textarea>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-paper-plane me-1"></i>Send Request
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    $('#requestJoinModal').remove();
    
    // Add modal to body
    $('body').append(modalHtml);
    
    // Handle form submission
    $('#requestJoinForm').on('submit', function(e) {
        e.preventDefault();
        submitJoinRequest(groupId, groupName);
    });
    
    // Show modal
    $('#requestJoinModal').modal('show');
}

// ✅ THÊM: Submit join request
function submitJoinRequest(groupId, groupName) {
    const currentUser = WorkManagement.currentUser();
    const formData = new FormData(document.getElementById('requestJoinForm'));
    
    const requestData = {
        user_id: currentUser.id,
        group_id: groupId,
        message: formData.get('message') || ''
    };
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall('/groups/join-request', {
        method: 'POST',
        data: JSON.stringify(requestData)
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', `Join request sent for "${groupName}" successfully!`);
        
        $('#requestJoinModal').modal('hide');
        
        // Refresh my requests
        setTimeout(() => {
            loadMyJoinRequests();
            loadGroups(); // Refresh groups to update button states
        }, 500);
        location.reload();
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to send join request';
        WorkManagement.showAlert('danger', message);
    });
}

// ✅ THÊM: Remove modal when hidden
$(document).on('hidden.bs.modal', '#requestJoinModal', function () {
    $(this).remove();
});

function filterAndDisplayGroups() {
    const searchName = $('#search-name').val().toLowerCase();
    const filterLeader = $('#filter-leader').val();
    const sortBy = $('#sort-by').val();
    
    let filteredGroups = allGroups.filter(group => {
        const nameMatch = group.name.toLowerCase().includes(searchName);
        
        let leaderMatch = true;
        if (filterLeader === 'no-leader') {
            leaderMatch = !group.leader_id;
        } else if (filterLeader) {
            leaderMatch = group.leader_id == filterLeader;
        }
        
        return nameMatch && leaderMatch;
    });
    
    // Sort groups
    filteredGroups.sort((a, b) => {
        switch (sortBy) {
            case 'name':
                return a.name.localeCompare(b.name);
            case 'member_count':
                return b.member_count - a.member_count;
            case 'completion_rate':
                return parseFloat(b.completion_rate) - parseFloat(a.completion_rate);
            case 'created_at':
                return new Date(b.created_at) - new Date(a.created_at);
            default:
                return 0;
        }
    });
    
    displayGroups(filteredGroups);
}

function openGroupModal(groupData = null) {
    const modal = $('#groupModal');
    const form = $('#group-form')[0];
    
    form.reset();
    form.classList.remove('was-validated');
    
    if (groupData) {
        // Edit mode
        $('#group-modal-title').html('<i class="fas fa-edit me-2"></i>Edit Group');
        $('#group-name').val(groupData.name);
        $('#group-description').val(groupData.description);
        $('#group-leader').val(groupData.leader_id || '');
        selectedGroupId = groupData.id;
    } else {
        // Create mode
        $('#group-modal-title').html('<i class="fas fa-plus me-2"></i>Create Group');
        selectedGroupId = null;
    }
    
    modal.modal('show');
}

function saveGroup() {
    const currentUser = WorkManagement.currentUser();
    const form = $('#group-form')[0];
    
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }
    
    const groupData = {
        name: $('#group-name').val(),
        description: $('#group-description').val(),
        leader_id: $('#group-leader').val() || null,
        admin_id: currentUser.id
    };
    
    const isEdit = selectedGroupId !== null;
    const url = isEdit ? `/groups/${selectedGroupId}` : '/groups/create';
    const method = isEdit ? 'PUT' : 'POST';
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall(url, {
        method: method,
        data: JSON.stringify(groupData)
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', response.message);
        $('#groupModal').modal('hide');
        
        // Refresh everything
        loadGroups(); // Refresh list
        loadAvailableLeaders(); // Refresh available leaders
        
        // Nếu đang xem details của group này, refresh
        if (isEdit && selectedGroupId && $('#groupDetailsModal').hasClass('show')) {
            viewGroupDetails(selectedGroupId);
        }
        
        if (!isEdit) {
            form.reset();
            form.classList.remove('was-validated');
        }
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to save group';
        WorkManagement.showAlert('danger', message);
    });
}

function showJoinModal(groupId) {
    const group = allGroups.find(g => g.id === groupId);
    if (!group) return;
    
    selectedGroupId = groupId;
    
    $('#join-group-details').html(`
        <div class="card">
            <div class="card-body">
                <h6 class="card-title">${group.name}</h6>
                <p class="card-text">${group.description || 'No description available'}</p>
                <div class="row g-3">
                    <div class="col-6">
                        <small class="text-muted">Leader:</small>
                        <div>${group.leader_name}</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Members:</small>
                        <div>${group.member_count} members</div>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    $('#joinGroupModal').modal('show');
}

function joinGroup(groupId) {
    const currentUser = WorkManagement.currentUser();
    WorkManagement.showLoading();
    
    WorkManagement.apiCall('/groups/join', {
        method: 'POST',
        data: JSON.stringify({
            user_id: currentUser.id,
            group_id: groupId
        })
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', response.message);
        $('#joinGroupModal').modal('hide');
        
        // Update current user's group info
        const group = allGroups.find(g => g.id === groupId);
        if (group) {
            currentUser.group = {
                id: group.id,
                name: group.name
            };
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
        }
        
        loadGroups(); // Refresh the list
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to join group';
        WorkManagement.showAlert('danger', message);
    });
}

function viewGroupDetails(groupId) {
    WorkManagement.showLoading();
    
    WorkManagement.apiCall(`/groups/${groupId}`)
        .then(response => {
            WorkManagement.hideLoading();
            displayGroupDetails(response);
            selectedGroupId = groupId;
            
            // Cập nhật group trong allGroups array để đồng bộ
            const groupIndex = allGroups.findIndex(g => g.id === groupId);
            if (groupIndex !== -1) {
                // Cập nhật thông tin cơ bản
                allGroups[groupIndex] = {
                    ...allGroups[groupIndex],
                    ...response,
                    // Giữ lại các field cần thiết cho list view
                    member_count: response.statistics ? response.statistics.total_members : response.member_count,
                    completion_rate: response.statistics ? response.statistics.completion_rate : response.completion_rate
                };
            }
            
            $('#groupDetailsModal').modal('show');
        })
        .catch(error => {
            WorkManagement.hideLoading();
            WorkManagement.showAlert('danger', 'Failed to load group details');
        });
}

function displayGroupDetails(group) {
    const currentUser = WorkManagement.currentUser();
    const canEdit = currentUser.role === 'admin' || 
                   (currentUser.role === 'leader' && group.leader && group.leader.id === currentUser.id);
    
    if (canEdit) {
        $('#btn-edit-group').show();
    } else {
        $('#btn-edit-group').hide();
    }
    
    $('#group-details-title').html(`<i class="fas fa-users me-2"></i>${group.name}`);
    
    const membersHtml = group.members.map(member => `
        <tr>
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar-sm rounded-circle bg-primary text-white d-flex align-items-center justify-content-center me-3">
                        ${member.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div class="fw-medium">${member.name}</div>
                        <small class="text-muted">${member.email}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge ${member.role === 'leader' ? 'bg-warning' : 'bg-secondary'}">${member.role}</span>
                ${group.leader && group.leader.id === member.id ? '<i class="fas fa-crown text-warning ms-1" title="Group Leader"></i>' : ''}
            </td>
            <td>${member.employee_code}</td>
            <td>${member.tasks_assigned}</td>
            <td>${member.tasks_completed}</td>
            <td>
                <span class="badge bg-success">${member.completion_rate}</span>
            </td>
            <td>
                ${canEdit ? `
                    <div class="dropdown">
                        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fas fa-cog"></i>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            ${/* THÊM: Assign Task - hiển thị cho admin và leader (trừ chính mình) */ ''}
                            ${canAssignTask(currentUser, member.id) ? `
                                <li><a class="dropdown-item" href="#" onclick="showAssignTaskModal(${member.id}, '${member.name}')">
                                    <i class="fas fa-tasks me-2 text-success"></i>Assign Task
                                </a></li>
                            ` : ''}
                            
                            ${/* Admin actions */ ''}
                            ${currentUser.role === 'admin' ? `
                                ${/* Promote to leader (nếu không phải leader hiện tại) */ ''}
                                ${!(group.leader && group.leader.id === member.id) ? `
                                    <li><a class="dropdown-item" href="#" onclick="promoteMemberToLeader(${member.id})">
                                        <i class="fas fa-crown me-2 text-warning"></i>Promote to Leader
                                    </a></li>
                                ` : ''}
                                
                                ${/* Transfer to another group */ ''}
                                <li><a class="dropdown-item" href="#" onclick="showTransferModal(${member.id})">
                                    <i class="fas fa-exchange-alt me-2 text-info"></i>Transfer to Group
                                </a></li>
                                
                                ${/* Thêm divider nếu có assign task hoặc admin actions */ ''}
                                ${canAssignTask(currentUser, member.id) || !(group.leader && group.leader.id === member.id) ? '<li><hr class="dropdown-divider"></li>' : ''}
                                
                                ${/* Remove member */ ''}
                                <li><a class="dropdown-item text-danger" href="#" onclick="removeMember(${member.id})">
                                    <i class="fas fa-times me-2"></i>Remove Member
                                </a></li>
                            ` : ''}
                            
                            ${/* Leader actions */ ''}
                            ${currentUser.role === 'leader' && group.leader && group.leader.id === currentUser.id ? `
                                ${/* Leader có thể transfer member (trừ chính mình) */ ''}
                                ${member.id !== currentUser.id ? `
                                    <li><a class="dropdown-item" href="#" onclick="showTransferModal(${member.id})">
                                        <i class="fas fa-exchange-alt me-2 text-info"></i>Transfer to Group
                                    </a></li>
                                ` : ''}
                                
                                ${/* Leader có thể remove employee (không phải leader và không phải chính mình) */ ''}
                                ${member.role === 'employee' && member.id !== currentUser.id ? `
                                    ${(member.id !== currentUser.id && canAssignTask(currentUser, member.id)) ? '<li><hr class="dropdown-divider"></li>' : ''}
                                    <li><a class="dropdown-item text-danger" href="#" onclick="removeMember(${member.id})">
                                        <i class="fas fa-times me-2"></i>Remove Member
                                    </a></li>
                                ` : ''}
                                
                                ${/* Hiển thị thông báo nếu không có action nào */ ''}
                                ${member.id === currentUser.id && !canAssignTask(currentUser, member.id) ? `
                                    <li><span class="dropdown-item-text text-muted">
                                        <i class="fas fa-info-circle me-2"></i>You cannot manage yourself
                                    </span></li>
                                ` : ''}
                            ` : ''}
                        </ul>
                    </div>
                ` : ''}
            </td>
        </tr>
    `).join('');
    
    $('#group-details-content').html(`
        <div class="row g-4">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">Group Information</h6>
                    </div>
                    <div class="card-body">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label text-muted">Group Name</label>
                                <div class="fw-medium">${group.name}</div>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label text-muted">Leader</label>
                                <div class="fw-medium">
                                    ${group.leader ? `
                                        <span class="text-warning">
                                            <i class="fas fa-crown me-1"></i>${group.leader.name}
                                        </span>
                                    ` : '<span class="text-muted">No leader assigned</span>'}
                                </div>
                            </div>
                            <div class="col-12">
                                <label class="form-label text-muted">Description</label>
                                <div>${group.description || 'No description available'}</div>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label text-muted">Created Date</label>
                                <div>${WorkManagement.formatDate(group.created_at)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">Statistics</h6>
                    </div>
                    <div class="card-body">
                        <div class="text-center mb-3">
                            <div class="h3 text-primary">${group.statistics.total_members}</div>
                            <div class="text-muted">Total Members</div>
                        </div>
                        <div class="row g-2 text-center">
                            <div class="col-6">
                                <div class="h5 text-success">${group.statistics.total_tasks}</div>
                                <div class="small text-muted">Total Tasks</div>
                            </div>
                            <div class="col-6">
                                <div class="h5 text-info">${group.statistics.completed_tasks}</div>
                                <div class="small text-muted">Completed</div>
                            </div>
                        </div>
                        <div class="mt-3">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="small">Completion Rate</span>
                                <span class="small fw-medium">${group.statistics.completion_rate}</span>
                            </div>
                            <div class="progress" style="height: 8px;">
                                <div class="progress-bar bg-success" style="width: ${group.statistics.completion_rate}"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${/* THÊM: Quick Actions Panel */ ''}
                ${canEdit ? `
                    <div class="card mt-3">
                        <div class="card-header">
                            <h6 class="mb-0">
                                <i class="fas fa-bolt me-2"></i>Quick Actions
                            </h6>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <button class="btn btn-outline-success" onclick="showBulkAssignTaskModal()">
                                    <i class="fas fa-tasks me-2"></i>Assign Task to Multiple
                                </button>
                                <button class="btn btn-outline-info" onclick="viewGroupTasks()">
                                    <i class="fas fa-list me-2"></i>View All Group Tasks
                                </button>
                                <button class="btn btn-outline-primary" onclick="generateGroupReport()">
                                    <i class="fas fa-chart-bar me-2"></i>Generate Group Report
                                </button>
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">Members (${group.members.length})</h6>
                        <div>
                            ${canEdit ? `
                                <button class="btn btn-sm btn-success me-2" onclick="showBulkAssignTaskModal()">
                                    <i class="fas fa-tasks me-1"></i>Assign Tasks
                                </button>
                                <button class="btn btn-sm btn-primary" onclick="showAddMemberModal()">
                                    <i class="fas fa-user-plus me-1"></i>Add Member
                                </button>
                            ` : ''}
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th>Member</th>
                                        <th>Role</th>
                                        <th>Code</th>
                                        <th>Tasks</th>
                                        <th>Completed</th>
                                        <th>Rate</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${membersHtml || '<tr><td colspan="7" class="text-center text-muted">No members found</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);
}

// Helper function để check quyền assign task
function canAssignTask(currentUser, memberId) {
    // Admin có thể assign cho tất cả
    if (currentUser.role === 'admin') {
        return true;
    }
    
    // Leader có thể assign cho members trong nhóm (trừ chính mình)
    if (currentUser.role === 'leader' && memberId !== currentUser.id) {
        return true;
    }
    
    return false;
}

function editGroup(groupId) {
    const group = allGroups.find(g => g.id === groupId);
    if (group) {
        openGroupModal(group);
    }
}

function editCurrentGroup() {
    if (selectedGroupId) {
        editGroup(selectedGroupId);
    }
}

function deleteGroup(groupId) {
    const currentUser = WorkManagement.currentUser();
    const group = allGroups.find(g => g.id === groupId);
    if (!group) return;
    
    if (confirm(`Are you sure you want to delete group "${group.name}"? This action cannot be undone.`)) {
        WorkManagement.showLoading();
        
        WorkManagement.apiCall(`/groups/${groupId}`, {
            method: 'DELETE',
            data: JSON.stringify({ admin_id: currentUser.id })
        })
        .then(response => {
            WorkManagement.hideLoading();
            WorkManagement.showAlert('success', response.message);
            loadGroups();
        })
        .catch(error => {
            WorkManagement.hideLoading();
            const message = error.responseJSON?.message || 'Failed to delete group';
            WorkManagement.showAlert('danger', message);
        });
    }
}

function removeMember(userId) {
    const currentUser = WorkManagement.currentUser();
    
    // Thay vì lấy từ allGroups, gọi API để lấy group details mới nhất
    WorkManagement.apiCall(`/groups/${selectedGroupId}`)
        .then(groupResponse => {
            const group = groupResponse;
            
            // Kiểm tra xem user có phải leader không
            let isLeader = false;
            let userName = '';
            
            if (group && group.leader && group.leader.id === userId) {
                isLeader = true;
                userName = group.leader.name;
            } else {
                // Tìm trong danh sách members
                const member = group.members && group.members.find(m => m.id === userId);
                if (member) {
                    userName = member.name;
                } else {
                    // Fallback: tìm user từ API
                    WorkManagement.apiCall(`/users/${userId}`)
                        .then(userResponse => {
                            userName = userResponse.name;
                            performRemoveMember(userId, userName, isLeader);
                        })
                        .catch(() => {
                            userName = 'Unknown User';
                            performRemoveMember(userId, userName, isLeader);
                        });
                    return;
                }
            }
            
            performRemoveMember(userId, userName, isLeader);
        })
        .catch(error => {
            console.error('Error getting group details:', error);
            // Fallback: thực hiện remove với thông tin tối thiểu
            performRemoveMember(userId, 'User', false);
        });
}

// Tách riêng logic remove để tái sử dụng
function performRemoveMember(userId, userName, isLeader) {
    const currentUser = WorkManagement.currentUser();
    
    const confirmMessage = isLeader ? 
        `Are you sure you want to remove leader "${userName}" from the group? The group will have no leader after this action.` :
        `Are you sure you want to remove "${userName}" from the group?`;
    
    if (confirm(confirmMessage)) {
        WorkManagement.showLoading();
        
        WorkManagement.apiCall('/groups/remove-member', {
            method: 'POST',
            data: JSON.stringify({
                admin_id: currentUser.id,
                user_id: userId
            })
        })
        .then(response => {
            WorkManagement.hideLoading();
            WorkManagement.showAlert('success', response.message);
            
            // Refresh everything to ensure data consistency
            loadGroups(); // Refresh list first
            loadAvailableLeaders(); // Refresh available leaders
            
            // Refresh group details if modal is still open
            if ($('#groupDetailsModal').hasClass('show')) {
                viewGroupDetails(selectedGroupId);
            }
        })
        .catch(error => {
            WorkManagement.hideLoading();
            const message = error.responseJSON?.message || 'Failed to remove member';
            WorkManagement.showAlert('danger', message);
        });
    }
}

// Leave current group (for employees)
function leaveCurrentGroup() {
    const currentUser = WorkManagement.currentUser();
    if (!currentUser.group) {
        WorkManagement.showAlert('warning', 'You are not in any group');
        return;
    }
    
    if (confirm(`Are you sure you want to leave "${currentUser.group.name}"?`)) {
        WorkManagement.showLoading();
        
        WorkManagement.apiCall('/groups/leave', {
            method: 'POST',
            data: JSON.stringify({ user_id: currentUser.id })
        })
        .then(response => {
            WorkManagement.hideLoading();
            WorkManagement.showAlert('success', response.message);
            
            // Update current user
            currentUser.group = null;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            loadGroups();
        })
        .catch(error => {
            WorkManagement.hideLoading();
            const message = error.responseJSON?.message || 'Failed to leave group';
            WorkManagement.showAlert('danger', message);
        });
    }
}

// Add leave button if user is in a group
$(document).ready(function() {
    const currentUser = WorkManagement.currentUser();
    if (currentUser && currentUser.group) {
        const leaveButton = `
            <button class="btn btn-danger ms-2" onclick="leaveCurrentGroup()">
                <i class="fas fa-sign-out-alt me-2"></i>Leave Current Group
            </button>
        `;
        
        // Add leave button to header
        $('.card-header .col-auto').append(leaveButton);
    }
});

// Show Add Member Modal
function showAddMemberModal() {
    const currentUser = WorkManagement.currentUser();
    
    // Load available employees (chỉ những người chưa có group)
    WorkManagement.apiCall('/users/employees')
        .then(response => {
            const employees = Array.isArray(response) ? response : [];
            
            // Filter out employees who already have a group
            const availableEmployees = employees.filter(emp => !emp.group);
            
            let employeeOptions = '';
            if (availableEmployees.length === 0) {
                employeeOptions = '<option value="">No available employees</option>';
            } else {
                availableEmployees.forEach(emp => {
                    employeeOptions += `<option value="${emp.id}">${emp.name} (${emp.employee_code}) - No Group</option>`;
                });
            }
            
            // Create modal HTML
            const modalHtml = `
                <div class="modal fade" id="addMemberModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-user-plus me-2"></i>Add Member to Group
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <form id="add-member-form">
                                <div class="modal-body">
                                    <div class="mb-3">
                                        <label class="form-label">Select Employee *</label>
                                        <select class="form-select" id="employee-select" required>
                                            <option value="">Choose an employee...</option>
                                            ${employeeOptions}
                                        </select>
                                        <div class="form-text">Only employees without a group are shown.</div>
                                    </div>
                                    
                                    ${availableEmployees.length === 0 ? `
                                        <div class="alert alert-warning">
                                            <i class="fas fa-exclamation-triangle me-2"></i>
                                            No available employees found. All employees are already assigned to groups.
                                        </div>
                                    ` : `
                                        <div class="alert alert-info">
                                            <i class="fas fa-info-circle me-2"></i>
                                            Found ${availableEmployees.length} available employee(s) without a group.
                                        </div>
                                    `}
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                    <button type="submit" class="btn btn-primary" ${availableEmployees.length === 0 ? 'disabled' : ''}>
                                        <i class="fas fa-plus me-2"></i>Add Member
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            $('#addMemberModal').remove();
            
            // Add modal to page
            $('body').append(modalHtml);
            
            // Show modal
            $('#addMemberModal').modal('show');
            
            // Handle form submission
            $('#add-member-form').off('submit').on('submit', function(e) {
                e.preventDefault();
                const employeeId = $('#employee-select').val();
                if (employeeId) {
                    addMemberToGroup(employeeId);
                }
            });
            
        })
        .catch(error => {
            console.error('Error loading employees:', error);
            WorkManagement.showAlert('danger', 'Failed to load available employees');
        });
}

// Add member to group
function addMemberToGroup(employeeId) {
    const currentUser = WorkManagement.currentUser();
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall('/groups/add-member', {
        method: 'POST',
        data: JSON.stringify({
            admin_id: currentUser.id,
            group_id: selectedGroupId,
            user_id: parseInt(employeeId)
        })
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', response.message);
        $('#addMemberModal').modal('hide');
        
        // Refresh everything to ensure data consistency
        loadGroups(); // Refresh list first
        
        // Refresh group details if modal is still open
        if ($('#groupDetailsModal').hasClass('show')) {
            viewGroupDetails(selectedGroupId);
        }
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to add member';
        WorkManagement.showAlert('danger', message);
    });
}

// Manage Members function
function manageMembers(groupId) {
    selectedGroupId = groupId;
    viewGroupDetails(groupId);
}

// Thêm function để remove modal khi đóng
$(document).on('hidden.bs.modal', '#addMemberModal', function () {
    $(this).remove();
});

// Promote member to leader
function promoteMemberToLeader(userId) {
    const currentUser = WorkManagement.currentUser();
    
    // Lấy thông tin member
    WorkManagement.apiCall(`/groups/${selectedGroupId}`)
        .then(groupResponse => {
            const group = groupResponse;
            const member = group.members.find(m => m.id === userId);
            
            if (!member) {
                WorkManagement.showAlert('danger', 'Member not found');
                return;
            }
            
            const confirmMessage = `Are you sure you want to promote "${member.name}" to leader of this group?\n\n` +
                                 `• ${member.name} will become the group leader\n` +
                                 `• ${member.name}'s role will be upgraded to "leader"\n` +
                                 `• Current leader (if any) will remain as a member`;
            
            if (confirm(confirmMessage)) {
                WorkManagement.showLoading();
                
                WorkManagement.apiCall('/groups/promote-member', {
                    method: 'POST',
                    data: JSON.stringify({
                        admin_id: currentUser.id,
                        user_id: userId,
                        group_id: selectedGroupId
                    })
                })
                .then(response => {
                    WorkManagement.hideLoading();
                    WorkManagement.showAlert('success', response.message);
                    
                    // Refresh everything
                    loadGroups();
                    loadAvailableLeaders();
                    viewGroupDetails(selectedGroupId);
                })
                .catch(error => {
                    WorkManagement.hideLoading();
                    const message = error.responseJSON?.message || 'Failed to promote member';
                    WorkManagement.showAlert('danger', message);
                });
            }
        })
        .catch(error => {
            console.error('Error getting group details:', error);
            WorkManagement.showAlert('danger', 'Failed to load group details');
        });
}

// Show transfer modal
function showTransferModal(userId) {
    const currentUser = WorkManagement.currentUser();
    
    // Lấy thông tin member và available groups
    Promise.all([
        WorkManagement.apiCall(`/groups/${selectedGroupId}`),
        WorkManagement.apiCall(`/groups/transfer-options/${selectedGroupId}`)
    ])
    .then(([groupResponse, transferOptions]) => {
        const group = groupResponse;
        const member = group.members.find(m => m.id === userId);
        
        if (!member) {
            WorkManagement.showAlert('danger', 'Member not found');
            return;
        }
        
        // Check if member is current leader
        if (group.leader && group.leader.id === userId) {
            WorkManagement.showAlert('warning', 'Cannot transfer group leader. Remove as leader first or promote another member to leader.');
            return;
        }
        
        let groupOptions = '';
        if (transferOptions.length === 0) {
            groupOptions = '<option value="">No available groups</option>';
        } else {
            transferOptions.forEach(targetGroup => {
                if (targetGroup.can_join) {
                    groupOptions += `<option value="${targetGroup.id}">${targetGroup.name} (${targetGroup.member_count} members, Leader: ${targetGroup.leader_name})</option>`;
                }
            });
        }
        
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="transferMemberModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-exchange-alt me-2"></i>Transfer Member to Group
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <form id="transfer-member-form">
                            <div class="modal-body">
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle me-2"></i>
                                    Transfer <strong>${member.name}</strong> from "<strong>${group.name}</strong>" to another group.
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Select Target Group *</label>
                                    <select class="form-select" id="target-group-select" required>
                                        <option value="">Choose target group...</option>
                                        ${groupOptions}
                                    </select>
                                    <div class="form-text">Only groups with leaders are shown.</div>
                                </div>
                                
                                ${transferOptions.length === 0 ? `
                                    <div class="alert alert-warning">
                                        <i class="fas fa-exclamation-triangle me-2"></i>
                                        No available groups found. All groups either have no leader or are the current group.
                                    </div>
                                ` : ''}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="submit" class="btn btn-primary" ${transferOptions.length === 0 ? 'disabled' : ''}>
                                    <i class="fas fa-exchange-alt me-2"></i>Transfer Member
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        $('#transferMemberModal').remove();
        
        // Add modal to page
        $('body').append(modalHtml);
        
        // Show modal
        $('#transferMemberModal').modal('show');
        
        // Handle form submission
        $('#transfer-member-form').off('submit').on('submit', function(e) {
            e.preventDefault();
            const targetGroupId = $('#target-group-select').val();
            if (targetGroupId) {
                transferMemberToGroup(userId, targetGroupId);
            }
        });
    })
    .catch(error => {
        console.error('Error loading transfer options:', error);
        WorkManagement.showAlert('danger', 'Failed to load transfer options');
    });
}

// Transfer member to group
function transferMemberToGroup(userId, targetGroupId) {
    const currentUser = WorkManagement.currentUser();
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall('/groups/transfer-member', {
        method: 'POST',
        data: JSON.stringify({
            admin_id: currentUser.id,
            user_id: userId,
            target_group_id: parseInt(targetGroupId)
        })
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', response.message);
        $('#transferMemberModal').modal('hide');
        
        // Refresh everything
        loadGroups();
        viewGroupDetails(selectedGroupId);
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to transfer member';
        WorkManagement.showAlert('danger', message);
    });
}

// Remove modal when closed
$(document).on('hidden.bs.modal', '#transferMemberModal', function () {
    $(this).remove();
});

$(document).ready(function() {
    // Handle dropdown positioning
    $(document).on('shown.bs.dropdown', '.dropdown', function() {
        const dropdown = $(this).find('.dropdown-menu');
        const toggle = $(this).find('.dropdown-toggle');
        
        // Ensure dropdown is visible
        dropdown.css({
            'z-index': '1060',
            'position': 'absolute'
        });
        
        // Check if dropdown is in a modal
        if ($(this).closest('.modal').length > 0) {
            dropdown.css('z-index', '1070');
        }
        
        // Check if dropdown is in a card
        if ($(this).closest('.card').length > 0) {
            dropdown.css('z-index', '1055');
        }
        
        // Adjust position if dropdown goes off screen
        const dropdownRect = dropdown[0].getBoundingClientRect();
        const windowHeight = window.innerHeight;
        const windowWidth = window.innerWidth;
        
        // If dropdown goes off bottom of screen, show it above the button
        if (dropdownRect.bottom > windowHeight) {
            dropdown.addClass('dropup');
        }
        
        // If dropdown goes off right side of screen, align it to the right
        if (dropdownRect.right > windowWidth) {
            dropdown.addClass('dropdown-menu-end');
        }
    });
    
    // Clean up on dropdown hide
    $(document).on('hidden.bs.dropdown', '.dropdown', function() {
        const dropdown = $(this).find('.dropdown-menu');
        dropdown.removeClass('dropup dropdown-menu-end');
    });
});

// Function to force dropdown positioning
function fixDropdownPosition(dropdownElement) {
    const $dropdown = $(dropdownElement);
    const $menu = $dropdown.find('.dropdown-menu');
    
    // Set high z-index
    $menu.css({
        'z-index': '1060',
        'position': 'absolute'
    });
    
    // Additional checks for specific containers
    if ($dropdown.closest('.modal').length) {
        $menu.css('z-index', '1070');
    }
    
    if ($dropdown.closest('.card-footer').length) {
        $menu.css('z-index', '1055');
    }
}

// Apply fix to all existing dropdowns
$(document).on('DOMNodeInserted', function(e) {
    if ($(e.target).hasClass('dropdown') || $(e.target).find('.dropdown').length) {
        setTimeout(() => {
            $('.dropdown').each(function() {
                fixDropdownPosition(this);
            });
        }, 100);
    }
});

function showAssignTaskModal(memberId, memberName) {
    const currentUser = WorkManagement.currentUser();
    
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="assignTaskModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-tasks me-2"></i>Assign Task to ${memberName}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <form id="assign-task-form">
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                Creating a new task and assigning it to <strong>${memberName}</strong>
                            </div>
                            
                            <div class="row g-3">
                                <div class="col-md-8">
                                    <label class="form-label">Task Title *</label>
                                    <input type="text" class="form-control" name="title" required maxlength="200">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Priority *</label>
                                    <select class="form-select" name="priority" required>
                                        <option value="low">Low</option>
                                        <option value="medium" selected>Medium</option>
                                        <option value="high">High</option>
                                    </select>
                                </div>
                                
                                <div class="col-12">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="4" placeholder="Describe the task details..."></textarea>
                                </div>
                                
                                
                                <div class="col-md-6">
                                    <label class="form-label">Deadline</label>
                                    <input type="date" class="form-control" name="deadline">
                                </div>
                                
                                <div class="col-md-6">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="todo" selected>To Do</option>
                                        <option value="doing">In Progress</option>
                                    </select>
                                </div>
                                
                                
                                
                                
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-check me-2"></i>Assign Task
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    $('#assignTaskModal').remove();
    
    // Add modal to page
    $('body').append(modalHtml);
    
    // Load parent task options
    loadParentTaskOptionsForMember(memberId);
    
    // Show modal
    $('#assignTaskModal').modal('show');
    
    // Handle form submission
    $('#assign-task-form').off('submit').on('submit', function(e) {
        e.preventDefault();
        assignTaskToMember(memberId, this);
    });
}

// Show bulk assign task modal
function showBulkAssignTaskModal() {
    const currentUser = WorkManagement.currentUser();
    
    // Get group members (exclude current user if leader)
    WorkManagement.apiCall(`/groups/${selectedGroupId}`)
        .then(group => {
            const availableMembers = group.members.filter(member => {
                // Admin có thể assign cho tất cả
                if (currentUser.role === 'admin') {
                    return true;
                }
                // Leader không thể assign cho chính mình
                return member.id !== currentUser.id;
            });
            
            if (availableMembers.length === 0) {
                WorkManagement.showAlert('warning', 'No members available to assign tasks');
                return;
            }
            
            let memberOptions = '';
            availableMembers.forEach(member => {
                memberOptions += `
                    <div class="form-check">
                        <input class="form-check-input member-checkbox" type="checkbox" value="${member.id}" id="member_${member.id}">
                        <label class="form-check-label d-flex align-items-center" for="member_${member.id}">
                            <div class="avatar-sm rounded-circle bg-primary text-white d-flex align-items-center justify-content-center me-2">
                                ${member.name.charAt(0).toUpperCase()}
                            </div>
                            <div>
                                <div class="fw-medium">${member.name}</div>
                                <small class="text-muted">${member.email} • ${member.role}</small>
                            </div>
                        </label>
                    </div>
                `;
            });
            
            const modalHtml = `
                <div class="modal fade" id="bulkAssignTaskModal" tabindex="-1">
                    <div class="modal-dialog modal-xl">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-tasks me-2"></i>Assign Task to Multiple Members
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <form id="bulk-assign-task-form">
                                <div class="modal-body">
                                    <div class="row">
                                        <div class="col-md-8">
                                            <div class="card">
                                                <div class="card-header">
                                                    <h6 class="mb-0">Task Details</h6>
                                                </div>
                                                <div class="card-body">
                                                    <div class="row g-3">
                                                        <div class="col-md-8">
                                                            <label class="form-label">Task Title *</label>
                                                            <input type="text" class="form-control" name="title" required maxlength="200">
                                                        </div>
                                                        <div class="col-md-3">
                                                            <label class="form-label">Priority *</label>
                                                            <select class="form-select" name="priority" required>
                                                                <option value="low">Low</option>
                                                                <option value="medium" selected>Medium</option>
                                                                <option value="high">High</option>
                                                            </select>
                                                        </div>
                                                        
                                                        <div class="col-12">
                                                            <label class="form-label">Description</label>
                                                            <textarea class="form-control" name="description" rows="4"></textarea>
                                                        </div>
                                                        
                                                    
                                                        <div class="col-md-6">
                                                            <label class="form-label">Deadline</label>
                                                            <input type="date" class="form-control" name="deadline">
                                                        </div>
                                                        
                                                        <div class="col-md-6">
                                                            <label class="form-label">Status</label>
                                                            <select class="form-select" name="status">
                                                                <option value="todo" selected>To Do</option>
                                                                <option value="doing">In Progress</option>
                                                            </select>
                                                        </div>
                                                        
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="col-md-4">
                                            <div class="card">
                                                <div class="card-header d-flex justify-content-between align-items-center">
                                                    <h6 class="mb-0">Select Members</h6>
                                                    <div>
                                                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="selectAllMembers()">All</button>
                                                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="clearAllMembers()">None</button>
                                                    </div>
                                                </div>
                                                <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                                                    ${memberOptions}
                                                </div>
                                            </div>
                                            
                                            <div class="alert alert-info mt-3">
                                                <small>
                                                    <i class="fas fa-info-circle me-1"></i>
                                                    Selected members will receive the same task. You can customize individual tasks later.
                                                </small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                    <button type="submit" class="btn btn-success">
                                        <i class="fas fa-check me-2"></i>Assign to Selected Members
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal
            $('#bulkAssignTaskModal').remove();
            
            // Add modal to page
            $('body').append(modalHtml);
            
            // Show modal
            $('#bulkAssignTaskModal').modal('show');
            
            // Handle form submission
            $('#bulk-assign-task-form').off('submit').on('submit', function(e) {
                e.preventDefault();
                bulkAssignTasks(this);
            });
        })
        .catch(error => {
            console.error('Error loading group members:', error);
            WorkManagement.showAlert('danger', 'Failed to load group members');
        });
}

// Load parent task options for member
function loadParentTaskOptionsForMember(memberId) {
    const currentUser = WorkManagement.currentUser();
    
    // Sử dụng endpoint mới cho parent task options
    let endpoint = '/tasks/parent-options';
    const params = new URLSearchParams();
    
    if (currentUser.role === 'admin') {
        // Admin có thể chọn từ tất cả tasks
        params.append('status', 'todo,doing');
    } else if (currentUser.role === 'leader') {
        // Leader chỉ chọn từ tasks trong group
        params.append('group_id', selectedGroupId);
        params.append('status', 'todo,doing');
    }
    
    if (params.toString()) {
        endpoint += '?' + params.toString();
    }
    
    WorkManagement.apiCall(endpoint)
        .then(tasks => {
            const parentSelect = $('#assignTaskModal select[name="parent_id"]');
            parentSelect.find('option:not(:first)').remove();
            
            if (Array.isArray(tasks)) {
                tasks.forEach(task => {
                    parentSelect.append(`<option value="${task.id}">${task.title} (${task.status}) - ${task.assignee}</option>`);
                });
            }
        })
        .catch(error => {
            console.error('Error loading parent tasks:', error);
        });
}

// Assign task to individual member
function assignTaskToMember(memberId, form) {
    const currentUser = WorkManagement.currentUser();
    const formData = new FormData(form);
    
    const taskData = {
        title: formData.get('title'),
        description: formData.get('description'),
        priority: formData.get('priority'),
        status: formData.get('status'),
        deadline: formData.get('deadline') || null,  // ✅ Loại bỏ start_date
        parent_task_id: formData.get('parent_id') || null,  // ✅ Sửa tên field
        assignee_id: memberId,
        assigner_id: currentUser.id,
        group_id: selectedGroupId
        // ✅ Loại bỏ estimated_hours và send_notification
    };
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall('/tasks/create', {
        method: 'POST',
        data: JSON.stringify(taskData)
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', 'Task assigned successfully');
        $('#assignTaskModal').modal('hide');
        viewGroupDetails(selectedGroupId);
    })
    .catch(error => {
        WorkManagement.hideLoading();
        const message = error.responseJSON?.message || 'Failed to assign task';
        WorkManagement.showAlert('danger', message);
    });
}

// Bulk assign tasks
function bulkAssignTasks(form) {
    const currentUser = WorkManagement.currentUser();
    const formData = new FormData(form);
    
    const selectedMembers = [];
    $('.member-checkbox:checked').each(function() {
        selectedMembers.push(parseInt($(this).val()));
    });
    
    if (selectedMembers.length === 0) {
        WorkManagement.showAlert('warning', 'Please select at least one member');
        return;
    }
    
    const title = formData.get('title');
    if (!title || title.trim() === '') {
        WorkManagement.showAlert('warning', 'Please enter task title');
        return;
    }
    
    const taskData = {
        title: title.trim(),
        description: formData.get('description') || '',
        priority: formData.get('priority') || 'medium',
        status: formData.get('status') || 'todo',
        deadline: formData.get('deadline') || null, 
        assignee_ids: selectedMembers,
        assigner_id: currentUser.id,
        group_id: selectedGroupId
    };
    
    console.log('Sending bulk assign data:', taskData);
    
    WorkManagement.showLoading();
    
    WorkManagement.apiCall('/tasks/bulk-create', {
        method: 'POST',
        data: JSON.stringify(taskData)
    })
    .then(response => {
        WorkManagement.hideLoading();
        WorkManagement.showAlert('success', `Tasks assigned to ${selectedMembers.length} member(s) successfully`);
        $('#bulkAssignTaskModal').modal('hide');
        viewGroupDetails(selectedGroupId);
    })
    .catch(error => {
        WorkManagement.hideLoading();
        console.error('Bulk assign error:', error);
        
        let message = 'Failed to assign tasks';
        if (error.responseJSON && error.responseJSON.message) {
            message = error.responseJSON.message;
        }
        
        WorkManagement.showAlert('danger', message);
    });
}

// Helper functions for bulk assign
function selectAllMembers() {
    $('.member-checkbox').prop('checked', true);
}

function clearAllMembers() {
    $('.member-checkbox').prop('checked', false);
}

// Quick action functions
function viewGroupTasks() {
    // Redirect to tasks page with group filter
    window.location.href = `/tasks?group_id=${selectedGroupId}`;
}

function generateGroupReport() {
    // Redirect to reports page with group pre-selected
    window.location.href = `/reports?group_id=${selectedGroupId}`;
}

// Clean up modals when closed
$(document).on('hidden.bs.modal', '#assignTaskModal, #bulkAssignTaskModal', function () {
    $(this).remove();
});