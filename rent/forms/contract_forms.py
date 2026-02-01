"""
Contract Forms
نماذج العقود وتعديلاتها
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date

from ..models import Contract, Tenant, Unit
from ..models.common_imports_models import PropertyStatus, ContractStatus, generate_contract_number

# ========================================
# Common Widgets
# ========================================
COMMON_WIDGETS = {
    'select': lambda: forms.Select(attrs={'class': 'form-control'}),
    'date_input': lambda: forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    'number_input': lambda help_text='', step='0.01', min='0': forms.NumberInput(attrs={
        'class': 'form-control',
        'step': step,
        'min': min,
        'placeholder': help_text
    }),
    'checkbox': lambda: forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    'textarea': lambda: forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
}


def validate_date_range(start_date, end_date):
    """Validate that end_date is after start_date"""
    if start_date >= end_date:
        raise ValidationError(_('تاريخ النهاية يجب أن يكون بعد تاريخ البداية'))


class BaseModelForm(forms.ModelForm):
    """Base form for models"""
    pass


# ========================================
# Contract Form
# ========================================
class ContractForm(BaseModelForm):
    """نموذج العقد مع حل مشاكل الحقول Required"""

    class Meta:
        model = Contract
        fields = [
            'contract_number', 'tenant', 'units',
            'start_date', 'contract_duration_months', 'end_date',
             'annual_rent','payment_frequency', 'payment_day',
            'security_deposit', 'allow_advance_payment',
            'status', 'notes'
        ]
        widgets = {
            'contract_number': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'tenant': COMMON_WIDGETS['select'](),
            'units': forms.CheckboxSelectMultiple(attrs={'class': 'units-checkbox'}),
            'start_date': COMMON_WIDGETS['date_input'](),
            'contract_duration_months': COMMON_WIDGETS['number_input']('مدة العقد بالأشهر', step='1', min='1'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'readonly': 'readonly'}),
            'annual_rent': COMMON_WIDGETS['number_input']('القيمة لكل فترة'),
            'payment_frequency': COMMON_WIDGETS['select'](),
            'payment_day': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '28'}),
            'security_deposit': COMMON_WIDGETS['number_input'](),
            'allow_advance_payment': COMMON_WIDGETS['checkbox'](),
            'status': COMMON_WIDGETS['select'](),
            'notes': COMMON_WIDGETS['textarea'](),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # =========================
        # قيم افتراضية عند الإنشاء
        # =========================
        if not self.instance.pk:
            self.initial.setdefault('contract_duration_months', 12)
            self.initial.setdefault('payment_day', 1)
            self.initial.setdefault('contract_number', generate_contract_number())

        # =========================
        # وحدات متاحة فقط
        # =========================
        if not self.instance.pk:
            self.fields['units'].queryset = Unit.objects.filter(
                status=PropertyStatus.AVAILABLE,
                is_active=True,
                is_deleted=False
            ).select_related('building').order_by('building__name', 'unit_number')
        else:
            current_units = self.instance.units.all()
            available_units = Unit.objects.filter(
                status=PropertyStatus.AVAILABLE,
                is_active=True,
                is_deleted=False
            )
            self.fields['units'].queryset = Unit.objects.filter(
                Q(pk__in=current_units) | Q(pk__in=available_units)
            ).select_related('building').order_by('building__name', 'unit_number').distinct()

        self.fields['units'].label = 'الوحدات (اختر وحدة أو أكثر)'
        self.fields['units'].help_text = 'يمكنك اختيار وحدة واحدة أو عدة وحدات'

        # المستأجرين النشطين فقط
        self.fields['tenant'].queryset = Tenant.objects.filter(
            is_active=True,
            is_deleted=False
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        units = cleaned_data.get('units')

        # تحقق من اختيار وحدة واحدة على الأقل
        if not units or units.count() == 0:
            raise ValidationError({'units': _('يجب اختيار وحدة واحدة على الأقل')})

        # تحقق من تواريخ العقد
        if start_date and end_date:
            validate_date_range(start_date, end_date)

        # تحقق من تداخل العقود لكل وحدة
        if units and start_date and end_date:
            for unit in units:
                overlapping = Contract.objects.filter(
                    units=unit,
                    status__in=[ContractStatus.DRAFT, ContractStatus.ACTIVE],
                    start_date__lt=end_date,
                    end_date__gt=start_date,
                    is_deleted=False
                )
                if self.instance.pk:
                    overlapping = overlapping.exclude(pk=self.instance.pk)
                if overlapping.exists():
                    existing = overlapping.first()
                    raise ValidationError({
                        'units': _(
                            f'⚠️ الوحدة {unit.unit_number} مؤجرة بالفعل!\n'
                            f'عقد: {existing.contract_number}\n'
                            f'الفترة: من {existing.start_date} إلى {existing.end_date}'
                        )
                    })
        return cleaned_data

    class Media:
        css = {'all': ('css/contract_form.css',)}
        js = ('js/contract_form.js',)


# ========================================
# Contract Quick Form
# ========================================
class ContractQuickForm(BaseModelForm):
    """نموذج مبسط للإنشاء السريع"""

    class Meta:
        model = Contract
        fields = [
            'tenant', 'units',
            'start_date', 'contract_duration_months',
            'annual_rent', 'payment_frequency',
            'status'
        ]
        widgets = {
            'tenant': COMMON_WIDGETS['select'](),
            'units': forms.CheckboxSelectMultiple(),
            'start_date': COMMON_WIDGETS['date_input'](),
            'contract_duration_months': COMMON_WIDGETS['number_input']('مدة العقد (أشهر)', step='1', min='1'),
            'annual_rent': COMMON_WIDGETS['number_input']('قيمة الإيجار'),
            'payment_frequency': COMMON_WIDGETS['select'](),
            'status': COMMON_WIDGETS['select'](),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # قيم افتراضية
        self.initial.setdefault('contract_duration_months', 12)

        # الوحدات المتاحة فقط
        self.fields['units'].queryset = Unit.objects.filter(
            status=PropertyStatus.AVAILABLE,
            is_active=True,
            is_deleted=False
        ).select_related('building').order_by('building__name', 'unit_number')

        # المستأجرين النشطين فقط
        self.fields['tenant'].queryset = Tenant.objects.filter(
            is_active=True,
            is_deleted=False
        )

        # الحالات المسموحة
        self.fields['status'].choices = [
            (ContractStatus.DRAFT, 'مسودة'),
            (ContractStatus.ACTIVE, 'نشط'),
        ]

    def clean_units(self):
        units = self.cleaned_data.get('units')
        if not units or units.count() == 0:
            raise ValidationError('يجب اختيار وحدة واحدة على الأقل')
        return units


# ========================================
# Contract Filter Form
# ========================================
class ContractFilterForm(forms.Form):
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.filter(is_active=True, is_deleted=False),
        required=False,
        label='المستأجر',
        widget=COMMON_WIDGETS['select']()
    )

    unit = forms.ModelChoiceField(
        queryset=Unit.objects.filter(is_deleted=False,status='AVAILABLE'),
        required=False,
        label='الوحدة',
        widget=COMMON_WIDGETS['select']()
    )

    status = forms.ChoiceField(
        choices=[('', 'الكل')] + list(ContractStatus.choices),
        required=False,
        label='الحالة',
        widget=COMMON_WIDGETS['select']()
    )

    start_date_from = forms.DateField(
        required=False,
        label='من تاريخ',
        widget=COMMON_WIDGETS['date_input']()
    )

    start_date_to = forms.DateField(
        required=False,
        label='إلى تاريخ',
        widget=COMMON_WIDGETS['date_input']()
    )
