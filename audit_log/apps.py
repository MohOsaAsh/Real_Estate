# ====================================
# 6. audit_log/apps.py
# ====================================

from django.apps import AppConfig

class AuditLogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit_log'
    verbose_name = 'نظام تسجيل التدقيق'
    
    def ready(self):
        import audit_log.signals