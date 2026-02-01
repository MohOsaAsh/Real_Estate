# models/notification_models.py

"""
Notification and Alert Models
نماذج الإشعارات والتنبيهات
"""

from .common_imports_models import *
from .contract_models import Contract
from .tenant_models import Tenant


# ========================================
# Choices/Enums  
# ========================================

class PriorityLevel(models.TextChoices):
    """مستوى الأولوية"""
    LOW = 'low', _('منخفض')
    MEDIUM = 'medium', _('متوسط')
    HIGH = 'high', _('عالي')
    URGENT = 'urgent', _('عاجل')


# ========================================
# Notification Model
# ========================================

class Notification(TimeStampedModel):
    """
    Notification Model
    نموذج الإشعارات
    
    يُستخدم لإدارة الإشعارات والتنبيهات في النظام
    """
    
    # ========================================
    # Notification Information
    # ========================================
    notification_type = models.CharField(
        _('نوع الإشعار'),
        max_length=50,
        choices=NotificationType.choices,  # ✅ من common_imports_models
        db_index=True,
        help_text=_('نوع/تصنيف الإشعار')
    )
    
    title = models.CharField(
        _('العنوان'),
        max_length=200,
        help_text=_('عنوان الإشعار')
    )
    
    message = models.TextField(
        _('الرسالة'),
        help_text=_('نص الإشعار التفصيلي')
    )
    
    priority = models.CharField(
        _('الأولوية'),
        max_length=20,
        choices=PriorityLevel.choices,
        default=PriorityLevel.MEDIUM,
        db_index=True,
        help_text=_('مستوى أولوية الإشعار')
    )
    
    # ========================================
    # Relationships (Optional)
    # ========================================
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('العقد'),
        help_text=_('العقد المرتبط بالإشعار (إن وجد)')
    )
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('المستأجر'),
        help_text=_('المستأجر المرتبط بالإشعار (إن وجد)')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('المستخدم'),
        help_text=_('المستخدم المستهدف بالإشعار')
    )
    
    # ========================================
    # Status
    # ========================================
    is_read = models.BooleanField(
        _('تم القراءة'),
        default=False,
        db_index=True,
        help_text=_('هل تمت قراءة الإشعار؟')
    )
    
    is_sent = models.BooleanField(
        _('تم الإرسال'),
        default=False,
        db_index=True,
        help_text=_('هل تم إرسال الإشعار؟')
    )
    
    is_dismissed = models.BooleanField(
        _('تم التجاهل'),
        default=False,
        db_index=True,
        help_text=_('هل تم تجاهل/إخفاء الإشعار؟')
    )
    
    # ========================================
    # Dates
    # ========================================
    due_date = models.DateField(
        _('تاريخ الاستحقاق'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('تاريخ الاستحقاق المرتبط بالإشعار')
    )
    
    sent_at = models.DateTimeField(
        _('تاريخ الإرسال'),
        null=True,
        blank=True,
        help_text=_('تاريخ ووقت إرسال الإشعار')
    )
    
    read_at = models.DateTimeField(
        _('تاريخ القراءة'),
        null=True,
        blank=True,
        help_text=_('تاريخ ووقت قراءة الإشعار')
    )
    
    dismissed_at = models.DateTimeField(
        _('تاريخ التجاهل'),
        null=True,
        blank=True,
        help_text=_('تاريخ ووقت تجاهل الإشعار')
    )
    
    # ========================================
    # Additional Data
    # ========================================
    action_url = models.CharField(
        _('رابط الإجراء'),
        max_length=500,
        blank=True,
        help_text=_('رابط الصفحة المرتبطة بالإشعار')
    )
    
    metadata = models.JSONField(
        _('بيانات إضافية'),
        null=True,
        blank=True,
        help_text=_('بيانات إضافية بصيغة JSON')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'notifications'
        verbose_name = _('إشعار')
        verbose_name_plural = _('الإشعارات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type', 'is_read']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['priority', 'is_read']),
            models.Index(fields=['due_date']),
            models.Index(fields=['created_at']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"
    
    def mark_as_read(self, user=None):
        """
        Mark notification as read
        تحديد الإشعار كمقروء
        
        Args:
            user: User marking as read
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_sent(self):
        """
        Mark notification as sent
        تحديد الإشعار كمُرسل
        """
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=['is_sent', 'sent_at'])
    
    def dismiss(self):
        """
        Dismiss notification
        تجاهل الإشعار
        """
        if not self.is_dismissed:
            self.is_dismissed = True
            self.dismissed_at = timezone.now()
            self.save(update_fields=['is_dismissed', 'dismissed_at'])
    
    def is_overdue(self):
        """
        Check if notification is overdue
        التحقق من تأخر الإشعار
        
        Returns:
            bool: True if overdue
        """
        if not self.due_date:
            return False
        return timezone.now().date() > self.due_date
    
    def get_age_hours(self):
        """
        Get notification age in hours
        الحصول على عمر الإشعار بالساعات
        
        Returns:
            float: Age in hours
        """
        delta = timezone.now() - self.created_at
        return delta.total_seconds() / 3600
    
    def get_age_days(self):
        """
        Get notification age in days
        الحصول على عمر الإشعار بالأيام
        
        Returns:
            int: Age in days
        """
        delta = timezone.now() - self.created_at
        return delta.days
    
    # ========================================
    # Class Methods - Auto Notification Generators
    # ========================================
    
    @classmethod
    def check_contract_expiry(cls, days_before=30):
        """
        Check and create notifications for expiring contracts
        التحقق وإنشاء إشعارات للعقود المنتهية قريباً
        
        Args:
            days_before: Number of days before expiry to notify
        """
        today = timezone.now().date()
        expiry_date = today + timedelta(days=days_before)
        
        expiring_contracts = Contract.objects.filter(
            status=ContractStatus.ACTIVE,
            end_date__lte=expiry_date,
            end_date__gt=today,
            is_deleted=False
        )
        
        for contract in expiring_contracts:
            days_left = calculate_days_between(today, contract.end_date)
            
            # التحقق من عدم وجود إشعار مسبق لنفس اليوم
            existing = cls.objects.filter(
                contract=contract,
                notification_type=NotificationType.CONTRACT_EXPIRY,
                created_at__date=today
            ).exists()
            
            if not existing:
                # تحديد الأولوية بناءً على الأيام المتبقية
                if days_left <= 7:
                    priority = PriorityLevel.URGENT
                elif days_left <= 15:
                    priority = PriorityLevel.HIGH
                else:
                    priority = PriorityLevel.MEDIUM
                
                cls.objects.create(
                    notification_type=NotificationType.CONTRACT_EXPIRY,
                    title=_('عقد على وشك الانتهاء'),
                    message=_(
                        f'العقد {contract.contract_number} للمستأجر {contract.tenant.name} '
                        f'ينتهي في {contract.end_date.strftime("%Y-%m-%d")} '
                        f'(باقي {days_left} يوم)'
                    ),
                    contract=contract,
                    tenant=contract.tenant,
                    priority=priority,
                    due_date=contract.end_date,
                    action_url=f'/contracts/{contract.pk}/'
                )
    
    @classmethod
    def check_payment_due(cls):
        """
        Check and create notifications for due payments
        التحقق وإنشاء إشعارات للدفعات المستحقة
        """
        today = timezone.now().date()
        
        # الحصول على العقود النشطة
        active_contracts = Contract.objects.filter(
            status=ContractStatus.ACTIVE,
            is_deleted=False
        )
        
        for contract in active_contracts:
            # حساب المبلغ المستحق
            outstanding = contract.get_outstanding_amount(include_future=False)
            
            if outstanding > 0:
                # التحقق من عدم وجود إشعار مسبق لنفس اليوم
                existing = cls.objects.filter(
                    contract=contract,
                    notification_type=NotificationType.PAYMENT_DUE,
                    created_at__date=today
                ).exists()
                
                if not existing:
                    cls.objects.create(
                        notification_type=NotificationType.PAYMENT_DUE,
                        title=_('دفعة مستحقة'),
                        message=_(
                            f'يوجد مبلغ مستحق للعقد {contract.contract_number}: '
                            f'{format_currency(outstanding)}'
                        ),
                        contract=contract,
                        tenant=contract.tenant,
                        priority=PriorityLevel.HIGH,
                        due_date=today,
                        action_url=f'/contracts/{contract.pk}/payments/'
                    )
    
    @classmethod
    def check_payment_overdue(cls):
        """
        Check and create notifications for overdue payments
        التحقق وإنشاء إشعارات للدفعات المتأخرة
        """
        today = timezone.now().date()
        
        # الحصول على العقود النشطة أو المنتهية
        contracts = Contract.objects.filter(
            status__in=[ContractStatus.ACTIVE, ContractStatus.EXPIRED],
            is_deleted=False
        )
        
        for contract in contracts:
            outstanding = contract.get_outstanding_amount(include_future=False)
            
            if outstanding > 0:
                # التحقق من التأخير (افتراضياً بعد فترة السماح)
                grace_days = contract.grace_period_days
                threshold_date = today - timedelta(days=grace_days)
                
                if contract.start_date <= threshold_date:
                    # التحقق من عدم وجود إشعار تأخير حديث
                    recent_overdue = cls.objects.filter(
                        contract=contract,
                        notification_type=NotificationType.PAYMENT_OVERDUE,
                        created_at__gte=today - timedelta(days=7)
                    ).exists()
                    
                    if not recent_overdue:
                        cls.objects.create(
                            notification_type=NotificationType.PAYMENT_OVERDUE,
                            title=_('دفعة متأخرة'),
                            message=_(
                                f'يوجد مبلغ متأخر للعقد {contract.contract_number}: '
                                f'{format_currency(outstanding)}'
                            ),
                            contract=contract,
                            tenant=contract.tenant,
                            priority=PriorityLevel.URGENT,
                            due_date=today,
                            action_url=f'/contracts/{contract.pk}/payments/'
                        )
    
    @classmethod
    def create_system_notification(cls, title, message, priority=PriorityLevel.MEDIUM, user=None):
        """
        Create system notification
        إنشاء إشعار نظام
        
        Args:
            title: Notification title
            message: Notification message
            priority: Priority level
            user: Target user
            
        Returns:
            Notification: Created notification
        """
        return cls.objects.create(
            notification_type=NotificationType.GENERAL,
            title=title,
            message=message,
            priority=priority,
            user=user
        )
    
    @classmethod
    def get_unread_count(cls, user=None):
        """
        Get count of unread notifications
        الحصول على عدد الإشعارات غير المقروءة
        
        Args:
            user: Filter by user
            
        Returns:
            int: Unread count
        """
        queryset = cls.objects.filter(is_read=False, is_dismissed=False)
        if user:
            queryset = queryset.filter(user=user)
        return queryset.count()
    
    @classmethod
    def mark_all_as_read(cls, user=None):
        """
        Mark all notifications as read
        تحديد جميع الإشعارات كمقروءة
        
        Args:
            user: Filter by user
        """
        queryset = cls.objects.filter(is_read=False)
        if user:
            queryset = queryset.filter(user=user)
        queryset.update(is_read=True, read_at=timezone.now())


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):
    """Signal handler after notification is saved"""
    if created:
        # يمكن إضافة منطق لإرسال الإشعار عبر البريد الإلكتروني أو SMS
        pass