/**
 * نظام إدارة العقارات - JavaScript الرئيسي
 */

(function($) {
    'use strict';

    // ========================================
    // Document Ready
    // ========================================
    $(document).ready(function() {
        // Initialize tooltips
        initTooltips();
        
        // Initialize popovers
        initPopovers();
        
        // Auto-hide alerts
        autoHideAlerts();
        
        // Load notifications count
        loadNotificationsCount();
        
        // Setup AJAX
        setupAjax();
        
        // Form validation
        setupFormValidation();
        
        // Confirm delete
        setupDeleteConfirmation();
        
        // Number formatting
        formatNumbers();
    });

    // ========================================
    // Initialize Tooltips
    // ========================================
    function initTooltips() {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // ========================================
    // Initialize Popovers
    // ========================================
    function initPopovers() {
        var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // ========================================
    // Auto Hide Alerts
    // ========================================
    function autoHideAlerts() {
        $('.alert:not(.alert-permanent)').each(function() {
            var $alert = $(this);
            setTimeout(function() {
                $alert.fadeOut(500, function() {
                    $(this).remove();
                });
            }, 5000);
        });
    }

    // ========================================
    // Load Notifications Count
    // ========================================
    function loadNotificationsCount() {
        // This would typically call an API endpoint
        // For now, we'll just set it from the page if available
        var count = $('#notification-count').data('count');
        if (count && count > 0) {
            $('#notification-count').text(count).show();
        }
    }

    // ========================================
    // Setup AJAX
    // ========================================
    function setupAjax() {
        // CSRF Token setup for AJAX
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            }
        });

        // Show loading spinner on AJAX calls
        $(document).ajaxStart(function() {
            showLoadingSpinner();
        }).ajaxStop(function() {
            hideLoadingSpinner();
        });
    }

    // ========================================
    // CSRF Token Helper
    // ========================================
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // ========================================
    // Loading Spinner
    // ========================================
    function showLoadingSpinner() {
        if ($('#loading-spinner').length === 0) {
            $('body').append(
                '<div id="loading-spinner" class="spinner-overlay">' +
                    '<div class="spinner-border spinner-border-lg text-primary" role="status">' +
                        '<span class="visually-hidden">جاري التحميل...</span>' +
                    '</div>' +
                '</div>'
            );
        }
    }

    function hideLoadingSpinner() {
        $('#loading-spinner').fadeOut(300, function() {
            $(this).remove();
        });
    }

    // ========================================
    // Form Validation
    // ========================================
    function setupFormValidation() {
        // Bootstrap validation
        var forms = document.querySelectorAll('.needs-validation');
        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });

        // Custom validation for Arabic inputs
        $('input[data-validate="arabic"]').on('input', function() {
            var value = $(this).val();
            var arabicPattern = /^[\u0600-\u06FF\s]+$/;
            
            if (value && !arabicPattern.test(value)) {
                $(this).addClass('is-invalid');
                $(this).siblings('.invalid-feedback').text('يجب إدخال نص عربي فقط');
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        // Phone number validation
        $('input[type="tel"]').on('input', function() {
            var value = $(this).val();
            var phonePattern = /^[0-9+\-\s()]+$/;
            
            if (value && !phonePattern.test(value)) {
                $(this).addClass('is-invalid');
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        // Amount validation
        $('input[data-validate="amount"]').on('input', function() {
            var value = $(this).val();
            var amountPattern = /^\d+(\.\d{1,2})?$/;
            
            if (value && !amountPattern.test(value)) {
                $(this).addClass('is-invalid');
                $(this).siblings('.invalid-feedback').text('يجب إدخال مبلغ صحيح');
            } else {
                $(this).removeClass('is-invalid');
            }
        });
    }

    // ========================================
    // Delete Confirmation
    // ========================================
    function setupDeleteConfirmation() {
        $('[data-confirm-delete]').on('click', function(e) {
            e.preventDefault();
            var message = $(this).data('confirm-delete') || 'هل أنت متأكد من الحذف؟';
            
            if (confirm(message)) {
                if ($(this).is('a')) {
                    window.location.href = $(this).attr('href');
                } else if ($(this).is('button')) {
                    $(this).closest('form').submit();
                }
            }
        });
    }

    // ========================================
    // Number Formatting
    // ========================================
    function formatNumbers() {
        $('.format-number').each(function() {
            var value = parseFloat($(this).text());
            if (!isNaN(value)) {
                $(this).text(value.toLocaleString('ar-SA', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }));
            }
        });
    }

    // ========================================
    // Date Picker Helper
    // ========================================
    function setupDatePickers() {
        // If using a date picker library, initialize it here
        $('input[type="date"]').each(function() {
            // Add any custom date picker initialization
        });
    }

    // ========================================
    // Export Functions
    // ========================================
    window.RentalManagement = {
        showAlert: function(message, type) {
            type = type || 'info';
            var alertHtml = 
                '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
                    message +
                    '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                '</div>';
            
            $('.messages').prepend(alertHtml);
            setTimeout(function() {
                $('.messages .alert').first().fadeOut(500, function() {
                    $(this).remove();
                });
            }, 5000);
        },
        
        showLoading: showLoadingSpinner,
        hideLoading: hideLoadingSpinner,
        
        confirmAction: function(message, callback) {
            if (confirm(message)) {
                callback();
            }
        },
        
        formatAmount: function(amount) {
            return parseFloat(amount).toLocaleString('ar-SA', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    };

    // ========================================
    // Print Function
    // ========================================
    window.printPage = function() {
        window.print();
    };

    // ========================================
    // Export to Excel (if needed)
    // ========================================
    window.exportToExcel = function(tableId, filename) {
        var table = document.getElementById(tableId);
        if (!table) return;
        
        var html = table.outerHTML;
        var url = 'data:application/vnd.ms-excel,' + encodeURIComponent(html);
        var downloadLink = document.createElement("a");
        
        filename = filename ? filename + ".xls" : "export.xls";
        downloadLink.href = url;
        downloadLink.download = filename;
        
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    };

})(jQuery);