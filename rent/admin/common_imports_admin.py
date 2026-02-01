"""
Common Imports for Admin
الاستيرادات المشتركة لجميع ملفات الـ Admin
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Q
from django.contrib import messages
from datetime import date, timedelta

# استيراد النماذج
from rent.models import (
    # User & Profile
    UserProfile,
    
    # Properties
    Land, Building, Unit,
    
    # Tenants
    Tenant, TenantDocument,
    
    # Contracts
    Contract, ContractModification,
    
    # Payments
    Receipt,
    
    # Notifications
    Notification,
    
    # System
     ReportTemplate, 
    
    # Backup & Tasks
    Backup, BackupSchedule,
    ScheduledTask, TaskExecution, TaskLog,
)

# استيراد Forms
from ..forms import TenantForm


# ========================================
# Base Admin Classes
# ========================================

class BaseModelAdmin(admin.ModelAdmin):
    """
    Admin أساسي لجميع النماذج
    يوفر وظائف مشتركة
    """
    
    def save_model(self, request, obj, form, change):
        """حفظ النموذج مع تسجيل المستخدم المنشئ"""
        if not change and hasattr(obj, 'created_by') and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """جعل حقول النظام للقراءة فقط"""
        readonly = list(super().get_readonly_fields(request, obj))
        
        system_fields = ['created_by', 'created_at', 'updated_at', 'uploaded_by', 'uploaded_at']
        for field in system_fields:
            if hasattr(self.model, field) and field not in readonly:
                readonly.append(field)
        
        return readonly


class BaseTabularInline(admin.TabularInline):
    """Inline أساسي للعرض الجدولي"""
    extra = 0
    can_delete = True
    show_change_link = True


class BaseStackedInline(admin.StackedInline):
    """Inline أساسي للعرض المكدس"""
    extra = 0
    can_delete = True
    show_change_link = True


# ========================================
# Common Helper Functions
# ========================================

def create_link(url, text, new_tab=False):
    """إنشاء رابط HTML"""
    target = ' target="_blank"' if new_tab else ''
    return format_html('<a href="{}"{}>{}</a>', url, target, text)


def create_model_link(model_name, object_id, display_text):
    """إنشاء رابط لنموذج في الـ Admin"""
    url = reverse(f'admin:rent_{model_name}_change', args=[object_id])
    return create_link(url, display_text)


def format_currency(amount):
    """تنسيق المبلغ المالي"""
    return f"{amount:,.2f} ريال" if amount is not None else "-"


def format_percentage(value):
    """تنسيق النسبة المئوية"""
    return f"{value:.1f}%" if value is not None else "-"


# ========================================
# Common List Filters
# ========================================

class ActiveFilter(admin.SimpleListFilter):
    """فلتر الحالة النشطة"""
    title = 'الحالة'
    parameter_name = 'is_active'
    
    def lookups(self, request, model_admin):
        return (
            ('1', 'نشط'),
            ('0', 'غير نشط'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(is_active=True)
        if self.value() == '0':
            return queryset.filter(is_active=False)
        return queryset


class DeletedFilter(admin.SimpleListFilter):
    """فلتر المحذوفات"""
    title = 'المحذوفات'
    parameter_name = 'is_deleted'
    
    def lookups(self, request, model_admin):
        return (
            ('0', 'موجود'),
            ('1', 'محذوف'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(is_deleted=True)
        if self.value() == '0':
            return queryset.filter(is_deleted=False)
        return queryset.filter(is_deleted=False)  # افتراضي: إخفاء المحذوفات


class DateRangeFilter(admin.SimpleListFilter):
    """فلتر نطاق التواريخ"""
    title = 'الفترة'
    parameter_name = 'date_range'
    date_field = 'created_at'  # يمكن تخصيصه في الفئات الفرعية
    
    def lookups(self, request, model_admin):
        return (
            ('today', 'اليوم'),
            ('week', 'هذا الأسبوع'),
            ('month', 'هذا الشهر'),
            ('quarter', 'هذا الربع'),
            ('year', 'هذا العام'),
        )
    
    def queryset(self, request, queryset):
        today = date.today()
        
        if self.value() == 'today':
            return queryset.filter(**{f'{self.date_field}__date': today})
        
        elif self.value() == 'week':
            start = today - timedelta(days=today.weekday())
            return queryset.filter(**{f'{self.date_field}__gte': start})
        
        elif self.value() == 'month':
            return queryset.filter(
                **{
                    f'{self.date_field}__year': today.year,
                    f'{self.date_field}__month': today.month
                }
            )
        
        elif self.value() == 'quarter':
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            return queryset.filter(
                **{
                    f'{self.date_field}__year': today.year,
                    f'{self.date_field}__month__gte': start_month,
                    f'{self.date_field}__month__lt': start_month + 3
                }
            )
        
        elif self.value() == 'year':
            return queryset.filter(**{f'{self.date_field}__year': today.year})
        
        return queryset


# ========================================
# Common Fieldsets
# ========================================

SYSTEM_INFO_FIELDSET = (
    'معلومات النظام', {
        'fields': ('created_by', 'created_at', 'updated_at'),
        'classes': ('collapse',)
    }
)

NOTES_FIELDSET = (
    'ملاحظات', {
        'fields': ('notes',),
        'classes': ('collapse',)
    }
)

STATUS_FIELDSET = lambda field='is_active': (
    'الحالة', {
        'fields': (field,)
    }
)