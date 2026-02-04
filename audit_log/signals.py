# ====================================
# 4. audit_log/signals.py
# ====================================

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from functools import lru_cache
import threading
from decimal import Decimal
from datetime import datetime, date

_thread_locals = threading.local()

# Cache for ContentType lookups to avoid repeated DB queries
@lru_cache(maxsize=100)
def get_content_type_cached(app_label, model_name):
    """Cached ContentType lookup to avoid repeated database queries"""
    try:
        return ContentType.objects.get(app_label=app_label, model=model_name.lower())
    except ContentType.DoesNotExist:
        return None

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
            # Use only() to fetch minimal fields needed for audit
            old_instance = sender.objects.only(*[f.name for f in sender._meta.fields]).get(pk=instance.pk)
            key = f"{sender.__name__}_{instance.pk}_{id(instance)}"
            _pre_save_instances[key] = get_model_fields_dict(old_instance)
        except sender.DoesNotExist:
            pass
        except Exception:
            # Don't let audit failures affect the main operation
            pass

@receiver(post_save)
def log_post_save(sender, instance, created, **kwargs):
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
            # Skip if no actual changes
            if not changes:
                return

    # Capture values before on_commit (they may change)
    audit_data = {
        'user': user,
        'user_name': user.username if user else 'نظام',
        'action': action,
        'app_label': sender._meta.app_label,
        'model_name_lower': sender.__name__.lower(),
        'model_name': sender.__name__,
        'object_id': instance.pk,
        'object_repr': str(instance)[:500],
        'old_values': old_data if not created else None,
        'new_values': new_data,
        'changes': changes,
        'request_path': request.path if request else None,
        'request_method': request.method if request else None,
        'ip_address': get_client_ip(request) if request else None,
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
    }

    def create_audit_log():
        from .models import AuditLog
        try:
            content_type = get_content_type_cached(audit_data['app_label'], audit_data['model_name_lower'])
            AuditLog.objects.create(
                user=audit_data['user'],
                user_name=audit_data['user_name'],
                action=audit_data['action'],
                content_type=content_type,
                object_id=audit_data['object_id'],
                model_name=audit_data['model_name'],
                object_repr=audit_data['object_repr'],
                old_values=audit_data['old_values'],
                new_values=audit_data['new_values'],
                changes=audit_data['changes'],
                request_path=audit_data['request_path'],
                request_method=audit_data['request_method'],
                ip_address=audit_data['ip_address'],
                user_agent=audit_data['user_agent'],
            )
        except Exception:
            pass  # Silent fail - don't affect main operation

    # Defer audit log creation until after transaction commits
    transaction.on_commit(create_audit_log)

@receiver(post_delete)
def log_post_delete(sender, instance, **kwargs):
    if not should_audit_model(sender):
        return

    request = get_current_request()
    user = get_current_user()
    old_data = get_model_fields_dict(instance)

    audit_data = {
        'user': user,
        'user_name': user.username if user else 'نظام',
        'model_name': sender.__name__,
        'object_repr': str(instance)[:500],
        'old_values': old_data,
        'request_path': request.path if request else None,
        'request_method': request.method if request else None,
        'ip_address': get_client_ip(request) if request else None,
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
    }

    def create_audit_log():
        from .models import AuditLog
        try:
            AuditLog.objects.create(
                user=audit_data['user'],
                user_name=audit_data['user_name'],
                action='delete',
                model_name=audit_data['model_name'],
                object_repr=audit_data['object_repr'],
                old_values=audit_data['old_values'],
                request_path=audit_data['request_path'],
                request_method=audit_data['request_method'],
                ip_address=audit_data['ip_address'],
                user_agent=audit_data['user_agent'],
            )
        except Exception:
            pass

    transaction.on_commit(create_audit_log)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    audit_data = {
        'user': user,
        'user_name': user.username,
        'request_path': request.path if request else None,
        'request_method': request.method if request else None,
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
    }

    def create_audit_log():
        from .models import AuditLog
        try:
            AuditLog.objects.create(
                user=audit_data['user'],
                user_name=audit_data['user_name'],
                action='login',
                model_name='User',
                object_repr=f"تسجيل دخول: {audit_data['user_name']}",
                request_path=audit_data['request_path'],
                request_method=audit_data['request_method'],
                ip_address=audit_data['ip_address'],
                user_agent=audit_data['user_agent'],
            )
        except Exception:
            pass

    transaction.on_commit(create_audit_log)

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    user_name = user.username if user and user.is_authenticated else 'مجهول'
    audit_data = {
        'user': user if user and user.is_authenticated else None,
        'user_name': user_name,
        'request_path': request.path if request else None,
        'request_method': request.method if request else None,
        'ip_address': get_client_ip(request) if request else None,
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
    }

    def create_audit_log():
        from .models import AuditLog
        try:
            AuditLog.objects.create(
                user=audit_data['user'],
                user_name=audit_data['user_name'],
                action='logout',
                model_name='User',
                object_repr=f"تسجيل خروج: {audit_data['user_name']}",
                request_path=audit_data['request_path'],
                request_method=audit_data['request_method'],
                ip_address=audit_data['ip_address'],
                user_agent=audit_data['user_agent'],
            )
        except Exception:
            pass

    transaction.on_commit(create_audit_log)

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'مجهول')
    audit_data = {
        'user_name': username,
        'request_path': request.path if request else None,
        'request_method': request.method if request else None,
        'ip_address': get_client_ip(request) if request else None,
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
    }

    def create_audit_log():
        from .models import AuditLog
        try:
            AuditLog.objects.create(
                user=None,
                user_name=audit_data['user_name'],
                action='login_failed',
                model_name='User',
                object_repr=f"محاولة دخول فاشلة: {audit_data['user_name']}",
                request_path=audit_data['request_path'],
                request_method=audit_data['request_method'],
                ip_address=audit_data['ip_address'],
                user_agent=audit_data['user_agent'],
            )
        except Exception:
            pass

    transaction.on_commit(create_audit_log)
