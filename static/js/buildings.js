 
    //  static/js/buildings.js
 
(function($) {
    'use strict';

    $(document).ready(function() {
        initBuildingFeatures();
    });

    function initBuildingFeatures() {
        // Animate building cards
        $('.building-card').each(function(index) {
            $(this).css({
                opacity: 0,
                transform: 'translateY(30px)'
            });
            
            setTimeout(() => {
                $(this).css({
                    opacity: 1,
                    transform: 'translateY(0)',
                    transition: 'all 0.6s ease'
                });
            }, index * 150);
        });

        // Update occupancy progress bars
        $('.progress-bar').each(function() {
            var width = $(this).data('width');
            setTimeout(() => {
                $(this).css('width', width + '%');
            }, 500);
        });
    }

})(jQuery);