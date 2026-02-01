# models/land_models.py

"""
Land Management Models
نماذج إدارة الأراضي
"""

from .common_imports_models import *


# ========================================
# Choices/Enums
# ========================================

class OwnershipType(models.TextChoices):
    """نوع ملكية الأرض"""
    OWNED = 'owned', _('ملك')
    RENTED = 'rented', _('إيجار')
    LEASED = 'leased', _('عقد إيجار طويل')
    SHARED = 'shared', _('مشاركة')


# ========================================
# Land Model
# ========================================

class Land(TimeStampedModel, UserTrackingModel, SoftDeleteModel):
    """
    Land/Plot Model
    نموذج الأرض/القطعة
    
    يمثل قطعة الأرض التي يُبنى عليها المباني
    """
    
    # ========================================
    # Basic Information
    # ========================================
    name = models.CharField(
        _('اسم الأرض'),
        max_length=200,
        help_text=_('اسم واضح للأرض أو القطعة')
    )
    
    area = models.DecimalField(
        _('المساحة (متر مربع)'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive_decimal],
        help_text=_('المساحة الإجمالية للأرض بالمتر المربع')
    )
    
    deed_number = models.CharField(
        _('رقم الصك'),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_('رقم صك الأرض (يجب أن يكون فريداً)')
    )
    
    location = models.CharField(
        _('الموقع'),
        max_length=255,
        blank=True,
        help_text=_('العنوان أو الموقع الجغرافي للأرض')
    )
    
    # ========================================
    # Ownership Information
    # ========================================
    owner_name = models.CharField(
        _('اسم المالك'),
        max_length=200,
        help_text=_('اسم مالك الأرض الحالي')
    )
    
    ownership_type = models.CharField(
        _('نوع الملكية'),
        max_length=20,
        choices=OwnershipType.choices,
        default=OwnershipType.OWNED,
        help_text=_('نوع ملكية الأرض')
    )
    
    # ========================================
    # Rental Information (if rented)
    # معلومات الإيجار (إذا كانت مستأجرة)
    # ========================================
    rent_start_date = models.DateField(
        _('تاريخ بداية الإيجار'),
        null=True,
        blank=True,
        help_text=_('تاريخ بداية عقد إيجار الأرض (إن وجد)')
    )
    
    rent_duration_years = models.PositiveIntegerField(
        _('مدة الإيجار (سنوات)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        help_text=_('مدة عقد الإيجار بالسنوات')
    )
    
    rent_end_date = models.DateField(
        _('تاريخ نهاية الإيجار'),
        null=True,
        blank=True,
        editable=False,  # يُحسب تلقائياً
        help_text=_('تاريخ انتهاء عقد الإيجار (يُحسب تلقائياً)')
    )
    
    annual_rent_amount = models.DecimalField(
        _('قيمة الإيجار السنوي'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('قيمة إيجار الأرض السنوي (إن كانت مستأجرة)')
    )
    
    # ========================================
    # Additional Information
    # ========================================
    is_active = models.BooleanField(
        _('نشط'),
        default=True,
        db_index=True,
        help_text=_('هل الأرض نشطة ومتاحة للاستخدام؟')
    )
    
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات إضافية عن الأرض')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'lands'
        verbose_name = _('أرض')
        verbose_name_plural = _('الأراضي')
        ordering = ['name']
        indexes = [
            models.Index(fields=['deed_number']),
            models.Index(fields=['ownership_type']),
            models.Index(fields=['is_active', 'is_deleted']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.name} - {self.deed_number}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate rent_end_date automatically"""
        # حساب تاريخ نهاية الإيجار تلقائياً
        if self.rent_start_date and self.rent_duration_years and not self.rent_end_date:
            self.rent_end_date = self.rent_start_date + relativedelta(
                years=self.rent_duration_years
            )
        
        # التحقق من صحة بيانات الإيجار
        if self.ownership_type == OwnershipType.RENTED:
            if not self.rent_start_date:
                raise ValidationError(_('يجب تحديد تاريخ بداية الإيجار للأراضي المستأجرة'))
            if not self.rent_duration_years:
                raise ValidationError(_('يجب تحديد مدة الإيجار للأراضي المستأجرة'))
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validation before saving"""
        super().clean()
        
        # التحقق من بيانات الإيجار
        if self.ownership_type == OwnershipType.RENTED:
            if not self.rent_start_date or not self.rent_duration_years:
                raise ValidationError({
                    'rent_start_date': _('مطلوب للأراضي المستأجرة'),
                    'rent_duration_years': _('مطلوب للأراضي المستأجرة')
                })
        
        # التحقق من أن المساحة موجبة
        if self.area and self.area <= 0:
            raise ValidationError({'area': _('المساحة يجب أن تكون أكبر من صفر')})
    
    def get_active_buildings(self):
        """
        Get active buildings on this land
        الحصول على المباني النشطة على هذه الأرض
        
        Returns:
            QuerySet: Active buildings
        """
        return self.buildings.filter(is_active=True, is_deleted=False)
    
    def get_total_units(self):
        """
        Get total number of units across all buildings
        الحصول على إجمالي عدد الوحدات في جميع المباني
        
        Returns:
            int: Total units count
        """
        return sum(building.units.filter(is_active=True).count() 
                   for building in self.get_active_buildings())
    
    def get_rented_units(self):
        """
        Get number of rented units
        الحصول على عدد الوحدات المؤجرة
        
        Returns:
            int: Rented units count
        """
        count = 0
        for building in self.get_active_buildings():
            count += building.units.filter(
                status=PropertyStatus.RENTED,
                is_active=True
            ).count()
        return count
    
    def get_occupancy_rate(self):
        """
        Calculate overall occupancy rate for all buildings
        حساب نسبة الإشغال الإجمالية لجميع المباني
        
        Returns:
            Decimal: Occupancy percentage (0-100)
        """
        total_units = self.get_total_units()
        if total_units == 0:
            return Decimal('0.00')
        
        rented_units = self.get_rented_units()
        return Decimal((rented_units / total_units) * 100).quantize(Decimal('0.01'))
    
    def is_rent_expiring_soon(self, days=90):
        """
        Check if land rent is expiring soon
        التحقق من قرب انتهاء عقد إيجار الأرض
        
        Args:
            days: Number of days threshold
            
        Returns:
            bool: True if expiring within specified days
        """
        if not self.rent_end_date or self.ownership_type != OwnershipType.RENTED:
            return False
        
        days_until_expiry = calculate_days_between(timezone.now().date(), self.rent_end_date)
        return 0 <= days_until_expiry <= days
    
    def get_rent_status(self):
        """
        Get current rent status
        الحصول على حالة الإيجار الحالية
        
        Returns:
            str: Status message
        """
        if self.ownership_type != OwnershipType.RENTED:
            return _('ملك')
        
        if not self.rent_end_date:
            return _('إيجار - لا يوجد تاريخ انتهاء')
        
        today = timezone.now().date()
        
        if self.rent_end_date < today:
            return _('إيجار منتهي')
        
        days_remaining = calculate_days_between(today, self.rent_end_date)
        
        if days_remaining <= 30:
            return _('إيجار - ينتهي خلال {} يوم').format(days_remaining)
        elif days_remaining <= 90:
            return _('إيجار - ينتهي خلال {} يوم').format(days_remaining)
        else:
            return _('إيجار نشط')


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=Land)
def land_post_save(sender, instance, created, **kwargs):
    """
    Signal handler after land is saved
    معالج الإشارة بعد حفظ الأرض
    """
    if created:
        # يمكن إضافة منطق عند إنشاء أرض جديدة
        # مثل: إنشاء سجل في 
        pass
    
    # التحقق من قرب انتهاء الإيجار وإرسال تنبيه
    if instance.is_rent_expiring_soon(days=60):
        # يمكن إنشاء إشعار تلقائي
        pass