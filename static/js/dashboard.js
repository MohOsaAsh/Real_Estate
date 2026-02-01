/**
 * Dashboard Specific JavaScript
 */

(function($) {
    'use strict';

    $(document).ready(function() {
        // Initialize dashboard
        initDashboard();
        
        // Load statistics
        loadStatistics();
        
        // Setup auto-refresh
        setupAutoRefresh();
    });

    // ========================================
    // Initialize Dashboard
    // ========================================
    function initDashboard() {
        // Animate statistics cards
        animateStatCards();
        
        // Initialize occupancy gauge
        initOccupancyGauge();
        
        // Load charts if available
        if (typeof Chart !== 'undefined') {
            loadRevenueChart();
            loadOccupancyChart();
        }
    }

    // ========================================
    // Animate Statistics Cards
    // ========================================
    function animateStatCards() {
        $('.dashboard-stats .card').each(function(index) {
            var $card = $(this);
            var $number = $card.find('h2');
            var target = parseInt($number.text().replace(/,/g, ''));
            
            if (!isNaN(target)) {
                $number.text('0');
                
                setTimeout(function() {
                    animateNumber($number, 0, target, 1000);
                }, index * 100);
            }
        });
    }

    function animateNumber($element, start, end, duration) {
        var range = end - start;
        var startTime = null;
        
        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = Math.min((timestamp - startTime) / duration, 1);
            var current = Math.floor(progress * range + start);
            
            $element.text(current.toLocaleString('ar-SA'));
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                $element.text(end.toLocaleString('ar-SA'));
            }
        }
        
        window.requestAnimationFrame(step);
    }

    // ========================================
    // Occupancy Gauge
    // ========================================
    function initOccupancyGauge() {
        var $gauge = $('.occupancy-gauge');
        if ($gauge.length === 0) return;
        
        var percentage = parseFloat($gauge.data('percentage')) || 0;
        var $circle = $gauge.find('.progress-circle');
        
        if ($circle.length === 0) return;
        
        var circumference = 2 * Math.PI * 70; // radius = 70
        var offset = circumference - (percentage / 100) * circumference;
        
        $circle.css({
            'stroke-dasharray': circumference,
            'stroke-dashoffset': circumference
        });
        
        setTimeout(function() {
            $circle.css('stroke-dashoffset', offset);
        }, 100);
        
        // Update color based on percentage
        if (percentage >= 80) {
            $circle.css('stroke', '#198754'); // success
        } else if (percentage >= 50) {
            $circle.css('stroke', '#ffc107'); // warning
        } else {
            $circle.css('stroke', '#dc3545'); // danger
        }
    }

    // ========================================
    // Revenue Chart
    // ========================================
    function loadRevenueChart() {
        var ctx = document.getElementById('revenueChart');
        if (!ctx) return;
        
        var revenueData = window.revenueData || {
            labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
            values: [150000, 180000, 165000, 195000, 210000, 225000]
        };
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: revenueData.labels,
                datasets: [{
                    label: 'الإيرادات الشهرية',
                    data: revenueData.values,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                family: 'Cairo',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toLocaleString('ar-SA') + ' ريال';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString('ar-SA');
                            }
                        }
                    }
                }
            }
        });
    }

    // ========================================
    // Occupancy Chart
    // ========================================
    function loadOccupancyChart() {
        var ctx = document.getElementById('occupancyChart');
        if (!ctx) return;
        
        var occupancyData = window.occupancyData || {
            labels: ['مؤجرة', 'متاحة', 'صيانة', 'مجمدة'],
            values: [75, 20, 3, 2],
            colors: ['#198754', '#0d6efd', '#ffc107', '#6c757d']
        };
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: occupancyData.labels,
                datasets: [{
                    data: occupancyData.values,
                    backgroundColor: occupancyData.colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                family: 'Cairo',
                                size: 12
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + ' وحدة';
                            }
                        }
                    }
                }
            }
        });
    }

    // ========================================
    // Load Statistics via AJAX
    // ========================================
    function loadStatistics() {
        // This would typically call an API endpoint
        // For now, statistics are loaded from the template
        // Example AJAX call:
        /*
        $.ajax({
            url: '/api/dashboard/stats/',
            method: 'GET',
            success: function(data) {
                updateStatistics(data);
            },
            error: function(xhr, status, error) {
                console.error('Failed to load statistics:', error);
            }
        });
        */
    }

    function updateStatistics(data) {
        // Update statistics cards with new data
        if (data.total_contracts) {
            $('.stat-contracts h2').text(data.total_contracts);
        }
        if (data.occupancy_rate) {
            $('.stat-occupancy h2').text(data.occupancy_rate.toFixed(1) + '%');
        }
        // ... update other statistics
    }

    // ========================================
    // Auto Refresh
    // ========================================
    function setupAutoRefresh() {
        // Refresh dashboard every 5 minutes
        var refreshInterval = 5 * 60 * 1000; // 5 minutes
        
        setInterval(function() {
            loadStatistics();
        }, refreshInterval);
    }

    // ========================================
    // Export Dashboard Data
    // ========================================
    window.exportDashboardReport = function() {
        RentalManagement.showLoading();
        
        $.ajax({
            url: '/api/dashboard/export/',
            method: 'GET',
            success: function(data) {
                // Create download link
                var blob = new Blob([data], { type: 'application/pdf' });
                var url = window.URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'dashboard-report-' + new Date().toISOString().split('T')[0] + '.pdf';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                RentalManagement.hideLoading();
                RentalManagement.showAlert('تم تصدير التقرير بنجاح', 'success');
            },
            error: function() {
                RentalManagement.hideLoading();
                RentalManagement.showAlert('فشل تصدير التقرير', 'danger');
            }
        });
    };

})(jQuery);