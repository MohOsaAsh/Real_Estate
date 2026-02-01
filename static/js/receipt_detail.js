// receipt_detail.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeConfirmations();
    animateProgressBars();
    setupPrintFunctionality();
    initializeTooltips();
});

/**
 * Initialize confirmation dialogs for actions
 */
function initializeConfirmations() {
    Delete confirmation is handled by deleteReceipt function
    Post confirmation is handled by postReceipt function
    Cancel confirmation is handled by cancelReceipt function
}

/**
 * Animate progress bars and statistics
 */
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0';
        
        setTimeout(() => {
            bar.style.transition = 'width 1s ease';
            bar.style.width = width;
        }, 100);
    });
}

/**
 * Post receipt
 * @param {number} receiptId - Receipt ID to post
 */
function postReceipt(receiptId) {
    if (!receiptId) {
        showAlert('خطأ', 'معرف السند غير صحيح', 'error');
        return;
    }
    
    // Show confirmation dialog
    if (!confirm('هل أنت متأكد من ترحيل هذا السند؟\nبعد الترحيل، لن تتمكن من تعديل السند.')) {
        return;
    }
    
    // Show loading state
    showLoading();
    
    // Send post request
    fetch(`/dashboard/receipts/${receiptId}/post/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('فشل ترحيل السند');
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showAlert('نجح', 'تم ترحيل السند بنجاح', 'success');
            
            // Reload page after delay
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert('خطأ', data.message || 'فشل ترحيل السند', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showAlert('خطأ', 'حدث خطأ أثناء ترحيل السند', 'error');
    });
}

/**
 * Cancel receipt
 * @param {number} receiptId - Receipt ID to cancel
 */
function cancelReceipt(receiptId) {
    if (!receiptId) {
        showAlert('خطأ', 'معرف السند غير صحيح', 'error');
        return;
    }
    
    // Show reason prompt
    const reason = prompt('الرجاء إدخال سبب الإلغاء:');
    
    if (reason === null) {
        return; // User cancelled
    }
    
    if (!reason.trim()) {
        showAlert('تحذير', 'يجب إدخال سبب الإلغاء', 'warning');
        return;
    }
    
    // Show loading state
    showLoading();
    
    // Send cancel request
    fetch(`/dashboard/receipts/${receiptId}/cancel/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            reason: reason
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('فشل إلغاء السند');
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showAlert('نجح', 'تم إلغاء السند بنجاح', 'success');
            
            // Reload page after delay
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert('خطأ', data.message || 'فشل إلغاء السند', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showAlert('خطأ', 'حدث خطأ أثناء إلغاء السند', 'error');
    });
}

/**
 * Delete receipt
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
    fetch(`/dashboard/receipts/${receiptId}/delete/`, {
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
            
            // Redirect to list after delay
            setTimeout(() => {
                window.location.href = '/receipts/';
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
 * Setup print functionality
 */
function setupPrintFunctionality() {
    // Add keyboard shortcut for print (Ctrl+P)
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'p') {
            e.preventDefault();
            window.print();
        }
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
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Format date
 * @param {string} dateString - Date string to format
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ar-SA').format(date);
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