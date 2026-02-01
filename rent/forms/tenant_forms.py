"""
Tenant Forms
نماذج المستأجرين ومستنداتهم
"""

from .common_imports_forms import (
    forms, _, ValidationError,
    Tenant, TenantDocument,
    COMMON_WIDGETS, BaseModelForm,
    validate_saudi_phone, validate_saudi_id
)


# ========================================
# Tenant Form
# ========================================

class TenantForm(BaseModelForm):
    """نموذج المستأجر"""
    
    class Meta:
        model = Tenant
        fields = [
            'tenant_type', 'name', 'phone', 'email',
            'id_number',
            'company_name',
            'has_authorization', 'authorization_number', 'authorization_date',
            'address',
            'is_active', 'notes'
        ]
        widgets = {
            'tenant_type': COMMON_WIDGETS['select'](),
            'name': COMMON_WIDGETS['text_input']('الاسم الكامل'),
            'phone': COMMON_WIDGETS['text_input']('05xxxxxxxx'),
            'email': COMMON_WIDGETS['email']('example@email.com'),
            'id_number': COMMON_WIDGETS['text_input']('10 أرقام'),
            'company_name': COMMON_WIDGETS['text_input']('اسم الشركة (للشركات فقط)'),
            'has_authorization': COMMON_WIDGETS['checkbox'](),
            'authorization_number': COMMON_WIDGETS['text_input'](),
            'authorization_date': COMMON_WIDGETS['date_input'](),
            'address': COMMON_WIDGETS['textarea'](placeholder='العنوان'),
            'is_active': COMMON_WIDGETS['checkbox'](),
            'notes': COMMON_WIDGETS['textarea'](placeholder='ملاحظات'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # جعل company_name اختياري في البداية
        self.fields['company_name'].required = False
    
    def clean(self):
        """التحقق من البيانات"""
        cleaned_data = super().clean()
        tenant_type = cleaned_data.get('tenant_type')
        company_name = cleaned_data.get('company_name')
        has_authorization = cleaned_data.get('has_authorization')
        authorization_number = cleaned_data.get('authorization_number')
        authorization_date = cleaned_data.get('authorization_date')
        
        # التحقق من بيانات الشركة
        if tenant_type == 'company' and not company_name:
            raise ValidationError({
                'company_name': _('اسم الشركة مطلوب للمستأجرين من نوع شركة')
            })
        
        # التحقق من بيانات الوكالة
        if has_authorization:
            if not authorization_number:
                raise ValidationError({
                    'authorization_number': _('رقم الوكالة مطلوب عند وجود وكالة')
                })
            if not authorization_date:
                raise ValidationError({
                    'authorization_date': _('تاريخ الوكالة مطلوب عند وجود وكالة')
                })
        
        return cleaned_data


# ========================================
# TenantDocument Form
# ========================================

class TenantDocumentForm(BaseModelForm):
    """نموذج مستندات المستأجر"""
    
    class Meta:
        model = TenantDocument
        fields = ['tenant', 'document_type', 'title', 'file', 'notes']
        widgets = {
            'tenant': COMMON_WIDGETS['select'](),
            'document_type': COMMON_WIDGETS['select'](),
            'title': COMMON_WIDGETS['text_input']('عنوان المستند'),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': COMMON_WIDGETS['textarea'](),
        }