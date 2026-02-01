# ====================================
# 7. audit_log/admin.py
# ====================================

from django.contrib import admin
from django.utils.html import format_html
from .models import AuditLog
import json

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'colored_action', 'user_name', 'model_name', 'short_object_repr', 'ip_address', 'formatted_created_at']
    list_filter = ['action', 'model_name', 'created_at', 'user']
    search_fields = ['user_name', 'model_name', 'object_repr', 'ip_address', 'request_path']
    readonly_fields = ['user', 'user_name', 'action', 'content_type', 'object_id', 'model_name', 'object_repr',
                      'formatted_old_values', 'formatted_new_values', 'formatted_changes',
                      'request_path', 'request_method', 'ip_address', 'user_agent', 'created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    def colored_action(self, obj):
        colors = {'create': '#28a745', 'update': '#ffc107', 'delete': '#dc3545', 
                 'login': '#17a2b8', 'logout': '#6c757d', 'login_failed': '#e83e8c'}
        color = colors.get(obj.action, '#000000')
        return format_html('<span style="color: {}; font-weight: bold; padding: 3px 8px; border-radius: 3px; background: {}20;">{}</span>',
                          color, color, obj.get_action_display())
    colored_action.short_description = 'العملية'
    
    def short_object_repr(self, obj):
        if obj.object_repr:
            return obj.object_repr[:50] + '...' if len(obj.object_repr) > 50 else obj.object_repr
        return '-'
    short_object_repr.short_description = 'الكائن'
    
    def formatted_created_at(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    formatted_created_at.short_description = 'التاريخ'
    
    def formatted_old_values(self, obj):
        if obj.old_values:
            formatted = json.dumps(obj.old_values, indent=2, ensure_ascii=False)
            return format_html('<pre style="direction: ltr; text-align: left;">{}</pre>', formatted)
        return '-'
    formatted_old_values.short_description = 'القيم القديمة'
    
    def formatted_new_values(self, obj):
        if obj.new_values:
            formatted = json.dumps(obj.new_values, indent=2, ensure_ascii=False)
            return format_html('<pre style="direction: ltr; text-align: left;">{}</pre>', formatted)
        return '-'
    formatted_new_values.short_description = 'القيم الجديدة'
    
    def formatted_changes(self, obj):
        if obj.changes:
            formatted = json.dumps(obj.changes, indent=2, ensure_ascii=False)
            return format_html('<pre style="direction: ltr; text-align: left; background: #fff3cd; padding: 10px;">{}</pre>', formatted)
        return '-'
    formatted_changes.short_description = 'التغييرات'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    fieldsets = (
        ('معلومات المستخدم', {'fields': ('user', 'user_name', 'ip_address', 'user_agent')}),
        ('معلومات العملية', {'fields': ('action', 'model_name', 'content_type', 'object_id', 'object_repr', 'created_at')}),
        ('معلومات الطلب', {'fields': ('request_method', 'request_path')}),
        ('البيانات', {'fields': ('formatted_changes', 'formatted_old_values', 'formatted_new_values'), 'classes': ('collapse',)}),
    )
