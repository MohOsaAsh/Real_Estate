# rent/mixins.py
from django.contrib.auth.mixins import AccessMixin
from django.contrib import messages
from django.shortcuts import redirect
from decimal import Decimal
from datetime import date, datetime
import json


class PermissionCheckMixin(AccessMixin):
    """Mixin للتحقق من الصلاحيات"""
    permission_required = None
    required_permission = None  # دعم الاسمين
    permission_denied_message = 'ليس لديك صلاحية للوصول إلى هذه الصفحة.'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        perm = self.permission_required or self.required_permission
        
        if not perm:
            return super().dispatch(request, *args, **kwargs)
        
        if not self.has_permission():
            messages.error(request, self.permission_denied_message)
            return redirect('auth_app:access-denied')
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_permission(self):
        """تحقق من الصلاحيات - يدعم صيغة Django (rent.add_receipt) والصيغة القديمة (can_process_payments)"""
        perms = self.permission_required or self.required_permission

        if isinstance(perms, str):
            perms = [perms]

        for perm in perms:
            if '.' in perm:
                # صيغة Django: rent.add_receipt
                if not self.request.user.has_perm(perm):
                    return False
            else:
                # صيغة قديمة: can_process_payments -> فحص UserProfile
                try:
                    profile = self.request.user.profile
                    if not getattr(profile, perm, False):
                        return False
                except Exception:
                    return False
        return True


class AuditLogMixin:
    """
    Mixin لتسجيل العمليات في سجل التدقيق
    """
    
    def log_action(self, action, obj, **kwargs):
        """
        تسجيل الإجراء في AuditLog
        """
        try:
            from audit_log.models import AuditLog
            
            # معالجة البيانات القديمة والجديدة
            old_data = kwargs.get('old_data', {})
            new_data = kwargs.get('new_data', {})
            
            # تحويل البيانات إلى JSON-safe format
            old_data = self._make_json_serializable(old_data)
            new_data = self._make_json_serializable(new_data)
            
            # إنشاء سجل التدقيق
            AuditLog.objects.create(
                user=self.request.user,
                model_name=obj.__class__.__name__,
                object_id=obj.pk,
                action=action,
                old_values=old_data,
                new_values=new_data,
                ip_address=self.get_client_ip(),
            )
        except Exception as e:
            # تسجيل الخطأ بدون إيقاف العملية
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to log action: {e}")
    
    def _make_json_serializable(self, data):
        """
        تحويل البيانات إلى JSON-safe format
        """
        if not data:
            return {}
        
        result = {}
        for key, value in data.items():
            # تحويل Decimal إلى float
            if isinstance(value, Decimal):
                result[key] = float(value)
            # تحويل date/datetime إلى string
            elif isinstance(value, (date, datetime)):
                result[key] = value.isoformat()
            # القيم الأخرى كما هي
            else:
                result[key] = value
        
        return result
    
    def get_client_ip(self):
        """الحصول على IP المستخدم"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', '')
        return ip