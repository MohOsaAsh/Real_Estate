// building_detail.js

document.addEventListener('DOMContentLoaded', function() {
    // Animate progress bar on load
    animateProgressBar();
    
    // Setup delete confirmation
    setupDeleteConfirmation();
    
    // Initialize Bootstrap tooltips
    initializeTooltips();
});

/**
 * Animate progress bar with smooth transition
 */
function animateProgressBar() {
    const progressBar = document.querySelector('.progress-bar');
    
    if (progressBar) {
        const width = progressBar.style.width;
        progressBar.style.width = '0';
        
        setTimeout(() => {
            progressBar.style.width = width;
        }, 300);
    }
}

/**
 * Setup confirmation dialog for delete action
 */
function setupDeleteConfirmation() {
    const deleteBtn = document.querySelector('a[href*="delete"]');
    
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function(e) {
            if (!confirm('هل أنت متأكد من حذف هذا المبنى؟')) {
                e.preventDefault();
            }
        });
    }
}

/**
 * Initialize Bootstrap tooltips for elements with title attribute
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}