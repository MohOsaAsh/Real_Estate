/**
 * Tenants Management JavaScript
 */

(function($) {
    'use strict';

    $(document).ready(function() {
        // Initialize tenant features
        initTenantFeatures();
        
        // Document upload
        setupDocumentUpload();
        
        // Search and filter
        setupTenantSearch();
        
        // Delete confirmation
        setupDeleteConfirmation();
    });

    // ========================================
    // Initialize Tenant Features
    // ========================================
    function initTenantFeatures() {
        // Animate tenant cards on load
        $('.tenant-card').each(function(index) {
            $(this).css({
                opacity: 0,
                transform: 'translateY(20px)'
            });
            
            setTimeout(() => {
                $(this).css({
                    opacity: 1,
                    transform: 'translateY(0)',
                    transition: 'all 0.5s ease'
                });
            }, index * 100);
        });
        
        // Load outstanding balances
        loadOutstandingBalances();
    }

    // ========================================
    // Load Outstanding Balances
    // ========================================
    function loadOutstandingBalances() {
        $('.tenant-card').each(function() {
            var $card = $(this);
            var tenantId = $card.data('tenant-id');
            
            if (tenantId) {
                // This would typically call an API endpoint
                // For now, the balance is loaded from the template
            }
        });
    }

    // ========================================
    // Document Upload
    // ========================================
    function setupDocumentUpload() {
        var $uploadArea = $('.file-upload-area');
        var $fileInput = $('#id_file');
        
        if ($uploadArea.length === 0) return;
        
        // Click to upload
        $uploadArea.on('click', function() {
            $fileInput.click();
        });
        
        // File selected
        $fileInput.on('change', function() {
            var files = this.files;
            if (files.length > 0) {
                displaySelectedFile(files[0]);
            }
        });
        
        // Drag and drop
        $uploadArea.on('dragover', function(e) {
            e.preventDefault();
            $(this).addClass('dragover');
        });
        
        $uploadArea.on('dragleave', function(e) {
            e.preventDefault();
            $(this).removeClass('dragover');
        });
        
        $uploadArea.on('drop', function(e) {
            e.preventDefault();
            $(this).removeClass('dragover');
            
            var files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                $fileInput[0].files = files;
                displaySelectedFile(files[0]);
            }
        });
    }

    function displaySelectedFile(file) {
        var $uploadArea = $('.file-upload-area');
        var fileSize = (file.size / 1024).toFixed(2);
        var fileName = file.name;
        
        $uploadArea.html(`
            <div class="selected-file">
                <i class="fas fa-file-alt fa-2x text-primary mb-2"></i>
                <div class="fw-bold">${fileName}</div>
                <div class="text-muted small">${fileSize} KB</div>
                <button type="button" class="btn btn-sm btn-danger mt-2" onclick="clearFileSelection()">
                    <i class="fas fa-times"></i> إلغاء
                </button>
            </div>
        `);
    }

    window.clearFileSelection = function() {
        $('#id_file').val('');
        $('.file-upload-area').html(`
            <i class="fas fa-cloud-upload-alt fa-3x mb-3"></i>
            <div class="fw-bold mb-2">اسحب وأفلت الملف هنا</div>
            <div class="text-muted">أو انقر للاختيار من جهازك</div>
            <small class="text-muted mt-2">الحد الأقصى: 10 MB</small>
        `);
    };

    // ========================================
    // Search and Filter
    // ========================================
    function setupTenantSearch() {
        var searchTimeout;
        
        $('input[name="search"]').on('input', function() {
            clearTimeout(searchTimeout);
            var $form = $(this).closest('form');
            
            searchTimeout = setTimeout(function() {
                // Auto-submit after 500ms of no typing
                // Uncomment to enable auto-search
                // $form.submit();
            }, 500);
        });
        
        // Filter by type
        $('select[name="type"]').on('change', function() {
            $(this).closest('form').submit();
        });
    }

    // ========================================
    // Delete Confirmation
    // ========================================
    function setupDeleteConfirmation() {
        $('a[href*="delete"]').on('click', function(e) {
            e.preventDefault();
            var $link = $(this);
            var tenantName = $link.closest('.tenant-card').find('.card-title a').text();
            
            if (confirm(`هل أنت متأكد من حذف المستأجر "${tenantName}"؟`)) {
                window.location.href = $link.attr('href');
            }
        });
    }

    // ========================================
    // Tenant Detail Page
    // ========================================
    if ($('.tenant-detail').length > 0) {
        initTenantDetail();
    }

    function initTenantDetail() {
        // Initialize contracts timeline
        initContractsTimeline();
        
        // Load tenant statistics
        loadTenantStatistics();
        
        // Setup document viewer
        setupDocumentViewer();
    }

    function initContractsTimeline() {
        var $timeline = $('.contracts-timeline');
        if ($timeline.length === 0) return;
        
        $timeline.find('.timeline-item').each(function(index) {
            $(this).css({
                opacity: 0,
                transform: 'translateX(20px)'
            });
            
            setTimeout(() => {
                $(this).css({
                    opacity: 1,
                    transform: 'translateX(0)',
                    transition: 'all 0.5s ease'
                });
            }, index * 150);
        });
    }

    function loadTenantStatistics() {
        // Animate statistics
        $('.tenant-stats .stat-value').each(function() {
            var $this = $(this);
            var value = parseInt($this.text().replace(/,/g, ''));
            
            if (!isNaN(value)) {
                $this.text('0');
                animateValue($this, 0, value, 1000);
            }
        });
    }

    function animateValue($element, start, end, duration) {
        var range = end - start;
        var startTime = null;
        
        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = Math.min((timestamp - startTime) / duration, 1);
            var current = Math.floor(progress * range + start);
            
            $element.text(current.toLocaleString('ar-SA'));
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        }
        
        window.requestAnimationFrame(step);
    }

    function setupDocumentViewer() {
        $('.document-item').on('click', function() {
            var fileUrl = $(this).data('file-url');
            var fileType = $(this).data('file-type');
            
            if (fileType === 'pdf') {
                window.open(fileUrl, '_blank');
            } else if (fileType === 'image') {
                showImageModal(fileUrl);
            } else {
                window.location.href = fileUrl;
            }
        });
    }

    function showImageModal(imageUrl) {
        var modalHtml = `
            <div class="modal fade" id="imageModal" tabindex="-1">
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">عرض المستند</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <img src="${imageUrl}" class="img-fluid" alt="Document">
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('body').append(modalHtml);
        var modal = new bootstrap.Modal(document.getElementById('imageModal'));
        modal.show();
        
        $('#imageModal').on('hidden.bs.modal', function() {
            $(this).remove();
        });
    }

    // ========================================
    // Form Validation
    // ========================================
    if ($('.tenant-form').length > 0) {
        setupTenantFormValidation();
    }

    function setupTenantFormValidation() {
        // ID Number validation (Saudi ID or CR)
        $('#id_id_number').on('input', function() {
            var value = $(this).val();
            var tenantType = $('#id_tenant_type').val();
            
            if (tenantType === 'individual') {
                // Saudi ID: 10 digits starting with 1 or 2
                var isValid = /^[12]\d{9}$/.test(value);
                toggleFieldValidity($(this), isValid, 'رقم هوية غير صحيح');
            } else {
                // Commercial Registration: 10 digits
                var isValid = /^\d{10}$/.test(value);
                toggleFieldValidity($(this), isValid, 'رقم سجل تجاري غير صحيح');
            }
        });
        
        // Phone number validation
        $('#id_phone').on('input', function() {
            var value = $(this).val();
            // Saudi phone: starts with 05 and 10 digits total
            var isValid = /^05\d{8}$/.test(value);
            toggleFieldValidity($(this), isValid, 'رقم هاتف غير صحيح (05XXXXXXXX)');
        });
        
        // Email validation
        $('#id_email').on('input', function() {
            var value = $(this).val();
            if (value) {
                var isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
                toggleFieldValidity($(this), isValid, 'بريد إلكتروني غير صحيح');
            }
        });
    }

    function toggleFieldValidity($field, isValid, errorMessage) {
        if (isValid) {
            $field.removeClass('is-invalid').addClass('is-valid');
            $field.siblings('.invalid-feedback').hide();
        } else {
            $field.removeClass('is-valid').addClass('is-invalid');
            $field.siblings('.invalid-feedback').text(errorMessage).show();
        }
    }

    // ========================================
    // Export Functions
    // ========================================
    window.TenantManagement = {
        refreshBalance: function(tenantId) {
            // Refresh tenant balance via AJAX
            $.ajax({
                url: `/api/tenants/${tenantId}/balance/`,
                method: 'GET',
                success: function(data) {
                    $(`.tenant-card[data-tenant-id="${tenantId}"] .outstanding-balance`).text(
                        RentalManagement.formatAmount(data.balance)
                    );
                }
            });
        },
        
        exportTenantData: function(tenantId) {
            window.location.href = `/tenants/${tenantId}/export/`;
        }
    };

})(jQuery);