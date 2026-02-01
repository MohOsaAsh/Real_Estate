    // static/js/receipts.js

(function($) {
    'use strict';

    $(document).ready(function() {
        initReceiptFeatures();
        setupPaymentValidation();
    });

    function initReceiptFeatures() {
        // Format amounts
        $('.receipt-amount').each(function() {
            var value = parseFloat($(this).text());
            if (!isNaN(value)) {
                $(this).text(value.toLocaleString('ar-SA', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }));
            }
        });
    }

    function setupPaymentValidation() {
        $('#id_amount').on('input', function() {
            var amount = parseFloat($(this).val());
            var outstanding = parseFloat($('#outstanding-amount').text());
            
            if (amount > outstanding) {
                $(this).addClass('is-invalid');
                $(this).siblings('.invalid-feedback')
                    .text('المبلغ يتجاوز المستحق')
                    .show();
            } else {
                $(this).removeClass('is-invalid');
            }
        });
    }

    // Print receipt
    window.printReceipt = function() {
        window.print();
    };

    // Export Functions
    window.ReceiptManager = {
        postReceipt: function(receiptId) {
            if (confirm('هل تريد ترحيل هذا السند؟')) {
                $.ajax({
                    url: `/receipts/${receiptId}/post/`,
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                    },
                    success: function() {
                        RentalManagement.showAlert('تم ترحيل السند بنجاح', 'success');
                        setTimeout(() => location.reload(), 1500);
                    },
                    error: function() {
                        RentalManagement.showAlert('فشل ترحيل السند', 'danger');
                    }
                });
            }
        }
    };

})(jQuery);
