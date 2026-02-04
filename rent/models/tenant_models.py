# models/tenant_models.py

"""
Tenant Management Models
نماذج إدارة المستأجرين
"""

from .common_imports_models import *


# ========================================
# Choices/Enums
# ========================================

class TenantType(models.TextChoices):
    """نوع المستأجر"""
    INDIVIDUAL = 'individual', _('فرد')
    COMPANY = 'company', _('شركة')
    INSTITUTION = 'institution', _('مؤسسة')
    GOVERNMENT = 'government', _('جهة حكومية')


class DocumentType(models.TextChoices):
    """نوع المستند"""
    NATIONAL_ID = 'national_id', _('الهوية الوطنية')
    IQAMA = 'iqama', _('الإقامة')
    PASSPORT = 'passport', _('جواز السفر')
    COMMERCIAL_REG = 'commercial_reg', _('السجل التجاري')
    AUTHORIZATION = 'authorization', _('الوكالة')
    CONTRACT = 'contract', _('العقد')
    FAMILY_BOOK = 'family_book', _('دفتر العائلة')
    OTHER = 'other', _('أخرى')


# ========================================
# Tenant Model
# ========================================

class Tenant(TimeStampedModel, UserTrackingModel, SoftDeleteModel):
    """
    Tenant Model
    نموذج المستأجر
    
    يمثل مستأجر (فرد أو شركة أو مؤسسة)
    """
    
    # ========================================
    # Basic Information
    # ========================================
    tenant_type = models.CharField(
        _('نوع المستأجر'),
        max_length=20,
        choices=TenantType.choices,
        default=TenantType.INDIVIDUAL,
        db_index=True,
        help_text=_('نوع المستأجر (فرد/شركة/مؤسسة)')
    )
    
    name = models.CharField(
        _('الاسم'),
        max_length=200,
        db_index=True,
        help_text=_('الاسم الكامل للمستأجر أو اسم الشركة')
    )
    
    # ========================================
    # Contact Information
    # ========================================
    phone = models.CharField(
        _('رقم الجوال'),
        max_length=20,
        validators=[validate_phone_number],
        help_text=_('رقم الجوال (05xxxxxxxx)')
    )
    
    email = models.EmailField(
        _('البريد الإلكتروني'),
        blank=True,
        help_text=_('البريد الإلكتروني للمراسلات')
    )
    
    # ========================================
    # Identification
    # ========================================
    id_number = models.CharField(
        _('رقم الهوية/السجل التجاري'),
        max_length=50,
        unique=True,
        db_index=True,
        validators=[validate_national_id],  # ✅ من common_imports_models
        help_text=_('رقم الهوية الوطنية أو رقم السجل التجاري')
    )
    
    id_type = models.CharField(
        _('نوع الهوية'),
        max_length=20,
        choices=[
            ('national_id', _('هوية وطنية')),
            ('iqama', _('إقامة')),
            ('commercial_reg', _('سجل تجاري')),
        ],
        default='national_id',
        help_text=_('نوع وثيقة الهوية')
    )
    
    id_expiry_date = models.DateField(
        _('تاريخ انتهاء الهوية/الإقامة'),
        null=True,
        blank=True,
        help_text=_('تاريخ انتهاء صلاحية الهوية أو الإقامة')
    )
    
    # ========================================
    # Authorization/Power of Attorney
    # معلومات الوكالة
    # ========================================
    has_authorization = models.BooleanField(
        _('يوجد وكالة'),
        default=False,
        help_text=_('هل يتعامل المستأجر بوكالة؟')
    )
    
    authorization_number = models.CharField(
        _('رقم الوكالة'),
        max_length=100,
        blank=True,
        help_text=_('رقم الوكالة الشرعية')
    )
    
    authorization_date = models.DateField(
        _('تاريخ الوكالة'),
        null=True,
        blank=True,
        help_text=_('تاريخ إصدار الوكالة')
    )
    
    authorization_expiry = models.DateField(
        _('تاريخ انتهاء الوكالة'),
        null=True,
        blank=True,
        help_text=_('تاريخ انتهاء صلاحية الوكالة')
    )
    
    authorized_person_name = models.CharField(
        _('اسم الوكيل'),
        max_length=200,
        blank=True,
        help_text=_('اسم الشخص المفوض بالوكالة')
    )
    
    # ========================================
    # Address
    # ========================================
    address = models.TextField(
        _('العنوان'),
        blank=True,
        help_text=_('العنوان الوطني أو عنوان السكن')
    )
    
    city = models.CharField(
        _('المدينة'),
        max_length=100,
        blank=True,
        help_text=_('المدينة')
    )
    
    district = models.CharField(
        _('الحي'),
        max_length=100,
        blank=True,
        help_text=_('الحي السكني')
    )
    
    # ========================================
    # Company/Institution Info (if applicable)
    # ========================================
    company_name = models.CharField(
        _('اسم الشركة'),
        max_length=200,
        blank=True,
        help_text=_('اسم الشركة أو المؤسسة (إن وجد)')
    )
    
    company_tax_number = models.CharField(
        _('الرقم الضريبي'),
        max_length=50,
        blank=True,
        help_text=_('الرقم الضريبي للشركة')
    )
    
    # ========================================
    # Financial Information
    # ========================================
    credit_limit = models.DecimalField(
        _('الحد الائتماني'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('أقصى رصيد مسموح به للمستأجر')
    )
    
    # ========================================
    # Status & Rating
    # ========================================
    is_active = models.BooleanField(
        _('نشط'),
        default=True,
        db_index=True,
        help_text=_('هل المستأجر نشط؟')
    )
    
    is_blacklisted = models.BooleanField(
        _('في القائمة السوداء'),
        default=False,
        db_index=True,
        help_text=_('هل المستأجر محظور من التعامل؟')
    )
    
    blacklist_reason = models.TextField(
        _('سبب الحظر'),
        blank=True,
        help_text=_('سبب إضافة المستأجر للقائمة السوداء')
    )
    
    rating = models.PositiveIntegerField(
        _('التقييم'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('تقييم المستأجر من 1 إلى 5')
    )
    
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات إضافية عن المستأجر')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'tenants'
        verbose_name = _('مستأجر')
        verbose_name_plural = _('المستأجرين')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['id_number']),
            models.Index(fields=['phone']),
            models.Index(fields=['tenant_type']),
            models.Index(fields=['is_active', 'is_deleted']),
            models.Index(fields=['is_blacklisted']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.name} - {self.id_number}"
    
    def clean(self):
        """Validation before saving"""
        super().clean()
        
        # التحقق من بيانات الوكالة
        if self.has_authorization:
            if not self.authorization_number:
                raise ValidationError({
                    'authorization_number': _('رقم الوكالة مطلوب عند وجود وكالة')
                })
            if not self.authorization_date:
                raise ValidationError({
                    'authorization_date': _('تاريخ الوكالة مطلوب عند وجود وكالة')
                })
        
        # التحقق من بيانات الشركة
        if self.tenant_type == TenantType.COMPANY:
            if not self.company_name:
                raise ValidationError({
                    'company_name': _('اسم الشركة مطلوب للمستأجرين من نوع شركة')
                })
        
        # التحقق من تاريخ انتهاء الهوية
        if self.id_expiry_date and self.id_expiry_date < timezone.now().date():
            raise ValidationError({
                'id_expiry_date': _('تاريخ انتهاء الهوية/الإقامة منتهي')
            })
    
    def get_active_contracts(self):
        """
        Get active contracts for this tenant
        الحصول على العقود النشطة للمستأجر
        
        Returns:
            QuerySet: Active contracts
        """
        return self.contracts.filter(
            status=ContractStatus.ACTIVE,
            is_deleted=False
        )
    
    def get_all_contracts(self):
        """
        Get all contracts (excluding deleted)
        الحصول على جميع العقود (باستثناء المحذوفة)
        
        Returns:
            QuerySet: All contracts
        """
        return self.contracts.filter(is_deleted=False).order_by('-start_date')
    
    def get_outstanding_balance(self):
        """
        Calculate total outstanding balance across all active contracts
        حساب إجمالي الرصيد المستحق عبر جميع العقود النشطة

        Returns:
            Decimal: Total outstanding amount
        """
        total = Decimal('0')

        try:
            from rent.services.contract_financial_service import ContractFinancialService
            for contract in self.get_active_contracts():
                try:
                    service = ContractFinancialService(contract)
                    outstanding = service.get_outstanding_amount()
                    if outstanding:
                        total += outstanding
                except Exception:
                    # في حالة فشل حساب عقد معين، نستمر مع البقية
                    pass
        except ImportError:
            # fallback: حساب مباشر من المدفوعات والمستحقات
            try:
                from django.db.models import Sum
                for contract in self.get_active_contracts():
                    # إجمالي المستحق = الإيجار السنوي
                    annual_rent = contract.annual_rent or Decimal('0')
                    # إجمالي المدفوع
                    paid = contract.receipts.filter(
                        status='posted',
                        is_deleted=False
                    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                    outstanding = annual_rent - paid
                    if outstanding > 0:
                        total += outstanding
            except Exception:
                pass

        return total
    
    def has_outstanding_payments(self):
        """
        Check if tenant has any outstanding payments
        التحقق من وجود مدفوعات متأخرة
        
        Returns:
            bool: True if has outstanding payments
        """
        return self.get_outstanding_balance() > 0
    
    def is_id_expired(self):
        """
        Check if ID/Iqama is expired
        التحقق من انتهاء صلاحية الهوية/الإقامة
        
        Returns:
            bool: True if expired
        """
        if not self.id_expiry_date:
            return False
        return self.id_expiry_date < timezone.now().date()
    
    def is_id_expiring_soon(self, days=60):
        """
        Check if ID is expiring soon
        التحقق من قرب انتهاء الهوية
        
        Args:
            days: Number of days threshold
            
        Returns:
            bool: True if expiring within specified days
        """
        if not self.id_expiry_date:
            return False
        
        days_until_expiry = calculate_days_between(
            timezone.now().date(),
            self.id_expiry_date
        )
        return 0 <= days_until_expiry <= days
    
    def is_authorization_valid(self):
        """
        Check if authorization is valid
        التحقق من صلاحية الوكالة
        
        Returns:
            bool: True if authorization is valid
        """
        if not self.has_authorization:
            return False
        
        if not self.authorization_expiry:
            return True  # لا يوجد تاريخ انتهاء
        
        return self.authorization_expiry >= timezone.now().date()
    
    def get_current_units(self):
        """
        Get currently rented units
        الحصول على الوحدات المؤجرة حالياً
        
        Returns:
            QuerySet: Currently rented units
        """
        active_contracts = self.get_active_contracts()
        unit_ids = active_contracts.values_list('unit_id', flat=True)
        
        from .unit_models import Unit
        return Unit.objects.filter(id__in=unit_ids)
    
    def get_payment_history(self):
        """
        Get payment history for all contracts
        الحصول على سجل المدفوعات لجميع العقود
        
        Returns:
            QuerySet: Payment receipts
        """
        from .receipt_models import Receipt
        contract_ids = self.get_all_contracts().values_list('id', flat=True)
        return Receipt.objects.filter(
            contract_id__in=contract_ids
        ).order_by('-payment_date')
    
    def get_statistics(self):
        """
        Get comprehensive tenant statistics
        الحصول على إحصائيات شاملة للمستأجر
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            'active_contracts': self.get_active_contracts().count(),
            'total_contracts': self.get_all_contracts().count(),
            'current_units': self.get_current_units().count(),
            'outstanding_balance': self.get_outstanding_balance(),
            'has_outstanding': self.has_outstanding_payments(),
            'is_id_expired': self.is_id_expired(),
            'is_blacklisted': self.is_blacklisted,
            'rating': self.rating,
        }


# ========================================
# TenantDocument Model
# ========================================

class TenantDocument(TimeStampedModel):
    """
    Tenant Document Model
    نموذج مستندات المستأجر
    
    لتخزين المستندات المتعلقة بالمستأجر
    """
    
    # ========================================
    # Relationships
    # ========================================
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('المستأجر'),
        help_text=_('المستأجر المرتبط بالمستند')
    )
    
    # ========================================
    # Document Information
    # ========================================
    document_type = models.CharField(
        _('نوع المستند'),
        max_length=20,
        choices=DocumentType.choices,
        db_index=True,
        help_text=_('نوع المستند')
    )
    
    title = models.CharField(
        _('العنوان'),
        max_length=200,
        help_text=_('عنوان أو وصف للمستند')
    )
    
    file = models.FileField(
        _('الملف'),
        upload_to='tenant_documents/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            )
        ],
        help_text=_('ملف المستند (PDF, JPG, PNG, DOC)')
    )
    
    file_size = models.PositiveIntegerField(
        _('حجم الملف (بايت)'),
        null=True,
        blank=True,
        editable=False,
        help_text=_('حجم الملف بالبايت (يُحسب تلقائياً)')
    )
    
    # ========================================
    # Additional Information
    # ========================================
    issue_date = models.DateField(
        _('تاريخ الإصدار'),
        null=True,
        blank=True,
        help_text=_('تاريخ إصدار المستند')
    )
    
    expiry_date = models.DateField(
        _('تاريخ الانتهاء'),
        null=True,
        blank=True,
        help_text=_('تاريخ انتهاء صلاحية المستند (إن وجد)')
    )
    
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات عن المستند')
    )
    
    # ========================================
    # Tracking
    # ========================================
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_tenant_documents',
        verbose_name=_('تم الرفع بواسطة'),
        help_text=_('المستخدم الذي رفع المستند')
    )
    
    uploaded_at = models.DateTimeField(
        _('تاريخ الرفع'),
        auto_now_add=True,
        help_text=_('تاريخ ووقت رفع المستند')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'tenant_documents'
        verbose_name = _('مستند مستأجر')
        verbose_name_plural = _('مستندات المستأجرين')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['tenant', 'document_type']),
            models.Index(fields=['document_type']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['-uploaded_at']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.tenant.name} - {self.get_document_type_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate file size"""
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """
        Check if document is expired
        التحقق من انتهاء صلاحية المستند
        
        Returns:
            bool: True if expired
        """
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()
    
    def is_expiring_soon(self, days=30):
        """
        Check if document is expiring soon
        التحقق من قرب انتهاء المستند
        
        Args:
            days: Number of days threshold
            
        Returns:
            bool: True if expiring within specified days
        """
        if not self.expiry_date:
            return False
        
        days_until_expiry = calculate_days_between(
            timezone.now().date(),
            self.expiry_date
        )
        return 0 <= days_until_expiry <= days
    
    def get_file_extension(self):
        """
        Get file extension
        الحصول على امتداد الملف
        
        Returns:
            str: File extension
        """
        import os
        return os.path.splitext(self.file.name)[1].lower()
    
    def get_formatted_file_size(self):
        """
        Get formatted file size
        الحصول على حجم الملف المنسق
        
        Returns:
            str: Formatted file size (KB, MB, etc.)
        """
        if not self.file_size:
            return '0 B'
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=Tenant)
def tenant_post_save(sender, instance, created, **kwargs):
    """
    Signal handler after tenant is saved
    معالج الإشارة بعد حفظ المستأجر
    """
    if created:
        # يمكن إضافة منطق عند إنشاء مستأجر جديد
        pass
    
    # التحقق من قرب انتهاء الهوية
    if instance.is_id_expiring_soon(days=30):
        # يمكن إنشاء إشعار تلقائي
        pass


@receiver(post_save, sender=TenantDocument)
def tenant_document_post_save(sender, instance, created, **kwargs):
    """
    Signal handler after document is saved
    معالج الإشارة بعد حفظ مستند
    """
    if created:
        # يمكن إضافة منطق عند رفع مستند جديد
        pass