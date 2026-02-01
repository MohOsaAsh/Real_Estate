# ====================================
# 4. audit_log/signals.py
# ====================================

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.contenttypes.models import ContentType
import threading
from decimal import Decimal
from datetime import datetime, date

_thread_locals = threading.local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

def get_current_user():
    request = get_current_request()
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None

def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def should_audit_model(model):
    excluded_models = ['AuditLog', 'Session', 'ContentType', 'Permission', 'LogEntry', 'Migration']
    excluded_apps = ['contenttypes', 'auth', 'sessions', 'admin']
    
    model_name = model.__name__
    app_label = model._meta.app_label
    
    return model_name not in excluded_models and app_label not in excluded_apps

def serialize_value(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, 'pk'):
        return {'id': value.pk, 'str': str(value)}
    if isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    return str(value)

def get_model_fields_dict(instance, exclude_fields=None):
    if exclude_fields is None:
        exclude_fields = ['password']
    
    data = {}
    for field in instance._meta.fields:
        if field.name not in exclude_fields:
            try:
                value = getattr(instance, field.name, None)
                data[field.name] = serialize_value(value)
            except Exception as e:
                data[field.name] = f"<خطأ: {str(e)}>"
    return data

def calculate_changes(old_data, new_data):
    if not old_data or not new_data:
        return None
    
    changes = {}
    for key in new_data:
        if key in old_data and old_data[key] != new_data[key]:
            changes[key] = {'old': old_data[key], 'new': new_data[key]}
    
    return changes if changes else None

_pre_save_instances = {}

@receiver(pre_save)
def store_pre_save_instance(sender, instance, **kwargs):
    if not should_audit_model(sender):
        return
    
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            key = f"{sender.__name__}_{instance.pk}_{id(instance)}"
            _pre_save_instances[key] = get_model_fields_dict(old_instance)
        except sender.DoesNotExist:
            pass

@receiver(post_save)
def log_post_save(sender, instance, created, **kwargs):
    from .models import AuditLog
    
    if not should_audit_model(sender):
        return
    
    request = get_current_request()
    user = get_current_user()
    
    action = 'create' if created else 'update'
    new_data = get_model_fields_dict(instance)
    old_data = None
    changes = None
    
    if not created:
        key = f"{sender.__name__}_{instance.pk}_{id(instance)}"
        old_data = _pre_save_instances.pop(key, None)
        if old_data:
            changes = calculate_changes(old_data, new_data)
    
    try:
        content_type = ContentType.objects.get_for_model(sender)
        
        AuditLog.objects.create(
            user=user,
            user_name=user.username if user else 'نظام',
            action=action,
            content_type=content_type,
            object_id=instance.pk,
            model_name=sender.__name__,
            object_repr=str(instance)[:500],
            old_values=old_data if not created else None,
            new_values=new_data,
            changes=changes,
            request_path=request.path if request else None,
            request_method=request.method if request else None,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Audit Log Error: {e}", exc_info=True)

@receiver(post_delete)
def log_post_delete(sender, instance, **kwargs):
    from .models import AuditLog
    
    if not should_audit_model(sender):
        return
    
    request = get_current_request()
    user = get_current_user()
    old_data = get_model_fields_dict(instance)
    
    try:
        AuditLog.objects.create(
            user=user,
            user_name=user.username if user else 'نظام',
            action='delete',
            model_name=sender.__name__,
            object_repr=str(instance)[:500],
            old_values=old_data,
            request_path=request.path if request else None,
            request_method=request.method if request else None,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Audit Log Error: {e}", exc_info=True)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    from .models import AuditLog
    
    try:
        AuditLog.objects.create(
            user=user,
            user_name=user.username,
            action='login',
            model_name='User',
            object_repr=f"تسجيل دخول: {user.username}",
            request_path=request.path if request else None,
            request_method=request.method if request else None,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Audit Log Error: {e}", exc_info=True)

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    from .models import AuditLog
    
    try:
        AuditLog.objects.create(
            user=user if user and user.is_authenticated else None,
            user_name=user.username if user and user.is_authenticated else 'مجهول',
            action='logout',
            model_name='User',
            object_repr=f"تسجيل خروج: {user.username if user and user.is_authenticated else 'مجهول'}",
            request_path=request.path if request else None,
            request_method=request.method if request else None,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Audit Log Error: {e}", exc_info=True)

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    from .models import AuditLog
    
    try:
        username = credentials.get('username', 'مجهول')
        AuditLog.objects.create(
            user=None,
            user_name=username,
            action='login_failed',
            model_name='User',
            object_repr=f"محاولة دخول فاشلة: {username}",
            request_path=request.path if request else None,
            request_method=request.method if request else None,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Audit Log Error: {e}", exc_info=True)
