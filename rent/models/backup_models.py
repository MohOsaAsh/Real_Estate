# models/backup_models.py

"""
Backup Models
نماذج النسخ الاحتياطي
"""

from .common_imports_models import *


# ========================================
# Choices/Enums
# ========================================

class BackupType(models.TextChoices):
    """نوع النسخ الاحتياطي"""
    FULL = 'full', _('كامل')
    INCREMENTAL = 'incremental', _('تزايدي')
    PARTIAL = 'partial', _('جزئي')
    DIFFERENTIAL = 'differential', _('تفاضلي')


class BackupStatus(models.TextChoices):
    """حالة النسخة الاحتياطية"""
    PENDING = 'pending', _('قيد الانتظار')
    IN_PROGRESS = 'in_progress', _('قيد التنفيذ')
    COMPLETED = 'completed', _('مكتمل')
    FAILED = 'failed', _('فشل')
    CORRUPTED = 'corrupted', _('تالف')


class BackupFrequency(models.TextChoices):
    """تكرار النسخ الاحتياطي"""
    HOURLY = 'hourly', _('كل ساعة')
    DAILY = 'daily', _('يومي')
    WEEKLY = 'weekly', _('أسبوعي')
    MONTHLY = 'monthly', _('شهري')
    MANUAL = 'manual', _('يدوي')


# ========================================
# Backup Model
# ========================================

class Backup(TimeStampedModel, UserTrackingModel):
    """
    Backup Model
    نموذج النسخة الاحتياطية
    
    يُسجل معلومات النسخة الاحتياطية المُنفذة
    """
    
    # ========================================
    # Backup Information
    # ========================================
    backup_type = models.CharField(
        _('نوع النسخ'),
        max_length=20,
        choices=BackupType.choices,
        default=BackupType.FULL,
        help_text=_('نوع النسخة الاحتياطية')
    )
    
    file_name = models.CharField(
        _('اسم الملف'),
        max_length=200,
        help_text=_('اسم ملف النسخة الاحتياطية')
    )
    
    file_path = models.CharField(
        _('مسار الملف'),
        max_length=500,
        help_text=_('المسار الكامل للملف')
    )
    
    file_size = models.BigIntegerField(
        _('حجم الملف'),
        default=0,
        help_text=_('حجم الملف بالبايت')
    )
    
    # ========================================
    # Backup Content
    # ========================================
    tables_count = models.PositiveIntegerField(
        _('عدد الجداول'),
        default=0,
        help_text=_('عدد الجداول المشمولة في النسخة')
    )
    
    records_count = models.PositiveIntegerField(
        _('عدد السجلات'),
        default=0,
        help_text=_('إجمالي عدد السجلات')
    )
    
    included_tables = models.JSONField(
        _('الجداول المشمولة'),
        null=True,
        blank=True,
        help_text=_('قائمة الجداول المشمولة في النسخة')
    )
    
    # ========================================
    # Status
    # ========================================
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=BackupStatus.choices,
        default=BackupStatus.PENDING,
        db_index=True,
        help_text=_('حالة النسخة الاحتياطية')
    )
    
    is_successful = models.BooleanField(
        _('ناجح'),
        default=True,
        db_index=True,
        help_text=_('هل النسخة الاحتياطية ناجحة؟')
    )
    
    error_message = models.TextField(
        _('رسالة الخطأ'),
        blank=True,
        help_text=_('رسالة الخطأ في حالة الفشل')
    )
    
    # ========================================
    # Timing
    # ========================================
    started_at = models.DateTimeField(
        _('بدأ في'),
        null=True,
        blank=True,
        help_text=_('وقت بدء النسخ الاحتياطي')
    )
    
    completed_at = models.DateTimeField(
        _('انتهى في'),
        null=True,
        blank=True,
        help_text=_('وقت انتهاء النسخ الاحتياطي')
    )
    
    duration = models.DurationField(
        _('المدة'),
        null=True,
        blank=True,
        help_text=_('مدة تنفيذ النسخ الاحتياطي')
    )
    
    # ========================================
    # Verification
    # ========================================
    is_verified = models.BooleanField(
        _('تم التحقق'),
        default=False,
        help_text=_('هل تم التحقق من سلامة النسخة؟')
    )
    
    verified_at = models.DateTimeField(
        _('تاريخ التحقق'),
        null=True,
        blank=True,
        help_text=_('تاريخ التحقق من النسخة')
    )
    
    checksum = models.CharField(
        _('المجموع الاختباري'),
        max_length=64,
        blank=True,
        help_text=_('MD5 أو SHA256 checksum للملف')
    )
    
    # ========================================
    # Retention
    # ========================================
    expires_at = models.DateTimeField(
        _('ينتهي في'),
        null=True,
        blank=True,
        help_text=_('تاريخ انتهاء صلاحية النسخة')
    )
    
    is_archived = models.BooleanField(
        _('مؤرشف'),
        default=False,
        help_text=_('هل النسخة مؤرشفة؟')
    )
    
    # ========================================
    # Additional Information
    # ========================================
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات عن النسخة')
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
        db_table = 'backups'
        verbose_name = _('نسخة احتياطية')
        verbose_name_plural = _('النسخ الاحتياطية')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['is_successful']),
            models.Index(fields=['backup_type']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.file_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Calculate duration before saving"""
        if self.completed_at and self.started_at:
            self.duration = self.completed_at - self.started_at
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """
        Get human-readable file size
        الحصول على حجم الملف بصيغة مقروءة
        
        Returns:
            str: File size (e.g., "1.5 GB")
        """
        size = self.file_size
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        
        return f"{size:.2f} PB"
    
    def mark_as_verified(self, checksum=None):
        """
        Mark backup as verified
        تحديد النسخة كمُتحقق منها
        """
        self.is_verified = True
        self.verified_at = timezone.now()
        if checksum:
            self.checksum = checksum
        self.save(update_fields=['is_verified', 'verified_at', 'checksum'])
    
    def mark_as_completed(self):
        """
        Mark backup as completed
        تحديد النسخة كمُكتملة
        """
        self.status = BackupStatus.COMPLETED
        self.completed_at = timezone.now()
        self.is_successful = True
        self.save()
    
    def mark_as_failed(self, error_message=''):
        """
        Mark backup as failed
        تحديد النسخة كفاشلة
        """
        self.status = BackupStatus.FAILED
        self.completed_at = timezone.now()
        self.is_successful = False
        self.error_message = error_message
        self.save()


# ========================================
# BackupSchedule Model
# ========================================

class BackupSchedule(TimeStampedModel, UserTrackingModel):
    """
    Backup Schedule Model
    نموذج جدول النسخ الاحتياطي
    
    يُحدد مواعيد وإعدادات النسخ الاحتياطي التلقائي
    """
    
    # ========================================
    # Schedule Information
    # ========================================
    name = models.CharField(
        _('اسم الجدول'),
        max_length=200,
        help_text=_('اسم واضح للجدول')
    )
    
    backup_type = models.CharField(
        _('نوع النسخ'),
        max_length=20,
        choices=BackupType.choices,
        default=BackupType.FULL,
        help_text=_('نوع النسخة الاحتياطية المجدولة')
    )
    
    frequency = models.CharField(
        _('التكرار'),
        max_length=20,
        choices=BackupFrequency.choices,
        default=BackupFrequency.DAILY,
        help_text=_('كم مرة يتم النسخ الاحتياطي')
    )
    
    # ========================================
    # Timing
    # ========================================
    execution_time = models.TimeField(
        _('وقت التنفيذ'),
        help_text=_('الوقت المحدد للنسخ الاحتياطي')
    )
    
    day_of_week = models.PositiveIntegerField(
        _('يوم الأسبوع'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text=_('0=الأحد, 6=السبت (للنسخ الأسبوعي)')
    )
    
    day_of_month = models.PositiveIntegerField(
        _('يوم الشهر'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_('اليوم من الشهر (للنسخ الشهري)')
    )
    
    # ========================================
    # Content Settings
    # ========================================
    include_all_tables = models.BooleanField(
        _('شمل جميع الجداول'),
        default=True,
        help_text=_('هل يتم نسخ جميع الجداول؟')
    )
    
    included_tables = models.JSONField(
        _('الجداول المشمولة'),
        null=True,
        blank=True,
        help_text=_('قائمة الجداول للنسخ (إذا لم يكن الكل)')
    )
    
    excluded_tables = models.JSONField(
        _('الجداول المستبعدة'),
        null=True,
        blank=True,
        help_text=_('جداول لا تُنسخ حتى لو كان الكل مفعّل')
    )
    
    # ========================================
    # Storage Settings
    # ========================================
    storage_path = models.CharField(
        _('مسار التخزين'),
        max_length=500,
        help_text=_('المسار لحفظ النسخ الاحتياطية')
    )
    
    retention_days = models.PositiveIntegerField(
        _('مدة الاحتفاظ (أيام)'),
        default=30,
        help_text=_('عدد الأيام للاحتفاظ بالنسخ القديمة')
    )
    
    max_backups_to_keep = models.PositiveIntegerField(
        _('أقصى عدد للنسخ'),
        default=10,
        help_text=_('الحد الأقصى لعدد النسخ المحفوظة')
    )
    
    compress_backup = models.BooleanField(
        _('ضغط النسخة'),
        default=True,
        help_text=_('هل يتم ضغط الملف؟')
    )
    
    # ========================================
    # Status
    # ========================================
    is_active = models.BooleanField(
        _('نشط'),
        default=True,
        db_index=True,
        help_text=_('هل الجدول مُفعّل؟')
    )
    
    last_run = models.DateTimeField(
        _('آخر تنفيذ'),
        null=True,
        blank=True,
        help_text=_('تاريخ ووقت آخر نسخ احتياطي')
    )
    
    next_run = models.DateTimeField(
        _('التنفيذ التالي'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('موعد النسخ الاحتياطي القادم')
    )
    
    last_backup = models.ForeignKey(
        Backup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_last',
        verbose_name=_('آخر نسخة'),
        help_text=_('آخر نسخة احتياطية مُنفذة')
    )
    
    # ========================================
    # Notifications
    # ========================================
    notify_on_success = models.BooleanField(
        _('إشعار عند النجاح'),
        default=False,
        help_text=_('إرسال إشعار عند نجاح النسخ')
    )
    
    notify_on_failure = models.BooleanField(
        _('إشعار عند الفشل'),
        default=True,
        help_text=_('إرسال إشعار عند فشل النسخ')
    )
    
    notification_emails = models.JSONField(
        _('بريد الإشعارات'),
        null=True,
        blank=True,
        help_text=_('قائمة البريد الإلكتروني للإشعارات')
    )
    
    # ========================================
    # Additional Information
    # ========================================
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات عن الجدول')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'backup_schedules'
        verbose_name = _('جدول نسخ احتياطي')
        verbose_name_plural = _('جداول النسخ الاحتياطي')
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'next_run']),
            models.Index(fields=['frequency']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"
    
    def calculate_next_run(self):
        """
        Calculate next backup time
        حساب وقت النسخ التالي
        """
        from datetime import datetime, timedelta
        
        now = timezone.now()
        base_time = self.execution_time
        
        if self.frequency == BackupFrequency.HOURLY:
            # كل ساعة
            self.next_run = now + timedelta(hours=1)
        
        elif self.frequency == BackupFrequency.DAILY:
            # يومي
            next_date = now.date() + timedelta(days=1)
            self.next_run = timezone.make_aware(
                datetime.combine(next_date, base_time)
            )
        
        elif self.frequency == BackupFrequency.WEEKLY:
            # أسبوعي
            days_ahead = 7
            if self.day_of_week is not None:
                current_day = now.weekday()
                days_ahead = (self.day_of_week - current_day) % 7
                if days_ahead == 0:
                    days_ahead = 7
            
            next_date = now.date() + timedelta(days=days_ahead)
            self.next_run = timezone.make_aware(
                datetime.combine(next_date, base_time)
            )
        
        elif self.frequency == BackupFrequency.MONTHLY:
            # شهري
            if self.day_of_month:
                next_month = now.month + 1
                next_year = now.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                
                try:
                    next_date = datetime(
                        next_year,
                        next_month,
                        self.day_of_month
                    ).date()
                except ValueError:
                    next_date = datetime(next_year, next_month, 1).date()
                
                self.next_run = timezone.make_aware(
                    datetime.combine(next_date, base_time)
                )
        
        self.save(update_fields=['next_run'])


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=BackupSchedule)
def backup_schedule_post_save(sender, instance, created, **kwargs):
    """Signal handler after schedule is saved"""
    if created:
        # حساب أول تنفيذ
        instance.calculate_next_run()


@receiver(post_save, sender=Backup)
def backup_post_save(sender, instance, created, **kwargs):
    """Signal handler after backup is saved"""
    if instance.status == BackupStatus.COMPLETED and instance.is_successful:
        # تحديث الجدول إذا كان مرتبط
        schedules = BackupSchedule.objects.filter(
            last_backup=instance
        )
        for schedule in schedules:
            schedule.last_run = instance.created_at
            schedule.calculate_next_run()