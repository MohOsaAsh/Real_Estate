"""
Task Admin
إدارة المهام المجدولة والتنفيذات
"""

from .common_imports_admin import (
    admin,
    ScheduledTask, TaskExecution, TaskLog,
    BaseModelAdmin, BaseTabularInline,
)


# ========================================
# ScheduledTask Admin
# ========================================

class TaskExecutionInline(BaseTabularInline):
    """Inline لتنفيذات المهمة"""
    model = TaskExecution
    can_delete = False
    fields = ('started_at', 'finished_at', 'duration', 'status')
    readonly_fields = ('started_at', 'finished_at', 'duration', 'status')


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(BaseModelAdmin):
    """إدارة المهام المجدولة"""
    
    list_display = (
        'name', 'task_type', 'frequency', 
        'is_active', 'last_run', 'next_run', 'success_rate'
    )
    
    list_filter = ('task_type', 'frequency', 'is_active')
    
    search_fields = ('name', 'task_function')
    
    readonly_fields = (
        'last_run', 'next_run', 'last_status', 
        'success_count', 'failure_count', 
        'total_run_time', 'average_run_time',
        'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('معلومات المهمة', {
            'fields': ('name', 'task_type', 'frequency')
        }),
        ('إعدادات التنفيذ', {
            'fields': (
                'execution_time', 'day_of_week', 
                'day_of_month', 'month_of_year'
            )
        }),
        ('تفاصيل المهمة', {
            'fields': ('task_function', 'task_parameters')
        }),
        ('حالة المهمة', {
            'fields': (
                'is_active', 'last_run', 
                'next_run', 'last_status'
            )
        }),
        ('إحصائيات', {
            'fields': (
                'success_count', 'failure_count', 
                'total_run_time', 'average_run_time'
            ),
            'classes': ('collapse',)
        }),
        ('ملاحظات', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaskExecutionInline]
    
    def success_rate(self, obj):
        """حساب نسبة النجاح"""
        total = obj.success_count + obj.failure_count
        if total > 0:
            rate = (obj.success_count / total) * 100
            return f"{rate:.1f}%"
        return "0%"
    success_rate.short_description = 'نسبة النجاح'


# ========================================
# TaskExecution Admin
# ========================================

@admin.register(TaskExecution)
class TaskExecutionAdmin(BaseModelAdmin):
    """إدارة تنفيذات المهام"""
    
    list_display = (
        'task', 'started_at', 'finished_at', 
        'duration', 'status'
    )
    
    list_filter = ('status', 'started_at')
    
    search_fields = ('task__name', 'result', 'error_message')
    
    readonly_fields = (
        'started_at', 'finished_at', 'duration', 
        'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('معلومات التنفيذ', {
            'fields': (
                'task', 'started_at', 
                'finished_at', 'duration', 'status'
            )
        }),
        ('النتائج', {
            'fields': ('result', 'output')
        }),
        ('الأخطاء', {
            'fields': ('error_message', 'traceback'),
            'classes': ('collapse',)
        }),
    )


# ========================================
# TaskLog Admin
# ========================================

@admin.register(TaskLog)
class TaskLogAdmin(BaseModelAdmin):
    """إدارة سجلات المهام"""
    
    list_display = (
        'task', 'level', 'message_short', 
        'execution', 'created_at'
    )
    
    list_filter = ('level', 'created_at')
    
    search_fields = ('task__name', 'message')
    
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('معلومات السجل', {
            'fields': ('task', 'execution', 'level')
        }),
        ('الرسالة', {
            'fields': ('message', 'details')
        }),
        ('التاريخ', {
            'fields': ('created_at',)
        }),
    )
    
    def message_short(self, obj):
        """اختصار الرسالة"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'الرسالة'