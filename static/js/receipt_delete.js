// receipt_delete.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize delete form
    initializeDeleteForm();
    setupConfirmationValidation();
});

/**
 * Initialize delete form
 */
function initializeDeleteForm() {
    const deleteForm = document.getElementById('deleteForm');
    
    if (deleteForm) {
        deleteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (validateDeleteForm()) {
                confirmDelete();
            }
        });
    }
}

/**
 * Setup confirmation validation
 */
function setupConfirmationValidation() {
    const confirmCheckbox = document.getElementById('confirmDelete');
    const submitButton = deleteForm.querySelector('button[type="submit"]');
    
    if (confirmCheckbox && submitButton) {
        // Disable submit button initially
        submitButton.disabled = true;
        
        confirmCheckbox.addEventListener('change', function() {
            submitButton.disabled = !this.checked;
            
            if (this.checked) {
                submitButton.classList.add('pulse');
                setTimeout(() => {
                    submitButton.classList.remove('pulse');
                }, 500);
            }
        });
    }
}

/**
 * Validate delete form
 * @returns {boolean} True if form is valid
 */
function validateDeleteForm() {
    const confirmCheckbox = document.getElementById('confirmDelete');
    
    if (!confirmCheckbox.checked) {
        showAlert('تحذير', 'يجب تأكيد الحذف بوضع علامة في المربع', 'warning');
        shakeElement(confirmCheckbox.parentElement);
        return false;
    }
    
    return true;
}

/**
 * Confirm and execute delete
 */
function confirmDelete() {
    // Final confirmation
    if (!confirm('هل أنت متأكد تماماً من حذف هذا السند؟\nهذا هو التأكيد النهائي.')) {
        return;
    }
    
    const form = document.getElementById('deleteForm');
    const formData = new FormData(form);
    
    // Show loading state
    showLoading();
    form.classList.add('loading');
    
    // Get receipt ID from URL
    const receiptId = getReceiptIdFromUrl();
    
    // Send delete request
    fetch(`/receipts/${receiptId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('فشل حذف السند');
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        form.classList.remove('loading');
        
        if (data.success) {
            showSuccessMessage();
            
            // Redirect after delay
            setTimeout(() => {
                window.location.href = '/receipts/';
            }, 2000);
        } else {
            showAlert('خطأ', data.message || 'فشل حذف السند', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        form.classList.remove('loading');
        console.error('Error:', error);
        showAlert('خطأ', 'حدث خطأ أثناء حذف السند', 'error');
    });
}

/**
 * Show success message
 */
function showSuccessMessage() {
    const successHtml = `
        <div class="delete-success show">
            <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
            <h4 class="text-success">تم الحذف بنجاح</h4>
            <p>سيتم تحويلك إلى قائمة السندات...</p>
        </div>
    `;
    
    const cardBody = document.querySelector('.card-body');
    if (cardBody) {
        cardBody.innerHTML = successHtml;
    }
}

/**
 * Get receipt ID from URL
 * @returns {number|null} Receipt ID
 */
function getReceiptIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    const receiptIndex = pathParts.indexOf('receipts');
    
    if (receiptIndex !== -1 && pathParts[receiptIndex + 1]) {
        return parseInt(pathParts[receiptIndex + 1]);
    }
    
    return null;
}

/**
 * Shake element for attention
 * @param {HTMLElement} element - Element to shake
 */
function shakeElement(element) {
    element.classList.add('shake');
    
    setTimeout(() => {
        element.classList.remove('shake');
    }, 500);
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
            <div class="spinner-border text-danger" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p style="margin-top: 15px; margin-bottom: 0; color: #dc3545;">
                <strong>جاري حذف السند...</strong>
            </p>
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
    
    const iconClass = {
        'success': 'fa-check-circle',
        'error': 'fa-times-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    }[type] || 'fa-info-circle';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert" 
             style="position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <i class="fas ${iconClass} me-2"></i>
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
 * Prevent accidental navigation
 */
window.addEventListener('beforeunload', function(e) {
    const form = document.getElementById('deleteForm');
    const confirmCheckbox = document.getElementById('confirmDelete');
    
    if (form && confirmCheckbox && confirmCheckbox.checked) {
        e.preventDefault();
        e.returnValue = '';
    }
});

/**
 * Add keyboard shortcut (Escape to cancel)
 */
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const cancelButton = document.querySelector('.btn-secondary');
        if (cancelButton) {
            window.location.href = cancelButton.href;
        }
    }
});