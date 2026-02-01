/* ===============================================
   Main JavaScript - نظام إدارة العقارات
   Pure JavaScript (No jQuery)
   =============================================== */

'use strict';

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeSidebar();
    initializeAlerts();
    initializeTooltips();
    initializeNotifications();
    
    console.log('نظام إدارة العقارات - تم التحميل بنجاح');
});

// ===============================================
// Sidebar Functions
// ===============================================
function initializeSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    // Handle collapse menus
    const collapseLinks = document.querySelectorAll('[data-bs-toggle="collapse"]');
    collapseLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const icon = this.querySelector('.collapse-icon');
            if (icon) {
                setTimeout(() => {
                    const isExpanded = this.getAttribute('aria-expanded') === 'true';
                    icon.style.transform = isExpanded ? 'rotate(180deg)' : 'rotate(0deg)';
                }, 10);
            }
        });
    });
    
    // Mobile sidebar toggle
    if (window.innerWidth < 768) {
        setupMobileSidebar();
    }
}

function setupMobileSidebar() {
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);
    
    // Toggle button (if exists)
    const toggleBtn = document.querySelector('.navbar-toggler');
    const sidebar = document.getElementById('sidebar');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        });
        
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }
}

// ===============================================
// Alerts Functions
// ===============================================
function initializeAlerts() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// ===============================================
// Tooltips Initialization
// ===============================================
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ===============================================
// Notifications Functions
// ===============================================
function initializeNotifications() {
    const notificationBadge = document.getElementById('notification-count');
    if (!notificationBadge) return;
    
    // Fetch notifications (example)
    fetchNotifications();
}

function fetchNotifications() {
    // This would be replaced with actual API call
    // Example:
    /*
    fetch('/api/notifications/')
        .then(response => response.json())
        .then(data => {
            updateNotificationBadge(data.count);
            updateNotificationDropdown(data.notifications);
        })
        .catch(error => console.error('Error fetching notifications:', error));
    */
}

function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-count');
    if (!badge) return;
    
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

// ===============================================
// Form Validation
// ===============================================
function validateForm(formElement) {
    if (!formElement) return false;
    
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// ===============================================
// Confirmation Dialog
// ===============================================
function confirmAction(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

// ===============================================
// Loading State
// ===============================================
function showLoading(element) {
    if (!element) return;
    
    element.disabled = true;
    const originalContent = element.innerHTML;
    element.dataset.originalContent = originalContent;
    element.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>جاري التحميل...';
}

function hideLoading(element) {
    if (!element) return;
    
    element.disabled = false;
    const originalContent = element.dataset.originalContent;
    if (originalContent) {
        element.innerHTML = originalContent;
    }
}

// ===============================================
// HTMX Event Handlers
// ===============================================
document.addEventListener('htmx:beforeRequest', function(event) {
    const target = event.detail.target;
    if (target) {
        showLoading(target);
    }
});

document.addEventListener('htmx:afterRequest', function(event) {
    const target = event.detail.target;
    if (target) {
        hideLoading(target);
    }
});

document.addEventListener('htmx:responseError', function(event) {
    console.error('HTMX Error:', event.detail);
    showNotification('حدث خطأ أثناء معالجة الطلب', 'error');
});

// ===============================================
// Utility Functions
// ===============================================

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="إغلاق"></button>
    `;
    
    const messagesContainer = document.querySelector('.messages') || createMessagesContainer();
    messagesContainer.appendChild(alertDiv);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages';
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(container, main.firstChild);
    }
    return container;
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-SA', {
        style: 'currency',
        currency: 'SAR'
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ar-SA').format(date);
}

// Debounce function
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

// ===============================================
// Export functions for global use
// ===============================================
window.AppUtils = {
    validateForm,
    confirmAction,
    showLoading,
    hideLoading,
    showNotification,
    formatCurrency,
    formatDate,
    debounce
};