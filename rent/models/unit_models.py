# models/unit_models.py

"""
Unit Management Models
نماذج إدارة الوحدات
"""

from .common_imports_models import *
from .common_imports_models import UnitType
from .building_models import Building  # ✅ استيراد صريح


# ========================================
# Unit Model
# ========================================

class Unit(TimeStampedModel, UserTrackingModel, SoftDeleteModel):
    """
    Unit Model
    نموذج الوحدة
    
    يمثل وحدة سكنية أو تجارية داخل مبنى
    """
    
    # ========================================
    # Relationships
    # ========================================
    building = models.ForeignKey(
        Building,
        on_delete=models.PROTECT,  # ✅ حماية من الحذف
        related_name='units',
        verbose_name=_('المبنى'),
        help_text=_('المبنى الذي تقع فيه الوحدة')
    )
    
    # ========================================
    # Basic Information
    # ========================================
    unit_number = models.CharField(
        _('رقم الوحدة'),
        max_length=50,
        db_index=True,
        help_text=_('رقم الوحدة داخل المبنى (مثال: 101، A-1)')
    )
    
    floor = models.IntegerField(
        _('الطابق'),
        validators=[MinValueValidator(-5), MaxValueValidator(200)],  # تدعم الطوابق السفلية
        help_text=_('رقم الطابق (0=أرضي، سالب=تحت الأرض)')
    )
    
    area = models.DecimalField(
        _('المساحة (متر مربع)'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive_decimal],
        help_text=_('مساحة الوحدة بالمتر المربع')
    )
    
    # ========================================
    # Unit Specifications
    # ========================================
    rooms_count = models.PositiveIntegerField(
        _('عدد الغرف'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text=_('عدد الغرف (غرف النوم فقط)')
    )
    
    bathrooms_count = models.PositiveIntegerField(
        _('عدد الحمامات'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text=_('عدد دورات المياه')
    )
    
    has_kitchen = models.BooleanField(
        _('يوجد مطبخ'),
        default=True,
        help_text=_('هل الوحدة مزودة بمطبخ؟')
    )
    
    has_balcony = models.BooleanField(
        _('يوجد شرفة'),
        default=False,
        help_text=_('هل الوحدة مزودة بشرفة؟')
    )
    
    # ========================================
    # Utilities & Meters
    # ========================================
    water_meter_number = models.CharField(
        _('رقم عداد المياه'),
        max_length=100,
        blank=True,
        help_text=_('رقم عداد المياه الخاص بالوحدة')
    )
    
    electricity_meter_number = models.CharField(
        _('رقم عداد الكهرباء'),
        max_length=100,
        blank=True,
        help_text=_('رقم عداد الكهرباء الخاص بالوحدة')
    )
    
    # ========================================
    # Financial Information
    # ========================================
    monthly_rent = models.DecimalField(
        _('الإيجار الشهري'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('القيمة الإيجارية الشهرية للوحدة')
    )
    
    security_deposit = models.DecimalField(
        _('مبلغ التأمين'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('مبلغ التأمين المطلوب عند التأجير')
    )
    
    # ========================================
    # Status
    # ========================================
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=PropertyStatus.choices,  # ✅ من common_imports_models
        default=PropertyStatus.AVAILABLE,
        db_index=True,
        help_text=_('الحالة الحالية للوحدة')
    )

    unit_type = models.CharField(
        _('نوع الوحده'),
        max_length=20,
        choices=UnitType.choices,  # ✅ من common_imports_models
        default=UnitType.SHOWROOM,
        db_index=True,
        help_text=_('الحالة الحالية للوحدة')
    )
    
    


    is_active = models.BooleanField(
        _('نشط'),
        default=True,
        db_index=True,
        help_text=_('هل الوحدة نشطة ومتاحة للاستخدام؟')
    )
    
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات إضافية عن الوحدة')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'units'
        verbose_name = _('وحدة')
        verbose_name_plural = _('الوحدات')
        ordering = ['building', 'floor', 'unit_number']
        unique_together = [['building', 'unit_number']]  # رقم فريد لكل وحدة في نفس المبنى
        indexes = [
            models.Index(fields=['building', 'floor']),
            models.Index(fields=['building', 'unit_number']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active', 'is_deleted']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.building.name} - وحدة {self.unit_number}"
    
    def clean(self):
        """Validation before saving"""
        super().clean()
        
        # التحقق من أن المساحة موجبة
        if self.area and self.area <= 0:
            raise ValidationError({
                'area': _('المساحة يجب أن تكون أكبر من صفر')
            })
        
        # التحقق من أن الإيجار الشهري موجب
        if self.monthly_rent and self.monthly_rent < 0:
            raise ValidationError({
                'monthly_rent': _('الإيجار الشهري يجب أن يكون موجباً')
            })
        
        # التحقق من منطقية رقم الطابق
        if self.floor and abs(self.floor) > self.building.floors_count:
            raise ValidationError({
                'floor': _('رقم الطابق يجب أن يكون ضمن نطاق طوابق المبنى')
            })
    
    def get_current_contract(self):
        """
        Get current active contract
        الحصول على العقد النشط الحالي
        
        Returns:
            Contract or None: Current active contract
        """
        today = timezone.now().date()
        return self.contracts.filter(
            status=ContractStatus.ACTIVE,
            start_date__lte=today,
            end_date__gte=today,
            is_deleted=False
        ).first()
    
    def get_current_tenant(self):
        """
        Get current tenant
        الحصول على المستأجر الحالي
        
        Returns:
            Tenant or None: Current tenant
        """
        current_contract = self.get_current_contract()
        return current_contract.tenant if current_contract else None
    
    def is_available_for_rent(self):
        """
        Check if unit is available for rent
        التحقق من أن الوحدة متاحة للتأجير
        
        Returns:
            bool: True if available
        """
        return (
            self.status == PropertyStatus.AVAILABLE and
            self.is_active and
            not self.is_deleted and
            self.monthly_rent is not None and
            self.monthly_rent > 0
        )
    
    def get_full_address(self):
        """
        Get full address including building and land
        الحصول على العنوان الكامل
        
        Returns:
            str: Full address
        """
        return f"{self.building.land.name} - {self.building.name} - وحدة {self.unit_number} - طابق {self.floor}"
    
    def get_rent_per_sqm(self):
        """
        Calculate rent per square meter
        حساب الإيجار لكل متر مربع
        
        Returns:
            Decimal or None: Rent per sqm
        """
        if self.monthly_rent and self.area and self.area > 0:
            return Decimal(self.monthly_rent / self.area).quantize(Decimal('0.01'))
        return None
    
    def get_annual_rent(self):
        """
        Calculate annual rent
        حساب الإيجار السنوي
        
        Returns:
            Decimal or None: Annual rent
        """
        if self.monthly_rent:
            return self.monthly_rent * 12
        return None
    
    def mark_as_rented(self):
        """
        Mark unit as rented
        وضع علامة مؤجر على الوحدة
        """
        self.status = PropertyStatus.RENTED
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_as_available(self):
        """
        Mark unit as available
        وضع علامة متاح على الوحدة
        """
        self.status = PropertyStatus.AVAILABLE
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_as_maintenance(self):
        """
        Mark unit as under maintenance
        وضع علامة تحت الصيانة على الوحدة
        """
        self.status = PropertyStatus.MAINTENANCE
        self.save(update_fields=['status', 'updated_at'])
    
    def get_contract_history(self):
        """
        Get all contracts for this unit
        الحصول على تاريخ العقود للوحدة
        
        Returns:
            QuerySet: All contracts ordered by start date
        """
        return self.contracts.filter(
            is_deleted=False
        ).order_by('-start_date')
    
    def get_statistics(self):
        """
        Get comprehensive unit statistics
        الحصول على إحصائيات شاملة للوحدة
        
        Returns:
            dict: Statistics dictionary
        """
        current_contract = self.get_current_contract()
        
        return {
            'status': self.get_status_display(),
            'current_tenant': self.get_current_tenant(),
            'monthly_rent': self.monthly_rent,
            'annual_rent': self.get_annual_rent(),
            'rent_per_sqm': self.get_rent_per_sqm(),
            'is_available': self.is_available_for_rent(),
            'current_contract': current_contract,
            'total_contracts': self.get_contract_history().count(),
        }


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=Unit)
def unit_post_save(sender, instance, created, **kwargs):
    """
    Signal handler after unit is saved
    معالج الإشارة بعد حفظ الوحدة
    """
    if created:
        # يمكن إضافة منطق عند إنشاء وحدة جديدة
        # مثل: إنشاء سجل في 
        pass


@receiver(pre_save, sender=Unit)
def unit_pre_save(sender, instance, **kwargs):
    """
    Signal handler before unit is saved
    معالج الإشارة قبل حفظ الوحدة
    """
    # التحقق من أن المبنى نشط
    if instance.building and not instance.building.is_active:
        raise ValidationError(_('لا يمكن إضافة وحدة في مبنى غير نشط'))
    
    # تحديث حالة الوحدة تلقائياً بناءً على العقود
    if instance.pk:  # إذا كانت الوحدة موجودة مسبقاً
        current_contract = instance.get_current_contract()
        if current_contract and instance.status != PropertyStatus.RENTED:
            instance.status = PropertyStatus.RENTED
        elif not current_contract and instance.status == PropertyStatus.RENTED:
            instance.status = PropertyStatus.AVAILABLE