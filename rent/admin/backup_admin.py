"""
Backup Admin
إدارة النسخ الاحتياطي والجداول
"""

from .common_imports_admin import (
    admin,
    Backup, BackupSchedule,
    BaseModelAdmin,
    SYSTEM_INFO_FIELDSET, NOTES_FIELDSET,
)


# ========================================
# Backup Admin
# ========================================

@admin.register(Backup)
class BackupAdmin(BaseModelAdmin):
    """إدارة النسخ الاحتياطية"""
    
    list_display = (
        'file_name', 'backup_type', 'file_size_display', 
        'tables_count', 'records_count', 'status', 
        'is_successful', 'created_at'
    )
    
    list_filter = (
        'backup_type', 'status', 'is_successful', 'created_at'
    )
    
    search_fields = ('file_name', 'file_path')
    
    readonly_fields = (
        'file_size', 'duration', 'checksum'
    )
    
    fieldsets = (
        ('معلومات النسخة', {
            'fields': (
                'backup_type', 'file_name', 
                'file_path', 'file_size'
            )
        }),
        ('المحتوى', {
            'fields': (
                'tables_count', 'records_count', 'included_tables'
            ),
            'classes': ('collapse',)
        }),
        ('التوقيت', {
            'fields': ('started_at', 'completed_at', 'duration')
        }),
        ('التحقق', {
            'fields': ('is_verified', 'verified_at', 'checksum'),
            'classes': ('collapse',)
        }),
        ('حالة النسخة', {
            'fields': (
                'status', 'is_successful', 'error_message'
            )
        }),
        ('الأرشفة', {
            'fields': ('expires_at', 'is_archived'),
            'classes': ('collapse',)
        }),
        ('معلومات إضافية', {
            'fields': ('notes', 'metadata'),
            'classes': ('collapse',)
        }),
        SYSTEM_INFO_FIELDSET,
    )
    
    def file_size_display(self, obj):
        """عرض حجم الملف منسق"""
        return obj.get_file_size_display()
    file_size_display.short_description = 'الحجم'


# ========================================
# BackupSchedule Admin
# ========================================

@admin.register(BackupSchedule)
class BackupScheduleAdmin(BaseModelAdmin):
    """إدارة جداول النسخ الاحتياطي"""
    
    list_display = (
        'name', 'backup_type', 'frequency', 
        'is_active', 'last_run', 'next_run'
    )
    
    list_filter = ('backup_type', 'frequency', 'is_active')
    
    search_fields = ('name', 'storage_path')
    
    readonly_fields = (
        'last_run', 'next_run'
    )
    
    fieldsets = (
        ('معلومات الجدول', {
            'fields': ('name', 'backup_type', 'frequency')
        }),
        ('التوقيت', {
            'fields': (
                'execution_time', 'day_of_week', 
                'day_of_month'
            )
        }),
        ('المحتوى', {
            'fields': (
                'include_all_tables', 
                'included_tables', 'excluded_tables'
            ),
            'classes': ('collapse',)
        }),
        ('التخزين', {
            'fields': (
                'storage_path', 'retention_days', 
                'max_backups_to_keep', 'compress_backup'
            )
        }),
        ('الحالة', {
            'fields': (
                'is_active', 'last_run', 
                'next_run', 'last_backup'
            )
        }),
        ('الإشعارات', {
            'fields': (
                'notify_on_success', 'notify_on_failure', 
                'notification_emails'
            ),
            'classes': ('collapse',)
        }),
        NOTES_FIELDSET,
        SYSTEM_INFO_FIELDSET,
    )