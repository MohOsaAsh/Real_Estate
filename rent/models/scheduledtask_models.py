# models/scheduledtask_models.py

"""
Scheduled Task Models
نماذج المهام المجدولة
"""

from .common_imports_models import *


# ========================================
# Choices/Enums
# ========================================

class TaskType(models.TextChoices):
    """نوع المهمة"""
    NOTIFICATION = 'notification', _('إشعار')
    REPORT = 'report', _('تقرير')
    BACKUP = 'backup', _('نسخ احتياطي')
    CLEANUP = 'cleanup', _('تنظيف')
    SYNC = 'sync', _('مزامنة')
    CALCULATION = 'calculation', _('حساب')


class TaskFrequency(models.TextChoices):
    """تكرار المهمة"""
    DAILY = 'daily', _('يومي')
    WEEKLY = 'weekly', _('أسبوعي')
    MONTHLY = 'monthly', _('شهري')
    QUARTERLY = 'quarterly', _('ربع سنوي')
    YEARLY = 'yearly', _('سنوي')
    CUSTOM = 'custom', _('مخصص')


class TaskStatus(models.TextChoices):
    """حالة تنفيذ المهمة"""
    PENDING = 'pending', _('قيد الانتظار')
    RUNNING = 'running', _('قيد التنفيذ')
    SUCCESS = 'success', _('نجح')
    FAILED = 'failed', _('فشل')
    CANCELLED = 'cancelled', _('ملغي')


# ========================================
# ScheduledTask Model
# ========================================

class ScheduledTask(TimeStampedModel):
    """
    Scheduled Task Model
    نموذج المهام المجدولة
    
    يُستخدم لجدولة المهام الدورية مثل:
    - إرسال الإشعارات
    - توليد التقارير
    - النسخ الاحتياطي
    - التنظيف
    """
    
    # ========================================
    # Basic Information
    # ========================================
    name = models.CharField(
        _('اسم المهمة'),
        max_length=200,
        help_text=_('اسم واضح للمهمة')
    )
    
    task_type = models.CharField(
        _('نوع المهمة'),
        max_length=20,
        choices=TaskType.choices,
        help_text=_('تصنيف المهمة')
    )
    
    frequency = models.CharField(
        _('التكرار'),
        max_length=20,
        choices=TaskFrequency.choices,
        default=TaskFrequency.DAILY,
        help_text=_('كم مرة تُنفذ المهمة')
    )
    
    # ========================================
    # Execution Settings
    # ========================================
    execution_time = models.TimeField(
        _('وقت التنفيذ'),
        null=True,
        blank=True,
        help_text=_('الوقت المحدد للتنفيذ اليومي')
    )
    
    day_of_week = models.PositiveIntegerField(
        _('يوم الأسبوع'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text=_('0=الأحد, 6=السبت')
    )
    
    day_of_month = models.PositiveIntegerField(
        _('يوم الشهر'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_('اليوم من الشهر (1-31)')
    )
    
    month_of_year = models.PositiveIntegerField(
        _('شهر السنة'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_('الشهر من السنة (1-12)')
    )
    
    # ========================================
    # Task Configuration
    # ========================================
    task_function = models.CharField(
        _('دالة المهمة'),
        max_length=500,
        help_text=_('المسار الكامل للدالة (مثال: app.tasks.send_notifications)')
    )
    
    task_parameters = models.JSONField(
        _('معاملات المهمة'),
        default=dict,
        blank=True,
        help_text=_('المعاملات المُمررة للدالة بصيغة JSON')
    )
    
    # ========================================
    # Status & Scheduling
    # ========================================
    is_active = models.BooleanField(
        _('نشط'),
        default=True,
        db_index=True,
        help_text=_('هل المهمة مُفعّلة للتنفيذ؟')
    )
    
    last_run = models.DateTimeField(
        _('آخر تنفيذ'),
        null=True,
        blank=True,
        help_text=_('تاريخ ووقت آخر تنفيذ')
    )
    
    last_status = models.CharField(
        _('الحالة الأخيرة'),
        max_length=20,
        choices=TaskStatus.choices,
        blank=True,
        help_text=_('نتيجة آخر تنفيذ')
    )
    
    next_run = models.DateTimeField(
        _('التنفيذ التالي'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('موعد التنفيذ القادم')
    )
    
    # ========================================
    # Statistics
    # ========================================
    success_count = models.PositiveIntegerField(
        _('عدد النجاحات'),
        default=0,
        help_text=_('عدد مرات التنفيذ الناجح')
    )
    
    failure_count = models.PositiveIntegerField(
        _('عدد الفشل'),
        default=0,
        help_text=_('عدد مرات فشل التنفيذ')
    )
    
    total_run_time = models.DurationField(
        _('إجمالي وقت التنفيذ'),
        null=True,
        blank=True,
        help_text=_('مجموع وقت تنفيذ جميع المهام')
    )
    
    average_run_time = models.DurationField(
        _('متوسط وقت التنفيذ'),
        null=True,
        blank=True,
        help_text=_('متوسط وقت تنفيذ المهمة')
    )
    
    # ========================================
    # Additional Information
    # ========================================
    notes = models.TextField(
        _('ملاحظات'),
        blank=True,
        help_text=_('أي ملاحظات عن المهمة')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'scheduled_tasks'
        verbose_name = _('مهمة مجدولة')
        verbose_name_plural = _('المهام المجدولة')
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'next_run']),
            models.Index(fields=['task_type']),
            models.Index(fields=['frequency']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"
    
    def calculate_next_run(self):
        """
        Calculate next execution time
        حساب وقت التنفيذ التالي
        """
        from datetime import datetime, timedelta
        
        now = timezone.now()
        
        if not self.execution_time:
            # إذا لم يكن هناك وقت محدد، استخدم الوقت الحالي
            base_time = now.time()
        else:
            base_time = self.execution_time
        
        if self.frequency == TaskFrequency.DAILY:
            # يومي: غداً في نفس الوقت
            next_date = now.date() + timedelta(days=1)
            self.next_run = timezone.make_aware(
                datetime.combine(next_date, base_time)
            )
        
        elif self.frequency == TaskFrequency.WEEKLY:
            # أسبوعي: في نفس يوم الأسبوع القادم
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
        
        elif self.frequency == TaskFrequency.MONTHLY:
            # شهري: في نفس اليوم من الشهر القادم
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
                    # إذا كان اليوم غير موجود في الشهر
                    next_date = datetime(
                        next_year, 
                        next_month, 
                        1
                    ).date()
                
                self.next_run = timezone.make_aware(
                    datetime.combine(next_date, base_time)
                )
        
        elif self.frequency == TaskFrequency.QUARTERLY:
            # ربع سنوي: بعد 3 أشهر
            next_date = now.date() + timedelta(days=90)
            self.next_run = timezone.make_aware(
                datetime.combine(next_date, base_time)
            )
        
        elif self.frequency == TaskFrequency.YEARLY:
            # سنوي: بعد سنة
            if self.month_of_year and self.day_of_month:
                next_year = now.year + 1
                try:
                    next_date = datetime(
                        next_year,
                        self.month_of_year,
                        self.day_of_month
                    ).date()
                except ValueError:
                    next_date = datetime(next_year, 1, 1).date()
                
                self.next_run = timezone.make_aware(
                    datetime.combine(next_date, base_time)
                )
        
        self.save(update_fields=['next_run'])
    
    def mark_execution_success(self, run_time=None):
        """
        Mark task as successfully executed
        تحديد المهمة كمنفذة بنجاح
        """
        self.last_run = timezone.now()
        self.last_status = TaskStatus.SUCCESS
        self.success_count += 1
        
        if run_time:
            if self.total_run_time:
                self.total_run_time += run_time
            else:
                self.total_run_time = run_time
            
            # حساب المتوسط
            total_executions = self.success_count + self.failure_count
            if total_executions > 0:
                self.average_run_time = self.total_run_time / total_executions
        
        self.calculate_next_run()
    
    def mark_execution_failed(self):
        """
        Mark task as failed
        تحديد المهمة كفاشلة
        """
        self.last_run = timezone.now()
        self.last_status = TaskStatus.FAILED
        self.failure_count += 1
        self.calculate_next_run()


# ========================================
# TaskExecution Model
# ========================================

class TaskExecution(TimeStampedModel):
    """
    Task Execution Record
    سجل تنفيذ المهمة
    
    يُسجل كل تنفيذ للمهمة مع تفاصيله
    """
    
    # ========================================
    # Relationships
    # ========================================
    task = models.ForeignKey(
        ScheduledTask,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name=_('المهمة'),
        help_text=_('المهمة المُنفذة')
    )
    
    # ========================================
    # Execution Information
    # ========================================
    started_at = models.DateTimeField(
        _('بدأ في'),
        help_text=_('وقت بدء التنفيذ')
    )
    
    finished_at = models.DateTimeField(
        _('انتهى في'),
        null=True,
        blank=True,
        help_text=_('وقت انتهاء التنفيذ')
    )
    
    duration = models.DurationField(
        _('المدة'),
        null=True,
        blank=True,
        help_text=_('مدة التنفيذ')
    )
    
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
        help_text=_('حالة التنفيذ')
    )
    
    # ========================================
    # Results
    # ========================================
    result = models.TextField(
        _('النتيجة'),
        blank=True,
        help_text=_('نتيجة التنفيذ (نجاح أو رسالة خطأ)')
    )
    
    output = models.JSONField(
        _('المخرجات'),
        null=True,
        blank=True,
        help_text=_('مخرجات المهمة بصيغة JSON')
    )
    
    error_message = models.TextField(
        _('رسالة الخطأ'),
        blank=True,
        help_text=_('رسالة الخطأ إن حدث')
    )
    
    traceback = models.TextField(
        _('تتبع الخطأ'),
        blank=True,
        help_text=_('Stack trace للخطأ')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'task_executions'
        verbose_name = _('تنفيذ مهمة')
        verbose_name_plural = _('تنفيذات المهام')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['task', '-started_at']),
            models.Index(fields=['status']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.task.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Calculate duration before saving"""
        if self.finished_at and self.started_at:
            self.duration = self.finished_at - self.started_at
        super().save(*args, **kwargs)


# ========================================
# TaskLog Model
# ========================================

class TaskLog(TimeStampedModel):
    """
    Task Log Model
    نموذج سجل المهام
    
    يُسجل كل حدث مهم في دورة حياة المهمة
    """
    
    # ========================================
    # Log Levels
    # ========================================
    class LogLevel(models.TextChoices):
        DEBUG = 'debug', _('تصحيح')
        INFO = 'info', _('معلومات')
        WARNING = 'warning', _('تحذير')
        ERROR = 'error', _('خطأ')
        CRITICAL = 'critical', _('حرج')
    
    # ========================================
    # Relationships
    # ========================================
    task = models.ForeignKey(
        ScheduledTask,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('المهمة'),
        help_text=_('المهمة المُسجلة')
    )
    
    execution = models.ForeignKey(
        TaskExecution,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name=_('التنفيذ'),
        help_text=_('التنفيذ المرتبط (إن وجد)')
    )
    
    # ========================================
    # Log Information
    # ========================================
    level = models.CharField(
        _('المستوى'),
        max_length=20,
        choices=LogLevel.choices,
        default=LogLevel.INFO,
        db_index=True,
        help_text=_('مستوى السجل')
    )
    
    message = models.TextField(
        _('الرسالة'),
        help_text=_('نص السجل')
    )
    
    details = models.JSONField(
        _('التفاصيل'),
        null=True,
        blank=True,
        help_text=_('تفاصيل إضافية بصيغة JSON')
    )
    
    # ========================================
    # Metadata
    # ========================================
    class Meta:
        db_table = 'task_logs'
        verbose_name = _('سجل مهمة')
        verbose_name_plural = _('سجلات المهام')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', '-created_at']),
            models.Index(fields=['level']),
        ]
    
    # ========================================
    # Methods
    # ========================================
    def __str__(self):
        return f"{self.task.name} - {self.get_level_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=ScheduledTask)
def scheduled_task_post_save(sender, instance, created, **kwargs):
    """Signal handler after task is saved"""
    if created:
        # حساب أول تنفيذ
        instance.calculate_next_run()


@receiver(post_save, sender=TaskExecution)
def task_execution_post_save(sender, instance, created, **kwargs):
    """Signal handler after execution is saved"""
    if not created and instance.status in [TaskStatus.SUCCESS, TaskStatus.FAILED]:
        # تحديث إحصائيات المهمة
        if instance.status == TaskStatus.SUCCESS:
            instance.task.mark_execution_success(instance.duration)
        else:
            instance.task.mark_execution_failed()