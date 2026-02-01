# models/building_models.py

"""
Building Management Models
نماذج إدارة المباني
"""

from .common_imports_models import *
from .land_models import Land  # ✅ استيراد صريح


# ========================================
# Choices/Enums
# ========================================

class BuildingType(models.TextChoices):
    """نوع المبنى"""
    RESIDENTIAL = 'residential', _('سكني')
    COMMERCIAL = 'commercial', _('تجاري')
    MALL = 'mall', _('مول تجاري')
    MIXED = 'mixed', _('مختلط (سكني + تجاري)')
    INDUSTRIAL = 'industrial', _('صناعي')
    OFFICE = 'office', _('مكاتب إدارية')


# ========================================
# Building Model
# ========================================

class Building(TimeStampedModel, UserTrackingModel, SoftDeleteModel):
    """
    Building Model
    نموذج المبنى
    
    يمثل مبنى على قطعة أرض معينة
    """
    
    # ========================================
    # Relationships
    # ========================================
    land = models.ForeignKey(
        Land,
        on_delete=models.PROTECT,  # ✅ حماية من الحذف
        related_name='buildings',
        verbose_name=_('الأرض'),
        help_text=_('الأرض التي يقع عليها المبنى')
    )
    
    # ========================================
    # Basic Information
    # ========================================
    name = models.CharField(
        _('اسم المبنى'),
        max_length=200,
        help_text=_('اسم واضح للمبنى')
    )
    
    building_type = models.CharField(
        _('نوع المبنى'),
        max_length=20,
        choices=BuildingType.choices,
        default=BuildingType.RESIDENTIAL,
        help_text=_('نوع استخدام المبنى')
    )
    
    total_area = models.DecimalField(
        _('المساحة الإجمالية (متر مربع)'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive_decimal],
        help_text=_('إجمالي مساحة المبنى بالمتر المربع')
    )
    
    floors_count = models.PositiveIntegerField(
        _('عدد الطوابق'),
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        help_text=_('عدد طوابق المبنى (شامل الأرضي)')
    )
    
    construction_year = models.PositiveIntegerField(
        _('سنة البناء'),
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(2100)
        ],
        help_text=_('السنة الهجرية أو الميلادية لبناء المبنى')
    )
    
    # ========================================
    # Additional Details
    # ========================================
    has_elevator = models.BooleanField(
        _('يوجد مصعد'),
        default=False,
        help_text=_('هل المبنى مزود بمصعد؟')
    )
    
    has_parking = models.BooleanField(
        _('يوجد مواقف'),
        default=False,
        help_text=_('هل يوجد مواقف سيارات؟')
    )
    
    parking_spaces = models.PositiveIntegerField(
        _('عدد مواقف السيارات'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('عدد مواقف السيارات المتاحة')
    )
    
    # ========================================
    # Status
    # ========================================
    is_active = models.BooleanField(
        _('نشط'),
        default=True,
        db_index=True,
        help_text=_('هل المبنى نشط ومتاح للاستخدام؟')
    )
    
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات إضافية عن المبنى')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'buildings'
        verbose_name = _('مبنى')
        verbose_name_plural = _('المباني')
        ordering = ['land', 'name']
        indexes = [
            models.Index(fields=['land', 'name']),
            models.Index(fields=['building_type']),
            models.Index(fields=['is_active', 'is_deleted']),
        ]
        unique_together = [['land', 'name']]  # اسم فريد لكل مبنى في نفس الأرض
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.land.name} - {self.name}"
    
    def clean(self):
        """Validation before saving"""
        super().clean()
        
        # التحقق من عدد المواقف
        if self.has_parking and not self.parking_spaces:
            raise ValidationError({
                'parking_spaces': _('يجب تحديد عدد المواقف إذا كان يوجد مواقف')
            })
        
        # التحقق من أن المساحة الإجمالية موجبة
        if self.total_area and self.total_area <= 0:
            raise ValidationError({
                'total_area': _('المساحة يجب أن تكون أكبر من صفر')
            })
        
        # التحقق من أن عدد الطوابق منطقي
        if self.floors_count and self.floors_count < 1:
            raise ValidationError({
                'floors_count': _('عدد الطوابق يجب أن يكون 1 على الأقل')
            })
    
    def get_active_units(self):
        """
        Get all active units
        الحصول على جميع الوحدات النشطة
        
        Returns:
            QuerySet: Active units
        """
        return self.units.filter(is_active=True, is_deleted=False)
    
    def get_available_units(self):
        """
        Get available units only
        الحصول على الوحدات المتاحة فقط
        
        Returns:
            QuerySet: Available units
        """
        return self.units.filter(
            status=PropertyStatus.AVAILABLE,
            is_active=True,
            is_deleted=False
        )
    
    def get_rented_units(self):
        """
        Get rented units
        الحصول على الوحدات المؤجرة
        
        Returns:
            QuerySet: Rented units
        """
        return self.units.filter(
            status=PropertyStatus.RENTED,
            is_active=True,
            is_deleted=False
        )
    
    def get_occupancy_rate(self):
        """
        Calculate occupancy rate
        حساب نسبة الإشغال
        
        Returns:
            Decimal: Occupancy percentage (0-100)
        """
        total_units = self.get_active_units().count()
        if total_units == 0:
            return Decimal('0.00')
        
        rented_units = self.get_rented_units().count()
        return Decimal((rented_units / total_units) * 100).quantize(Decimal('0.01'))
    
    def get_total_monthly_revenue(self):
        """
        Calculate total monthly revenue from all rented units
        حساب إجمالي الإيرادات الشهرية من جميع الوحدات المؤجرة
        
        Returns:
            Decimal: Total monthly revenue
        """
        rented_units = self.get_rented_units()
        total = Decimal('0')
        
        for unit in rented_units:
            if unit.monthly_rent:
                total += unit.monthly_rent
        
        return total
    
    def get_potential_monthly_revenue(self):
        """
        Calculate potential monthly revenue if all units were rented
        حساب الإيرادات الشهرية المحتملة لو تم تأجير جميع الوحدات
        
        Returns:
            Decimal: Potential monthly revenue
        """
        units = self.get_active_units()
        total = Decimal('0')
        
        for unit in units:
            if unit.monthly_rent:
                total += unit.monthly_rent
        
        return total
    
    def get_units_by_floor(self, floor_number):
        """
        Get units on a specific floor
        الحصول على وحدات في طابق محدد
        
        Args:
            floor_number: Floor number
            
        Returns:
            QuerySet: Units on the floor
        """
        return self.get_active_units().filter(floor=floor_number)
    
    def get_floor_range(self):
        """
        Get the range of floors with units
        الحصول على نطاق الطوابق التي تحتوي على وحدات
        
        Returns:
            tuple: (min_floor, max_floor)
        """
        units = self.get_active_units()
        if not units.exists():
            return (0, 0)
        
        from django.db.models import Min, Max
        result = units.aggregate(Min('floor'), Max('floor'))
        return (result['floor__min'] or 0, result['floor__max'] or 0)
    
    def get_statistics(self):
        """
        Get comprehensive building statistics
        الحصول على إحصائيات شاملة للمبنى
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            'total_units': self.get_active_units().count(),
            'available_units': self.get_available_units().count(),
            'rented_units': self.get_rented_units().count(),
            'maintenance_units': self.units.filter(
                status=PropertyStatus.MAINTENANCE,
                is_active=True
            ).count(),
            'occupancy_rate': self.get_occupancy_rate(),
            'monthly_revenue': self.get_total_monthly_revenue(),
            'potential_revenue': self.get_potential_monthly_revenue(),
            'revenue_loss': self.get_potential_monthly_revenue() - self.get_total_monthly_revenue(),
        }


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=Building)
def building_post_save(sender, instance, created, **kwargs):
    """
    Signal handler after building is saved
    معالج الإشارة بعد حفظ المبنى
    """
    if created:
        # يمكن إضافة منطق عند إنشاء مبنى جديد
        # مثل: إنشاء سجل في 
        pass


@receiver(pre_save, sender=Building)
def building_pre_save(sender, instance, **kwargs):
    """
    Signal handler before building is saved
    معالج الإشارة قبل حفظ المبنى
    """
    # التحقق من أن الأرض نشطة
    if instance.land and not instance.land.is_active:
        raise ValidationError(_('لا يمكن إضافة مبنى على أرض غير نشطة'))