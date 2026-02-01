"""
Report and System Forms
نماذج التقارير والإعدادات
"""

from .common_imports_forms import (
    forms, _,
    Tenant, Building, Contract, 
    COMMON_WIDGETS
)


# ========================================
# Report Filter Form
# ========================================

class ReportFilterForm(forms.Form):
    """نموذج فلاتر التقارير"""
    
    start_date = forms.DateField(
        label=_('من تاريخ'),
        required=False,
        widget=COMMON_WIDGETS['date_input']()
    )
    
    end_date = forms.DateField(
        label=_('إلى تاريخ'),
        required=False,
        widget=COMMON_WIDGETS['date_input']()
    )
    
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.filter(is_active=True, is_deleted=False),
        label=_('المستأجر'),
        required=False,
        widget=COMMON_WIDGETS['select']()
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
        choices=[('', '--- الكل ---')] + list(Contract._meta.get_field('status').choices),
        widget=COMMON_WIDGETS['select']()
    )


