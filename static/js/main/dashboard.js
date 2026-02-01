/* ===============================================
   Dashboard JavaScript
   Pure JavaScript (No jQuery)
   =============================================== */

'use strict';

// Dashboard initialization
document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.stat-card')) return; // Not on dashboard page
    
    initializeDashboard();
});

function initializeDashboard() {
    console.log('Dashboard initialized');
    
    // Animate statistics
    animateStatistics();
    
    // Initialize charts if needed
    // initializeCharts();
    
    // Setup refresh button if exists
    setupRefreshButton();
}

// ===============================================
// Statistics Animation
// ===============================================
function animateStatistics() {
    const statCards = document.querySelectorAll('.stat-card h2');
    
    statCards.forEach((stat, index) => {
        const value = parseInt(stat.textContent.replace(/[^0-9]/g, ''));
        if (isNaN(value)) return;
        
        animateValue(stat, 0, value, 1000, index * 100);
    });
}

function animateValue(element, start, end, duration, delay) {
    setTimeout(() => {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                current = end;
                clearInterval(timer);
            }
            
            // Format the number
            const formatted = Math.floor(current).toLocaleString('ar-SA');
            element.textContent = formatted;
        }, 16);
    }, delay);
}

// ===============================================
// Refresh Button
// ===============================================
function setupRefreshButton() {
    const refreshBtn = document.getElementById('refresh-dashboard');
    if (!refreshBtn) return;
    
    refreshBtn.addEventListener('click', function(e) {
        e.preventDefault();
        refreshDashboard();
    });
}

function refreshDashboard() {
    // Show loading state
    const refreshBtn = document.getElementById('refresh-dashboard');
    if (refreshBtn) {
        window.AppUtils.showLoading(refreshBtn);
    }
    
    // Reload page or fetch new data via HTMX
    setTimeout(() => {
        location.reload();
    }, 500);
}

// ===============================================
// Table Actions
// ===============================================

// Handle quick view buttons
document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-outline-primary')) {
        const btn = e.target.closest('.btn-outline-primary');
        if (btn.querySelector('.fa-eye')) {
            handleQuickView(btn);
        }
    }
});

function handleQuickView(button) {
    // Add visual feedback
    button.classList.add('active');
    setTimeout(() => {
        button.classList.remove('active');
    }, 200);
}

// ===============================================
// Export functions
// ===============================================
window.DashboardUtils = {
    refreshDashboard,
    animateStatistics
};