# models/user_models.py

from .common_imports_models import *

# ========================================
# 1. نظام المستخدمين والصلاحيات
# ========================================

class UserProfile(models.Model):
    """ملف تعريف المستخدم مع الصلاحيات"""
    ROLE_CHOICES = [
        ('admin', 'مدير النظام'),
        ('accountant', 'محاسب'),
        ('leasing_manager', 'مدير إيجار'),
        ('receptionist', 'موظف استقبال'),
        ('viewer', 'مشاهد فقط'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('المستخدم'))
    role = models.CharField(_('الدور'), max_length=20, choices=ROLE_CHOICES, default='viewer')
    phone = models.CharField(_('رقم الهاتف'), max_length=20, blank=True)
    national_id = models.CharField(max_length=50, verbose_name='الرقم الوطني', blank=True, null=True)

    
    # الصلاحيات
    can_manage_contracts = models.BooleanField(_('يمكن إدارة العقود'), default=False)
    can_manage_tenants = models.BooleanField(_('يمكن إدارة المستأجرين'), default=False)
    can_manage_properties = models.BooleanField(_('يمكن إدارة العقارات'), default=False)
    can_process_payments = models.BooleanField(_('يمكن معالجة المدفوعات'), default=False)
    can_view_reports = models.BooleanField(_('يمكن مشاهدة التقارير'), default=False)
    can_manage_users = models.BooleanField(_('يمكن إدارة المستخدمين'), default=False)
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('ملف مستخدم')
        verbose_name_plural = _('ملفات المستخدمين')
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
