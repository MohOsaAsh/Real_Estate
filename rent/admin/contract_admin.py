"""
Contract Admin
إدارة العقود وتعديلاتها
"""

from .common_imports_admin import (
    admin, format_html, reverse, messages,
    Contract, ContractModification, Receipt, Unit,
    BaseModelAdmin, BaseTabularInline,
    create_model_link, format_currency,
    SYSTEM_INFO_FIELDSET, NOTES_FIELDSET,
)


# ========================================
# Contract Inlines
# ========================================

class ContractModificationInline(BaseTabularInline):
    """Inline لتعديلات العقد"""
    model = ContractModification
    can_delete = False
    fields = (
        'modification_type', 'effective_date', 
        'is_applied', 'get_summary_display'
    )
    readonly_fields = ('get_summary_display', 'is_applied')
    
    def get_summary_display(self, obj):
        """عرض ملخص التعديل"""
        if obj.pk:
            return obj.get_summary()
        return '-'
    get_summary_display.short_description = 'الملخص'
    
    def has_add_permission(self, request, obj=None):
        """منع الإضافة من inline - يجب الإضافة من صفحة منفصلة"""
        return False


class ReceiptInline(BaseTabularInline):
    """Inline لسندات القبض"""
    model = Receipt
    fields = (
        'receipt_number', 'receipt_date', 'amount', 
        'payment_method', 'payment_type', 'status'
    )
    readonly_fields = ('receipt_number', 'created_at')


# ========================================
# Contract Admin
# ========================================

@admin.register(Contract)
class ContractAdmin(BaseModelAdmin):
    """إدارة العقود"""
    
    list_display = (
        'contract_number', 'tenant_link', 'units_display',
        'start_date', 'end_date', 'status', 
        'total_amount', 'total_paid', 'remaining'
    )
    
    list_filter = (
        'status', 'payment_frequency', 
        'start_date', 'end_date'
    )
    
    search_fields = (
        'contract_number', 'tenant__name', 'tenant__id_number',
        'units__unit_number'
    )
    
    readonly_fields = ('contract_number', 'total_paid_amount', 'end_date', 'payment_day')
    
    # ✅ UPDATED: استخدام filter_horizontal للوحدات
    filter_horizontal = ('units',)
    
    fieldsets = (
        ('معلومات العقد', {
            'fields': (
                'contract_number', 'tenant', 
                'units',  # ✅ UPDATED: حقل واحد فقط
                'start_date', 'contract_duration_months', 'end_date'
            )
        }),
        ('القيمة والدفع', {
            'fields': (
                'annual_rent', 'payment_frequency',
                'payment_day', 'security_deposit',
                'allow_advance_payment'
            )
        }),
        ('حالة العقد', {
            'fields': (
                'status', 'actual_end_date', 
                'termination_reason'
            )
        }),
        ('المدفوعات', {
            'fields': ('total_paid_amount',),
            'classes': ('collapse',)
        }),
        NOTES_FIELDSET,
        SYSTEM_INFO_FIELDSET,
    )
    
    # ✅ UPDATED: إزالة ContractUnitsInline
    inlines = [ContractModificationInline, ReceiptInline]
    
    def tenant_link(self, obj):
        """رابط المستأجر"""
        return create_model_link('tenant', obj.tenant.id, obj.tenant.name)
    tenant_link.short_description = 'المستأجر'
    
    def units_display(self, obj):
        """✅ عرض الوحدات"""
        if not obj.pk:
            return '-'
        
        units = obj.units.all()
        count = units.count()
        
        if count == 0:
            return '⚠️ لا توجد وحدات'
        elif count == 1:
            unit = units.first()
            return f'📍 {unit.unit_number}'
        else:
            units_list = ', '.join([u.unit_number for u in units[:3]])
            if count > 3:
                units_list += f' ... (+{count-3})'
            return f'📍 {units_list} ({count} وحدة)'
    units_display.short_description = 'الوحدات'
    
    def total_paid(self, obj):
        """المبلغ المدفوع"""
        return format_currency(obj.total_paid_amount)
    total_paid.short_description = 'المدفوع'
    
    def remaining(self, obj):
        """المبلغ المتبقي"""
        remaining = obj.get_remaining_amount()
        return format_currency(remaining)
    remaining.short_description = 'المتبقي'
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """✅ NEW: تخصيص عرض الوحدات"""
        if db_field.name == "units":
            # عرض الوحدات المتاحة فقط عند إنشاء عقد جديد
            # (عند التعديل، filter_horizontal يتيح الوصول لكل الوحدات)
            kwargs["queryset"] = Unit.objects.filter(
                is_deleted=False
            ).select_related('building').order_by('building__name', 'unit_number')
        return super().formfield_for_manytomany(db_field, request, **kwargs)


# ========================================
# ContractModification Admin
# ========================================

@admin.register(ContractModification)
class ContractModificationAdmin(BaseModelAdmin):
    """إدارة تعديلات العقود"""
    
    list_display = (
        'contract_link', 'modification_type', 
        'effective_date', 'get_summary_display', 
        'is_applied', 'created_at'
    )
    
    list_filter = (
        'modification_type', 'is_applied', 
        'effective_date', 'created_at'
    )
    
    search_fields = (
        'contract__contract_number', 
        'contract__tenant__name',
        'description', 'notes'
    )
    
    readonly_fields = (
        'contract_link', 'change_amount', 'change_percentage',
        'new_end_date', 'vat_amount', 'is_applied',
        'applied_at', 'applied_by',
    )
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': (
                'contract', 'modification_type', 
                'effective_date', 'description'
            )
        }),
        ('1. تمديد العقد', {
            'fields': (
                'extension_months', 'new_end_date'
            ),
            'classes': ('collapse', 'extension-fields'),
        }),
        ('2. زيادة/تخفيض الإيجار', {
            'fields': (
                'old_rent_amount', 'new_rent_amount',
                'change_amount', 'change_percentage'
            ),
            'classes': ('collapse', 'rent-change-fields'),
        }),
        ('3. خصم', {
            'fields': (
                'discount_amount', 'discount_period_number'
            ),
            'classes': ('collapse', 'discount-fields'),
        }),
        ('4. قيمة مضافة', {
            'fields': (
                'vat_percentage', 'vat_amount', 
                'vat_period_number'
            ),
            'classes': ('collapse', 'vat-fields'),
        }),
        ('5. إنهاء العقد', {
            'fields': (
                'termination_date', 'termination_reason'
            ),
            'classes': ('collapse', 'termination-fields'),
        }),
        ('حالة التطبيق', {
            'fields': (
                'is_applied', 'applied_at', 'applied_by'
            ),
            'classes': ('collapse',),
        }),
        NOTES_FIELDSET,
        SYSTEM_INFO_FIELDSET,
    )
    
    actions = ['apply_selected_modifications']
    
    def contract_link(self, obj):
        """رابط العقد"""
        if obj.contract:
            return create_model_link(
                'contract', 
                obj.contract.id, 
                obj.contract.contract_number
            )
        return '-'
    contract_link.short_description = 'العقد'
    
    def get_summary_display(self, obj):
        """ملخص التعديل"""
        return obj.get_summary()
    get_summary_display.short_description = 'الملخص'
    
    def apply_selected_modifications(self, request, queryset):
        """تطبيق التعديلات المحددة"""
        applied_count = 0
        errors = []
        
        for modification in queryset:
            if not modification.is_applied:
                success, message = modification.apply_modification(user=request.user)
                if success:
                    applied_count += 1
                else:
                    errors.append(f'{modification}: {message}')
        
        if applied_count:
            self.message_user(
                request,
                f'تم تطبيق {applied_count} تعديل بنجاح',
                messages.SUCCESS
            )
        
        if errors:
            self.message_user(
                request,
                'فشل تطبيق: ' + '; '.join(errors),
                messages.ERROR
            )
    
    apply_selected_modifications.short_description = 'تطبيق التعديلات المحددة'
    
    class Media:
        js = ('admin/js/contract_modification.js',)
        css = {
            'all': ('admin/css/contract_modification.css',)
        }


# ========================================
# Custom Filters
# ========================================

class OutstandingAmountFilter(admin.SimpleListFilter):
    """فلتر المستحقات"""
    title = 'المستحقات'
    parameter_name = 'outstanding'
    
    def lookups(self, request, model_admin):
        return (
            ('has_outstanding', 'يوجد مستحقات'),
            ('no_outstanding', 'لا يوجد مستحقات'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'has_outstanding':
            contracts_with_outstanding = [
                c.id for c in queryset 
                if c.get_remaining_amount() > 0
            ]
            return queryset.filter(id__in=contracts_with_outstanding)
        
        elif self.value() == 'no_outstanding':
            contracts_no_outstanding = [
                c.id for c in queryset 
                if c.get_remaining_amount() == 0
            ]
            return queryset.filter(id__in=contracts_no_outstanding)
        
        return queryset


# إضافة الفلتر إلى ContractAdmin
ContractAdmin.list_filter = ContractAdmin.list_filter + (OutstandingAmountFilter,)