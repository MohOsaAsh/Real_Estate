/**
 * Notifications JavaScript
 */

(function($) {
    'use strict';

    $(document).ready(function() {
        // Initialize notifications
        initNotifications();
        
        // Auto-refresh notifications
        setupAutoRefresh();
        
        // Load notification count
        updateNotificationCount();
    });

    // ========================================
    // Initialize Notifications
    // ========================================
    function initNotifications() {
        // Animate notification items
        $('.notification-item').each(function(index) {
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
            }, index * 100);
        });
        
        // Setup click handlers
        setupClickHandlers();
    }

    function setupClickHandlers() {
        // Click on notification to mark as read
        $('.notification-item.unread').on('click', function(e) {
            if (!$(e.target).closest('.btn').length) {
                var notificationId = $(this).data('notification-id');
                markAsRead(notificationId);
            }
        });
    }

    // ========================================
    // Mark as Read
    // ========================================
    window.markAsRead = function(notificationId) {
        $.ajax({
            url: `/notifications/${notificationId}/mark-read/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                // Update UI
                var $notification = $(`.notification-item[data-notification-id="${notificationId}"]`);
                $notification.removeClass('unread');
                $notification.find('.notification-actions-menu .btn:first').remove();
                
                // Update count
                updateNotificationCount();
                
                // Show success message
                showToast('تم تحديد الإشعار كمقروء', 'success');
            },
            error: function() {
                showToast('فشل تحديث الإشعار', 'danger');
            }
        });
    };

    // ========================================
    // Mark All as Read
    // ========================================
    window.markAllAsRead = function() {
        if (!confirm('هل تريد تحديد جميع الإشعارات كمقروءة؟')) {
            return;
        }
        
        RentalManagement.showLoading();
        
        var notificationIds = [];
        $('.notification-item.unread').each(function() {
            notificationIds.push($(this).data('notification-id'));
        });
        
        if (notificationIds.length === 0) {
            RentalManagement.hideLoading();
            showToast('لا توجد إشعارات غير مقروءة', 'info');
            return;
        }
        
        // Mark all as read
        var promises = notificationIds.map(function(id) {
            return $.ajax({
                url: `/notifications/${id}/mark-read/`,
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
        });
        
        Promise.all(promises).then(function() {
            RentalManagement.hideLoading();
            location.reload();
        }).catch(function() {
            RentalManagement.hideLoading();
            showToast('فشل تحديث بعض الإشعارات', 'danger');
        });
    };

    // ========================================
    // Delete Notification
    // ========================================
    window.deleteNotification = function(notificationId) {
        if (!confirm('هل تريد حذف هذا الإشعار؟')) {
            return;
        }
        
        $.ajax({
            url: `/notifications/${notificationId}/delete/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function() {
                // Remove from UI
                var $notification = $(`.notification-item[data-notification-id="${notificationId}"]`);
                $notification.fadeOut(300, function() {
                    $(this).remove();
                    
                    // Check if empty
                    if ($('.notification-item').length === 0) {
                        location.reload();
                    }
                });
                
                // Update count
                updateNotificationCount();
                
                showToast('تم حذف الإشعار', 'success');
            },
            error: function() {
                showToast('فشل حذف الإشعار', 'danger');
            }
        });
    };

    // ========================================
    // Update Notification Count
    // ========================================
    function updateNotificationCount() {
        $.ajax({
            url: '/api/notifications/count/',
            method: 'GET',
            success: function(data) {
                var count = data.unread_count || 0;
                var $badge = $('#notification-count');
                
                if (count > 0) {
                    $badge.text(count).show();
                } else {
                    $badge.hide();
                }
                
                // Update page title
                if (count > 0) {
                    document.title = `(${count}) ${document.title.replace(/^\(\d+\) /, '')}`;
                }
            }
        });
    }

    // ========================================
    // Auto Refresh
    // ========================================
    function setupAutoRefresh() {
        // Refresh every 30 seconds
        setInterval(function() {
            updateNotificationCount();
            checkNewNotifications();
        }, 30000);
    }

    function checkNewNotifications() {
        $.ajax({
            url: '/api/notifications/latest/',
            method: 'GET',
            success: function(data) {
                if (data.notifications && data.notifications.length > 0) {
                    data.notifications.forEach(function(notification) {
                        showNotificationToast(notification);
                    });
                }
            }
        });
    }

    function showNotificationToast(notification) {
        var iconClass = getNotificationIcon(notification.type);
        var colorClass = getNotificationColor(notification.priority);
        
        var toastHtml = `
            <div class="toast-notification ${colorClass}">
                <div class="toast-header">
                    <i class="${iconClass} me-2"></i>
                    <strong class="me-auto">${notification.title}</strong>
                    <small>${notification.time}</small>
                    <button type="button" class="btn-close" onclick="closeToast(this)"></button>
                </div>
                <div class="toast-body">
                    ${notification.message}
                </div>
            </div>
        `;
        
        $('body').append(toastHtml);
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            $('.toast-notification').last().addClass('hiding');
            setTimeout(function() {
                $('.toast-notification').last().remove();
            }, 300);
        }, 5000);
        
        // Play notification sound (optional)
        playNotificationSound();
    }

    function getNotificationIcon(type) {
        var icons = {
            'contract_expiry': 'fas fa-calendar-times',
            'payment_due': 'fas fa-money-bill-wave',
            'payment_overdue': 'fas fa-exclamation-triangle',
            'contract_renewal': 'fas fa-sync-alt',
            'system': 'fas fa-bell'
        };
        return icons[type] || 'fas fa-bell';
    }

    function getNotificationColor(priority) {
        var colors = {
            'urgent': 'bg-danger',
            'high': 'bg-warning',
            'medium': 'bg-info',
            'low': 'bg-secondary'
        };
        return colors[priority] || 'bg-info';
    }

    function playNotificationSound() {
        // Optional: Play notification sound
        // var audio = new Audio('/static/sounds/notification.mp3');
        // audio.play();
    }

    // ========================================
    // Toast Messages
    // ========================================
    function showToast(message, type) {
        var toastHtml = `
            <div class="toast-notification bg-${type}">
                <div class="toast-body text-white">
                    ${message}
                </div>
            </div>
        `;
        
        $('body').append(toastHtml);
        
        setTimeout(function() {
            $('.toast-notification').last().addClass('hiding');
            setTimeout(function() {
                $('.toast-notification').last().remove();
            }, 300);
        }, 3000);
    }

    window.closeToast = function(button) {
        $(button).closest('.toast-notification').addClass('hiding');
        setTimeout(function() {
            $(button).closest('.toast-notification').remove();
        }, 300);
    };

    // ========================================
    // Helper Functions
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

    // ========================================
    // Export Functions
    // ========================================
    window.NotificationManager = {
        updateCount: updateNotificationCount,
        
        checkNew: checkNewNotifications,
        
        showToast: showToast,
        
        requestPermission: function() {
            if ('Notification' in window) {
                Notification.requestPermission().then(function(permission) {
                    if (permission === 'granted') {
                        showToast('تم تفعيل إشعارات المتصفح', 'success');
                    }
                });
            }
        },
        
        sendBrowserNotification: function(title, message) {
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(title, {
                    body: message,
                    icon: '/static/img/logo.png',
                    badge: '/static/img/logo.png'
                });
            }
        }
    };

})(jQuery);