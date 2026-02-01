# models/contract_models.py

from django.db.models import Q  # استيراد صريح
from .common_imports_models import *
from .unit_models import Unit
from .tenant_models import Tenant
from rent.services.contract_financial_service import ContractFinancialService


# ========================================
# Contract Model
# ========================================

class Contract(TimeStampedModel, UserTrackingModel, SoftDeleteModel):
       
    # ========================================
    # Relationships
    # ========================================
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name=_('المستأجر'),
        help_text=_('المستأجر الموقع على العقد')
    )
    
    # ✅ UPDATED: حقل واحد فقط للوحدات (ManyToMany)
    units = models.ManyToManyField(
        Unit,
        related_name='contracts',
        verbose_name=_('الوحدات'),
        help_text=_('الوحدات المؤجرة (وحدة واحدة أو أكثر)')
    )
    
    # ========================================
    # Contract Information
    # ========================================
    contract_number = models.PositiveIntegerField(
        _('رقم العقد'),        
        unique=True,
        default=generate_contract_number,
        db_index=True,
        help_text=_('رقم العقد الفريد (يُولد تلقائياً)')
    )
    
    start_date = models.DateField(
        _('تاريخ البداية'),
        db_index=True,
        help_text=_('تاريخ بداية سريان العقد')
    )
    
    contract_duration_months = models.PositiveIntegerField(
        _('مدة العقد (أشهر)'),
        default=12,
        validators=[MinValueValidator(1)],
        help_text=_('مدة العقد بالأشهر (افتراضي: 12 شهر)')
    )
    
    end_date = models.DateField(
        _('تاريخ النهاية'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('تاريخ انتهاء العقد (يُحسب تلقائياً من تاريخ البداية + المدة)')
    )
    
    # ========================================
    # Financial Information
    # ========================================
    payment_frequency = models.CharField(
        _('دورية السداد'),
        max_length=20,
        choices=RentType.choices,
        default=RentType.MONTHLY,
        help_text=_('كم مرة يتم الدفع (شهري، ربع سنوي، إلخ)')
    )
    
    payment_day = models.PositiveIntegerField(
        _('يوم الدفع من الشهر'),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text=_('اليوم المحدد من الشهر للدفع (1-28)')
    )
    
    # ========================================
    # Additional Fields for Billing Service
    # ========================================
   
    annual_rent = models.DecimalField(
        _('الإيجار السنوي'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal,MinValueValidator(1)],
        help_text=_('إجمالي الإيجار السنوي')
    )
    
    security_deposit = models.DecimalField(
        _('الضمان المالي'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[validate_positive_decimal],
        help_text=_('مبلغ التأمين/الضمان المالي')
    )
    
    # ========================================
    # Payment Settings
    # ========================================
    allow_advance_payment = models.BooleanField(
        _('السماح بالسداد المقدم'),
        default=True,
        help_text=_('هل يُسمح بدفع مقدم لفترات مستقبلية؟')
    )
        
    late_fee_percentage = models.DecimalField(
        _('نسبة غرامة التأخير %'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[validate_percentage],
        help_text=_('نسبة الغرامة على المدفوعات المتأخرة')
    )
    
    # ========================================
    # Status
    # ========================================
    status = models.CharField(
        _('حالة العقد'),
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.DRAFT,
        db_index=True,
        help_text=_('الحالة الحالية للعقد')
    )
    
    # ========================================
    # Termination Information
    # ========================================
    actual_end_date = models.DateField(
        _('تاريخ الإنهاء الفعلي'),
        null=True,
        blank=True,
        help_text=_('التاريخ الفعلي لإنهاء العقد (إذا تم إنهاؤه مبكراً)')
    )
    
    termination_reason = models.TextField(
        _('سبب الإنهاء'),
        blank=True,
        help_text=_('سبب إنهاء العقد مبكراً')
    )
    
    termination_penalty = models.DecimalField(
        _('غرامة الإنهاء'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('قيمة الغرامة في حالة الإنهاء المبكر')
    )
    
   
    # ========================================
    # Additional Information
    # ========================================
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات إضافية عن العقد')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'contracts'
        verbose_name = _('عقد')
        verbose_name_plural = _('العقود')
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status']),
            models.Index(fields=['is_deleted']),
        ]
        permissions = [
            ('activate_contract', 'تفعيل عقد'),
            ('terminate_contract', 'إنهاء عقد'),
            ('view_contract_statement', 'عرض كشف حساب العقد'),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        units_count = self.units.count() if self.pk else 0
        units_text = f"{units_count} وحدة" if units_count != 1 else "وحدة واحدة"
        return f"عقد {self.contract_number} - {self.tenant.name} ({units_text})"
    
    def delete(self, *args, **kwargs):
        """Override delete to free up units"""
        # عند الحذف، إعادة الوحدات للحالة المتاحة
        self._update_units_status(PropertyStatus.AVAILABLE)
        super().delete(*args, **kwargs)
    
    def clean(self):
        """Validation before saving"""
        super().clean()
        
        # حساب end_date إذا لم يكن موجوداً (لأن clean يُستدعى قبل save)
        if self.start_date and not self.end_date:
            from dateutil.relativedelta import relativedelta
            if not self.contract_duration_months:
                self.contract_duration_months = 12
            self.end_date = self.start_date + relativedelta(months=self.contract_duration_months) - relativedelta(days=1)
        
        # التحقق من التواريخ
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError({
                    'end_date': _('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
                })
        
        # ✅ التحقق من وجود وحدة واحدة على الأقل (بعد الحفظ)
        if self.pk and self.units.count() == 0:
            raise ValidationError({
                'units': _('يجب اختيار وحدة واحدة على الأقل')
            })
        
        # التحقق من عدم التداخل - فقط إذا كانت التواريخ موجودة
        if self.start_date and self.end_date and self.status in [ContractStatus.DRAFT, ContractStatus.ACTIVE]:
            self._check_unit_overlap()
    
    def save(self, *args, **kwargs):
        """Override save for calculations and validations"""
        from dateutil.relativedelta import relativedelta
        
        is_new = self.pk is None
        old_status = None
        
        # حفظ الحالة القديمة إذا كان العقد موجوداً
        if not is_new:
            try:
                old_contract = Contract.objects.get(pk=self.pk)
                old_status = old_contract.status
            except Contract.DoesNotExist:
                pass
        
        # 1. حساب تاريخ النهاية تلقائياً
        if self.start_date and not self.end_date:
            if not self.contract_duration_months:
                self.contract_duration_months = 12
            self.end_date = self.start_date + relativedelta(months=self.contract_duration_months) - relativedelta(days=1)
        
        # 2. حساب يوم الدفع
        if self.start_date and not self.payment_day:
            self.payment_day = self.start_date.day
            if self.payment_day > 28:
                self.payment_day = 28
                        
        # حفظ العقد
        super().save(*args, **kwargs)
        
        # 6. تحديث حالة الوحدات عند تغيير الحالة
        status_changed = (old_status != self.status) or is_new
        
        if status_changed:
            self._sync_units_status()
                     
        # حساب القيمة الشهرية
        frequency_map = {
            RentType.MONTHLY: 1,
            RentType.QUARTERLY: 3,
            RentType.SEMI_ANNUAL: 6,
            RentType.ANNUAL: 12,
        }
        
      
    
    # ========================================
    # ✅ UPDATED: Unit Management Methods
    # ========================================
    def _get_units_to_check(self):
        """
        ✅ UPDATED: جمع جميع الوحدات المرتبطة بالعقد
        
        Returns:
            QuerySet: الوحدات
        """
        if self.pk:
            return self.units.all()
        return Unit.objects.none()
    
    def _check_unit_overlap(self):
        """
        ✅ UPDATED: التحقق من عدم تداخل العقود على نفس الوحدة
        
        القواعد:
        1. الوحدة المؤجرة في نفس الفترة → ممنوع ❌
        2. فجوة زمنية بين عقدين → مسموح ✅
        3. تمديد بعد انتهاء العقد السابق → مسموح ✅
        """
        # التحقق من وجود التواريخ
        if not self.start_date or not self.end_date:
            return
        
        units_to_check = self._get_units_to_check()
        
        if not units_to_check.exists():
            return
        
        for unit in units_to_check:
            # البحث عن عقود متداخلة زمنياً
            overlapping_contracts = Contract.objects.filter(
                units=unit,  # ✅ UPDATED: استخدام units فقط
                status__in=[ContractStatus.DRAFT, ContractStatus.ACTIVE],
                is_deleted=False,
                start_date__lt=self.end_date,
                end_date__gt=self.start_date
            )
            
            # استثناء العقد الحالي
            if self.pk:
                overlapping_contracts = overlapping_contracts.exclude(pk=self.pk)
            
            if overlapping_contracts.exists():
                existing = overlapping_contracts.first()
                raise ValidationError({
                    'units': self._get_overlap_error_message(unit, existing)
                })
    
    def _get_overlap_error_message(self, unit, existing_contract):
        """
        رسالة خطأ واضحة عند التداخل الزمني
        """
        return _(
            f'⚠️ تداخل زمني!\n\n'
            f'الوحدة: {unit.unit_number}\n'
            f'محجوزة لعقد: {existing_contract.contract_number}\n'
            f'الحالة: {existing_contract.get_status_display()}\n'
            f'الفترة: من {existing_contract.start_date} إلى {existing_contract.end_date}\n\n'
            f'العقد الحالي:\n'
            f'الفترة المطلوبة: من {self.start_date} إلى {self.end_date}\n\n'
            f'💡 الحل: اختر تاريخ بدء بعد {existing_contract.end_date}'
        )
    
    def _sync_units_status(self):
        """
        ✅ UPDATED: تحديث حالة الوحدات بناءً على حالة العقد
        
        التدفق:
        - DRAFT → RENTED (مؤجرة مباشرة!)
        - ACTIVE → RENTED (مؤجرة)
        - EXPIRED/TERMINATED → AVAILABLE (متاحة)
        """
        # تحديد الحالة الجديدة للوحدات
        if self.status in [ContractStatus.DRAFT, ContractStatus.ACTIVE]:
            new_status = PropertyStatus.RENTED  # ✅ UPDATED: مؤجرة في الحالتين
        elif self.status in [ContractStatus.EXPIRED, ContractStatus.TERMINATED]:
            new_status = PropertyStatus.AVAILABLE
        else:
            return
        
        # تحديث الوحدات
        self._update_units_status(new_status)
    
    def _update_units_status(self, status):
        """
        ✅ UPDATED: تحديث حالة جميع الوحدات المرتبطة بالعقد
        
        Args:
            status: الحالة الجديدة (PropertyStatus)
        """
        if not self.pk:
            return
        
        # تحديث جميع الوحدات
        self.units.update(status=status)
    
       # ========================================
    # ✅ UPDATED: Class Methods للوحدات المتاحة
    # ========================================
    @classmethod
    def get_available_units(cls, start_date, end_date, exclude_contract_id=None):
        """
        ✅ UPDATED: الحصول على الوحدات المتاحة في فترة معينة
        
        Args:
            start_date: تاريخ بدء الفترة
            end_date: تاريخ نهاية الفترة
            exclude_contract_id: استثناء عقد معين
            
        Returns:
            QuerySet: الوحدات المتاحة
        """
        # البحث عن العقود المشغولة
        busy_contracts = cls.objects.filter(
            status__in=[ContractStatus.DRAFT, ContractStatus.ACTIVE],
            is_deleted=False,
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        
        if exclude_contract_id:
            busy_contracts = busy_contracts.exclude(pk=exclude_contract_id)
        
        # ✅ UPDATED: جمع IDs الوحدات المشغولة (استعلام محسّن)
        busy_unit_ids = busy_contracts.values_list('units', flat=True).distinct()
        
        # إرجاع الوحدات المتاحة
        return Unit.objects.filter(
            is_deleted=False
        ).exclude(id__in=busy_unit_ids)
    

    @property
    def calculator(self):
        """
        محرك الحسابات للعقد
        
        Returns:
            ContractCalculator: instance من المحرك الحسابي
        """
        if not hasattr(self, '_calculator'):
            self._calculator = ContractFinancialService(self)
            return self._calculator

    @classmethod
    def check_unit_availability(cls, unit, start_date, end_date, exclude_contract_id=None):
        """
        ✅ UPDATED: التحقق من توفر وحدة معينة
        
        Args:
            unit: الوحدة
            start_date: تاريخ البدء
            end_date: تاريخ النهاية
            exclude_contract_id: استثناء عقد معين
            
        Returns:
            tuple: (bool, str) - (متاحة, رسالة)
        """
        # البحث عن عقود متداخلة
        overlapping = cls.objects.filter(
            units=unit,  # ✅ UPDATED: استخدام units
            status__in=[ContractStatus.DRAFT, ContractStatus.ACTIVE],
            is_deleted=False,
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        
        if exclude_contract_id:
            overlapping = overlapping.exclude(pk=exclude_contract_id)
        
        if overlapping.exists():
            existing = overlapping.first()
            message = _(
                f'الوحدة {unit.unit_number} محجوزة لعقد {existing.contract_number} '
                f'من {existing.start_date} إلى {existing.end_date}'
            )
            return False, message
        
        return True, _('الوحدة متاحة')
    
    # ========================================
    # ✅ UPDATED: Existing Methods
    # ========================================
    def get_all_units(self):
        """
        ✅ UPDATED: الحصول على جميع الوحدات
        
        Returns:
            QuerySet: All units
        """
        if self.pk:
            return self.units.all()
        return Unit.objects.none()
    
   
            
    def is_expired(self):
        """Check if contract is expired"""
        return timezone.now().date() > self.end_date
    
    def is_expiring_soon(self, days=30):
        """Check if contract is expiring soon"""
        if self.status != ContractStatus.ACTIVE:
            return False
        
        days_until_expiry = calculate_days_between(
            timezone.now().date(),
            self.end_date
        )
        return 0 <= days_until_expiry <= days
    
  
    
    def terminate_contract(self, reason='', penalty=None, user=None):
        """Terminate contract early"""
        if self.status != ContractStatus.ACTIVE:
            return False
        
        self.status = ContractStatus.TERMINATED
        self.actual_end_date = timezone.now().date()
        self.termination_reason = reason
        if penalty:
            self.termination_penalty = penalty
        
        if user:
            self.updated_by = user
        
        self.save()
        return True
    
    def get_statistics(self):
        """Get comprehensive contract statistics"""
        return {
            'contract_number': self.contract_number,
            'tenant': self.tenant.name,
            'units_count': self.get_all_units().count(),
            'status': self.get_status_display(),
            'duration_months': self.get_duration_months(),
            'total_amount': self.total_amount,
            'paid_amount': self.total_paid_amount,
            'remaining_amount': self.get_remaining_amount(),
            'outstanding_amount': self.get_outstanding_amount(),
            'payment_percentage': self.get_payment_percentage(),
            'is_expired': self.is_expired(),
            'days_until_expiry': calculate_days_between(
                timezone.now().date(),
                self.end_date
            ) if not self.is_expired() else 0,
        }

    # إضافة هذا الـ method إلى Contract model في contract_models.py
    def get_outstanding_amount(self, include_future=False):
            service = ContractFinancialService(self)
            return service.get_outstanding_amount(include_future=include_future)
    
    def get_contract_summary(self):
        service = ContractFinancialService(self)
        return service.get_contract_summary()
    
    def get_periods(self):
        service = ContractFinancialService(self)
        return service.calculate_periods()
    
    def get_periods_with_payments(self):
        service = ContractFinancialService(self)
        return service.calculate_periods_with_payments()
    
    def can_accept_payment(self, amount):
        from decimal import Decimal
        
        if not isinstance(amount, Decimal):
            try:
                amount = Decimal(str(amount))
            except:
                return False, "قيمة غير صحيحة"
        
        # السماح بتسديد المستحقات للعقود النشطة والمجدة والمنتهية والملغاة
        if self.status not in ['active', 'renewed', 'expired', 'terminated']:
            return False, "العقد غير نشط"
        
        if amount <= 0:
            return False, "المبلغ يجب أن يكون أكبر من صفر"
        
        return True, ""
    
    def get_payment_distribution_preview(self, amount):
        service = ContractFinancialService(self)
        return service.calculate_payment_distribution(amount)
    

# ========================================
# Signals
# ========================================

@receiver(post_save, sender=Contract)
def contract_post_save(sender, instance, created, **kwargs):
    """Signal handler after contract is saved"""
    if created:
        # يمكن إضافة منطق عند إنشاء عقد جديد
        pass
    
    # التحقق من قرب انتهاء العقد
    if instance.is_expiring_soon(days=30):
        # يمكن إنشاء إشعار تلقائي
        pass


@receiver(pre_save, sender=Contract)
def contract_pre_save(sender, instance, **kwargs):
    """Signal handler before contract is saved"""
    # تحديث حالة العقد تلقائياً
    if instance.is_expired() and instance.status == ContractStatus.ACTIVE:
        instance.status = ContractStatus.EXPIRED