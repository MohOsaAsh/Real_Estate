# ====================================
# 1. audit_log/models.py
# ====================================

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class AuditLog(models.Model):
    """نموذج لتخزين سجلات التدقيق التلقائية"""
    
    ACTION_CHOICES = [
        ('create', 'إنشاء'),
        ('update', 'تحديث'),
        ('delete', 'حذف'),
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('login_failed', 'محاولة دخول فاشلة'),
        ('access', 'دخول صفحة'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='المستخدم',
        related_name='audit_logs'
    )
    user_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='اسم المستخدم')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name='العملية')

    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='نوع المحتوى'
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='معرف الكائن')
    content_object = GenericForeignKey('content_type', 'object_id')

    model_name = models.CharField(max_length=255, verbose_name='اسم الموديل', db_index=True)
    object_repr = models.CharField(max_length=500, null=True, blank=True, verbose_name='تمثيل الكائن')

    old_values = models.JSONField(null=True, blank=True, verbose_name='القيم القديمة')
    new_values = models.JSONField(null=True, blank=True, verbose_name='القيم الجديدة')
    changes = models.JSONField(null=True, blank=True, verbose_name='التغييرات فقط')

    request_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='مسار الطلب')
    request_method = models.CharField(max_length=10, null=True, blank=True, verbose_name='نوع الطلب')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='عنوان IP')
    user_agent = models.TextField(null=True, blank=True, verbose_name='معلومات المتصفح')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'سجل التدقيق'
        verbose_name_plural = 'سجلات التدقيق'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='idx_audit_created'),
            models.Index(fields=['user', '-created_at'], name='idx_audit_user'),
            models.Index(fields=['action', '-created_at'], name='idx_audit_action'),
            models.Index(fields=['model_name', '-created_at'], name='idx_audit_model'),
            models.Index(fields=['ip_address'], name='idx_audit_ip'),
        ]

    def __str__(self):
        return f"{self.user_name or 'نظام'} - {self.get_action_display()} - {self.model_name}"

    @classmethod
    def get_statistics(cls, days=30):
        """الحصول على إحصائيات النظام"""
        start_date = timezone.now() - timedelta(days=days)
        qs = cls.objects.filter(created_at__gte=start_date)

        return {
            'total_logs': qs.count(),
            'creates': qs.filter(action='create').count(),
            'updates': qs.filter(action='update').count(),
            'deletes': qs.filter(action='delete').count(),
            'logins': qs.filter(action='login').count(),
            'failed_logins': qs.filter(action='login_failed').count(),
            'by_action': qs.values('action').annotate(count=Count('id')),
            'by_user': qs.values('user_name').annotate(count=Count('id')).order_by('-count')[:10],
            'by_model': qs.values('model_name').annotate(count=Count('id')).order_by('-count')[:10],
            'suspicious_ips': qs.filter(action='login_failed').values('ip_address').annotate(count=Count('id')).filter(count__gte=3).order_by('-count'),
            'recent_logs': cls.objects.select_related('user').order_by('-created_at')[:20],
        }
