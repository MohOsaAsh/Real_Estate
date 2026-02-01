
     //static/js/units.js

(function($) {
    'use strict';

    $(document).ready(function() {
        initUnitFeatures();
    });

    function initUnitFeatures() {
        // Animate unit cards
        $('.unit-card').each(function(index) {
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
    }

    // Status color coding
    $('.unit-status').each(function() {
        var status = $(this).data('status');
        if (status === 'available') {
            $(this).addClass('bg-success');
        } else if (status === 'rented') {
            $(this).addClass('bg-info');
        } else if (status === 'maintenance') {
            $(this).addClass('bg-warning');
        }
    });

})(jQuery);

