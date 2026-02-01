from .common_imports_view import *

# ========================================
# 12. إدارة الإشعارات (Views كاملة)
# ========================================

class NotificationListView(LoginRequiredMixin, ListView):
    """قائمة الإشعارات"""
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Notification.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        ).order_by('-created_at')
        
        # الفلترة حسب النوع
        notification_type = self.request.GET.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # الفلترة حسب الحالة
        is_read = self.request.GET.get('is_read')
        if is_read == 'true':
            queryset = queryset.filter(is_read=True)
        elif is_read == 'false':
            queryset = queryset.filter(is_read=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True),
            is_read=False
        ).count()
        return context


class NotificationMarkReadView(LoginRequiredMixin,  DetailView):
    """تحديد الإشعار كمقروء"""
    model = Notification
    
    def post(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.mark_as_read()
        
        self.log_action('modify', notification, description='تحديد الإشعار كمقروء')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'تم تحديد الإشعار كمقروء')
        return redirect('rental:notification_list')