# forms/contract_modification_forms.py

"""
Contract Modification Forms - Enhanced Version
نماذج تعديلات العقود - النسخة المحسنة
"""
import logging
from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rent.models import ContractModification, Contract
from rent.models.contractmodify_models import ModificationType
from rent.utils.contract_utils import (
    calculate_contract_due_dates,
    format_due_dates_error_message,
    calculate_rent_change,
    calculate_vat_amount,
)

logger = logging.getLogger(__name__)


# ========================================
# Base Form
# ========================================

class BaseContractModificationForm(forms.ModelForm):
    """
    Base form for all contract modifications
    نموذج أساسي لجميع التعديلات
    """
    
    class Meta:
        model = ContractModification
        fields = [
            'contract', 'modification_type', 'effective_date',
            'description', 'notes'
        ]
        widgets = {
            'contract': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'modification_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
                'readonly': 'readonly'

            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف تفصيلي للتعديل'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ملاحظات إضافية'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # عرض العقود النشطة فقط
        self.fields['contract'].queryset = Contract.objects.filter(
            status__in=['draft', 'active'],
            is_deleted=False
        ).select_related('tenant').order_by('-created_at')
        
        # تحسين labels
        self.fields['contract'].label = 'العقد'
        self.fields['effective_date'].label = 'تاريخ السريان'
        self.fields['description'].label = 'الوصف'
        self.fields['notes'].label = 'ملاحظات'
    
    def clean_contract(self):
        """التحقق من صلاحية العقد"""
        contract = self.cleaned_data.get('contract')
        
        if not contract:
            raise ValidationError(_('يجب اختيار عقد'))
        
        if contract.status not in ['draft', 'active']:
            raise ValidationError(_('لا يمكن تعديل عقد غير نشط'))
        
        return contract


# ========================================
# 1. Extension Form (تمديد عقد)
# ========================================

class ExtensionForm(BaseContractModificationForm):
    """Form for contract extension"""
    
    class Meta(BaseContractModificationForm.Meta):
        fields = BaseContractModificationForm.Meta.fields + [
            'extension_months', 'new_end_date'
        ]
        widgets = {
            **BaseContractModificationForm.Meta.widgets,
            'extension_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'عدد الأشهر',
                'required': True
            }),
            'new_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'readonly': 'readonly'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modification_type'].initial = ModificationType.EXTENSION
        self.fields['modification_type'].widget = forms.HiddenInput()
        
        # جعل new_end_date للقراءة فقط
        self.fields['new_end_date'].required = False
        self.fields['extension_months'].label = 'عدد أشهر التمديد'
        self.fields['new_end_date'].label = 'تاريخ الانتهاء الجديد'
        
        contract = None
        
        # حساب تاريخ السريان تلقائياً = اليوم التالي لانتهاء العقد
        # محاولة الحصول على العقد من مصادر مختلفة
        
        # 1. من initial (عند الإنشاء من URL params)
        if 'initial' in kwargs and 'contract' in kwargs['initial']:
            try:
                contract_id = kwargs['initial']['contract']
                contract = Contract.objects.get(id=contract_id)
            except (Contract.DoesNotExist, ValueError, TypeError):
                pass
        
        # 2. من self.data (عند POST)
        if not contract and 'contract' in self.data:
            try:
                from datetime import timedelta
                contract_id = self.data.get('contract')
                contract = Contract.objects.get(id=contract_id)
            except (Contract.DoesNotExist, ValueError, TypeError):
                pass
        
        # 3. من self.instance (عند التعديل)
        if not contract and self.instance and self.instance.contract_id:
            try:
                contract = self.instance.contract
            except Exception:
                pass
        
        # حساب تاريخ السريان إذا تم العثور على العقد
        if contract:
            try:
                from datetime import timedelta
                # البحث عن آخر تمديد مُطبق لهذا العقد
                last_extension = ContractModification.objects.filter(
                    contract=contract,
                    modification_type=ModificationType.EXTENSION,
                    is_applied=True
                ).order_by('-new_end_date').first()
                
                if last_extension and last_extension.new_end_date:
                    # استخدام تاريخ الانتهاء من آخر تمديد
                    base_date = last_extension.new_end_date
                else:
                    # استخدام تاريخ الانتهاء الأصلي من العقد
                    base_date = contract.end_date
                
                # تاريخ السريان = اليوم التالي لتاريخ الانتهاء
                self.fields['effective_date'].initial = base_date + timedelta(days=1)
            except Exception as e:
                logger.error(f'Error calculating effective date: {str(e)}')
        
        # جعل effective_date للقراءة فقط
        self.fields['effective_date'].widget.attrs['readonly'] = 'readonly'
        self.fields['effective_date'].help_text = 'يُحسب تلقائياً: اليوم التالي لتاريخ انتهاء العقد'
    
    def clean_extension_months(self):
        """التحقق من عدد أشهر التمديد"""
        months = self.cleaned_data.get('extension_months')
        
        if not months or months < 1:
            raise ValidationError(_('يجب تحديد عدد أشهر التمديد (1 على الأقل)'))
        
        if months > 120:  # 10 سنوات كحد أقصى
            raise ValidationError(_('عدد أشهر التمديد يجب ألا يتجاوز 120 شهراً'))
        
        return months
    
    def clean(self):
        """حساب تاريخ الانتهاء الجديد"""
        cleaned_data = super().clean()
        contract = cleaned_data.get('contract')
        months = cleaned_data.get('extension_months')
        effective_date = cleaned_data.get('effective_date')
        
        if contract and months:
            from dateutil.relativedelta import relativedelta
            from datetime import timedelta
            try:
                # حساب تاريخ السريان إذا لم يكن موجوداً
                if not effective_date:
                    # البحث عن آخر تمديد مُطبق
                    last_extension = ContractModification.objects.filter(
                        contract=contract,
                        modification_type=ModificationType.EXTENSION,
                        is_applied=True
                    ).order_by('-new_end_date').first()
                    
                    if last_extension and last_extension.new_end_date:
                        base_date = last_extension.new_end_date
                    else:
                        base_date = contract.end_date
                    
                    effective_date = base_date + timedelta(days=1)
                    cleaned_data['effective_date'] = effective_date
                
                # حساب تاريخ الانتهاء الجديد من تاريخ السريان + عدد الأشهر
                # تاريخ الانتهاء الجديد = تاريخ السريان + الأشهر - يوم واحد
                # لأن تاريخ السريان هو أول يوم في الفترة الجديدة
                new_end_date = effective_date + relativedelta(months=months) - timedelta(days=1)
                cleaned_data['new_end_date'] = new_end_date
                
            except Exception as e:
                logger.error(f'Error calculating new end date: {str(e)}')
                raise ValidationError(_('خطأ في حساب تاريخ الانتهاء الجديد'))
        
        return cleaned_data


# ========================================
# 2. Rent Change Form (زيادة/تخفيض إيجار)
# ========================================

class RentChangeForm(BaseContractModificationForm):
    """Form for rent increase/decrease"""
    
    class Meta(BaseContractModificationForm.Meta):
        fields = BaseContractModificationForm.Meta.fields + [
            'old_rent_amount', 'new_rent_amount',
            'change_amount', 'change_percentage'
        ]
        widgets = {
            **BaseContractModificationForm.Meta.widgets,
            'old_rent_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'step': '0.01'
            }),
            'new_rent_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'قيمة الإيجار الجديدة',
                'required': True
            }),
            'change_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'step': '0.01'
            }),
            'change_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'step': '0.01'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # جعل الحقول المحسوبة للقراءة فقط
        self.fields['old_rent_amount'].required = False
        self.fields['change_amount'].required = False
        self.fields['change_percentage'].required = False
        
        # تحسين labels
        self.fields['old_rent_amount'].label = 'قيمة الإيجار القديمة'
        self.fields['new_rent_amount'].label = 'قيمة الإيجار الجديدة'
        self.fields['change_amount'].label = 'مبلغ التغيير'
        self.fields['change_percentage'].label = 'نسبة التغيير %'
        
        # ملء old_rent_amount تلقائياً
        if self.instance and self.instance.pk and hasattr(self.instance, 'contract') and self.instance.contract_id:
            self.fields['old_rent_amount'].initial = self.instance.contract.annual_rent
        
        # جعل effective_date للقراءة فقط وعرض فترات الاستحقاق
        contract = None
        if 'contract' in self.data:
            try:
                contract_id = self.data.get('contract')
                contract = Contract.objects.get(id=contract_id)
            except (Contract.DoesNotExist, ValueError, TypeError):
                pass
        elif self.instance and self.instance.contract_id:
            contract = self.instance.contract
        
        if contract:
            try:
                due_dates = calculate_contract_due_dates(contract)
                if due_dates:
                    # عرض أول 10 فترات استحقاق
                    dates_display = ', '.join([d.strftime('%Y-%m-%d') for d in due_dates[:10]])
                    remaining = len(due_dates) - 10
                    
                    self.fields['effective_date'].help_text = 'اختر من فترات الاستحقاق أدناه'
                    
                    # تغيير نوع الحقل إلى text بدلاً من date لمنع date picker
                    # وجعله للقراءة فقط - يُملأ فقط عبر الأزرار
                    self.fields['effective_date'].widget = forms.TextInput(attrs={
                        'class': 'form-control',
                        'readonly': 'readonly',
                        'placeholder': 'اختر من الأزرار أدناه'
                    })
            except Exception as e:
                logger.warning(f'Could not calculate due dates: {str(e)}')
    
    def clean_effective_date(self):
        """التحقق من أن تاريخ السريان هو تاريخ استحقاق"""
        effective_date = self.cleaned_data.get('effective_date')
        contract = self.cleaned_data.get('contract')
        
        if effective_date and contract:
            try:
                due_dates = calculate_contract_due_dates(contract)
                
                if not due_dates:
                    raise ValidationError(_('لا يمكن حساب تواريخ الاستحقاق للعقد'))
                
                if effective_date not in due_dates:
                    raise ValidationError(
                        format_due_dates_error_message(due_dates)
                    )
            
            except ValidationError:
                raise
            except Exception as e:
                logger.error(f'Error validating effective date: {str(e)}')
                raise ValidationError(_('خطأ في التحقق من تاريخ السريان'))
        
        return effective_date
    
    def clean_new_rent_amount(self):
        """التحقق من قيمة الإيجار الجديدة"""
        new_rent = self.cleaned_data.get('new_rent_amount')
        
        if not new_rent or new_rent <= 0:
            raise ValidationError(_('يجب تحديد قيمة الإيجار الجديدة'))
        
        return new_rent
    
    def clean(self):
        """حساب المبالغ والنسب"""
        cleaned_data = super().clean()
        contract = cleaned_data.get('contract')
        new_rent = cleaned_data.get('new_rent_amount')
        
        if contract and new_rent:
            try:
                old_rent = contract.annual_rent
                cleaned_data['old_rent_amount'] = old_rent
                
                # استخدام الدالة المشتركة
                change_amt, change_pct = calculate_rent_change(old_rent, new_rent)
                cleaned_data['change_amount'] = change_amt
                cleaned_data['change_percentage'] = change_pct
                
            except Exception as e:
                logger.error(f'Error calculating rent change: {str(e)}')
                raise ValidationError(_('خطأ في حساب التغيير في الإيجار'))
        
        return cleaned_data


class RentIncreaseForm(RentChangeForm):
    """Form specifically for rent increase"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modification_type'].initial = ModificationType.RENT_INCREASE
        self.fields['modification_type'].widget = forms.HiddenInput()
    
    def clean_new_rent_amount(self):
        """التحقق من أن الإيجار الجديد أكبر من القديم"""
        new_rent = super().clean_new_rent_amount()
        contract = self.cleaned_data.get('contract')
        
        if contract and new_rent:
            if new_rent <= contract.annual_rent:
                raise ValidationError(
                    _('قيمة الإيجار الجديدة يجب أن تكون أكبر من القيمة الحالية')
                )
        
        return new_rent


class RentDecreaseForm(RentChangeForm):
    """Form specifically for rent decrease"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modification_type'].initial = ModificationType.RENT_DECREASE
        self.fields['modification_type'].widget = forms.HiddenInput()
    
    def clean_new_rent_amount(self):
        """التحقق من أن الإيجار الجديد أقل من القديم"""
        new_rent = super().clean_new_rent_amount()
        contract = self.cleaned_data.get('contract')
        
        if contract and new_rent:
            if new_rent >= contract.annual_rent:
                raise ValidationError(
                    _('قيمة الإيجار الجديدة يجب أن تكون أقل من القيمة الحالية')
                )
        
        return new_rent


# ========================================
# 3. Discount Form (خصم)
# ========================================

class DiscountForm(BaseContractModificationForm):
    """Form for discount"""
    
    class Meta(BaseContractModificationForm.Meta):
        fields = BaseContractModificationForm.Meta.fields + [
            'discount_amount', 'discount_period_number'
        ]
        widgets = {
            **BaseContractModificationForm.Meta.widgets,
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'مبلغ الخصم',
                'required': True
            }),
            'discount_period_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'رقم الفترة',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modification_type'].initial = ModificationType.DISCOUNT
        self.fields['modification_type'].widget = forms.HiddenInput()
        
        self.fields['discount_amount'].label = 'مبلغ الخصم'
        self.fields['discount_period_number'].label = 'رقم الفترة'
        
        # جعل رقم الفترة وتاريخ السريان للقراءة فقط - يتم اختيارهم من الأزرار
        self.fields['discount_period_number'].widget.attrs['readonly'] = 'readonly'
        self.fields['discount_period_number'].help_text = 'سيتم تحديده تلقائياً عند اختيار الفترة'
        
        self.fields['effective_date'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'placeholder': 'اختر من الأزرار أدناه'
        })
        self.fields['effective_date'].help_text = 'اختر الفترة المراد تطبيق الخصم عليها من الأزرار أدناه'
        
        # عرض فترات الاستحقاق للمساعدة (في حالة إعادة التحميل مع وجود عقد)
        contract = None
        if 'contract' in self.data:
            try:
                contract_id = self.data.get('contract')
                contract = Contract.objects.get(id=contract_id)
            except (Contract.DoesNotExist, ValueError, TypeError):
                pass
        elif self.instance and self.instance.contract_id:
            contract = self.instance.contract
            
        if contract:
             try:
                due_dates = calculate_contract_due_dates(contract)
                if due_dates:
                     self.fields['effective_date'].widget.attrs['title'] = 'اختر من فترات الاستحقاق المتاحة'
             except Exception:
                 pass
    
    def clean_discount_amount(self):
        """التحقق من مبلغ الخصم"""
        amount = self.cleaned_data.get('discount_amount')
        
        if not amount or amount <= 0:
            raise ValidationError(_('يجب تحديد مبلغ الخصم'))
        
        # التحقق من أن الخصم لا يتجاوز قيمة الإيجار
        contract = self.cleaned_data.get('contract')
        if contract and amount > contract.annual_rent:
            raise ValidationError(
                _('مبلغ الخصم لا يمكن أن يتجاوز قيمة الإيجار السنوي')
            )
        
        return amount
    
    def clean_discount_period_number(self):
        """التحقق من رقم الفترة"""
        period = self.cleaned_data.get('discount_period_number')
        
        if not period or period < 1:
            raise ValidationError(_('يجب تحديد رقم الفترة'))
        
        return period


# ========================================
# 4. VAT Form (قيمة مضافة)
# ========================================

class VATForm(BaseContractModificationForm):
    """Form for VAT"""
    
    class Meta(BaseContractModificationForm.Meta):
        fields = BaseContractModificationForm.Meta.fields + [
            'vat_percentage', 'vat_amount', 'vat_period_number'
        ]
        widgets = {
            **BaseContractModificationForm.Meta.widgets,
            'vat_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'value': '15.00',
                'placeholder': 'نسبة القيمة المضافة %'
            }),
            'vat_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                #'readonly': 'readonly'
            }),
            'vat_period_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'رقم الفترة',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modification_type'].initial = ModificationType.VAT
        self.fields['modification_type'].widget = forms.HiddenInput()
        
        self.fields['vat_amount'].required = False
        self.fields['vat_percentage'].initial = Decimal('15.00')
        
        self.fields['vat_percentage'].label = 'نسبة القيمة المضافة %'
        self.fields['vat_amount'].label = 'مبلغ القيمة المضافة'
        self.fields['vat_period_number'].label = 'رقم الفترة'
        
        # جعل رقم الفترة وتاريخ السريان للقراءة فقط - يتم اختيارهم من الأزرار
        self.fields['vat_period_number'].widget.attrs['readonly'] = 'readonly'
        self.fields['vat_period_number'].help_text = 'سيتم تحديده تلقائياً عند اختيار الفترة'
        
        self.fields['effective_date'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'placeholder': 'اختر من الأزرار أدناه'
        })
        self.fields['effective_date'].help_text = 'اختر الفترة المراد تطبيق الضريبة عليها من الأزرار أدناه'
        
        # عرض فترات الاستحقاق للمساعدة (في حالة إعادة التحميل مع وجود عقد)
        contract = None
        if 'contract' in self.data:
            try:
                contract_id = self.data.get('contract')
                contract = Contract.objects.get(id=contract_id)
            except (Contract.DoesNotExist, ValueError, TypeError):
                pass
        elif self.instance and self.instance.contract_id:
            contract = self.instance.contract
        
        if contract:
            try:
                due_dates = calculate_contract_due_dates(contract)
                if due_dates:
                    self.fields['effective_date'].widget.attrs['title'] = 'اختر من فترات الاستحقاق المتاحة'
            except Exception as e:
                logger.warning(f'Could not calculate due dates for VAT: {str(e)}')
    
    def clean_vat_percentage(self):
        """التحقق من نسبة القيمة المضافة"""
        percentage = self.cleaned_data.get('vat_percentage')
        
        if not percentage:
            percentage = Decimal('15.00')
        
        if percentage < 0 or percentage > 100:
            raise ValidationError(_('نسبة القيمة المضافة يجب أن تكون بين 0 و 100'))
        
        return percentage
    
    def clean_vat_period_number(self):
        """التحقق من رقم الفترة"""
        period = self.cleaned_data.get('vat_period_number')
        
        if not period or period < 1:
            raise ValidationError(_('يجب تحديد رقم الفترة'))
        
        return period
    
    def clean(self):
        """حساب مبلغ القيمة المضافة وتاريخ السريان"""
        cleaned_data = super().clean()
        contract = cleaned_data.get('contract')
        percentage = cleaned_data.get('vat_percentage') or Decimal('15.00')
        vat_period_number = cleaned_data.get('vat_period_number')
        
        # حساب تاريخ السريان من رقم الفترة
        if contract and vat_period_number:
            try:
                due_dates = calculate_contract_due_dates(contract)
                
                if not due_dates:
                    raise ValidationError({'vat_period_number': _('لا يمكن حساب فترات الاستحقاق للعقد')})
                
                if vat_period_number < 1 or vat_period_number > len(due_dates):
                    raise ValidationError({
                        'vat_period_number': _(f'رقم الفترة يجب أن يكون بين 1 و {len(due_dates)}')
                    })
                
                # حساب التاريخ من رقم الفترة (الفترة 1 = Index 0)
                cleaned_data['effective_date'] = due_dates[vat_period_number - 1]
                
            except ValidationError:
                raise
            except Exception as e:
                logger.error(f'Error calculating effective date from period: {str(e)}')
                raise ValidationError({'vat_period_number': _('خطأ في حساب تاريخ السريان من رقم الفترة')})
        
        # حساب مبلغ القيمة المضافة
        if contract and contract.annual_rent:
            try:
                # استخدام الدالة المشتركة
                vat_amount = calculate_vat_amount(contract.annual_rent, percentage)
                cleaned_data['vat_amount'] = vat_amount
            
            except Exception as e:
                logger.error(f'Error calculating VAT amount: {str(e)}')
                raise ValidationError(_('خطأ في حساب مبلغ القيمة المضافة'))
        
        return cleaned_data


# ========================================
# 5. Termination Form (إنهاء عقد)
# ========================================

class TerminationForm(BaseContractModificationForm):
    """Form for contract termination"""
    
    class Meta(BaseContractModificationForm.Meta):
        fields = BaseContractModificationForm.Meta.fields + [
            'termination_date', 'termination_reason', 'termination_period_number'
        ]
        widgets = {
            **BaseContractModificationForm.Meta.widgets,
            'termination_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'readonly': 'readonly'
            }),
            'termination_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'سبب إنهاء العقد',
                'required': True
            }),
            'termination_period_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'رقم الفترة للإنهاء (اختياري)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modification_type'].initial = ModificationType.TERMINATION
        self.fields['modification_type'].widget = forms.HiddenInput()
        
        self.fields['termination_date'].label = 'تاريخ الإنهاء'
        self.fields['termination_reason'].label = 'سبب الإنهاء'
        self.fields['termination_period_number'].label = 'رقم فترة الإنهاء'
        self.fields['termination_period_number'].required = False
        
        # جعل termination_date للقراءة فقط - سيُحسب من termination_period_number
        self.fields['termination_date'].help_text = 'سيتم حسابه من رقم الفترة إذا تم تحديده'
        
        # عرض فترات الاستحقاق
        contract = None
        if 'contract' in self.data:
            try:
                contract_id = self.data.get('contract')
                contract = Contract.objects.get(id=contract_id)
            except (Contract.DoesNotExist, ValueError, TypeError):
                pass
        elif self.instance and self.instance.contract_id:
            contract = self.instance.contract
        
        if contract:
            try:
                due_dates = calculate_contract_due_dates(contract)
                if due_dates:
                    periods_info = '\n'.join([
                        f'الفترة {i+1}: {d.strftime("%Y-%m-%d")}'
                        for i, d in enumerate(due_dates[:10])
                    ])
                    remaining = len(due_dates) - 10
                    if remaining > 0:
                        periods_info += f'\n... و {remaining} فترة أخرى'
                    
                    self.fields['termination_period_number'].help_text = (
                        f'اختر رقم الفترة للإنهاء عندها (لن يُحتسب إيجار بعدها):\n{periods_info}'
                    )
            except Exception as e:
                logger.warning(f'Could not calculate due dates for termination: {str(e)}')
    
    def clean_termination_date(self):
        """التحقق من تاريخ الإنهاء"""
        term_date = self.cleaned_data.get('termination_date')
        contract = self.cleaned_data.get('contract')
        
        if term_date and contract:
            if term_date < contract.start_date:
                raise ValidationError(
                    _('تاريخ الإنهاء لا يمكن أن يكون قبل تاريخ بداية العقد')
                )
            
            if term_date > contract.end_date:
                raise ValidationError(
                    _('تاريخ الإنهاء لا يمكن أن يكون بعد تاريخ نهاية العقد')
                )
        
        return term_date
    
    def clean_termination_reason(self):
        """التحقق من سبب الإنهاء"""
        reason = self.cleaned_data.get('termination_reason')
        
        if not reason or len(reason.strip()) < 10:
            raise ValidationError(_('يجب تحديد سبب الإنهاء (10 أحرف على الأقل)'))
        
        return reason.strip()


# ========================================
# Unified Form (للـ Admin)
# ========================================

class ContractModificationAdminForm(forms.ModelForm):
    """
    Unified form for admin that shows/hides fields dynamically
    نموذج موحد للـ Admin مع إخفاء/إظهار ديناميكي
    """
    
    class Meta:
        model = ContractModification
        fields = '__all__'
        widgets = {
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'modification_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_modification_type'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'extension_months': forms.NumberInput(attrs={
                'class': 'form-control extension-field'
            }),
            'new_end_date': forms.DateInput(attrs={
                'class': 'form-control extension-field',
                'readonly': 'readonly'
            }),
            'old_rent_amount': forms.NumberInput(attrs={
                'class': 'form-control rent-change-field',
                'readonly': 'readonly'
            }),
            'new_rent_amount': forms.NumberInput(attrs={
                'class': 'form-control rent-change-field'
            }),
            'change_amount': forms.NumberInput(attrs={
                'class': 'form-control rent-change-field',
                'readonly': 'readonly'
            }),
            'change_percentage': forms.NumberInput(attrs={
                'class': 'form-control rent-change-field',
                'readonly': 'readonly'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control discount-field'
            }),
            'discount_period_number': forms.NumberInput(attrs={
                'class': 'form-control discount-field'
            }),
            'vat_percentage': forms.NumberInput(attrs={
                'class': 'form-control vat-field'
            }),
            'vat_amount': forms.NumberInput(attrs={
                'class': 'form-control vat-field',
                'readonly': 'readonly'
            }),
            'vat_period_number': forms.NumberInput(attrs={
                'class': 'form-control vat-field'
            }),
            'termination_date': forms.DateInput(attrs={
                'class': 'form-control termination-field',
                'type': 'date'
            }),
            'termination_reason': forms.Textarea(attrs={
                'class': 'form-control termination-field',
                'rows': 4
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # عرض العقود النشطة
        self.fields['contract'].queryset = Contract.objects.filter(
            status__in=['draft', 'active'],
            is_deleted=False
        ).select_related('tenant')
        
        # ملء old_rent_amount
        if self.instance and self.instance.contract:
            self.fields['old_rent_amount'].initial = self.instance.contract.annual_rent


# ========================================
# Form Factory
# ========================================

def get_modification_form(modification_type):
    """
    Factory function to get the appropriate form based on modification type
    دالة لإرجاع النموذج المناسب حسب نوع التعديل
    
    Args:
        modification_type: نوع التعديل
    
    Returns:
        Form class
    
    Example:
        >>> form_class = get_modification_form(ModificationType.EXTENSION)
        >>> form = form_class()
    """
    form_map = {
        ModificationType.EXTENSION: ExtensionForm,
        ModificationType.RENT_INCREASE: RentIncreaseForm,
        ModificationType.RENT_DECREASE: RentDecreaseForm,
        ModificationType.DISCOUNT: DiscountForm,
        ModificationType.VAT: VATForm,
        ModificationType.TERMINATION: TerminationForm,
    }
    
    form_class = form_map.get(modification_type, BaseContractModificationForm)
    logger.debug(f'Getting form class for modification type: {modification_type}')
    
    return form_class