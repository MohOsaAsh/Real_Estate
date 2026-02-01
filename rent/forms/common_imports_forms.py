"""
Common Imports for Forms
الاستيرادات المشتركة لجميع النماذج
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
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
    
    # System
    ReportTemplate, 
)

# استيراد Enums
from rent.models.common_imports_models import PropertyStatus


# ========================================
# Base Form Classes
# ========================================

class BaseModelForm(forms.ModelForm):
    """
    نموذج أساسي لجميع النماذج
    يوفر إعدادات مشتركة
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة classes للحقول تلقائياً
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.Textarea):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
            else:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'


# ========================================
# Common Widget Configurations
# ========================================

COMMON_WIDGETS = {
    'text_input': lambda placeholder='': forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': placeholder}
    ),
    'number_input': lambda placeholder='', step='0.01', **kwargs: forms.NumberInput(
        attrs={'class': 'form-control', 'step': step, 'placeholder': placeholder, **kwargs}
    ),
    'date_input': lambda: forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date'}
    ),
    'select': lambda: forms.Select(
        attrs={'class': 'form-select'}
    ),
    'checkbox': lambda: forms.CheckboxInput(
        attrs={'class': 'form-check-input'}
    ),
    'textarea': lambda rows=3, placeholder='': forms.Textarea(
        attrs={'class': 'form-control', 'rows': rows, 'placeholder': placeholder}
    ),
    'email': lambda placeholder='': forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': placeholder}
    ),
    'password': lambda: forms.PasswordInput(
        attrs={'class': 'form-control'}
    ),
}


# ========================================
# Common Field Validators
# ========================================

def validate_saudi_phone(value):
    """التحقق من رقم الهاتف السعودي"""
    if value and not value.startswith('05'):
        raise ValidationError(_('رقم الهاتف يجب أن يبدأ بـ 05'))
    if value and len(value) != 10:
        raise ValidationError(_('رقم الهاتف يجب أن يكون 10 أرقام'))


def validate_saudi_id(value):
    """التحقق من رقم الهوية السعودية"""
    if value and len(value) != 10:
        raise ValidationError(_('رقم الهوية يجب أن يكون 10 أرقام'))
    if value and not value.isdigit():
        raise ValidationError(_('رقم الهوية يجب أن يحتوي على أرقام فقط'))


def validate_positive_decimal(value):
    """التحقق من القيمة الموجبة"""
    if value and value < 0:
        raise ValidationError(_('القيمة يجب أن تكون موجبة'))


def validate_future_date(value):
    """التحقق من أن التاريخ في المستقبل"""
    if value and value < date.today():
        raise ValidationError(_('التاريخ يجب أن يكون في المستقبل'))


def validate_date_range(start_date, end_date):
    """التحقق من صحة نطاق التواريخ"""
    if start_date and end_date and start_date >= end_date:
        raise ValidationError({
            'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
        })