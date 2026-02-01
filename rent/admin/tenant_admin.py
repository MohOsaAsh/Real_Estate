"""
Tenant Admin
إدارة المستأجرين ومستنداتهم
"""

from .common_imports_admin import (
    admin,
    Tenant, TenantDocument,
    TenantForm,
    BaseModelAdmin, BaseTabularInline,
    SYSTEM_INFO_FIELDSET, NOTES_FIELDSET,
)


# ========================================
# Tenant Admin
# ========================================

class TenantDocumentInline(BaseTabularInline):
    """Inline لمستندات المستأجر"""
    model = TenantDocument
    fields = ('document_type', 'title', 'file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Tenant)
class TenantAdmin(BaseModelAdmin):
    """إدارة المستأجرين"""
    
    form = TenantForm  # استخدام النموذج المخصص
    
    list_display = (
        'name', 'tenant_type', 'id_number', 'phone', 
        'email', 'is_blacklisted', 'is_active'
    )
    
    list_filter = (
        'tenant_type', 'is_active', 
        'is_blacklisted', 'has_authorization'
    )
    
    search_fields = (
        'name', 'id_number', 'phone', 'email'
    )
    
    fieldsets = (
        ('معلومات المستأجر', {
            'fields': (
                'tenant_type', 'name', 
                'phone', 'email'
            )
        }),
        ('الهوية', {
            'fields': ('id_number',)
        }),
        ('بيانات الشركة', {
            'fields': ('company_name',),
            'description': 'مطلوب للمستأجرين من نوع شركة'
        }),
        ('بيانات الوكالة', {
            'fields': (
                'has_authorization', 'authorization_number', 
                'authorization_date'
            ),
            'classes': ('collapse',)
        }),
        ('العنوان', {
            'fields': ('address',)
        }),
        ('الحالة', {
            'fields': ('is_active', 'is_blacklisted')
        }),
        NOTES_FIELDSET,
        SYSTEM_INFO_FIELDSET,
    )
    
    inlines = [TenantDocumentInline]


# ========================================
# TenantDocument Admin
# ========================================

@admin.register(TenantDocument)
class TenantDocumentAdmin(BaseModelAdmin):
    """إدارة مستندات المستأجرين"""
    
    list_display = (
        'tenant', 'document_type', 'title', 'uploaded_at'
    )
    
    list_filter = ('document_type', 'uploaded_at')
    
    search_fields = ('tenant__name', 'title')
    
    readonly_fields = ('uploaded_by', 'uploaded_at')
    
    fieldsets = (
        ('معلومات المستند', {
            'fields': ('tenant', 'document_type', 'title', 'file')
        }),
        ('معلومات النظام', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """حفظ المستند مع تسجيل المستخدم الرافع"""
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)