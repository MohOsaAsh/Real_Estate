"""
Contract Modification Models - Enhanced Version
نماذج تعديلات العقود - النسخة المحسنة

يدعم 6 أنواع من التعديلات:
1. Extension - تمديد عقد
2. Rent Increase - زيادة إيجار
3. Rent Decrease - تخفيض إيجار
4. Discount - خصم
5. VAT - قيمة مضافة
6. Termination - إنهاء عقد
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .common_imports_models import *
from .contract_models import Contract

# استيراد الدوال المساعدة
from rent.utils.contract_utils import (
    calculate_contract_due_dates,
    format_due_dates_error_message,
    calculate_rent_change,
    calculate_vat_amount
)

# إعداد Logger
logger = logging.getLogger(__name__)


# ========================================
# Enums
# ========================================

class ModificationType(models.TextChoices):
    """أنواع التعديلات"""
    EXTENSION = 'extension', _('تمديد عقد')
    RENT_INCREASE = 'rent_increase', _('زيادة إيجار')
    RENT_DECREASE = 'rent_decrease', _('تخفيض إيجار')
    DISCOUNT = 'discount', _('خصم')
    VAT = 'vat', _('قيمة مضافة')
    TERMINATION = 'termination', _('إنهاء عقد')


# ========================================
# ContractModification Model
# ========================================

class ContractModification(TimeStampedModel, UserTrackingModel):
    """
    Contract Modification Model - Enhanced Version
    نموذج تعديلات العقود - النسخة المحسنة
    """
    
    # ========================================
    # Relationships
    # ========================================
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='modifications',
        verbose_name=_('العقد'),
        help_text=_('العقد المطلوب تعديله')
    )
    
    # ========================================
    # Basic Information
    # ========================================
    modification_type = models.CharField(
        _('نوع التعديل'),
        max_length=20,
        choices=ModificationType.choices,
        db_index=True,
        help_text=_('نوع التعديل المطلوب')
    )
    
    effective_date = models.DateField(
        _('تاريخ السريان'),
        db_index=True,
        help_text=_('تاريخ سريان التعديل')
    )
    
    # ========================================
    # 1. Extension Fields (تمديد العقد)
    # ========================================
    extension_months = models.PositiveIntegerField(
        _('عدد أشهر التمديد'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_('عدد الأشهر المطلوب تمديدها')
    )
    
    new_end_date = models.DateField(
        _('تاريخ الانتهاء الجديد'),
        null=True,
        blank=True,
        help_text=_('تاريخ انتهاء العقد بعد التمديد (يُحسب تلقائياً)')
    )
    
    # ========================================
    # 2. Rent Change Fields (زيادة/تخفيض الإيجار)
    # ========================================
    old_rent_amount = models.DecimalField(
        _('قيمة الإيجار القديمة'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('قيمة الإيجار قبل التعديل')
    )
    
    new_rent_amount = models.DecimalField(
        _('قيمة الإيجار الجديدة'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('قيمة الإيجار بعد التعديل')
    )
    
    change_amount = models.DecimalField(
        _('مبلغ التغيير'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('مبلغ الزيادة أو التخفيض')
    )
    
    change_percentage = models.DecimalField(
        _('نسبة التغيير %'),
        max_digits=10,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[MinValueValidator(-100), MaxValueValidator(100)],
        help_text=_('نسبة الزيادة (+) أو التخفيض (-) %')
    )
    
    # ========================================
    # 3. Discount Fields (خصم)
    # ========================================
    discount_amount = models.DecimalField(
        _('مبلغ الخصم'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('مبلغ الخصم على الفترة')
    )
    
    discount_period_number = models.PositiveIntegerField(
        _('رقم فترة الخصم'),
        null=True,
        blank=True,
        help_text=_('رقم الفترة المطلوب تطبيق الخصم عليها')
    )
    
    # ========================================
    # 4. VAT Fields (قيمة مضافة)
    # ========================================
    VAT_INPUT_PERCENTAGE = 'percentage'
    VAT_INPUT_FIXED = 'fixed'
    VAT_INPUT_TYPE_CHOICES = [
        (VAT_INPUT_PERCENTAGE, _('نسبة من الإيجار')),
        (VAT_INPUT_FIXED, _('مبلغ مقطوع')),
    ]

    vat_input_type = models.CharField(
        _('طريقة إدخال القيمة المضافة'),
        max_length=20,
        choices=VAT_INPUT_TYPE_CHOICES,
        default=VAT_INPUT_PERCENTAGE,
        blank=True,
        help_text=_('اختر طريقة إدخال القيمة المضافة: نسبة أو مبلغ مقطوع')
    )

    vat_percentage = models.DecimalField(
        _('نسبة القيمة المضافة %'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal('15.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('نسبة القيمة المضافة % (افتراضي: 15%)')
    )

    vat_amount = models.DecimalField(
        _('مبلغ القيمة المضافة'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('مبلغ القيمة المضافة (يُحسب تلقائياً أو يُدخل مباشرة)')
    )

    vat_period_number = models.PositiveIntegerField(
        _('رقم فترة القيمة المضافة'),
        null=True,
        blank=True,
        help_text=_('رقم الفترة المطلوب تطبيق القيمة المضافة عليها')
    )
    
    # ========================================
    # 5. Termination Fields (إنهاء العقد)
    # ========================================
    termination_date = models.DateField(
        _('تاريخ الإنهاء الفعلي'),
        null=True,
        blank=True,
        help_text=_('تاريخ إنهاء العقد فعلياً')
    )
    
    termination_reason = models.TextField(
        _('سبب الإنهاء'),
        blank=True,
        help_text=_('سبب إنهاء العقد قبل موعده')
    )
    
    termination_period_number = models.PositiveIntegerField(
        _('رقم فترة الإنهاء'),
        null=True,
        blank=True,
        help_text=_('رقم الفترة التي سيتم الإنهاء عندها - لا يتم احتساب إيجار بعدها')
    )
    
    # ========================================
    # Status & Application
    # ========================================
    is_applied = models.BooleanField(
        _('مُطبّق'),
        default=False,
        db_index=True,
        help_text=_('هل تم تطبيق التعديل على العقد؟')
    )
    
    applied_at = models.DateTimeField(
        _('تاريخ التطبيق'),
        null=True,
        blank=True,
        help_text=_('تاريخ ووقت تطبيق التعديل')
    )
    
    applied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applied_modifications',
        verbose_name=_('طُبّق بواسطة'),
        help_text=_('المستخدم الذي طبّق التعديل')
    )
    
    # ========================================
    # Additional Info
    # ========================================
    description = models.TextField(
        _('الوصف'),
        blank=True,
        help_text=_('وصف تفصيلي للتعديل')
    )
    
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('ملاحظات إضافية')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'contract_modifications'
        verbose_name = _('تعديل عقد')
        verbose_name_plural = _('تعديلات العقود')
        ordering = ['-effective_date', '-created_at']
        indexes = [
            models.Index(fields=['contract', 'modification_type']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['is_applied']),
        ]
        permissions = [
            ('apply_contractmodification', 'تطبيق تعديل عقد'),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.contract.contract_number} - {self.get_modification_type_display()} - {self.effective_date}"
    
    def clean(self):
        """Validation before saving - Enhanced Version"""
        super().clean()
        
        # استخدام dictionary للـ validators
        validators = {
            ModificationType.EXTENSION: self._validate_extension,
            ModificationType.RENT_INCREASE: self._validate_rent_change,
            ModificationType.RENT_DECREASE: self._validate_rent_change,
            ModificationType.DISCOUNT: self._validate_discount,
            ModificationType.VAT: self._validate_vat,
            ModificationType.TERMINATION: self._validate_termination,
        }
        
        validator = validators.get(self.modification_type)
        if validator:
            try:
                validator()
            except Exception as e:
                logger.error(
                    f'Validation error for modification type {self.modification_type}: {str(e)}'
                )
                raise
    
    def _validate_extension(self):
        """التحقق من حقول التمديد"""
        if not self.extension_months:
            raise ValidationError({
                'extension_months': _('يجب تحديد عدد أشهر التمديد')
            })
        
        # حساب تاريخ الانتهاء الجديد
        if self.contract and self.contract.end_date:
            from dateutil.relativedelta import relativedelta
            self.new_end_date = self.contract.end_date + relativedelta(
                months=self.extension_months
            )
    
    def _validate_rent_change(self):
        """التحقق من حقول زيادة/تخفيض الإيجار"""
        if not self.new_rent_amount and not self.change_amount:
            raise ValidationError({
                'new_rent_amount': _('يجب تحديد قيمة الإيجار الجديدة أو مبلغ التغيير')
            })
        
        # التحقق من أن تاريخ السريان هو تاريخ استحقاق
        if self.contract:
            self._validate_effective_date_is_due_date()
        
        # ملء القيم التلقائية
        if self.contract and not self.old_rent_amount:
            self.old_rent_amount = self.contract.annual_rent


        if self.new_rent_amount and self.old_rent_amount:
            from rent.utils.contract_utils import calculate_rent_change
            self.change_amount, self.change_percentage = calculate_rent_change(
                self.old_rent_amount,
                self.new_rent_amount
            )
        elif self.change_amount and self.old_rent_amount:
            self.new_rent_amount = self.old_rent_amount + self.change_amount
            from rent.utils.contract_utils import calculate_rent_change
            _, self.change_percentage = calculate_rent_change(
                self.old_rent_amount,
                self.new_rent_amount
            )
        
        # حساب المبالغ باستخدام الدالة المساعدة
        # if self.new_rent_amount and self.old_rent_amount:
        #     self.change_amount, self.change_percentage = calculate_rent_change(
        #         self.old_rent_amount,
        #         self.new_rent_amount
        #     )
        # elif self.change_amount and self.old_rent_amount:
        #     self.new_rent_amount = self.old_rent_amount + self.change_amount
        #     _, self.change_percentage = calculate_rent_change(
        #         self.old_rent_amount,
        #         self.new_rent_amount
        #     )
    
    def _validate_discount(self):
        """التحقق من حقول الخصم"""
        if not self.discount_amount:
            raise ValidationError({
                'discount_amount': _('يجب تحديد مبلغ الخصم')
            })
        if not self.discount_period_number:
            raise ValidationError({
                'discount_period_number': _('يجب تحديد رقم الفترة المطلوب الخصم عليها')
            })
    
    def _validate_vat(self):
        """التحقق من حقول القيمة المضافة"""
        if not self.vat_period_number:
            raise ValidationError({
                'vat_period_number': _('يجب تحديد رقم الفترة المطلوب تطبيق القيمة المضافة عليها')
            })

        # التحقق حسب طريقة الإدخال
        if self.vat_input_type == self.VAT_INPUT_FIXED:
            # مبلغ مقطوع - يجب إدخال المبلغ مباشرة
            if not self.vat_amount or self.vat_amount <= 0:
                raise ValidationError({
                    'vat_amount': _('يجب إدخال مبلغ القيمة المضافة')
                })
            # مسح النسبة لأنها غير مستخدمة في هذا الوضع
            self.vat_percentage = None
        else:
            # نسبة من الإيجار (الوضع الافتراضي)
            if not self.vat_percentage:
                self.vat_percentage = Decimal('15.00')  # القيمة الافتراضية

            # حساب مبلغ القيمة المضافة باستخدام الدالة المساعدة
            if self.contract and self.contract.annual_rent:
                self.vat_amount = calculate_vat_amount(
                    self.contract.annual_rent,
                    self.vat_percentage
                )
    
    def _validate_termination(self):
        """التحقق من حقول إنهاء العقد"""
        if not self.termination_date:
            raise ValidationError({
                'termination_date': _('يجب تحديد تاريخ الإنهاء الفعلي')
            })
        
        if self.contract and self.contract.start_date:
            if self.termination_date < self.contract.start_date:
                raise ValidationError({
                    'termination_date': _('تاريخ الإنهاء لا يمكن أن يكون قبل تاريخ بداية العقد')
                })
        
        # التحقق من رقم فترة الإنهاء إذا كان موجوداً
        if self.termination_period_number and self.contract:
            try:
                due_dates = calculate_contract_due_dates(self.contract)
                if not due_dates:
                    raise ValidationError({
                        'termination_period_number': _('لا يمكن حساب فترات الاستحقاق للعقد')
                    })
                
                if self.termination_period_number < 1 or self.termination_period_number > len(due_dates):
                    raise ValidationError({
                        'termination_period_number': _(f'رقم الفترة يجب أن يكون بين 1 و {len(due_dates)}')
                    })
                
                # حساب تاريخ الإنهاء من رقم الفترة
                self.termination_date = due_dates[self.termination_period_number - 1]
                self.effective_date = self.termination_date
            except ValidationError:
                raise
            except Exception as e:
                logger.error(f'Error validating termination period: {str(e)}')
                raise ValidationError({
                    'termination_period_number': _('خطأ في التحقق من رقم الفترة')
                })
    
    def _validate_effective_date_is_due_date(self):
        """
        التحقق من أن تاريخ السريان هو أحد تواريخ الاستحقاق
        Enhanced with utility function
        """
        if not self.contract or not self.effective_date:
            return
        
        due_dates = calculate_contract_due_dates(self.contract)
        
        if not due_dates:
            raise ValidationError({
                'effective_date': _('لا يمكن حساب تواريخ الاستحقاق للعقد')
            })
        
        if self.effective_date not in due_dates:
            raise ValidationError({
                'effective_date': format_due_dates_error_message(due_dates)
            })
    
    @transaction.atomic
    def apply_modification(self, user=None):
        """
        تطبيق التعديل على العقد
        
        Args:
            user: المستخدم الذي يطبق التعديل
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # التحقق من أن التعديل لم يُطبق مسبقاً
        if self.is_applied:
            logger.warning(
                f'Attempted to apply already applied modification: ID={self.id}'
            )
            return False, _('التعديل مُطبّق مسبقاً')
        
        try:
            logger.info(
                f'Starting to apply modification: ID={self.id}, '
                f'Type={self.modification_type}, '
                f'Contract={self.contract.contract_number}'
            )
            
            # ============================================
            # 1. تمديد العقد
            # ============================================
            if self.modification_type == ModificationType.EXTENSION:
                if not self.new_end_date:
                    return False, 'يجب تحديد تاريخ النهاية الجديد'
                
                self.contract.end_date = self.new_end_date
                self.contract.save(update_fields=['end_date'])
                
                message = f'تم تمديد العقد {self.extension_months} شهر حتى {self.new_end_date}'
                
                logger.info(
                    f'Extension applied: Contract={self.contract.contract_number}, '
                    f'New end date={self.new_end_date}'
                )
            
            # ============================================
            # 2. زيادة/تخفيض الإيجار
            # ============================================
            elif self.modification_type in [ModificationType.RENT_INCREASE, ModificationType.RENT_DECREASE]:
                if not self.new_rent_amount:
                    return False, 'يجب تحديد قيمة الإيجار الجديدة'
                
                # تحديث الإيجار في العقد
                self.contract.annual_rent = self.new_rent_amount
                self.contract.save(update_fields=['annual_rent'])
                
                change_type = 'زيادة' if self.modification_type == ModificationType.RENT_INCREASE else 'تخفيض'
                message = f'تم {change_type} الإيجار من {self.old_rent_amount:,.2f} إلى {self.new_rent_amount:,.2f} ريال'
                
                logger.info(
                    f'Rent change applied: Contract={self.contract.contract_number}, '
                    f'Old={self.old_rent_amount}, New={self.new_rent_amount}'
                )
            
            # ============================================
            # 3. الخصم
            # ============================================
            elif self.modification_type == ModificationType.DISCOUNT:
                if not self.discount_amount or self.discount_amount <= 0:
                    return False, 'يجب تحديد قيمة الخصم'
                
                # الخصم يُسجل فقط في ContractModification
                # لا نُنشئ Receipt منفصل - كشف الحساب سيأخذه تلقائياً
                
                message = f'تم تطبيق خصم قدره {self.discount_amount:,.2f} ريال'
                
                # إضافة رقم الفترة إذا كان موجوداً
                if hasattr(self, 'discount_period') and self.discount_period:
                    message += f' على الفترة رقم {self.discount_period}'
                
                # إضافة الوصف
                if self.description:
                    message += f' - {self.description}'
                
                logger.info(
                    f'Discount applied: Modification={self.id}, '
                    f'Contract={self.contract.contract_number}, '
                    f'Amount={self.discount_amount}, '
                    f'Period={getattr(self, "discount_period", "N/A")}'
                )
            
            # ============================================
            # 4. القيمة المضافة (VAT)
            # ============================================
            elif self.modification_type == ModificationType.VAT:
                if not self.vat_amount or self.vat_amount <= 0:
                    return False, 'يجب تحديد قيمة الضريبة المضافة'
                
                # القيمة المضافة تُسجل فقط في ContractModification
                # كشف الحساب سيأخذها تلقائياً
                
                message = f'تم تسجيل قيمة مضافة {self.vat_percentage}% = {self.vat_amount:,.2f} ريال'
                
                if hasattr(self, 'vat_period_number') and self.vat_period_number:
                    message += f' على الفترة رقم {self.vat_period_number}'
                
                logger.info(
                    f'VAT registered: Modification={self.id}, '
                    f'Percentage={self.vat_percentage}%, '
                    f'Amount={self.vat_amount}, '
                    f'Period={getattr(self, "vat_period_number", "N/A")}'
                )
            
            # ============================================
            # 5. إنهاء العقد
            # ============================================
            elif self.modification_type == ModificationType.TERMINATION:
                if not self.termination_date:
                    return False, 'يجب تحديد تاريخ الإنهاء'
                
                from .contract_models import ContractStatus, PropertyStatus
                
                # تحديث حالة العقد
                self.contract.status = ContractStatus.TERMINATED
                self.contract.actual_end_date = self.termination_date
                self.contract.termination_reason = self.termination_reason
                self.contract.save(update_fields=['status', 'actual_end_date', 'termination_reason'])
                
                # تحرير الوحدات
                self.contract._update_units_status(PropertyStatus.AVAILABLE)
                
                message = f'تم إنهاء العقد بتاريخ {self.termination_date} وتحرير الوحدات'
                
                # إضافة معلومات السبب إذا كان موجوداً
                if self.termination_reason:
                    message += f' - السبب: {self.termination_reason}'
                
                logger.info(
                    f'Contract terminated: Contract={self.contract.contract_number}, '
                    f'Date={self.termination_date}, '
                    f'Reason={self.termination_reason or "N/A"}'
                )
            
            # ============================================
            # نوع غير معروف
            # ============================================
            else:
                message = 'تم تطبيق التعديل'
                logger.warning(
                    f'Unknown modification type applied: {self.modification_type}'
                )
            
            # ============================================
            # تحديث حالة التطبيق
            # ============================================
            self.is_applied = True
            self.applied_at = timezone.now()
            self.applied_by = user
            self.save(update_fields=['is_applied', 'applied_at', 'applied_by'])
            
            logger.info(
                f'Modification applied successfully: ID={self.id}, '
                f'Type={self.modification_type}, '
                f'Message={message}'
            )
            
            return True, message
        
        except Exception as e:
            logger.error(
                f'Error applying modification: ID={self.id}, '
                f'Type={self.modification_type}, '
                f'Error={str(e)}',
                exc_info=True
            )
            return False, f'خطأ في تطبيق التعديل: {str(e)}'
            
        
    def get_summary(self):
        """Get summary of modification"""
        if self.modification_type == ModificationType.EXTENSION:
            return f'تمديد {self.extension_months} شهر حتى {self.new_end_date}'
        
        elif self.modification_type == ModificationType.RENT_INCREASE:
            return f'زيادة من {self.old_rent_amount} إلى {self.new_rent_amount} (+{self.change_percentage:.1f}%)'
        
        elif self.modification_type == ModificationType.RENT_DECREASE:
            return f'تخفيض من {self.old_rent_amount} إلى {self.new_rent_amount} ({self.change_percentage:.1f}%)'
        
        elif self.modification_type == ModificationType.DISCOUNT:
            return f'خصم {self.discount_amount} على الفترة {self.discount_period_number}'
        
        elif self.modification_type == ModificationType.VAT:
            return f'قيمة مضافة {self.vat_percentage}% = {self.vat_amount} على الفترة {self.vat_period_number}'
        
        elif self.modification_type == ModificationType.TERMINATION:
            return f'إنهاء بتاريخ {self.termination_date}'
        
        return self.get_modification_type_display()
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate values"""
        # استدعاء clean للحسابات التلقائية
        try:
            self.full_clean()
        except ValidationError as e:
            logger.warning(
                f'Validation warning during save: ID={self.id if self.pk else "new"}, '
                f'Error={str(e)}'
            )
            # لا نرفع الخطأ هنا لأنه سيتم رفعه في الـ view
            pass
        
        super().save(*args, **kwargs)
        
        logger.debug(
            f'Modification saved: ID={self.id}, '
            f'Type={self.modification_type}, '
            f'Applied={self.is_applied}'
        )

    # models/contract_modification_models.py


    @property
    def settlement_calculation(self):
        """
        حساب التسوية ديناميكياً
        يُستدعى عند الحاجة فقط
        """
        if self.modification_type != ModificationType.TERMINATION:
            return None
        
        if not self.termination_date:
            return None
        
        from rent.utils.contract_utils import calculate_termination_settlement
        
        return calculate_termination_settlement(
            self.contract,
            self.termination_date
        )
    
    @property
    def outstanding_balance(self):
        """المديونية المتبقية - محسوبة ديناميكياً"""
        settlement = self.settlement_calculation
        if settlement and settlement.get('success'):
            return settlement['outstanding_balance']
        return Decimal('0.00')
    
    @property
    def prorated_rent(self):
        """الإيجار الجزئي - محسوب ديناميكياً"""
        settlement = self.settlement_calculation
        if settlement and settlement.get('success'):
            return settlement['prorated_rent']
        return Decimal('0.00')
    
    @property
    def total_amount_due(self):
        """إجمالي المبلغ المستحق - محسوب ديناميكياً"""
        settlement = self.settlement_calculation
        if settlement and settlement.get('success'):
            return settlement['total_amount_due']
        return Decimal('0.00')
    
    @property
    def settlement_details(self):
        """تفاصيل التسوية - محسوبة ديناميكياً"""
        settlement = self.settlement_calculation
        if settlement and settlement.get('success'):
            return settlement['settlement_details']
        return {}
    
    @property
    def has_outstanding_balance(self):
        """هل يوجد مديونية؟"""
        return self.outstanding_balance > 0
    
    @property
    def settlement_status(self):
        """حالة التسوية"""
        balance = self.outstanding_balance
        
        if balance > 0:
            return {
                'status': 'outstanding',
                'label': 'مديونية',
                'class': 'danger',
                'icon': 'exclamation-triangle'
            }
        elif balance < 0:
            return {
                'status': 'overpaid',
                'label': 'رصيد زائد',
                'class': 'info',
                'icon': 'info-circle'
            }
        else:
            return {
                'status': 'settled',
                'label': 'متوازن',
                'class': 'success',
                'icon': 'check-circle'
            }