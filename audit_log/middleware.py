# ====================================
# 5. audit_log/middleware.py
# ====================================

from .signals import _thread_locals

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        _thread_locals.request = request
        
        try:
            response = self.get_response(request)
        finally:
            if hasattr(_thread_locals, 'request'):
                delattr(_thread_locals, 'request')
        
        return response
