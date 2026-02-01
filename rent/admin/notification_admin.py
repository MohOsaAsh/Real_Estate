"""
Notification Admin
إدارة الإشعارات
"""

from .common_imports_admin import (
    admin,
    Notification,
    BaseModelAdmin,
    create_model_link,
)


# ========================================
# Notification Admin
# ========================================

@admin.register(Notification)
class NotificationAdmin(BaseModelAdmin):
    """إدارة الإشعارات"""
    
    list_display = (
        'title', 'notification_type', 'priority', 
        'contract_link', 'tenant_link', 
        'is_read', 'is_sent', 'due_date', 'created_at'
    )
    
    list_filter = (
        'notification_type', 'priority', 
        'is_read', 'is_sent', 'is_dismissed', 'created_at'
    )
    
    search_fields = (
        'title', 'message', 
        'contract__contract_number', 'tenant__name'
    )
    
    readonly_fields = (
        'created_at', 'sent_at', 'read_at', 'dismissed_at'
    )
    
    fieldsets = (
        ('معلومات الإشعار', {
            'fields': (
                'notification_type', 'title', 
                'message', 'priority'
            )
        }),
        ('الروابط', {
            'fields': ('contract', 'tenant', 'user'),
            'classes': ('collapse',)
        }),
        ('الإجراء', {
            'fields': ('action_url', 'metadata'),
            'classes': ('collapse',)
        }),
        ('حالة الإشعار', {
            'fields': (
                'is_read', 'is_sent', 'is_dismissed', 
                'due_date'
            )
        }),
        ('تواريخ', {
            'fields': (
                'sent_at', 'read_at', 
                'dismissed_at', 'created_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_sent']
    
    def contract_link(self, obj):
        """رابط العقد"""
        if obj.contract:
            return create_model_link(
                'contract', 
                obj.contract.id, 
                obj.contract.contract_number
            )
        return "-"
    contract_link.short_description = 'العقد'
    
    def tenant_link(self, obj):
        """رابط المستأجر"""
        if obj.tenant:
            return create_model_link(
                'tenant', 
                obj.tenant.id, 
                obj.tenant.name
            )
        return "-"
    tenant_link.short_description = 'المستأجر'
    
    def mark_as_read(self, request, queryset):
        """تحديد الإشعارات كمقروءة"""
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(
            request, 
            f'تم تحديد {queryset.count()} إشعار كمقروء'
        )
    mark_as_read.short_description = 'تحديد كمقروء'
    
    def mark_as_sent(self, request, queryset):
        """تحديد الإشعارات كمُرسلة"""
        for notification in queryset:
            notification.mark_as_sent()
        self.message_user(
            request, 
            f'تم تحديد {queryset.count()} إشعار كمُرسل'
        )
    mark_as_sent.short_description = 'تحديد كمُرسل'