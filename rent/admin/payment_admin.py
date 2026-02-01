"""
Payment Admin
إدارة المدفوعات وسندات القبض
"""

from .common_imports_admin import (
    admin,
    Receipt, Contract,
    BaseModelAdmin,
    create_model_link,
    SYSTEM_INFO_FIELDSET, NOTES_FIELDSET,
)


# ========================================
# Receipt Admin
# ========================================

@admin.register(Receipt)
class ReceiptAdmin(BaseModelAdmin):
    """إدارة سندات القبض"""
    
    list_display = (
        'receipt_number', 'contract_link', 'receipt_date', 
        'amount', 'payment_method', 'status'
    )
    
    list_filter = (
        'status', 'payment_method', 'receipt_date'
    )
    
    search_fields = (
        'receipt_number', 'contract__contract_number', 
        'reference_number'
    )
    
    fieldsets = (
        ('معلومات السند', {
            'fields': (
                'receipt_number', 'contract', 
                'receipt_date', 'amount'
            )
        }),
        ('طريقة الدفع', {
            'fields': (
                'payment_method', 'reference_number'
            )
        }),
        ('الفترة', {
            'fields': (
                'period_start', 'period_end', 'due_date'
            ),
            'classes': ('collapse',)
        }),
        ('حالة السند', {
            'fields': ('status',)
        }),
        NOTES_FIELDSET,
        SYSTEM_INFO_FIELDSET,
    )
    
    def contract_link(self, obj):
        """رابط العقد"""
        return create_model_link(
            'contract', 
            obj.contract.id, 
            obj.contract.contract_number
        )
    contract_link.short_description = 'العقد'