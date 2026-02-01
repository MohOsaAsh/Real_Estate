"""
System Admin
إدارة النظام (السجلات، القوالب، الإعدادات)
"""

from .common_imports_admin import (
    admin,
    ReportTemplate, 
    BaseModelAdmin,
)



# ========================================
# ReportTemplate Admin
# ========================================

@admin.register(ReportTemplate)
class ReportTemplateAdmin(BaseModelAdmin):
    """إدارة قوالب التقارير"""
    
    list_display = (
        'name', 'report_type', 'is_active', 
        'created_by', 'created_at'
    )
    
    list_filter = ('report_type', 'is_active')
    
    search_fields = ('name', 'description')
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('معلومات القالب', {
            'fields': ('name', 'report_type', 'description')
        }),
        ('إعدادات التقرير', {
            'fields': ('filters', 'columns', 'sort_by', 'group_by')
        }),
        ('حالة القالب', {
            'fields': ('is_active',)
        }),
        ('معلومات النظام', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


# ========================================
# SystemSetting Admin
# ========================================

