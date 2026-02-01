"""
Payment Forms - Fixed Version
نماذج المدفوعات والإيصالات - نسخة محدثة
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from datetime import date

from rent.models import Receipt, Contract


# Common Widgets
COMMON_WIDGETS = {
    'text_input': lambda placeholder='': forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': placeholder
    }),
    'number_input': lambda: forms.NumberInput(attrs={
        'class': 'form-control',
        'step': '0.01',
        'min': '0'
    }),
    'date_input': lambda: forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date'
    }),
    'textarea': lambda: forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 4
    }),
    'select': lambda: forms.Select(attrs={
        'class': 'form-select'
    }),
}


class BaseModelForm(forms.ModelForm):
    """Base form with common functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add 'form-control' class to all fields
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'


class ReceiptForm(BaseModelForm):
    """نموذج سند القبض - Fixed Version"""
    
    class Meta:
        model = Receipt
        fields = [
            'contract', 'receipt_number', 'receipt_date',
            'amount', 'payment_method', 'reference_number',
            'check_number', 'check_date', 'bank_name',
            'period_start', 'period_end', 'due_date',
            'status', 'notes'
        ]
        widgets = {
            'contract': COMMON_WIDGETS['select'](),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                #'readonly': 'readonly'
            }),
            'receipt_date': COMMON_WIDGETS['date_input'](),
            'amount': COMMON_WIDGETS['number_input'](),
            'payment_method': COMMON_WIDGETS['select'](),
            'reference_number': COMMON_WIDGETS['text_input']('رقم الإيصال/الشيك/التحويل'),
            'check_number': COMMON_WIDGETS['text_input']('رقم الشيك'),
            'check_date': COMMON_WIDGETS['date_input'](),
            'bank_name': COMMON_WIDGETS['text_input']('اسم البنك'),
            'period_start': COMMON_WIDGETS['date_input'](),
            'period_end': COMMON_WIDGETS['date_input'](),
            'due_date': COMMON_WIDGETS['date_input'](),
            'status': COMMON_WIDGETS['select'](),
            'notes': COMMON_WIDGETS['textarea'](),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # عرض العقود النشطة + المنتهية + الملغاة
        # (دون حساب مسبق للمستحقات لتفادي أي أخطاء في الخدمات المالية)
        self.fields['contract'].queryset = Contract.objects.filter(
            status__in=['active', 'expired', 'terminated'],
            is_deleted=False
        ).select_related('tenant').order_by('-created_at')
        
        # تخصيص عرض العقد في القائمة المنسدلة
        self.fields['contract'].label_from_instance = self.contract_label_from_instance
        
        # تعيين تاريخ الإيصال الافتراضي
        if not self.instance.pk:
            self.fields['receipt_date'].initial = date.today()
        
        # جعل بعض الحقول اختيارية في الواجهة
        self.fields['check_number'].required = False
        self.fields['check_date'].required = False
        self.fields['bank_name'].required = False
        self.fields['reference_number'].required = False
        self.fields['period_start'].required = False
        self.fields['period_end'].required = False
        self.fields['due_date'].required = False
        self.fields['notes'].required = False
    
    def contract_label_from_instance(self, obj):
        """
        تخصيص كيفية عرض العقد في القائمة المنسدلة
        """
        try:
            # محاولة الوصول للوحدة بشكل آمن
            unit_info = ""
            if hasattr(obj, 'unit') and obj.unit:
                unit_info = f" - وحدة: {obj.unit.unit_number}"
            
            return f"{obj.contract_number} - {obj.tenant.name}{unit_info}"
        except Exception:
            # في حالة حدوث خطأ، نعرض المعلومات الأساسية فقط
            return f"{obj.contract_number} - {obj.tenant.name}"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()
        
        # التحقق من المبلغ
        amount = cleaned_data.get('amount')
        if amount and amount <= 0:
            self.add_error('amount', 'المبلغ يجب أن يكون أكبر من صفر')
        
        # التحقق من طريقة الدفع
        payment_method = cleaned_data.get('payment_method')
        check_number = cleaned_data.get('check_number')
        
        if payment_method == 'check' and not check_number:
            self.add_error('check_number', 'رقم الشيك مطلوب عند الدفع بالشيك')
        
        # التحقق من الفترة
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        
        if period_start and period_end:
            if period_start > period_end:
                self.add_error('period_end', 'نهاية الفترة يجب أن تكون بعد البداية')
        
        return cleaned_data
    
    def save(self, commit=True):
        """حفظ النموذج"""
        instance = super().save(commit=False)
        
        # يمكن إضافة منطق إضافي هنا قبل الحفظ
        
        if commit:
            instance.save()
        
        return instance


class ReceiptFilterForm(forms.Form):
    """نموذج تصفية سندات القبض"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'البحث برقم السند، العقد، أو المستأجر...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'جميع الحالات')] + list(Receipt._meta.get_field('status').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'من تاريخ'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'إلى تاريخ'
        })
    )
    
    payment_method = forms.ChoiceField(
        required=False,
        choices=[('', 'جميع طرق الدفع')] + list(Receipt._meta.get_field('payment_method').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ReceiptCancelForm(forms.Form):
    """نموذج إلغاء سند القبض"""
    
    cancellation_reason = forms.CharField(
        label='سبب الإلغاء',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'أدخل سبب إلغاء السند...',
            'required': True
        })
    )
    
    def clean_cancellation_reason(self):
        reason = self.cleaned_data.get('cancellation_reason')
        if not reason or not reason.strip():
            raise forms.ValidationError('يجب إدخال سبب الإلغاء')
        return reason.strip()