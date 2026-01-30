// dashboard.js - Dashboard specific functionality

// Sample data for the dashboard
const sampleReports = [
    { id: 1024, type: 'pothole', location: 'Main Street, Downtown', priority: 'high', date: '2023-10-15', status: 'pending', assignedTo: null },
    { id: 1023, type: 'crack', location: 'Oak Avenue', priority: 'medium', date: '2023-10-14', status: 'assigned', assignedTo: 'Team Alpha' },
    { id: 1022, type: 'speed-hump', location: 'River Road', priority: 'low', date: '2023-10-13', status: 'resolved', assignedTo: 'Team Beta' },
    { id: 1021, type: 'flooding', location: 'Park Avenue', priority: 'high', date: '2023-10-15', status: 'pending', assignedTo: null },
    { id: 1020, type: 'pothole', location: '5th Avenue', priority: 'high', date: '2023-10-15', status: 'assigned', assignedTo: 'Team Gamma' },
    { id: 1019, type: 'debris', location: 'Central Park West', priority: 'medium', date: '2023-10-14', status: 'pending', assignedTo: null },
    { id: 1018, type: 'crack', location: 'Broadway', priority: 'low', date: '2023-10-13', status: 'resolved', assignedTo: 'Team Alpha' },
    { id: 1017, type: 'pothole', location: 'Wall Street', priority: 'high', date: '2023-10-15', status: 'pending', assignedTo: null },
    { id: 1016, type: 'signage', location: '7th Avenue', priority: 'medium', date: '2023-10-14', status: 'assigned', assignedTo: 'Team Beta' },
    { id: 1015, type: 'other', location: 'Battery Park', priority: 'low', date: '2023-10-12', status: 'resolved', assignedTo: 'Team Gamma' },
];

let currentPage = 1;
const itemsPerPage = 5;

document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.getElementById('loginBtn');
    const loginPromptBtn = document.getElementById('loginPromptBtn');
    const loginModal = document.getElementById('loginModal');
    const closeModal = document.getElementById('closeModal');
    const loginForm = document.getElementById('loginForm');
    const dashboardContent = document.getElementById('dashboardContent');
    const loginPrompt = document.getElementById('loginPrompt');
    const logoutBtn = document.getElementById('logoutBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const exportBtn = document.getElementById('exportBtn');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    const reportsTableBody = document.getElementById('reportsTableBody');
    
    // Check if user is already logged in
    if (localStorage.getItem('dashboardLoggedIn') === 'true') {
        showDashboard();
    }
    
    // Set up event listeners
    if (loginBtn) loginBtn.addEventListener('click', showLoginModal);
    if (loginPromptBtn) loginPromptBtn.addEventListener('click', showLoginModal);
    if (closeModal) closeModal.addEventListener('click', hideLoginModal);
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);
    if (refreshBtn) refreshBtn.addEventListener('click', refreshDashboard);
    if (exportBtn) exportBtn.addEventListener('click', exportData);
    if (prevPageBtn) prevPageBtn.addEventListener('click', goToPrevPage);
    if (nextPageBtn) nextPageBtn.addEventListener('click', goToNextPage);
    
    // Show login modal
    function showLoginModal(e) {
        e.preventDefault();
        loginModal.classList.add('active');
    }
    
    // Hide login modal
    function hideLoginModal() {
        loginModal.classList.remove('active');
    }
    
    // Handle login
    function handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const rememberMe = document.getElementById('rememberMe').checked;
        
        // Simple validation (in real app, this would be server-side)
        if (username && password) {
            // Demo credentials check
            if (username === 'admin' && password === 'password123') {
                localStorage.setItem('dashboardLoggedIn', 'true');
                if (rememberMe) {
                    localStorage.setItem('dashboardRememberMe', 'true');
                    localStorage.setItem('dashboardUsername', username);
                }
                
                hideLoginModal();
                showDashboard();
                updateLastLogin();
            } else {
                alert('Invalid credentials. Use admin/password123 for demo.');
            }
        }
    }
    
    // Handle logout
    function handleLogout() {
        localStorage.removeItem('dashboardLoggedIn');
        dashboardContent.style.display = 'none';
        loginPrompt.style.display = 'block';
        if (loginBtn) loginBtn.style.display = 'inline-block';
    }
    
    // Show dashboard after login
    function showDashboard() {
        dashboardContent.style.display = 'block';
        loginPrompt.style.display = 'none';
        if (loginBtn) loginBtn.style.display = 'none';
        
        // Load dashboard data
        loadDashboardData();
        renderReportsTable();
        updatePagination();
    }
    
    // Update last login time
    function updateLastLogin() {
        const now = new Date();
        const options = { 
            weekday: 'short', 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        document.getElementById('lastLogin').textContent = now.toLocaleDateString('en-US', options);
    }
    
    // Load dashboard data
    function loadDashboardData() {
        // Update statistics
        updateStatistics();
        
        // Load user name if saved
        const savedUsername = localStorage.getItem('dashboardUsername');
        if (savedUsername) {
            document.getElementById('userName').textContent = savedUsername.charAt(0).toUpperCase() + savedUsername.slice(1);
        }
    }
    
    // Update statistics
    function updateStatistics() {
        const totalComplaints = sampleReports.length;
        const pendingIssues = sampleReports.filter(r => r.status === 'pending').length;
        const resolvedIssues = sampleReports.filter(r => r.status === 'resolved').length;
        const highPriority = sampleReports.filter(r => r.priority === 'high').length;
        
        // Animate statistics
        animateValue(document.getElementById('totalComplaints'), 0, totalComplaints, 1000);
        animateValue(document.getElementById('pendingIssues'), 0, pendingIssues, 1000);
        animateValue(document.getElementById('resolvedIssues'), 0, resolvedIssues, 1000);
        document.getElementById('avgResponseTime').textContent = '2.4';
        
        // Update showing counts
        document.getElementById('totalCount').textContent = totalComplaints;
    }
    
    // Animate value counter
    function animateValue(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            element.textContent = value;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
    
    // Render reports table
    function renderReportsTable() {
        reportsTableBody.innerHTML = '';
        
        // Calculate start and end indices for current page
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, sampleReports.length);
        
        // Update showing count
        document.getElementById('showingCount').textContent = `${startIndex + 1}-${endIndex}`;
        
        // Get reports for current page
        const pageReports = sampleReports.slice(startIndex, endIndex);
        
        // Render each report
        pageReports.forEach(report => {
            const row = document.createElement('tr');
            
            // Priority badge class
            let priorityClass = '';
            if (report.priority === 'high') priorityClass = 'priority-high';
            else if (report.priority === 'medium') priorityClass = 'priority-medium';
            else priorityClass = 'priority-low';
            
            // Status badge
            let statusBadge = '';
            if (report.status === 'pending') {
                statusBadge = '<span class="priority-badge priority-high">Pending</span>';
            } else if (report.status === 'assigned') {
                statusBadge = '<span class="priority-badge priority-medium">Assigned</span>';
            } else {
                statusBadge = '<span class="priority-badge priority-low">Resolved</span>';
            }
            
            // Actions based on status
            let actions = '';
            if (report.status === 'pending') {
                actions = `
                    <button class="action-btn btn-assign" data-id="${report.id}">Assign</button>
                    <button class="action-btn btn-resolve" data-id="${report.id}">Resolve</button>
                `;
            } else if (report.status === 'assigned') {
                actions = `
                    <button class="action-btn btn-resolve" data-id="${report.id}">Mark Resolved</button>
                    <button class="action-btn" style="background-color: #6c757d; color: white;" data-id="${report.id}">Reassign</button>
                `;
            } else {
                actions = '<span style="color: #28a745;">Completed</span>';
            }
            
            row.innerHTML = `
                <td>#${report.id}</td>
                <td>${report.type.charAt(0).toUpperCase() + report.type.slice(1)}</td>
                <td>${report.location}</td>
                <td><span class="priority-badge ${priorityClass}">${report.priority.toUpperCase()}</span></td>
                <td>${report.date}</td>
                <td>${statusBadge}</td>
                <td>${actions}</td>
            `;
            
            reportsTableBody.appendChild(row);
        });
        
        // Add event listeners to action buttons
        addActionButtonListeners();
    }
    
    // Add event listeners to action buttons
    function addActionButtonListeners() {
        // Assign buttons
        document.querySelectorAll('.btn-assign').forEach(btn => {
            btn.addEventListener('click', function() {
                const reportId = parseInt(this.getAttribute('data-id'));
                assignReport(reportId);
            });
        });
        
        // Resolve buttons
        document.querySelectorAll('.btn-resolve').forEach(btn => {
            btn.addEventListener('click', function() {
                const reportId = parseInt(this.getAttribute('data-id'));
                resolveReport(reportId);
            });
        });
    }
    
    // Assign a report
    function assignReport(reportId) {
        const report = sampleReports.find(r => r.id === reportId);
        if (report) {
            const team = prompt('Enter team name to assign (Alpha, Beta, Gamma):', 'Team Alpha');
            if (team) {
                report.status = 'assigned';
                report.assignedTo = team;
                renderReportsTable();
                updateStatistics();
                alert(`Report #${reportId} assigned to ${team}`);
            }
        }
    }
    
    // Resolve a report
    function resolveReport(reportId) {
        const report = sampleReports.find(r => r.id === reportId);
        if (report) {
            report.status = 'resolved';
            renderReportsTable();
            updateStatistics();
            alert(`Report #${reportId} marked as resolved`);
        }
    }
    
    // Refresh dashboard
    function refreshDashboard() {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        
        // Simulate API call
        setTimeout(() => {
            loadDashboardData();
            renderReportsTable();
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            alert('Dashboard data refreshed');
        }, 1000);
    }
    
    // Export data
    function exportData() {
        exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
        
        // Simulate export
        setTimeout(() => {
            const dataStr = JSON.stringify(sampleReports, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportFileDefaultName = `road-reports-${new Date().toISOString().split('T')[0]}.json`;
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
            
            exportBtn.innerHTML = '<i class="fas fa-download"></i> Export';
            alert('Data exported successfully');
        }, 1500);
    }
    
    // Go to previous page
    function goToPrevPage() {
        if (currentPage > 1) {
            currentPage--;
            renderReportsTable();
            updatePagination();
        }
    }
    
    // Go to next page
    function goToNextPage() {
        const totalPages = Math.ceil(sampleReports.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderReportsTable();
            updatePagination();
        }
    }
    
    // Update pagination buttons
    function updatePagination() {
        const totalPages = Math.ceil(sampleReports.length / itemsPerPage);
        
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages;
    }
    
    // Initialize dashboard if remembered
    if (localStorage.getItem('dashboardRememberMe') === 'true' && localStorage.getItem('dashboardLoggedIn') === 'true') {
        showDashboard();
    }
});