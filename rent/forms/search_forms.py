"""
Search Forms
نماذج البحث والفلترة
"""

from .common_imports_forms import (
    forms, _,
    Tenant, Contract, Building, Unit,
    COMMON_WIDGETS
)


# ========================================
# Tenant Search Form
# ========================================

class TenantSearchForm(forms.Form):
    """نموذج البحث عن المستأجرين"""
    
    search = forms.CharField(
        label=_('البحث'),
        required=False,
        widget=COMMON_WIDGETS['text_input'](_('ابحث بالاسم، رقم الهاتف، أو رقم الهوية'))
    )
    
    tenant_type = forms.ChoiceField(
        label=_('النوع'),
        required=False,
        choices=[('', '--- الكل ---')] + list(Tenant._meta.get_field('tenant_type').choices),
        widget=COMMON_WIDGETS['select']()
    )
    
    is_active = forms.NullBooleanField(
        label=_('الحالة'),
        required=False,
        widget=forms.Select(
            choices=[('', '--- الكل ---'), ('true', 'نشط'), ('false', 'غير نشط')],
            attrs={'class': 'form-select'}
        )
    )


# ========================================
# Contract Search Form
# ========================================

class ContractSearchForm(forms.Form):
    """نموذج البحث عن العقود"""
    
    search = forms.CharField(
        label=_('البحث'),
        required=False,
        widget=COMMON_WIDGETS['text_input'](_('ابحث برقم العقد أو اسم المستأجر'))
    )
    
    status = forms.ChoiceField(
        label=_('الحالة'),
        required=False,
        choices=[('', '--- الكل ---')] + list(Contract._meta.get_field('status').choices),
        widget=COMMON_WIDGETS['select']()
    )
    
    start_date_from = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=COMMON_WIDGETS['date_input']()
    )
    
    start_date_to = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=COMMON_WIDGETS['date_input']()
    )


# ========================================
# Unit Search Form
# ========================================

class UnitSearchForm(forms.Form):
    """نموذج البحث عن الوحدات"""
    
    search = forms.CharField(
        label=_('البحث'),
        required=False,
        widget=COMMON_WIDGETS['text_input'](_('ابحث برقم الوحدة'))
    )
    
    building = forms.ModelChoiceField(
        queryset=Building.objects.filter(is_active=True, is_deleted=False),
        label=_('المبنى'),
        required=False,
        widget=COMMON_WIDGETS['select']()
    )
    
    status = forms.ChoiceField(
        label=_('الحالة'),
        required=False,
        choices=[('', '--- الكل ---')] + list(Unit._meta.get_field('status').choices),
        widget=COMMON_WIDGETS['select']()
    )