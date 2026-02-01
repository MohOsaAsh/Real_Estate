// receipt_list.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeTableInteractions();
    initializeFilters();
    setupExportFunctionality();
    
    // Auto-submit search on enter
    setupSearchAutoSubmit();
});

/**
 * Initialize table row interactions
 */
function initializeTableInteractions() {
    const rows = document.querySelectorAll('.receipt-row');
    
    rows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't navigate if clicking on action buttons
            if (e.target.closest('.btn-group')) {
                return;
            }
            
            const url = this.dataset.url;
            if (url) {
                window.location.href = url;
            }
        });
    });
}

/**
 * Initialize filter interactions
 */
function initializeFilters() {
    const statusSelect = document.querySelector('select[name="status"]');
    
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            this.closest('form').submit();
        });
    }
}

/**
 * Setup search auto-submit on enter
 */
function setupSearchAutoSubmit() {
    const searchInput = document.querySelector('input[name="search"]');
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.closest('form').submit();
            }
        });
    }
}

/**
 * Export data to Excel
 */
function exportData() {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('export', 'excel');
    window.location.href = currentUrl.toString();
}

/**
 * Delete receipt with confirmation
 * @param {number} receiptId - Receipt ID to delete
 */
function deleteReceipt(receiptId) {
    if (!receiptId) {
        showAlert('خطأ', 'معرف السند غير صحيح', 'error');
        return;
    }
    
    // Show confirmation dialog
    if (!confirm('هل أنت متأكد من حذف هذا السند؟\nهذا الإجراء لا يمكن التراجع عنه.')) {
        return;
    }
    
    // Show loading state
    showLoading();
    
    // Send delete request
    const row = document.querySelector(`tr[data-receipt-id="${receiptId}"]`);
    const deleteUrl = row ? row.dataset.deleteUrl : null;
    if (!deleteUrl) {
        showAlert('خطأ', 'رابط الحذف غير موجود', 'error');
        return;
    }

    fetch(deleteUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('فشل حذف السند');
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showAlert('نجح', 'تم حذف السند بنجاح', 'success');
            
            // Remove row from table
            const row = document.querySelector(`tr[data-receipt-id="${receiptId}"]`);
            if (row) {
                row.style.transition = 'all 0.3s ease';
                row.style.opacity = '0';
                setTimeout(() => row.remove(), 300);
            }
            
            // Reload page after delay
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert('خطأ', data.message || 'فشل حذف السند', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showAlert('خطأ', 'حدث خطأ أثناء حذف السند', 'error');
    });
}

/**
 * Show loading overlay
 */
function showLoading() {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;
    
    overlay.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p style="margin-top: 15px; margin-bottom: 0;">جاري المعالجة...</p>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Show alert message
 * @param {string} title - Alert title
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, error, warning, info)
 */
function showAlert(title, message, type = 'info') {
    // You can use Bootstrap alerts or a custom modal
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert" style="position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; min-width: 300px;">
            <strong>${title}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Get CSRF token from cookie
 * @returns {string} CSRF token
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    return cookieValue;
}

/**
 * Setup export functionality
 */
function setupExportFunctionality() {
    // Add keyboard shortcut for export (Ctrl+E)
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            exportData();
        }
    });
}

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @returns {string} Formatted amount
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-SA', {
        style: 'currency',
        currency: 'SAR'
    }).format(amount);
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize tooltips on load
initializeTooltips();