# models/receipt_models.py

"""
Receipt/Payment Models
نماذج سندات القبض والمدفوعات
"""

from .common_imports_models import *
from .contract_models import Contract


# ========================================
# Choices/Enums
# ========================================

class ReceiptStatus(models.TextChoices):
    """حالة السند"""
    DRAFT = 'draft', _('مسودة')
    POSTED = 'posted', _('مرحل')
    CANCELLED = 'cancelled', _('ملغي')
    RETURNED = 'returned', _('مرتجع')


# ========================================
# Receipt Model
# ========================================

class Receipt(TimeStampedModel, UserTrackingModel, SoftDeleteModel):
      
    # ========================================
    # Relationships
    # ========================================
    contract = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        related_name='receipts',
        verbose_name=_('العقد'),
        help_text=_('العقد المرتبط بالسند')
    )
    
    # ========================================
    # Receipt Information
    # ========================================
    receipt_number = models.PositiveIntegerField(
        _('رقم السند'),
        unique=True,
        default=generate_receipt_number,
        db_index=True,
        help_text=_('رقم السند الفريد (يُولد تلقائياً)')
    )
    
    receipt_date = models.DateField(
        _('تاريخ السند'),
        default=date.today,
        db_index=True,
        help_text=_('تاريخ إصدار السند')
    )
    
    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=12,
        decimal_places=2,
        validators=[validate_positive_decimal],
        help_text=_('قيمة الدفعة')
    )
    
    # ========================================
    # Payment Details
    # ========================================
    payment_method = models.CharField(
        _('طريقة الدفع'),
        max_length=20,
        choices=PaymentMethod.choices,  # ✅ من common_imports_models
        default=PaymentMethod.CASH,
        help_text=_('طريقة الدفع المستخدمة')
    )
    
    reference_number = models.CharField(
        _('رقم المرجع'),
        max_length=100,
        blank=True,
        help_text=_('رقم الإيصال، الشيك، أو التحويل البنكي')
    )
    
    bank_name = models.CharField(
        _('اسم البنك'),
        max_length=200,
        blank=True,
        help_text=_('اسم البنك (للتحويل البنكي أو الشيك)')
    )
    
    check_number = models.CharField(
        _('رقم الشيك'),
        max_length=50,
        blank=True,
        help_text=_('رقم الشيك (إذا كانت طريقة الدفع شيك)')
    )
    
    check_date = models.DateField(
        _('تاريخ الشيك'),
        null=True,
        blank=True,
        help_text=_('تاريخ استحقاق الشيك')
    )

    # صورة إثبات الدفع (شيك أو تحويل)
    payment_proof = models.FileField(
        _('صورة إثبات الدفع'),
        upload_to='receipts/payment_proofs/%Y/%m/',
        blank=True,
        null=True,
        help_text=_('صورة الشيك أو إيصال التحويل (PDF أو صورة)')
    )

    # ========================================
    # Period Information
    # ========================================
    period_start = models.DateField(
        _('بداية الفترة'),
        null=True,
        blank=True,
        help_text=_('تاريخ بداية الفترة المدفوعة')
    )
    
    period_end = models.DateField(
        _('نهاية الفترة'),
        null=True,
        blank=True,
        help_text=_('تاريخ نهاية الفترة المدفوعة')
    )
    
    due_date = models.DateField(
        _('تاريخ الاستحقاق'),
        null=True,
        blank=True,
        help_text=_('تاريخ استحقاق الدفعة الأصلي')
    )
    
    # ========================================
    # Additional Fields for Billing Service
    # حقول إضافية لخدمة الحسابات
    # ========================================
    related_period_number = models.PositiveIntegerField(
        _('رقم الفترة المرتبطة'),
        null=True,
        blank=True,
        help_text=_('رقم فترة العقد المرتبطة بهذا السند (اختياري)')
    )
    
    payment_type = models.CharField(
        _('نوع الدفعة'),
        max_length=20,
        choices=[
            ('rent', _('إيجار')),
            ('vat', _('ضريبة القيمة المضافة')),
            ('advance', _('دفعة مقدمة')),
            ('charge', _('رسوم إضافية')),
        ],
        default='rent',
        help_text=_('نوع الدفعة (إيجار، ضريبة، إلخ)')
    )
    
    # ========================================
    # Status
    # ========================================
    status = models.CharField(
        _('حالة السند'),
        max_length=20,
        choices=ReceiptStatus.choices,
        default=ReceiptStatus.DRAFT,
        db_index=True,
        help_text=_('الحالة الحالية للسند')
    )
    
    posted_at = models.DateTimeField(
        _('تاريخ الترحيل'),
        null=True,
        blank=True,
        help_text=_('تاريخ ووقت ترحيل السند')
    )
    
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_receipts',
        verbose_name=_('رُحل بواسطة'),
        help_text=_('المستخدم الذي رحّل السند')
    )
    
    # ========================================
    # Cancellation Information
    # ========================================
    cancelled_at = models.DateTimeField(
        _('تاريخ الإلغاء'),
        null=True,
        blank=True,
        help_text=_('تاريخ ووقت إلغاء السند')
    )
    
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_receipts',
        verbose_name=_('أُلغي بواسطة'),
        help_text=_('المستخدم الذي ألغى السند')
    )
    
    cancellation_reason = models.TextField(
        _('سبب الإلغاء'),
        blank=True,
        help_text=_('سبب إلغاء السند')
    )
    
    # ========================================
    # Additional Information
    # ========================================
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات إضافية')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'receipts'
        verbose_name = _('سند قبض')
        verbose_name_plural = _('سندات القبض')
        ordering = ['-receipt_date', '-created_at']
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['contract', 'receipt_date']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['is_deleted']),
        ]
        permissions = [
            ('post_receipt', 'ترحيل سند قبض'),
            ('cancel_receipt', 'إلغاء سند قبض'),
            ('print_receipt', 'طباعة سند قبض'),
            ('export_receipt_pdf', 'تصدير سند PDF'),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"سند {self.receipt_number} - {format_currency(self.amount)}"
        
    @property
    def amount_in_words(self):
        """
        المبلغ بالحروف العربية
        """
        try:
            from rent.utils.tafqeet import tafqeet
            return tafqeet(self.amount)
        except ImportError:
            return str(self.amount)
    
    def clean(self):
        """Validation before saving"""
        super().clean()
        
        # التحقق من المبلغ
        if self.amount and self.amount <= 0:
            raise ValidationError({
                'amount': _('المبلغ يجب أن يكون أكبر من صفر')
            })
        
        # التحقق من الفترة
        if self.period_start and self.period_end:
            if self.period_start > self.period_end:
                raise ValidationError({
                    'period_end': _('نهاية الفترة يجب أن تكون بعد البداية')
                })
        
        # التحقق من طريقة الدفع
        if self.payment_method == PaymentMethod.CHECK:
            if not self.check_number:
                raise ValidationError({
                    'check_number': _('رقم الشيك مطلوب عند الدفع بالشيك')
                })
        
        # التحقق من إمكانية السداد للعقد
        if self.status == ReceiptStatus.DRAFT and self.contract:
            can_pay, message = self.contract.can_accept_payment(self.amount)
            if not can_pay:
                raise ValidationError({
                    'amount': _(f'لا يمكن قبول السند: {message}')
                })
    
    def save(self, *args, **kwargs):
        """Override save"""
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_receipt = Receipt.objects.get(pk=self.pk)
                old_status = old_receipt.status
            except Receipt.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # تحديث العقد عند تغيير الحالة إلى مرحل
        # if old_status != ReceiptStatus.POSTED and self.status == ReceiptStatus.POSTED:
        #     self.contract._update_total_paid()
        
        # تحديث العقد عند الإلغاء
        # elif old_status == ReceiptStatus.POSTED and self.status == ReceiptStatus.CANCELLED:
        #     self.contract._update_total_paid()
    
    def post_receipt(self, user=None):
        """
        Post/Finalize receipt
        ترحيل السند
        
        Args:
            user: User posting the receipt
            
        Returns:
            tuple: (success, message)
        """
        if self.status != ReceiptStatus.DRAFT:
            return False, _('يجب أن يكون السند في حالة مسودة')
        
        # التحقق من إمكانية السداد
        can_pay, message = self.contract.can_accept_payment(self.amount)
        if not can_pay:
            return False, message
        
        self.status = ReceiptStatus.POSTED
        self.posted_at = timezone.now()
        if user:
            self.posted_by = user
        
        self.save()
        
        return True, _('تم ترحيل السند بنجاح')
    
    def cancel_receipt(self, reason='', user=None):
        """
        Cancel receipt
        إلغاء السند
        
        Args:
            reason: Cancellation reason
            user: User cancelling the receipt
            
        Returns:
            tuple: (success, message)
        """
        if self.status == ReceiptStatus.CANCELLED:
            return False, _('السند ملغي مسبقاً')
        
        if self.status != ReceiptStatus.POSTED:
            return False, _('يمكن إلغاء السندات المرحلة فقط')
        
        self.status = ReceiptStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        if user:
            self.cancelled_by = user
        
        self.save()
        
        return True, _('تم إلغاء السند بنجاح')
    
    def is_late_payment(self):
        """
        Check if payment is late
        التحقق من تأخر الدفع
        
        Returns:
            bool: True if late
        """
        if not self.due_date:
            return False
        
        grace_days = self.contract.grace_period_days if self.contract else 0
        return is_overdue(self.due_date, grace_days)
    
    def calculate_late_fee(self):
        """
        Calculate late payment fee
        حساب غرامة التأخير
        
        Returns:
            Decimal: Late fee amount
        """
        if not self.is_late_payment():
            return Decimal('0.00')
        
        if not self.contract or not self.contract.late_fee_percentage:
            return Decimal('0.00')
        
        return self.amount * (self.contract.late_fee_percentage / Decimal('100'))
    
    def get_payment_period_months(self):
        """
        Calculate payment period in months
        حساب فترة الدفع بالأشهر
        
        Returns:
            float or None: Period in months
        """
        if not self.period_start or not self.period_end:
            return None
        
        return calculate_days_between(self.period_start, self.period_end) / 30
    
    def get_days_overdue(self):
        """
        Calculate days overdue
        حساب عدد أيام التأخير
        
        Returns:
            int: Days overdue (0 if not overdue)
        """
        if not self.due_date:
            return 0
        
        if self.receipt_date <= self.due_date:
            return 0
        
        return calculate_days_between(self.due_date, self.receipt_date)
    
    def get_covered_periods(self):
        if not self.contract or not self.amount:
            return []

        calculator = self.contract.calculator
        return calculator.calculate_payment_distribution(self.amount)



    def get_tenant(self):
        """
        Get tenant from contract
        الحصول على المستأجر من العقد
        
        Returns:
            Tenant: The tenant
        """
        return self.contract.tenant if self.contract else None
    
    def get_statistics(self):
        """
        Get comprehensive receipt statistics
        الحصول على إحصائيات شاملة للسند
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            'receipt_number': self.receipt_number,
            'contract_number': self.contract.contract_number if self.contract else None,
            'tenant': self.get_tenant().name if self.get_tenant() else None,
            'amount': self.amount,
            'status': self.get_status_display(),
            'payment_method': self.get_payment_method_display(),
            'receipt_date': self.receipt_date,
            'is_late': self.is_late_payment(),
            'days_overdue': self.get_days_overdue(),
            'late_fee': self.calculate_late_fee(),
            'period_months': self.get_payment_period_months(),
        }


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=Receipt)
def receipt_post_save(sender, instance, created, **kwargs):
    """Signal handler after receipt is saved"""
    if created:
        # يمكن إضافة منطق عند إنشاء سند جديد
        pass
    
    # إنشاء إشعار عند الترحيل
    if instance.status == ReceiptStatus.POSTED:
        # يمكن إنشاء إشعار للمستخدم
        pass


@receiver(pre_save, sender=Receipt)
def receipt_pre_save(sender, instance, **kwargs):
    """Signal handler before receipt is saved"""
    # السماح بالسندات للعقود النشطة والمجدة والمنتهية والملغاة (لتسديد المستحقات)
    if instance.contract and instance.contract.status not in [
        ContractStatus.ACTIVE,
        ContractStatus.RENEWED,
        ContractStatus.EXPIRED,
        ContractStatus.TERMINATED,
    ]:
        if instance.status != ReceiptStatus.CANCELLED:
            raise ValidationError(_('لا يمكن إنشاء سند لعقد غير نشط'))