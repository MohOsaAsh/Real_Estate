// receipt_form.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeForm();
    setupPaymentMethodHandling();
    setupFormValidation();
    setupContractSelection();
    setupDateValidation();
});

/**
 * Initialize form
 */
function initializeForm() {
    // Set today's date as default
    const receiptDateInput = document.querySelector('input[name="receipt_date"]');
    if (receiptDateInput && !receiptDateInput.value) {
        receiptDateInput.valueAsDate = new Date();
    }
    
    // Initialize payment method fields visibility
    togglePaymentMethodFields();
}

/**
 * Setup payment method handling
 */
function setupPaymentMethodHandling() {
    const paymentMethodSelect = document.querySelector('select[name="payment_method"]');
    
    if (paymentMethodSelect) {
        paymentMethodSelect.addEventListener('change', function() {
            togglePaymentMethodFields();
        });
    }
}

/**
 * Toggle payment method specific fields
 */
function togglePaymentMethodFields() {
    const paymentMethod = document.querySelector('select[name="payment_method"]')?.value;
    
    const checkNumberField = document.getElementById('checkNumberField');
    const checkDateField = document.getElementById('checkDateField');
    const bankNameField = document.getElementById('bankNameField');
    
    // Hide all fields first
    if (checkNumberField) checkNumberField.style.display = 'none';
    if (checkDateField) checkDateField.style.display = 'none';
    if (bankNameField) bankNameField.style.display = 'none';
    
    // Show relevant fields based on payment method
    if (paymentMethod === 'check') {
        if (checkNumberField) {
            checkNumberField.style.display = 'block';
            checkNumberField.classList.add('show');
        }
        if (checkDateField) {
            checkDateField.style.display = 'block';
            checkDateField.classList.add('show');
        }
        if (bankNameField) {
            bankNameField.style.display = 'block';
            bankNameField.classList.add('show');
        }
    } else if (paymentMethod === 'bank_transfer') {
        if (bankNameField) {
            bankNameField.style.display = 'block';
            bankNameField.classList.add('show');
        }
    }
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const form = document.getElementById('receiptForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                showAlert('خطأ', 'الرجاء تصحيح الأخطاء في النموذج', 'error');
            }
        });
    }
}

/**
 * Validate form
 * @returns {boolean} True if form is valid
 */
function validateForm() {
    let isValid = true;
    
    // Validate contract
    const contract = document.querySelector('select[name="contract"]');
    if (contract && !contract.value) {
        showFieldError(contract, 'يجب اختيار العقد');
        isValid = false;
    } else {
        hideFieldError(contract);
    }
    
    // Validate amount
    const amount = document.querySelector('input[name="amount"]');
    if (amount) {
        const amountValue = parseFloat(amount.value);
        if (!amountValue || amountValue <= 0) {
            showFieldError(amount, 'المبلغ يجب أن يكون أكبر من صفر');
            isValid = false;
        } else {
            hideFieldError(amount);
        }
    }
    
    // Validate receipt date
    const receiptDate = document.querySelector('input[name="receipt_date"]');
    if (receiptDate && !receiptDate.value) {
        showFieldError(receiptDate, 'تاريخ السند مطلوب');
        isValid = false;
    } else {
        hideFieldError(receiptDate);
    }
    
    // Validate payment method specific fields
    const paymentMethod = document.querySelector('select[name="payment_method"]')?.value;
    
    if (paymentMethod === 'check') {
        const checkNumber = document.getElementById('check_number');
        if (checkNumber && !checkNumber.value.trim()) {
            showFieldError(checkNumber, 'رقم الشيك مطلوب عند الدفع بالشيك');
            isValid = false;
        } else if (checkNumber) {
            hideFieldError(checkNumber);
        }
    }
    
    // Validate period dates
    const periodStart = document.querySelector('input[name="period_start"]');
    const periodEnd = document.querySelector('input[name="period_end"]');
    
    if (periodStart && periodEnd && periodStart.value && periodEnd.value) {
        if (new Date(periodStart.value) > new Date(periodEnd.value)) {
            showFieldError(periodEnd, 'نهاية الفترة يجب أن تكون بعد البداية');
            isValid = false;
        } else {
            hideFieldError(periodEnd);
        }
    }
    
    return isValid;
}

/**
 * Show field error
 * @param {HTMLElement} field - Form field element
 * @param {string} message - Error message
 */
function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    // Remove existing error message
    const existingError = field.parentElement.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;
    field.parentElement.appendChild(errorDiv);
}

/**
 * Hide field error
 * @param {HTMLElement} field - Form field element
 */
function hideFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentElement.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Setup contract selection
 */
function setupContractSelection() {
    const contractSelect = document.querySelector('select[name="contract"]');
    
    if (contractSelect) {
        contractSelect.addEventListener('change', function() {
            const contractId = this.value;
            
            if (contractId) {
                // Fetch contract details and populate form
                fetchContractDetails(contractId);
            }
        });
    }
}

/**
 * Fetch contract details
 * @param {number} contractId - Contract ID
 */
function fetchContractDetails(contractId) {
    fetch(`/api/contracts/${contractId}/details/`, {
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Populate suggested amount
            const amountField = document.querySelector('input[name="amount"]');
            if (amountField && data.suggested_amount) {
                amountField.value = data.suggested_amount;
            }
            
            // Show contract info
            showContractInfo(data);
        }
    })
    .catch(error => {
        console.error('Error fetching contract details:', error);
    });
}

/**
 * Show contract information
 * @param {Object} data - Contract data
 */
function showContractInfo(data) {
    // You can show a tooltip or info box with contract details
    console.log('Contract details:', data);
}

/**
 * Setup date validation
 */
function setupDateValidation() {
    const periodStart = document.querySelector('input[name="period_start"]');
    const periodEnd = document.querySelector('input[name="period_end"]');
    
    if (periodStart && periodEnd) {
        periodStart.addEventListener('change', function() {
            if (periodEnd.value && this.value > periodEnd.value) {
                showFieldError(this, 'بداية الفترة يجب أن تكون قبل النهاية');
            } else {
                hideFieldError(this);
            }
        });
        
        periodEnd.addEventListener('change', function() {
            if (periodStart.value && this.value < periodStart.value) {
                showFieldError(this, 'نهاية الفترة يجب أن تكون بعد البداية');
            } else {
                hideFieldError(this);
            }
        });
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
 * Format currency input
 */
function setupCurrencyFormatting() {
    const amountInput = document.querySelector('input[name="amount"]');
    
    if (amountInput) {
        amountInput.addEventListener('blur', function() {
            if (this.value) {
                const value = parseFloat(this.value);
                if (!isNaN(value)) {
                    this.value = value.toFixed(2);
                }
            }
        });
    }
}

// Initialize currency formatting
setupCurrencyFormatting();

/**
 * Auto-save form as draft
 */
function setupAutoSave() {
    const form = document.getElementById('receiptForm');
    
    if (form) {
        // Save every 30 seconds
        setInterval(() => {
            const formData = new FormData(form);
            localStorage.setItem('receipt_draft', JSON.stringify(Object.fromEntries(formData)));
        }, 30000);
    }
}

// Initialize auto-save
setupAutoSave();