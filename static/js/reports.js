/**
 * Reports JavaScript - Final Fixed Version
 * نسخة نهائية بدون أخطاء
 */

'use strict';

console.log('✅ Reports.js loaded');

// ========================================
// Global Object
// ========================================

window.ReportsModule = {
    chart: null, // حفظ مرجع المخطط
    
    /**
     * تنسيق الأرقام
     */
    formatNumber(num) {
        return new Intl.NumberFormat('ar-SA', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    },

    /**
     * عرض رسالة
     */
    showAlert(message, type = 'success') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            if (alertDiv.parentElement) {
                alertDiv.remove();
            }
        }, 5000);
    },

    /**
     * تصدير إلى Excel باستخدام SheetJS
     */
    exportToExcel(tableId, filename = 'report') {
        const table = document.getElementById(tableId);
        if (!table) {
            console.error('Table not found:', tableId);
            this.showAlert('لم يتم العثور على الجدول', 'danger');
            return;
        }

        // التحقق من وجود مكتبة XLSX
        if (typeof XLSX === 'undefined') {
            console.warn('XLSX library not loaded, using fallback method');
            // استخدام الطريقة القديمة كبديل
            const html = table.outerHTML;
            const url = 'data:application/vnd.ms-excel;charset=utf-8,' + encodeURIComponent(html);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename + '.xls';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            this.showAlert('✅ تم تصدير التقرير بنجاح', 'success');
            return;
        }

        try {
            // إنشاء workbook من الجدول
            const wb = XLSX.utils.table_to_book(table, {
                sheet: 'التقرير',
                raw: true
            });

            // ضبط اتجاه RTL للعربية
            const ws = wb.Sheets['التقرير'];
            if (!ws['!cols']) ws['!cols'] = [];

            // تعديل عرض الأعمدة
            const range = XLSX.utils.decode_range(ws['!ref']);
            for (let i = 0; i <= range.e.c; i++) {
                ws['!cols'][i] = { wch: 20 }; // عرض 20 حرف
            }

            // تصدير الملف
            XLSX.writeFile(wb, filename + '.xlsx');

            this.showAlert('✅ تم تصدير التقرير بنجاح', 'success');
        } catch (error) {
            console.error('Excel export error:', error);
            this.showAlert('❌ خطأ في تصدير الملف: ' + error.message, 'danger');
        }
    },

    /**
     * تصدير إلى CSV
     */
    exportToCSV(tableId, filename = 'report') {
        const table = document.getElementById(tableId);
        if (!table) {
            console.error('Table not found:', tableId);
            this.showAlert('لم يتم العثور على الجدول', 'danger');
            return;
        }
        
        const rows = Array.from(table.querySelectorAll('tr'));
        const csv = rows.map(row => {
            const cols = Array.from(row.querySelectorAll('td, th'));
            return cols.map(col => {
                let data = col.innerText.trim().replace(/"/g, '""');
                return '"' + data + '"';
            }).join(',');
        }).join('\n');
        
        const BOM = '\uFEFF';
        const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.href = url;
        link.download = filename + '.csv';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
        
        this.showAlert('✅ تم تصدير التقرير بنجاح', 'success');
    },

    /**
     * تحريك الأرقام
     */
    animateValue(element, start, end, duration) {
        if (!element || isNaN(end)) return;
        
        const range = end - start;
        let startTime = null;
        
        const step = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const current = Math.floor(progress * range + start);
            
            element.textContent = current.toLocaleString('ar-SA');
            
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        
        requestAnimationFrame(step);
    },

    /**
     * تحريك ظهور العناصر
     */
    fadeInElements(selector, delay = 100) {
        const elements = document.querySelectorAll(selector);
        
        elements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * delay);
        });
    },

    /**
     * إنشاء مخطط الإيرادات
     */
    initRevenueChart() {
        console.log('🔍 Initializing revenue chart...');
        
        const canvas = document.getElementById('revenueChart');
        
        if (!canvas) {
            console.log('⚠️ Canvas #revenueChart not found');
            return;
        }
        
        console.log('✅ Canvas found');
        
        // التحقق من Chart.js
        if (typeof Chart === 'undefined') {
            console.error('❌ Chart.js is NOT loaded!');
            console.log('💡 Solution: Add Chart.js CDN before reports.js');
            this.showAlert('⚠️ مكتبة Chart.js غير محملة', 'warning');
            return;
        }
        
        console.log('✅ Chart.js loaded');
        
        // التحقق من البيانات
        if (!window.revenueChartData) {
            console.error('❌ window.revenueChartData is NOT defined');
            console.log('💡 Solution: Define window.revenueChartData before reports.js');
            return;
        }
        
        const chartData = window.revenueChartData;
        console.log('📊 Chart data:', chartData);
        
        if (!chartData.labels || chartData.labels.length === 0) {
            console.warn('⚠️ No chart data available (empty labels)');
            canvas.parentElement.innerHTML = '<p class="text-center text-muted p-5">لا توجد بيانات لعرضها</p>';
            return;
        }
        
        // مسح المخطط القديم إن وجد
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        const ctx = canvas.getContext('2d');
        
        // إنشاء المخطط
        try {
            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        label: 'الإيرادات الشهرية',
                        data: chartData.values,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            rtl: true,
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                family: 'Cairo, sans-serif',
                                size: 14
                            },
                            bodyFont: {
                                family: 'Cairo, sans-serif',
                                size: 13
                            },
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
                                },
                                font: {
                                    family: 'Cairo, sans-serif'
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: {
                                    family: 'Cairo, sans-serif'
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
            
            console.log('✅ Chart created successfully!');
            
        } catch (error) {
            console.error('❌ Error creating chart:', error);
            this.showAlert('❌ خطأ في إنشاء المخطط: ' + error.message, 'danger');
        }
    },

    /**
     * إنشاء مخطط الإشغال (Doughnut Chart)
     */
    initOccupancyChart() {
        console.log('🔍 Initializing occupancy chart...');

        const canvas = document.getElementById('occupancyChart');

        if (!canvas) {
            console.log('⚠️ Canvas #occupancyChart not found');
            return;
        }

        console.log('✅ Canvas found');

        // التحقق من Chart.js
        if (typeof Chart === 'undefined') {
            console.error('❌ Chart.js is NOT loaded!');
            console.log('💡 Solution: Add Chart.js CDN before reports.js');
            this.showAlert('⚠️ مكتبة Chart.js غير محملة', 'warning');
            return;
        }

        console.log('✅ Chart.js loaded');

        // التحقق من البيانات
        if (!window.occupancyChartData) {
            console.error('❌ window.occupancyChartData is NOT defined');
            console.log('💡 Solution: Define window.occupancyChartData before reports.js');
            return;
        }

        const chartData = window.occupancyChartData;
        console.log('📊 Chart data:', chartData);

        if (!chartData.labels || chartData.labels.length === 0) {
            console.warn('⚠️ No chart data available (empty labels)');
            canvas.parentElement.innerHTML = '<p class="text-center text-muted p-5">لا توجد بيانات لعرضها</p>';
            return;
        }

        // مسح المخطط القديم إن وجد
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        const ctx = canvas.getContext('2d');

        // ألوان المخطط
        const colors = [
            '#198754', // أخضر للمؤجرة
            '#0dcaf0', // أزرق للمتاحة
            '#ffc107', // أصفر للصيانة
            '#6c757d'  // رمادي للمجمدة
        ];

        // إنشاء المخطط
        try {
            this.chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        data: chartData.values,
                        backgroundColor: colors,
                        borderColor: '#fff',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            rtl: true,
                            labels: {
                                font: {
                                    family: 'Cairo, sans-serif',
                                    size: 13
                                },
                                padding: 15,
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            rtl: true,
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                family: 'Cairo, sans-serif',
                                size: 14
                            },
                            bodyFont: {
                                family: 'Cairo, sans-serif',
                                size: 13
                            },
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} وحدة (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });

            console.log('✅ Occupancy chart created successfully!');

        } catch (error) {
            console.error('❌ Error creating chart:', error);
            this.showAlert('❌ خطأ في إنشاء المخطط: ' + error.message, 'danger');
        }
    },

    /**
     * تحريك الأرقام في البطاقات
     */
    animateNumbers() {
        const numbers = document.querySelectorAll('.report-stats .fw-bold.fs-3');

        numbers.forEach(element => {
            const text = element.textContent.trim();
            const value = parseFloat(text.replace(/[^0-9.-]+/g, ''));

            if (!isNaN(value) && value > 0) {
                element.textContent = '0';
                this.animateValue(element, 0, value, 1000);
            }
        });
    },

    /**
     * تحريك أشرطة التقدم في بطاقات المباني
     */
    animateBuildingCards() {
        const buildingCards = document.querySelectorAll('.building-stat-card');

        buildingCards.forEach((card, index) => {
            const rate = parseFloat(card.dataset.occupancyRate) || 0;
            const progressBar = card.querySelector('.progress-bar');

            if (progressBar) {
                // تحديد اللون بناءً على النسبة
                let colorClass = 'bg-danger';
                if (rate >= 80) {
                    colorClass = 'bg-success';
                } else if (rate >= 50) {
                    colorClass = 'bg-warning';
                }

                progressBar.classList.add(colorClass);

                // تأخير الحركة لكل بطاقة
                setTimeout(() => {
                    progressBar.style.transition = 'width 1s ease';
                    progressBar.style.width = rate + '%';
                }, index * 100);
            }
        });
    },

    /**
     * تهيئة التقرير
     */
    init() {
        console.log('🚀 Initializing reports...');

        // تحريك البطاقات
        this.fadeInElements('.report-stats .card', 100);
        this.fadeInElements('.report-table tbody tr', 50);

        // تحريك الأرقام
        this.animateNumbers();

        // تحريك أشرطة التقدم في بطاقات المباني
        this.animateBuildingCards();

        // إنشاء المخططات (مع تأخير للتأكد من تحميل كل شيء)
        setTimeout(() => {
            // مخطط الإيرادات
            if (document.getElementById('revenueChart')) {
                this.initRevenueChart();
            }

            // مخطط الإشغال
            if (document.getElementById('occupancyChart')) {
                this.initOccupancyChart();
            }
        }, 300);

        console.log('✅ Reports initialized');
    }
};

// ========================================
// Global Shortcuts
// ========================================

window.exportToExcel = function(tableId, filename) {
    window.ReportsModule.exportToExcel(tableId, filename);
};

window.exportToCSV = function(tableId, filename) {
    window.ReportsModule.exportToCSV(tableId, filename);
};

// للتوافق مع الأكواد القديمة
window.ReportUtils = window.ReportsModule;
window.ChartManager = window.ReportsModule;
window.ExportUtils = window.ReportsModule;

// ========================================
// Auto-Initialize
// ========================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        window.ReportsModule.init();
    });
} else {
    // إذا كان الصفحة محملة بالفعل
    window.ReportsModule.init();
}

console.log('📊 Reports module ready');